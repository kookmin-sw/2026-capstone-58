"""
Lambda 함수: YouTube 데이터 수집 → 백분위 테이블 계산 → S3 저장
- percentiles/{날짜}.json  — 백분위 테이블 이력
- summaries/{날짜}.json    — 카테고리별 요약 통계
- latest.json              — 최신 백분위 (crit-server가 읽음)
"""

import json
import os
from datetime import datetime, timezone

import boto3

from youtube_api import (
    CATEGORIES, discover_channels, get_channel, get_video_ids, get_videos, sub_tier,
)

# ── 환경변수 ──
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
S3_BUCKET = os.environ["S3_BUCKET"]

s3 = boto3.client("s3")


# ── 수집 ──────────────────────────────────────────────────────────

def collect_all_categories(category_ids=None):
    if category_ids is None:
        category_ids = list(CATEGORIES.keys())

    all_videos = []
    total_channels = 0
    cat_stats = {}

    for cat_id in category_ids:
        channel_ids = discover_channels(YOUTUBE_API_KEY, cat_id)
        cat_channels = 0
        cat_videos = 0
        cat_subs = []

        for ch_id in channel_ids:
            ch = get_channel(YOUTUBE_API_KEY, ch_id)
            if not ch or ch["subscriber_count"] == 0:
                continue
            video_ids = get_video_ids(YOUTUBE_API_KEY, ch["uploads_playlist"])
            videos = get_videos(YOUTUBE_API_KEY, video_ids)

            # 채널 평균 조회수 계산 (vs_channel_avg용)
            channel_views = [v["view_count"] for v in videos if v["view_count"] > 0]
            channel_avg_views = sum(channel_views) / len(channel_views) if channel_views else 1

            for v in videos:
                if v["view_count"] == 0:
                    continue
                v["subscriber_count"] = ch["subscriber_count"]
                v["vps"] = v["view_count"] / ch["subscriber_count"]
                v["engagement_rate"] = (v["like_count"] + v["comment_count"]) / v["view_count"]
                v["like_rate"] = v["like_count"] / v["view_count"]
                v["vs_channel_avg"] = v["view_count"] / channel_avg_views
                v["daily_views"] = v["view_count"] / max(v.get("days_since_upload", 1), 1)
                all_videos.append(v)
            cat_channels += 1
            cat_videos += len(videos)
            cat_subs.append(ch["subscriber_count"])

        if cat_channels > 0:
            cat_vids = [v for v in all_videos if v["category_id"] == cat_id]
            shorts = [v for v in cat_vids if v["is_short"]]
            longs = [v for v in cat_vids if not v["is_short"]]
            cat_stats[cat_id] = {
                "name": CATEGORIES.get(cat_id, cat_id),
                "channels": cat_channels,
                "videos": cat_videos,
                "short_count": len(shorts),
                "long_count": len(longs),
                "avg_subscribers": int(sum(cat_subs) / len(cat_subs)),
                "avg_vps": round(sum(v["vps"] for v in cat_vids) / max(len(cat_vids), 1), 4),
            }
        total_channels += cat_channels

    return all_videos, total_channels, category_ids, cat_stats


# ── 백분위 계산 ───────────────────────────────────────────────────

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
        for metric_name, metric_key in [("vps", "vps"), ("engagement", "engagement_rate"), ("like_rate", "like_rate"), ("vs_channel_avg", "vs_channel_avg"), ("daily_views", "daily_views")]:
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

    if category_ids is None:
        category_ids = list(CATEGORIES.keys())

    videos, total_channels, categories, cat_stats = collect_all_categories(category_ids)

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
