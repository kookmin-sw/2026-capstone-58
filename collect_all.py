"""
전체 카테고리 일괄 수집
- mostPopular로 카테고리별 채널 발견 → 채널별 영상 수집
- 카테고리별 CSV 분리 저장
"""

import sys
import time
from datetime import datetime

from dotenv import load_dotenv

from collect import API_KEY, DATA_DIR, compute_metrics, save_csv
from youtube_api import CATEGORIES, discover_channels, get_channel, get_video_ids, get_videos

load_dotenv()


def collect_category(cat_id: str, cat_name: str) -> dict:
    """카테고리 1개 수집. 채널 발견 → 영상 수집."""
    print(f"\n{'='*60}")
    print(f"카테고리 [{cat_id}] {cat_name}")
    print(f"{'='*60}")

    # 1) 채널 발견
    print(f"[채널 발견] mostPopular에서 채널 추출 중...")
    channel_ids = discover_channels(API_KEY, cat_id)
    print(f"  ✓ {len(channel_ids)}개 유니크 채널 발견")

    # 2) 채널별 영상 수집
    today = datetime.now().strftime("%Y%m%d")
    filepath = DATA_DIR / f"cat_{cat_id}_{cat_name.replace(' & ', '_').replace(' ', '_').lower()}_{today}.csv"

    total_videos = 0
    success = 0
    for i, ch_id in enumerate(channel_ids, 1):
        print(f"  [{i}/{len(channel_ids)}] {ch_id}", end=" ")
        channel = get_channel(API_KEY, ch_id)
        if not channel:
            print("✗ 조회 실패")
            continue
        print(f"→ {channel['channel_title']} (구독자 {channel['subscriber_count']:,})", end=" ")

        video_ids = get_video_ids(API_KEY, channel["uploads_playlist"])
        videos = get_videos(API_KEY, video_ids, include_details=True)
        videos = compute_metrics(channel, videos)
        save_csv(videos, filepath)

        total_videos += len(videos)
        success += 1
        print(f"✓ {len(videos)}개 영상")

        time.sleep(0.1)  # API rate limit 방지

    print(f"\n  → 저장: {filepath}")
    print(f"  → {success}개 채널, {total_videos}개 영상")

    return {"category": cat_name, "channels": success, "videos": total_videos}


def main():
    if not API_KEY:
        print("YOUTUBE_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    # 특정 카테고리만 지정 가능: python3 collect_all.py 20 28
    target_ids = sys.argv[1:] if len(sys.argv) > 1 else list(CATEGORIES.keys())

    results = []
    quota_used = 0
    for cat_id in target_ids:
        cat_name = CATEGORIES.get(cat_id, f"Unknown({cat_id})")
        stats = collect_category(cat_id, cat_name)
        results.append(stats)
        # 쿼터 추정: discover(~4) + 채널당 3
        quota_used += 4 + stats["channels"] * 3

    # 요약
    print(f"\n{'='*60}")
    print(f"전체 수집 완료")
    print(f"{'='*60}")
    total_ch = sum(r["channels"] for r in results)
    total_vid = sum(r["videos"] for r in results)
    for r in results:
        print(f"  {r['category']:25s} | {r['channels']:3d}채널 | {r['videos']:5d}영상")
    print(f"  {'합계':25s} | {total_ch:3d}채널 | {total_vid:5d}영상")
    print(f"  예상 쿼터 사용: ~{quota_used}유닛")


if __name__ == "__main__":
    main()
