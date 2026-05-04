"""
Lambda 함수: YouTube 데이터 수집 → 백분위 테이블 계산 → S3 저장
- percentiles/{날짜}.json  — 백분위 테이블 이력
- summaries/{날짜}.json    — 카테고리별 요약 통계
- latest.json              — 최신 백분위 (crit-server가 읽음)
"""

import json
import os
import re
from datetime import datetime, timezone

import boto3
import requests

# ── 환경변수 ──
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
S3_BUCKET = os.environ["S3_BUCKET"]

BASE = "https://www.googleapis.com/youtube/v3"
s3 = boto3.client("s3")

CATEGORIES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "19": "Travel & Events",
    "20": "Gaming", "22": "People & Blogs", "23": "Comedy",
    "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology",
}


# ── YouTube API ───────────────────────────────────────────────────

def discover_channels(category_id, max_pages=4):
    """mostPopularで채널 발견. 결과 0이면 search.list로 fallback."""
    channel_ids = _discover_by_popular(category_id, max_pages)
    if not channel_ids:
        channel_ids = _discover_by_search(category_id, max_pages)
    return list(channel_ids)


def _discover_by_popular(category_id, max_pages):
    channel_ids = set()
    page_token = None
    for _ in range(max_pages):
        params = {
            "key": YOUTUBE_API_KEY, "chart": "mostPopular",
            "videoCategoryId": category_id, "regionCode": "KR",
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


def _discover_by_search(category_id, max_pages):
    channel_ids = set()
    page_token = None
    for _ in range(max_pages):
        params = {
            "key": YOUTUBE_API_KEY, "type": "video",
            "videoCategoryId": category_id, "regionCode": "KR",
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


def get_channel(channel_id):
    r = requests.get(f"{BASE}/channels", params={
        "key": YOUTUBE_API_KEY, "id": channel_id,
        "part": "snippet,statistics,contentDetails",
    }).json()
    if not r.get("items"):
        return None
    item = r["items"][0]
    stats = item["statistics"]
    return {
        "channel_id": item["id"],
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "uploads_playlist": item["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def get_video_ids(uploads_playlist):
    r = requests.get(f"{BASE}/playlistItems", params={
        "key": YOUTUBE_API_KEY, "playlistId": uploads_playlist,
        "part": "contentDetails", "maxResults": 50,
    }).json()
    return [item["contentDetails"]["videoId"] for item in r.get("items", [])]


def get_videos(video_ids):
    if not video_ids:
        return []
    r = requests.get(f"{BASE}/videos", params={
        "key": YOUTUBE_API_KEY, "id": ",".join(video_ids),
        "part": "snippet,statistics,contentDetails",
    }).json()
    videos = []
    for item in r.get("items", []):
        stats = item["statistics"]
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        dur = _parse_duration(item["contentDetails"].get("duration", "PT0S"))
        if views == 0:
            continue
        videos.append({
            "view_count": views, "like_count": likes, "comment_count": comments,
            "duration_sec": dur, "category_id": item["snippet"].get("categoryId", ""),
            "is_short": dur < 60,
        })
    return videos


def _parse_duration(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


# ── 수집 ──────────────────────────────────────────────────────────

def collect_all_categories(category_ids=None):
    if category_ids is None:
        category_ids = list(CATEGORIES.keys())

    all_videos = []
    total_channels = 0
    cat_stats = {}

    for cat_id in category_ids:
        channel_ids = discover_channels(cat_id)
        cat_channels = 0
        cat_videos = 0
        cat_subs = []

        for ch_id in channel_ids:
            ch = get_channel(ch_id)
            if not ch or ch["subscriber_count"] == 0:
                continue
            video_ids = get_video_ids(ch["uploads_playlist"])
            videos = get_videos(video_ids)
            for v in videos:
                v["subscriber_count"] = ch["subscriber_count"]
                v["vps"] = v["view_count"] / ch["subscriber_count"]
                v["engagement_rate"] = (v["like_count"] + v["comment_count"]) / v["view_count"]
                v["like_rate"] = v["like_count"] / v["view_count"]
            all_videos.extend(videos)
            cat_channels += 1
            cat_videos += len(videos)
            cat_subs.append(ch["subscriber_count"])

        if cat_channels > 0:
            shorts = [v for v in all_videos if v["category_id"] == cat_id and v["is_short"]]
            longs = [v for v in all_videos if v["category_id"] == cat_id and not v["is_short"]]
            cat_stats[cat_id] = {
                "name": CATEGORIES.get(cat_id, cat_id),
                "channels": cat_channels,
                "videos": cat_videos,
                "short_count": len(shorts),
                "long_count": len(longs),
                "avg_subscribers": int(sum(cat_subs) / len(cat_subs)),
                "avg_vps": round(sum(v["vps"] for v in shorts + longs) / max(len(shorts + longs), 1), 4),
            }
        total_channels += cat_channels

    return all_videos, total_channels, category_ids, cat_stats


# ── 백분위 계산 ───────────────────────────────────────────────────

def sub_tier(s):
    if s < 50000: return "S"
    if s < 200000: return "M"
    if s < 500000: return "L"
    return "XL"


def build_percentile_tables(videos):
    groups = {}
    for v in videos:
        key = f"{sub_tier(v['subscriber_count'])}_{int(v['is_short'])}_{v['category_id']}"
        groups.setdefault(key, []).append(v)

    tables = {}
    for key, data in groups.items():
        if len(data) < 20:
            continue
        tables[key] = {"sample_count": len(data)}
        for metric_name, metric_key in [("vps", "vps"), ("engagement", "engagement_rate"), ("like_rate", "like_rate")]:
            vals = sorted([d[metric_key] for d in data])
            n = len(vals)
            tables[key][metric_name] = [vals[min(int(n * p / 100), n - 1)] for p in range(101)]

    return tables


# ── S3 저장 (기존 데이터 병합) ─────────────────────────────────────

def load_existing_from_s3():
    """S3에서 기존 latest.json 로드. 없으면 빈 구조 반환."""
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key="latest.json")
        return json.loads(obj["Body"].read())
    except Exception:
        return {"collected_at": None, "total_channels": 0, "total_videos": 0, "groups": 0, "tables": {}, "category_timestamps": {}}


def save_to_s3(new_tables, cat_stats, total_channels, total_videos, categories):
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    now = datetime.now(timezone.utc).isoformat()

    # 기존 데이터 로드
    existing = load_existing_from_s3()
    merged_tables = existing.get("tables", {})
    cat_timestamps = existing.get("category_timestamps", {})

    # 새 테이블 병합 (같은 키는 덮어쓰기)
    merged_tables.update(new_tables)

    # 수집한 카테고리의 타임스탬프 갱신
    for cat_id in categories:
        cat_timestamps[cat_id] = now

    percentile_data = {
        "collected_at": now,
        "total_channels": existing.get("total_channels", 0) + total_channels,
        "total_videos": existing.get("total_videos", 0) + total_videos,
        "groups": len(merged_tables),
        "tables": merged_tables,
        "category_timestamps": cat_timestamps,
    }

    summary_data = {
        "collected_at": now,
        "total_channels": total_channels,
        "total_videos": total_videos,
        "quota_used": total_channels * 3 + len(categories) * 4,
        "categories": cat_stats,
    }

    # 날짜별 이력
    s3.put_object(Bucket=S3_BUCKET, Key=f"percentiles/{today}.json",
                  Body=json.dumps(percentile_data, ensure_ascii=False), ContentType="application/json")
    s3.put_object(Bucket=S3_BUCKET, Key=f"summaries/{today}.json",
                  Body=json.dumps(summary_data, ensure_ascii=False), ContentType="application/json")

    # 최신 (crit-server가 읽는 파일)
    s3.put_object(Bucket=S3_BUCKET, Key="latest.json",
                  Body=json.dumps(percentile_data, ensure_ascii=False), ContentType="application/json")

    return {"percentiles": f"percentiles/{today}.json", "summaries": f"summaries/{today}.json", "latest": "latest.json"}


# ── Lambda 핸들러 ─────────────────────────────────────────────────

def lambda_handler(event, context):
    category_ids = None
    if event and isinstance(event, dict):
        category_ids = event.get("categories")

    # 전체 카테고리 요청 시, 7일 이내 수집된 카테고리는 스킵
    if category_ids is None:
        category_ids = list(CATEGORIES.keys())

    force = event.get("force", False) if event and isinstance(event, dict) else False

    existing = load_existing_from_s3()
    cat_timestamps = existing.get("category_timestamps", {})
    now = datetime.now(timezone.utc)
    stale_days = 7

    fresh = []
    skipped = []
    for cat_id in category_ids:
        if not force:
            ts = cat_timestamps.get(cat_id)
            if ts:
                collected = datetime.fromisoformat(ts)
                age = (now - collected).days
                if age < stale_days:
                    skipped.append(cat_id)
                    continue
        fresh.append(cat_id)

    if not fresh:
        return {"statusCode": 200, "body": json.dumps({
            "message": "All categories are fresh (< 7 days)",
            "skipped": skipped,
        })}

    videos, total_channels, categories, cat_stats = collect_all_categories(fresh)

    if not videos:
        return {"statusCode": 200, "body": json.dumps({"message": "No videos collected"})}

    tables = build_percentile_tables(videos)
    saved = save_to_s3(tables, cat_stats, total_channels, len(videos), categories)

    result = {
        "message": "Collection complete",
        "channels": total_channels,
        "videos": len(videos),
        "categories": categories,
        "skipped": skipped,
        "groups": len(tables),
        "s3_files": saved,
    }
    return {"statusCode": 200, "body": json.dumps(result)}
