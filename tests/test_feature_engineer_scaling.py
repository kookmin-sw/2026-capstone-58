"""Feature Engineer 스케일링 및 이상치 처리 단위 테스트.

Task 2.2에서 구현된 기능을 검증한다:
- fit_scalers: 학습 데이터 기반 스케일러 파라미터 fit
- 수치 피처에 log1p 변환 적용
- clip_outliers: Comparison Group 내 상위/하위 1% 윈저화
- 학습/추론 동일 변환 보장
"""

import numpy as np
import pandas as pd
import pytest

from src.feature_engineer import (
    ALL_FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    SCALABLE_FEATURES,
    TOTAL_FEATURE_DIM,
    FeatureEngineer,
)

# 피처 인덱스 상수
_IDX_VPS_RAW = NUMERIC_FEATURES.index("vps_raw")                          # 0
_IDX_VPS_PCT = NUMERIC_FEATURES.index("vps_percentile")                   # 1
_IDX_ENG_PCT = NUMERIC_FEATURES.index("engagement_percentile")            # 3
_IDX_LIKE_PCT = NUMERIC_FEATURES.index("like_rate_percentile")            # 5
_IDX_DURATION = NUMERIC_FEATURES.index("duration_sec")                    # 10
_IDX_SUBS = NUMERIC_FEATURES.index("subscriber_count")                    # 12
_IDX_ONEHOT_START = len(NUMERIC_FEATURES)                                 # 13


class TestFitScalers:
    """fit_scalers 메서드 테스트."""

    def test_returns_dict_with_required_keys(self, sample_percentile_tables):
        """반환값에 fitted_at과 scalers 키가 포함된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        videos = [
            {
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "subscriber_count": 100_000,
                "duration_sec": 300,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-01-01T00:00:00Z",
            }
        ]
        result = fe.fit_scalers(videos)
        assert "fitted_at" in result
        assert "scalers" in result
        assert result["fitted_at"] is not None

    def test_scalers_contain_all_scalable_features(self, sample_percentile_tables):
        """모든 스케일링 대상 피처에 대한 파라미터가 생성된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        videos = [
            {
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "subscriber_count": 100_000,
                "duration_sec": 300,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-01-01T00:00:00Z",
            }
        ]
        result = fe.fit_scalers(videos)
        for feat in SCALABLE_FEATURES:
            assert feat in result["scalers"]
            assert result["scalers"][feat]["type"] == "log1p"
            assert "clip_min" in result["scalers"][feat]
            assert "clip_max" in result["scalers"][feat]

    def test_clip_bounds_match_data_range(self, sample_percentile_tables):
        """clip_min/clip_max가 학습 데이터의 실제 min/max와 일치한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        videos = [
            {
                "view_count": 500,
                "like_count": 10,
                "comment_count": 5,
                "subscriber_count": 50_000,
                "duration_sec": 60,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-04-01T00:00:00Z",
            },
            {
                "view_count": 100_000,
                "like_count": 5000,
                "comment_count": 500,
                "subscriber_count": 500_000,
                "duration_sec": 3600,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-01-01T00:00:00Z",
            },
        ]
        result = fe.fit_scalers(videos)

        # VPS: 500/50000=0.01, 100000/500000=0.2
        assert result["scalers"]["vps_raw"]["clip_min"] == pytest.approx(0.01)
        assert result["scalers"]["vps_raw"]["clip_max"] == pytest.approx(0.2)

        # duration_sec: 60, 3600
        assert result["scalers"]["duration_sec"]["clip_min"] == pytest.approx(60.0)
        assert result["scalers"]["duration_sec"]["clip_max"] == pytest.approx(3600.0)

    def test_empty_videos_returns_empty_scalers(self, sample_percentile_tables):
        """빈 리스트 입력 시 빈 scalers를 반환한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.fit_scalers([])
        assert result["scalers"] == {}
        assert result["fitted_at"] is not None

    def test_single_video_min_equals_max(self, sample_percentile_tables):
        """단일 영상일 때 clip_min == clip_max."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        videos = [
            {
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "subscriber_count": 100_000,
                "duration_sec": 300,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-01-01T00:00:00Z",
            }
        ]
        result = fe.fit_scalers(videos)
        for feat in SCALABLE_FEATURES:
            assert result["scalers"][feat]["clip_min"] == result["scalers"][feat]["clip_max"]

    def test_result_is_json_serializable(self, sample_percentile_tables):
        """반환값이 JSON 직렬화 가능하다."""
        import json

        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        videos = [
            {
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "subscriber_count": 100_000,
                "duration_sec": 300,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-01-01T00:00:00Z",
            }
        ]
        result = fe.fit_scalers(videos)
        # Should not raise
        json_str = json.dumps(result)
        assert json_str is not None


class TestScalingInTransform:
    """transform에서 스케일링 적용 테스트."""

    def test_no_scaling_when_scaler_params_none(
        self, sample_percentile_tables, sample_video_data
    ):
        """scaler_params=None이면 원시값이 그대로 반환된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)
        result = fe.transform(sample_video_data)
        # VPS raw = 150000 / 250000 = 0.6
        assert result[_IDX_VPS_RAW] == pytest.approx(0.6)
        # duration_sec = 480
        assert result[_IDX_DURATION] == pytest.approx(480.0)

    def test_scaling_applies_log1p(
        self, sample_percentile_tables, sample_scaler_params, sample_video_data
    ):
        """scaler_params가 있으면 log1p 변환이 적용된다."""
        fe = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=sample_scaler_params,
        )
        result = fe.transform(sample_video_data)

        # VPS raw = 0.6, clip to [0, 500] → 0.6, log1p(0.6) ≈ 0.4700
        expected_vps = np.log1p(0.6)
        assert result[_IDX_VPS_RAW] == pytest.approx(expected_vps, rel=1e-6)

        # duration_sec = 480, clip to [1, 86400] → 480, log1p(480) ≈ 6.175
        expected_duration = np.log1p(480.0)
        assert result[_IDX_DURATION] == pytest.approx(expected_duration, rel=1e-6)

        # subscriber_count = 250000, clip to [0, 100000000] → 250000, log1p(250000)
        expected_sub = np.log1p(250000.0)
        assert result[_IDX_SUBS] == pytest.approx(expected_sub, rel=1e-6)

    def test_scaling_clips_before_log1p(self, sample_percentile_tables):
        """클리핑이 log1p 전에 적용된다."""
        scaler_params = {
            "fitted_at": "2026-01-01T00:00:00+00:00",
            "scalers": {
                "vps_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 1.0},
                "engagement_rate_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 1.0},
                "like_rate_raw": {"type": "log1p", "clip_min": 0.0, "clip_max": 1.0},
                "duration_sec": {"type": "log1p", "clip_min": 1, "clip_max": 100},
                "days_since_upload": {"type": "log1p", "clip_min": 0, "clip_max": 3650},
                "subscriber_count": {"type": "log1p", "clip_min": 0, "clip_max": 100000000},
            },
        }
        fe = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=scaler_params,
        )
        # VPS = 10000000/250000 = 40.0, but clip_max=1.0 → clipped to 1.0
        video = {
            "view_count": 10_000_000,
            "like_count": 100,
            "comment_count": 10,
            "subscriber_count": 250_000,
            "duration_sec": 500,  # clip_max=100 → clipped to 100
            "category_id": "20",
            "is_short": False,
            "published_at": "2026-01-01T00:00:00Z",
        }
        result = fe.transform(video)

        # VPS clipped to 1.0, then log1p(1.0) = ln(2) ≈ 0.6931
        assert result[_IDX_VPS_RAW] == pytest.approx(np.log1p(1.0), rel=1e-6)
        # duration clipped to 100, then log1p(100) ≈ 4.615
        assert result[_IDX_DURATION] == pytest.approx(np.log1p(100.0), rel=1e-6)

    def test_percentile_features_not_scaled(
        self, sample_percentile_tables, sample_scaler_params, sample_video_data
    ):
        """백분위 피처(vps_percentile 등)는 스케일링되지 않는다."""
        fe_no_scale = FeatureEngineer(percentile_tables=sample_percentile_tables)
        fe_with_scale = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=sample_scaler_params,
        )
        result_no_scale = fe_no_scale.transform(sample_video_data)
        result_with_scale = fe_with_scale.transform(sample_video_data)

        # 백분위 피처 인덱스
        assert result_no_scale[_IDX_VPS_PCT] == result_with_scale[_IDX_VPS_PCT]  # vps_percentile
        assert result_no_scale[_IDX_ENG_PCT] == result_with_scale[_IDX_ENG_PCT]  # engagement_percentile
        assert result_no_scale[_IDX_LIKE_PCT] == result_with_scale[_IDX_LIKE_PCT]  # like_rate_percentile

    def test_onehot_features_not_affected_by_scaling(
        self, sample_percentile_tables, sample_scaler_params, sample_video_data
    ):
        """One-Hot 피처는 스케일링에 영향받지 않는다."""
        fe_no_scale = FeatureEngineer(percentile_tables=sample_percentile_tables)
        fe_with_scale = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=sample_scaler_params,
        )
        result_no_scale = fe_no_scale.transform(sample_video_data)
        result_with_scale = fe_with_scale.transform(sample_video_data)

        # One-Hot 피처: indices _IDX_ONEHOT_START 이후
        np.testing.assert_array_equal(result_no_scale[_IDX_ONEHOT_START:], result_with_scale[_IDX_ONEHOT_START:])

    def test_output_dimension_with_scaling(
        self, sample_percentile_tables, sample_scaler_params, sample_video_data
    ):
        """스케일링 적용 후에도 출력이 27차원이다."""
        fe = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=sample_scaler_params,
        )
        result = fe.transform(sample_video_data)
        assert result.shape == (TOTAL_FEATURE_DIM,)

    def test_transform_batch_with_scaling(
        self, sample_percentile_tables, sample_scaler_params, sample_video_data
    ):
        """transform_batch에서도 스케일링이 동일하게 적용된다."""
        fe = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=sample_scaler_params,
        )
        single_result = fe.transform(sample_video_data)
        batch_result = fe.transform_batch([sample_video_data])
        np.testing.assert_array_almost_equal(
            batch_result.iloc[0].values, single_result
        )


class TestClipOutliers:
    """clip_outliers 메서드 테스트."""

    def test_clips_to_1_99_percentile(self, sample_percentile_tables):
        """수치 피처가 [1%, 99%] 범위로 클리핑된다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)

        # 100개 데이터 생성 (일부 극단값 포함)
        np.random.seed(42)
        n = 100
        data = {col: np.zeros(n) for col in ALL_FEATURE_COLUMNS}
        data["vps_raw"] = np.concatenate([
            np.random.uniform(0.1, 5.0, 98),
            [100.0],  # 극단적 상위 이상치
            [0.001],  # 극단적 하위 이상치
        ])
        data["engagement_rate_raw"] = np.random.uniform(0.01, 0.5, n)
        data["like_rate_raw"] = np.random.uniform(0.01, 0.3, n)
        data["duration_sec"] = np.random.uniform(60, 3600, n).astype(float)
        data["days_since_upload"] = np.random.uniform(1, 365, n)
        data["subscriber_count"] = np.random.uniform(1000, 1000000, n)

        df = pd.DataFrame(data)
        result = fe.clip_outliers(df, "L_0_20")

        # 클리핑 후 vps_raw의 최대값이 원래 100.0보다 작아야 함
        assert result["vps_raw"].max() < 100.0
        # 클리핑 후 vps_raw의 최소값이 원래 0.001보다 커야 함
        assert result["vps_raw"].min() > 0.001

    def test_does_not_clip_percentile_features(self, sample_percentile_tables):
        """백분위 피처는 클리핑하지 않는다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)

        n = 100
        data = {col: np.random.uniform(0, 1, n) for col in ALL_FEATURE_COLUMNS}
        # 백분위 피처에 극단값 설정
        data["vps_percentile"] = np.concatenate([np.random.uniform(0, 1, 99), [0.99]])
        data["engagement_percentile"] = np.concatenate([np.random.uniform(0, 1, 99), [0.01]])

        df = pd.DataFrame(data)
        result = fe.clip_outliers(df, "L_0_20")

        # 백분위 피처는 변경되지 않아야 함
        np.testing.assert_array_equal(
            result["vps_percentile"].values, df["vps_percentile"].values
        )
        np.testing.assert_array_equal(
            result["engagement_percentile"].values, df["engagement_percentile"].values
        )

    def test_unknown_group_returns_unchanged(self, sample_percentile_tables):
        """백분위 테이블에 없는 그룹이면 변환 없이 반환한다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)

        n = 10
        data = {col: np.random.uniform(0, 1, n) for col in ALL_FEATURE_COLUMNS}
        data["vps_raw"] = np.array([0.001, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0, 500.0])
        df = pd.DataFrame(data)

        result = fe.clip_outliers(df, "UNKNOWN_GROUP")
        pd.testing.assert_frame_equal(result, df)

    def test_does_not_modify_original_dataframe(self, sample_percentile_tables):
        """원본 DataFrame을 수정하지 않는다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)

        n = 50
        data = {col: np.random.uniform(0, 1, n) for col in ALL_FEATURE_COLUMNS}
        data["vps_raw"] = np.concatenate([np.random.uniform(0.1, 5.0, 48), [100.0], [0.001]])
        df = pd.DataFrame(data)
        original_vps = df["vps_raw"].copy()

        fe.clip_outliers(df, "L_0_20")

        # 원본이 변경되지 않아야 함
        pd.testing.assert_series_equal(df["vps_raw"], original_vps)

    def test_all_values_within_bounds_after_clip(self, sample_percentile_tables):
        """클리핑 후 모든 값이 [p1, p99] 범위 내에 있다."""
        fe = FeatureEngineer(percentile_tables=sample_percentile_tables)

        np.random.seed(123)
        n = 200
        data = {col: np.random.uniform(0, 1, n) for col in ALL_FEATURE_COLUMNS}
        data["vps_raw"] = np.random.exponential(2.0, n)
        data["duration_sec"] = np.random.uniform(10, 10000, n).astype(float)
        df = pd.DataFrame(data)

        # 클리핑 전 경계 계산
        p1_vps = np.percentile(df["vps_raw"], 1)
        p99_vps = np.percentile(df["vps_raw"], 99)

        result = fe.clip_outliers(df, "L_0_20")

        # 모든 값이 경계 내
        assert result["vps_raw"].min() >= p1_vps - 1e-10
        assert result["vps_raw"].max() <= p99_vps + 1e-10


class TestScalingConsistency:
    """학습/추론 동일 변환 보장 테스트."""

    def test_fit_then_transform_consistency(self, sample_percentile_tables):
        """fit_scalers로 생성한 파라미터로 transform하면 일관된 결과를 얻는다."""
        videos = [
            {
                "view_count": 1000,
                "like_count": 50,
                "comment_count": 10,
                "subscriber_count": 100_000,
                "duration_sec": 300,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-01-01T00:00:00Z",
            },
            {
                "view_count": 50_000,
                "like_count": 2500,
                "comment_count": 200,
                "subscriber_count": 300_000,
                "duration_sec": 600,
                "category_id": "20",
                "is_short": False,
                "published_at": "2026-02-01T00:00:00Z",
            },
        ]

        # fit
        fe_fit = FeatureEngineer(percentile_tables=sample_percentile_tables)
        scaler_params = fe_fit.fit_scalers(videos)

        # transform with fitted params
        fe_infer = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=scaler_params,
        )
        result1 = fe_infer.transform(videos[0])
        result2 = fe_infer.transform(videos[0])

        # 동일 입력 → 동일 출력
        np.testing.assert_array_equal(result1, result2)

    def test_transform_and_transform_batch_consistent_with_scaling(
        self, sample_percentile_tables, sample_scaler_params
    ):
        """스케일링 적용 시에도 transform과 transform_batch 결과가 일치한다."""
        fe = FeatureEngineer(
            percentile_tables=sample_percentile_tables,
            scaler_params=sample_scaler_params,
        )
        video = {
            "view_count": 5000,
            "like_count": 200,
            "comment_count": 30,
            "subscriber_count": 150_000,
            "duration_sec": 420,
            "category_id": "20",
            "is_short": False,
            "published_at": "2026-03-15T00:00:00Z",
        }

        single = fe.transform(video)
        batch = fe.transform_batch([video])

        np.testing.assert_array_almost_equal(batch.iloc[0].values, single)
