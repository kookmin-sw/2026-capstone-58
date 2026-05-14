"""공통 테스트 fixture 정의.

모든 테스트에서 공유하는 샘플 데이터 및 설정을 제공한다.
"""

import pytest
import numpy as np


@pytest.fixture
def sample_video_data():
    """샘플 영상 데이터 딕셔너리.

    모든 필수 필드를 포함하는 유효한 영상 데이터.
    """
    return {
        "video_id": "test_video_001",
        "channel_id": "test_channel_001",
        "view_count": 150000,
        "like_count": 8500,
        "comment_count": 320,
        "subscriber_count": 250000,
        "duration_sec": 480,
        "category_id": "20",
        "is_short": False,
        "published_at": "2026-04-28T12:00:00Z",
        "comparison_group": "L_0_20",
        "vps": 0.6,
        "vs_channel_avg": 1.2,
        "daily_views": 9375.0,
    }


@pytest.fixture
def sample_percentile_tables():
    """샘플 백분위 테이블 딕셔너리.

    Comparison Group별 VPS, engagement, like_rate 백분위 배열을 포함.
    """
    percentiles = np.linspace(0, 1, 101).tolist()
    vps_values = np.linspace(0, 10, 101).tolist()
    engagement_values = np.linspace(0, 0.5, 101).tolist()
    like_rate_values = np.linspace(0, 0.3, 101).tolist()

    return {
        "L_0_20": {
            "vps": vps_values,
            "engagement_rate": engagement_values,
            "like_rate": like_rate_values,
            "vs_channel_avg": np.linspace(0, 5, 101).tolist(),
            "daily_views": np.linspace(0, 100000, 101).tolist(),
            "percentiles": percentiles,
        },
        "M_0_20": {
            "vps": vps_values,
            "engagement_rate": engagement_values,
            "like_rate": like_rate_values,
            "vs_channel_avg": np.linspace(0, 5, 101).tolist(),
            "daily_views": np.linspace(0, 100000, 101).tolist(),
            "percentiles": percentiles,
        },
        "S_0_20": {
            "vps": vps_values,
            "engagement_rate": engagement_values,
            "like_rate": like_rate_values,
            "vs_channel_avg": np.linspace(0, 5, 101).tolist(),
            "daily_views": np.linspace(0, 100000, 101).tolist(),
            "percentiles": percentiles,
        },
        "XL_0_20": {
            "vps": vps_values,
            "engagement_rate": engagement_values,
            "like_rate": like_rate_values,
            "vs_channel_avg": np.linspace(0, 5, 101).tolist(),
            "daily_views": np.linspace(0, 100000, 101).tolist(),
            "percentiles": percentiles,
        },
    }


@pytest.fixture
def sample_feature_config():
    """피처 설정 딕셔너리.

    feature_config.json의 내용과 동일한 구조.
    """
    return {
        "version": "3.0",
        "numeric_features": [
            "vps_raw",
            "vps_percentile",
            "engagement_rate_raw",
            "engagement_percentile",
            "like_rate_raw",
            "like_rate_percentile",
            "vs_channel_avg_raw",
            "vs_channel_avg_percentile",
            "daily_views_raw",
            "daily_views_percentile",
            "duration_sec",
            "days_since_upload",
            "subscriber_count",
        ],
        "categorical_features": {
            "sub_tier": ["S", "M", "L", "XL"],
            "is_short": [0, 1],
            "category_id": [
                "1", "2", "10", "15", "17", "20", "22", "23", "24", "25", "26", "28"
            ],
        },
        "total_feature_dim": 31,
    }


@pytest.fixture
def sample_scaler_params():
    """스케일러 파라미터 딕셔너리.

    scaler_params.json의 내용과 동일한 구조.
    """
    return {
        "fitted_at": None,
        "scalers": {
            "vps_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 500.0},
            "engagement_rate_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 1.0},
            "like_rate_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 1.0},
            "vs_channel_avg_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 50.0},
            "daily_views_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 50000000.0},
            "duration_sec": {"type": "log1p", "clip_min": 1, "clip_max": 86400},
            "days_since_upload": {"type": "log1p", "clip_min": 1, "clip_max": 3650},
            "subscriber_count": {"type": "log1p", "clip_min": 0, "clip_max": 100000000},
        },
    }
