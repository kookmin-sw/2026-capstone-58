"""
YouTube 채널 데이터 수집기
- channels.list (1유닛): 채널 메타 정보
- playlistItems.list (1유닛): 영상 ID 목록
- videos.list (1유닛): 영상 상세 정보 (50개 배치)
= 채널당 3유닛, 하루 ~3,300채널 수집 가능
"""

import csv
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE = "https://www.googleapis.com/youtube/v3"
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ── YouTube API 호출 ──────────────────────────────────────────────

def get_channel(channel_input: str) -> dict | None:
    """channels.list — 1유닛. @handle, 채널ID, URL 모두 지원."""
    channel_id = _resolve_channel_id(channel_input)
    if not channel_id:
        return None
    r = requests.get(f"{BASE}/channels", params={
        "key": API_KEY,
        "id": channel_id,
        "part": "snippet,statistics,contentDetails",
    }).json()
    if not r.get("items"):
        return None
    item = r["items"][0]
    stats = item["statistics"]
    return {
        "channel_id": item["id"],
        "channel_title": item["snippet"]["title"],
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "total_view_count": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "created_at": item["snippet"]["publishedAt"],
        "uploads_playlist": item["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def get_video_ids(uploads_playlist: str, max_results: int = 50) -> list[str]:
    """playlistItems.list — 1유닛. 최근 영상 ID 최대 50개."""
    r = requests.get(f"{BASE}/playlistItems", params={
        "key": API_KEY,
        "playlistId": uploads_playlist,
        "part": "contentDetails",
        "maxResults": min(max_results, 50),
    }).json()
    return [item["contentDetails"]["videoId"] for item in r.get("items", [])]


def get_videos(video_ids: list[str]) -> list[dict]:
    """videos.list — 1유닛 (최대 50개 배치). 영상 상세 정보."""
    if not video_ids:
        return []
    r = requests.get(f"{BASE}/videos", params={
        "key": API_KEY,
        "id": ",".join(video_ids),
        "part": "snippet,statistics,contentDetails,topicDetails",
    }).json()
    now = datetime.now(timezone.utc)
    videos = []
    for item in r.get("items", []):
        stats = item["statistics"]
        published = datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00"))
        days_since = max((now - published).days, 1)
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        duration_sec = _parse_duration(item["contentDetails"].get("duration", "PT0S"))
        topics = item.get("topicDetails", {}).get("topicCategories", [])
        videos.append({
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "published_at": item["snippet"]["publishedAt"],
            "days_since_upload": days_since,
            "category_id": item["snippet"].get("categoryId", ""),
            "duration_sec": duration_sec,
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
            "tags": "|".join(item["snippet"].get("tags", [])),
            "topic_categories": "|".join(topics),
        })
    return videos


# ── 파생 지표 계산 ────────────────────────────────────────────────

def _calc_stats(views_list: list[int]) -> tuple:
    """조회수 리스트 → (평균, 중앙값, 표준편차)."""
    if not views_list:
        return 1, 1, 0
    avg = sum(views_list) / len(views_list)
    s = sorted(views_list)
    n = len(s)
    med = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2
    std = (sum((v - avg) ** 2 for v in views_list) / n) ** 0.5
    return avg or 1, med or 1, std


def compute_metrics(channel: dict, videos: list[dict]) -> list[dict]:
    """채널 정보 + 영상 원시 데이터 → 파생 지표 추가. 숏폼/롱폼 분리 계산."""
    if not videos:
        return []
    subs = channel["subscriber_count"] or 1

    # 숏폼/롱폼 분류 (60초 기준)
    for v in videos:
        v["is_short"] = 1 if v["duration_sec"] < 60 else 0
        dur = v["duration_sec"]
        v["duration_category"] = ("short" if dur < 60 else
                                  "medium" if dur < 600 else
                                  "long" if dur < 1800 else "very_long")

    shorts = [v for v in videos if v["is_short"]]
    longs = [v for v in videos if not v["is_short"]]

    # 숏폼/롱폼 각각 통계
    s_avg, s_med, s_std = _calc_stats([v["view_count"] for v in shorts])
    l_avg, l_med, l_std = _calc_stats([v["view_count"] for v in longs])
    # 전체 통계 (채널 전체 비교용)
    a_avg, a_med, a_std = _calc_stats([v["view_count"] for v in videos])

    for v in videos:
        views = v["view_count"] or 1
        likes = v["like_count"]
        comments = v["comment_count"]
        avg, med, std = (s_avg, s_med, s_std) if v["is_short"] else (l_avg, l_med, l_std)

        # 채널 메타
        v["channel_id"] = channel["channel_id"]
        v["channel_title"] = channel["channel_title"]
        v["subscriber_count"] = subs

        # 영상 단위 지표
        v["views_per_sub"] = round(views / subs, 6)
        v["engagement_rate"] = round((likes + comments) / views, 6) if views else 0
        v["like_rate"] = round(likes / views, 6) if views else 0
        v["comment_like_ratio"] = round(comments / likes, 6) if likes else 0
        v["daily_views"] = round(views / v["days_since_upload"], 2)

        # 같은 형식(숏폼/롱폼) 내 상대 지표
        v["vs_channel_avg"] = round(views / avg, 4)
        v["vs_channel_median"] = round(views / med, 4)
        v["z_score"] = round((views - avg) / std, 4) if std else 0

        # 전체 대비 지표
        v["vs_all_avg"] = round(views / a_avg, 4)

    # 숏폼/롱폼 각각 순위 계산
    for group in (shorts, longs):
        ranked = sorted(enumerate(group), key=lambda x: x[1]["view_count"], reverse=True)
        for rank, (idx, _) in enumerate(ranked, 1):
            group[idx]["channel_rank"] = rank
            group[idx]["channel_percentile"] = round(1 - (rank - 1) / len(group), 4)

    return videos


# ── CSV 저장 ──────────────────────────────────────────────────────

CSV_FIELDS = [
    "channel_id", "channel_title", "subscriber_count",
    "video_id", "title", "published_at", "days_since_upload",
    "category_id", "duration_sec", "duration_category", "is_short",
    "view_count", "like_count", "comment_count", "tags", "topic_categories",
    # 파생 지표 (숏폼/롱폼 분리 계산)
    "views_per_sub", "engagement_rate", "like_rate", "comment_like_ratio",
    "daily_views", "vs_channel_avg", "vs_channel_median", "vs_all_avg",
    "channel_rank", "channel_percentile", "z_score",
]


def save_csv(videos: list[dict], filepath: Path):
    """CSV에 append. 파일 없으면 헤더 포함 생성."""
    exists = filepath.exists()
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerows(videos)


# ── mostPopular로 카테고리별 채널 추출 ─────────────────────────────

CATEGORIES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "19": "Travel & Events",
    "20": "Gaming", "22": "People & Blogs", "23": "Comedy",
    "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology",
}


def discover_channels(category_id: str, region: str = "KR", max_pages: int = 4) -> list[str]:
    """mostPopular 영상에서 유니크 채널 ID 추출. 페이지당 1유닛."""
    channel_ids = set()
    page_token = None
    for page in range(max_pages):
        params = {
            "key": API_KEY,
            "chart": "mostPopular",
            "videoCategoryId": category_id,
            "regionCode": region,
            "part": "snippet",
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(f"{BASE}/videos", params=params).json()
        for item in r.get("items", []):
            channel_ids.add(item["snippet"]["channelId"])
        page_token = r.get("nextPageToken")
        if not page_token:
            break
    return list(channel_ids)


# ── 유틸 ──────────────────────────────────────────────────────────

def _resolve_channel_id(channel_input: str) -> str | None:
    """@handle, URL, 채널ID → 채널ID로 변환."""
    s = channel_input.strip().rstrip("/")
    # URL에서 추출
    if "youtube.com" in s:
        if "/@" in s:
            s = "@" + s.split("/@")[-1]
        elif "/channel/" in s:
            return s.split("/channel/")[-1].split("/")[0]
    # @handle → API로 채널ID 조회
    if s.startswith("@"):
        r = requests.get(f"{BASE}/channels", params={
            "key": API_KEY, "forHandle": s, "part": "id",
        }).json()
        items = r.get("items", [])
        return items[0]["id"] if items else None
    # 이미 채널ID
    if s.startswith("UC") and len(s) == 24:
        return s
    return None


def _parse_duration(iso: str) -> int:
    """PT1H2M30S → 초 변환."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


# ── 메인 ──────────────────────────────────────────────────────────

def collect_channel(channel_input: str) -> list[dict]:
    """채널 1개 수집 (3유닛). 수집 결과 반환 + CSV 저장."""
    print(f"[1/3] 채널 정보 조회: {channel_input}")
    channel = get_channel(channel_input)
    if not channel:
        print(f"  ✗ 채널을 찾을 수 없습니다: {channel_input}")
        return []
    print(f"  ✓ {channel['channel_title']} (구독자 {channel['subscriber_count']:,})")

    print(f"[2/3] 영상 ID 목록 조회...")
    video_ids = get_video_ids(channel["uploads_playlist"])
    print(f"  ✓ {len(video_ids)}개 영상 발견")

    print(f"[3/3] 영상 상세 정보 조회...")
    videos = get_videos(video_ids)
    print(f"  ✓ {len(videos)}개 영상 데이터 수집 완료")

    videos = compute_metrics(channel, videos)

    today = datetime.now().strftime("%Y%m%d")
    filepath = DATA_DIR / f"videos_{today}.csv"
    save_csv(videos, filepath)
    print(f"  → 저장: {filepath} ({len(videos)}행 추가)")

    return videos


def main():
    if not API_KEY:
        print("YOUTUBE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    # 인자로 채널 목록 전달, 없으면 예시 채널
    channels = sys.argv[1:] or [
        "@MBCentertainment",  # 예시: MBC 엔터테인먼트
    ]

    total_videos = 0
    for ch in channels:
        videos = collect_channel(ch)
        total_videos += len(videos)
        print()

    print(f"=== 수집 완료: {len(channels)}개 채널, {total_videos}개 영상 ===")
    print(f"=== 사용 쿼터: ~{len(channels) * 3}유닛 ===")


if __name__ == "__main__":
    main()
