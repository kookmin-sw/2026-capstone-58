"""Feature Engineer 단위 테스트.

FeatureEngineer 클래스의 핵심 기능을 검증한다.
- transform: 단일 영상 → 31차원 피처 벡터
- transform_batch: 영상 리스트 → DataFrame
- 수치 피처 계산 (VPS, Engagement Rate, Like Rate, vs_channel_avg, daily_views, 백분위)
- 범주형 피처 인코딩 (sub_tier, is_short, category_id)
"""

import numpy as np
import pandas as pd
import pytest

from src.feature_engineer import (
    ALL_FEATURE_COLUMNS,
    CATEGORY_IDS,
    NUMERIC_FEATURES,
    SUB_TIER_COLUMNS,
    IS_SHORT_COLUMNS,
    CATEGORY_COLUMNS,
    TOTAL_FEATURE_DIM,
    FeatureEngineer,
)

# 피처 인덱스 상수 (NUMERIC_FEATURES 순서 기반)
_IDX_VPS_RAW = NUMERIC_FEATURES.index("vps_raw")                          # 0
_IDX_VPS_PCT = NUMERIC_FEATURES.index("vps_percentile")                   # 1
_IDX_ENG_RAW = NUMERIC_FEATURES.index("engagement_rate_raw")              # 2
_IDX_ENG_PCT = NUMERIC_FEATURES.index("engagement_percentile")            # 3
_IDX_LIKE_RAW = NUMERIC_FEATURES.index("like_rate_raw")                   # 4
_IDX_LIKE_PCT = NUMERIC_FEATURES.index("like_rate_percentile")            # 5
_IDX_VCA_RAW = NUMERIC_FEATURES.index("vs_channel_avg_raw")              # 6
_IDX_VCA_PCT = NUMERIC_FEATURES.index("vs_channel_avg_percentile")       # 7
_IDX_DV_RAW = NUMERIC_FEATURES.index("daily_views_raw")                  # 8
_IDX_DV_PCT = NUMERIC_FEATURES.index("daily_views_percentile")           # 9
_IDX_DURATION = NUMERIC_FEATURES.index("duration_sec")                    # 10
_IDX_DAYS = NUMERIC_FEATURES.index("days_since_upload")                   # 11
_IDX_SUBS = NUMERIC_FEATURES.index("subscriber_count")                    # 12

# 범주형 피처 시작 인덱스
_IDX_SUB_TIER_START = len(NUMERIC_FEATURES)                               # 13
_IDX_IS_SHORT_START = _IDX_SUB_TIER_START + len(SUB_TIER_COLUMNS)         # 17
_IDX_CATEGORY_START = _IDX_IS_SHORT_START + len(IS_SHORT_COLUMNS)         # 19


class TestFeatureEngineerInit:
    """FeatureEngineer 초기화 테스트."""

    def test_init_with_percentile_tables(self, sample_percentile_tables):
        """백분위 테이블로 초기화할 수 있다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        assert fe.percentile_tables == sample_percentile_tables
        assert fe.scaler_params is None

    def test_init_with_scaler_params(
        self, sample_percentile_tables, sample_scaler_params
    ):
        """스케일러 파라미터와 함께 초기화할 수 있다."""
        fe = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=sample_scaler_params,
        )
        assert fe.scaler_params == sample_scaler_params


class TestTransform:
    """transform 메서드 테스트."""

    def test_output_dimension(self, sample_percentile_tables, sample_video_data):
        """출력 벡터가 27차원이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        assert result.shape == (TOTAL_FEATURE_DIM,)

    def test_output_type(self, sample_percentile_tables, sample_video_data):
        """출력이 numpy 배열이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64

    def test_vps_calculation(self, sample_percentile_tables, sample_video_data):
        """VPS = view_count / subscriber_count 계산이 정확하다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        expected_vps = 150000 / 250000  # 0.6
        assert result[_IDX_VPS_RAW] == pytest.approx(expected_vps)

    def test_engagement_rate_calculation(
        self, sample_percentile_tables, sample_video_data
    ):
        """Engagement Rate = (like + comment) / view 계산이 정확하다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        expected_engagement = (8500 + 320) / 150000
        assert result[_IDX_ENG_RAW] == pytest.approx(expected_engagement)

    def test_like_rate_calculation(self, sample_percentile_tables, sample_video_data):
        """Like Rate = like / view 계산이 정확하다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        expected_like_rate = 8500 / 150000
        assert result[_IDX_LIKE_RAW] == pytest.approx(expected_like_rate)

    def test_duration_sec_feature(self, sample_percentile_tables, sample_video_data):
        """duration_sec 피처가 올바르게 포함된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        assert result[_IDX_DURATION] == 480.0

    def test_subscriber_count_feature(
        self, sample_percentile_tables, sample_video_data
    ):
        """subscriber_count 피처가 올바르게 포함된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        assert result[_IDX_SUBS] == 250000.0

    def test_percentile_in_range(self, sample_percentile_tables, sample_video_data):
        """백분위 값이 [0, 1] 범위에 있다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        # vps_percentile, engagement_percentile, like_rate_percentile
        assert 0.0 <= result[_IDX_VPS_PCT] <= 1.0
        assert 0.0 <= result[_IDX_ENG_PCT] <= 1.0
        assert 0.0 <= result[_IDX_LIKE_PCT] <= 1.0

    def test_sub_tier_onehot_l(self, sample_percentile_tables, sample_video_data):
        """구독자 250K → sub_tier L이 One-Hot 인코딩된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        # sub_tier columns: S, M, L, XL
        assert result[_IDX_SUB_TIER_START + 0] == 0.0  # S
        assert result[_IDX_SUB_TIER_START + 1] == 0.0  # M
        assert result[_IDX_SUB_TIER_START + 2] == 1.0  # L
        assert result[_IDX_SUB_TIER_START + 3] == 0.0  # XL

    def test_is_short_onehot_false(self, sample_percentile_tables, sample_video_data):
        """is_short=False → is_short_0=1, is_short_1=0."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        assert result[_IDX_IS_SHORT_START + 0] == 1.0  # is_short_0
        assert result[_IDX_IS_SHORT_START + 1] == 0.0  # is_short_1

    def test_is_short_onehot_true(self, sample_percentile_tables, sample_video_data):
        """is_short=True → is_short_0=0, is_short_1=1."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        video = {**sample_video_data, "is_short": True}
        result = fe.transform(video)
        assert result[_IDX_IS_SHORT_START + 0] == 0.0  # is_short_0
        assert result[_IDX_IS_SHORT_START + 1] == 1.0  # is_short_1

    def test_category_id_onehot(self, sample_percentile_tables, sample_video_data):
        """category_id=20이 올바르게 One-Hot 인코딩된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        for i, cid in enumerate(CATEGORY_IDS):
            if cid == "20":
                assert result[_IDX_CATEGORY_START + i] == 1.0
            else:
                assert result[_IDX_CATEGORY_START + i] == 0.0

    def test_onehot_sum_is_one(self, sample_percentile_tables, sample_video_data):
        """각 범주형 그룹의 One-Hot 합이 1이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        # sub_tier
        sub_end = _IDX_SUB_TIER_START + len(SUB_TIER_COLUMNS)
        assert sum(result[_IDX_SUB_TIER_START:sub_end]) == 1.0
        # is_short
        short_end = _IDX_IS_SHORT_START + len(IS_SHORT_COLUMNS)
        assert sum(result[_IDX_IS_SHORT_START:short_end]) == 1.0
        # category_id
        cat_end = _IDX_CATEGORY_START + len(CATEGORY_COLUMNS)
        assert sum(result[_IDX_CATEGORY_START:cat_end]) == 1.0


class TestSubTierDetermination:
    """구독자 구간 결정 테스트."""

    def test_sub_tier_s(self, sample_percentile_tables):
        """구독자 0~50K → S."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        assert fe._determine_sub_tier(0) == "S"
        assert fe._determine_sub_tier(49_999) == "S"

    def test_sub_tier_m(self, sample_percentile_tables):
        """구독자 50K~200K → M."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        assert fe._determine_sub_tier(50_000) == "M"
        assert fe._determine_sub_tier(199_999) == "M"

    def test_sub_tier_l(self, sample_percentile_tables):
        """구독자 200K~500K → L."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        assert fe._determine_sub_tier(200_000) == "L"
        assert fe._determine_sub_tier(499_999) == "L"

    def test_sub_tier_xl(self, sample_percentile_tables):
        """구독자 500K+ → XL."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        assert fe._determine_sub_tier(500_000) == "XL"
        assert fe._determine_sub_tier(10_000_000) == "XL"


class TestPercentileCalculation:
    """백분위 계산 테스트."""

    def test_percentile_at_minimum(self, sample_percentile_tables):
        """최소값에서 백분위가 0에 가깝다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        # vps_values = linspace(0, 10, 101), 값 0은 첫 번째 위치
        result = fe._lookup_percentile(0.0, np.linspace(0, 10, 101).tolist())
        assert result == pytest.approx(0.01)  # searchsorted right → index 1

    def test_percentile_at_maximum(self, sample_percentile_tables):
        """최대값 이상에서 백분위가 1.0이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe._lookup_percentile(15.0, np.linspace(0, 10, 101).tolist())
        assert result == 1.0

    def test_percentile_at_midpoint(self, sample_percentile_tables):
        """중간값에서 백분위가 약 0.5이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe._lookup_percentile(5.0, np.linspace(0, 10, 101).tolist())
        assert 0.45 <= result <= 0.55

    def test_percentile_monotonic(self, sample_percentile_tables):
        """값이 증가하면 백분위도 증가한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        sorted_values = np.linspace(0, 10, 101).tolist()
        p1 = fe._lookup_percentile(2.0, sorted_values)
        p2 = fe._lookup_percentile(5.0, sorted_values)
        p3 = fe._lookup_percentile(8.0, sorted_values)
        assert p1 <= p2 <= p3


class TestTransformBatch:
    """transform_batch 메서드 테스트."""

    def test_batch_output_type(self, sample_percentile_tables, sample_video_data):
        """출력이 DataFrame이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform_batch([sample_video_data])
        assert isinstance(result, pd.DataFrame)

    def test_batch_columns(self, sample_percentile_tables, sample_video_data):
        """DataFrame 컬럼이 ALL_FEATURE_COLUMNS와 일치한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform_batch([sample_video_data])
        assert list(result.columns) == ALL_FEATURE_COLUMNS

    def test_batch_row_count(self, sample_percentile_tables, sample_video_data):
        """입력 영상 수만큼 행이 생성된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        videos = [sample_video_data, sample_video_data, sample_video_data]
        result = fe.transform_batch(videos)
        assert len(result) == 3

    def test_batch_consistency_with_transform(
        self, sample_percentile_tables, sample_video_data
    ):
        """transform_batch의 각 행이 transform 결과와 동일하다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        single_result = fe.transform(sample_video_data)
        batch_result = fe.transform_batch([sample_video_data])
        np.testing.assert_array_almost_equal(
            batch_result.iloc[0].values, single_result
        )

    def test_batch_empty_list(self, sample_percentile_tables):
        """빈 리스트 입력 시 빈 DataFrame을 반환한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform_batch([])
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ALL_FEATURE_COLUMNS


class TestComparisonGroup:
    """Comparison Group 결정 테스트."""

    def test_group_key_format(self, sample_percentile_tables, sample_video_data):
        """그룹 키가 {sub_tier}_{is_short_int}_{category_id} 형식이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        group = fe._compute_comparison_group(sample_video_data)
        assert group == "L_0_20"

    def test_group_key_short_form(self, sample_percentile_tables, sample_video_data):
        """숏폼 영상의 그룹 키에 is_short=1이 포함된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        video = {**sample_video_data, "is_short": True}
        group = fe._compute_comparison_group(video)
        assert group == "L_1_20"

    def test_missing_group_uses_default_percentile(self, sample_percentile_tables):
        """백분위 테이블에 없는 그룹은 기본값 0.5를 사용한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        video = {
            "view_count": 1000,
            "like_count": 50,
            "comment_count": 10,
            "subscriber_count": 100,
            "duration_sec": 60,
            "category_id": "99",  # 존재하지 않는 카테고리
            "is_short": False,
            "published_at": "2026-01-01T00:00:00Z",
        }
        result = fe.transform(video)
        # 백분위 값이 0.5 (기본값)
        assert result[_IDX_VPS_PCT] == 0.5  # vps_percentile
        assert result[_IDX_ENG_PCT] == 0.5  # engagement_percentile
        assert result[_IDX_LIKE_PCT] == 0.5  # like_rate_percentile


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_zero_view_count(self, sample_percentile_tables):
        """조회수 0일 때 engagement/like rate가 0이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        video = {
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "subscriber_count": 100_000,
            "duration_sec": 300,
            "category_id": "20",
            "is_short": False,
            "published_at": "2026-01-01T00:00:00Z",
        }
        result = fe.transform(video)
        assert result[_IDX_ENG_RAW] == 0.0  # engagement_rate_raw
        assert result[_IDX_LIKE_RAW] == 0.0  # like_rate_raw

    def test_very_large_subscriber_count(self, sample_percentile_tables):
        """매우 큰 구독자 수에서도 정상 동작한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        video = {
            "view_count": 10_000_000,
            "like_count": 500_000,
            "comment_count": 50_000,
            "subscriber_count": 50_000_000,
            "duration_sec": 600,
            "category_id": "20",
            "is_short": False,
            "published_at": "2026-01-01T00:00:00Z",
        }
        result = fe.transform(video)
        assert result.shape == (TOTAL_FEATURE_DIM,)
        # sub_tier XL: index _IDX_SUB_TIER_START + 3
        assert result[_IDX_SUB_TIER_START + 3] == 1.0  # sub_tier_XL

    def test_missing_published_at(self, sample_percentile_tables):
        """published_at이 없으면 days_since_upload가 0이다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        video = {
            "view_count": 1000,
            "like_count": 50,
            "comment_count": 10,
            "subscriber_count": 100_000,
            "duration_sec": 300,
            "category_id": "20",
            "is_short": False,
            "published_at": None,
        }
        result = fe.transform(video)
        assert result[_IDX_DAYS] == 0.0  # days_since_upload
