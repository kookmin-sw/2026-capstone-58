"""
YouTube Data API v3 공통 모듈
- collect.py, lambda_function.py에서 공유
"""

import re
from datetime import datetime, timezone

import requests


CATEGORIES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "19": "Travel & Events",
    "20": "Gaming", "22": "People & Blogs", "23": "Comedy",
    "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology",
}

BASE = "https://www.googleapis.com/youtube/v3"


def parse_duration(iso: str) -> int:
    """PT1H2M30S → 초 변환."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def discover_channels(api_key: str, category_id: str, region: str = "KR", max_pages: int = 4) -> list[str]:
    """mostPopular 영상에서 유니크 채널 ID 추출. 페이지당 1유닛."""
    channel_ids = _discover_by_popular(api_key, category_id, region, max_pages)
    if not channel_ids:
        channel_ids = _discover_by_search(api_key, category_id, region, max_pages)
    return list(channel_ids)


def _discover_by_popular(api_key, category_id, region, max_pages):
    channel_ids = set()
    page_token = None
    for _ in range(max_pages):
        params = {
            "key": api_key, "chart": "mostPopular",
            "videoCategoryId": category_id, "regionCode": region,
            "part": "snippet", "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(f"{BASE}/videos", params=params).json()
        for item in r.get("items", []):
            channel_ids.add(item["snippet"]["channelId"])
        page_token = r.get("nextPageToken")
        if not page_token:
            break
    return channel_ids


def _discover_by_search(api_key, category_id, region, max_pages):
    channel_ids = set()
    page_token = None
    for _ in range(max_pages):
        params = {
            "key": api_key, "type": "video",
            "videoCategoryId": category_id, "regionCode": region,
            "part": "snippet", "maxResults": 50, "order": "viewCount",
        }
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(f"{BASE}/search", params=params).json()
        for item in r.get("items", []):
            channel_ids.add(item["snippet"]["channelId"])
        page_token = r.get("nextPageToken")
        if not page_token:
            break
    return channel_ids


def get_channel(api_key: str, channel_id: str) -> dict | None:
    """channels.list — 1유닛."""
    r = requests.get(f"{BASE}/channels", params={
        "key": api_key, "id": channel_id,
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


def get_video_ids(api_key: str, uploads_playlist: str, max_results: int = 50) -> list[str]:
    """playlistItems.list — 1유닛. 최근 영상 ID 최대 50개."""
    r = requests.get(f"{BASE}/playlistItems", params={
        "key": api_key, "playlistId": uploads_playlist,
        "part": "contentDetails", "maxResults": min(max_results, 50),
    }).json()
    return [item["contentDetails"]["videoId"] for item in r.get("items", [])]


def get_videos(api_key: str, video_ids: list[str], include_details: bool = False) -> list[dict]:
    """videos.list — 1유닛 (최대 50개 배치). 영상 상세 정보."""
    if not video_ids:
        return []
    parts = "snippet,statistics,contentDetails"
    if include_details:
        parts += ",topicDetails"
    r = requests.get(f"{BASE}/videos", params={
        "key": api_key, "id": ",".join(video_ids), "part": parts,
    }).json()
    now = datetime.now(timezone.utc)
    videos = []
    for item in r.get("items", []):
        stats = item["statistics"]
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        duration_sec = parse_duration(item["contentDetails"].get("duration", "PT0S"))

        video = {
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "published_at": item["snippet"]["publishedAt"],
            "category_id": item["snippet"].get("categoryId", ""),
            "duration_sec": duration_sec,
            "is_short": duration_sec < 60,
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
        }

        # 로컬 수집용 추가 필드
        if include_details:
            published = datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00"))
            video["days_since_upload"] = max((now - published).days, 1)
            video["tags"] = "|".join(item["snippet"].get("tags", []))
            topics = item.get("topicDetails", {}).get("topicCategories", [])
            video["topic_categories"] = "|".join(topics)

        videos.append(video)
    return videos


def resolve_channel_id(api_key: str, channel_input: str) -> str | None:
    """@handle, URL, 채널ID → 채널ID로 변환."""
    s = channel_input.strip().rstrip("/")
    if "youtube.com" in s:
        if "/@" in s:
            s = "@" + s.split("/@")[-1]
        elif "/channel/" in s:
            return s.split("/channel/")[-1].split("/")[0]
    if s.startswith("@"):
        r = requests.get(f"{BASE}/channels", params={
            "key": api_key, "forHandle": s, "part": "id",
        }).json()
        items = r.get("items", [])
        return items[0]["id"] if items else None
    if s.startswith("UC") and len(s) == 24:
        return s
    return None


def sub_tier(subscriber_count: int) -> str:
    """구독자 수 → 구간 분류."""
    if subscriber_count < 50000:
        return "S"
    if subscriber_count < 200000:
        return "M"
    if subscriber_count < 500000:
        return "L"
    return "XL"
