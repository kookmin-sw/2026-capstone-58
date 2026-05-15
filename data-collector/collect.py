"""
YouTube 채널 데이터 수집기 (로컬용)
- 채널당 3유닛 (channels + playlistItems + videos)
- CSV 저장
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from youtube_api import (
    CATEGORIES, get_channel, get_video_ids, get_videos,
    resolve_channel_id, discover_channels,
)

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


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

    # 숏폼/롱폼 분류
    for v in videos:
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


# ── 메인 ──────────────────────────────────────────────────────────

def collect_channel(channel_input: str) -> list[dict]:
    """채널 1개 수집 (3유닛). 수집 결과 반환 + CSV 저장."""
    print(f"[1/3] 채널 정보 조회: {channel_input}")
    channel_id = resolve_channel_id(API_KEY, channel_input)
    if not channel_id:
        print(f"  ✗ 채널을 찾을 수 없습니다: {channel_input}")
        return []
    channel = get_channel(API_KEY, channel_id)
    if not channel:
        print(f"  ✗ 채널 정보를 가져올 수 없습니다: {channel_input}")
        return []
    print(f"  ✓ {channel['channel_title']} (구독자 {channel['subscriber_count']:,})")

    print(f"[2/3] 영상 ID 목록 조회...")
    video_ids = get_video_ids(API_KEY, channel["uploads_playlist"])
    print(f"  ✓ {len(video_ids)}개 영상 발견")

    print(f"[3/3] 영상 상세 정보 조회...")
    videos = get_videos(API_KEY, video_ids, include_details=True)
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

    channels = sys.argv[1:] or ["@MBCentertainment"]

    total_videos = 0
    for ch in channels:
        videos = collect_channel(ch)
        total_videos += len(videos)
        print()

    print(f"=== 수집 완료: {len(channels)}개 채널, {total_videos}개 영상 ===")
    print(f"=== 사용 쿼터: ~{len(channels) * 3}유닛 ===")


if __name__ == "__main__":
    main()
