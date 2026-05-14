"""Model Server 단위 테스트.

ModelServer 클래스의 핵심 기능을 검증한다:
- predict 반환 형식 검증
- 점수 범위 (0~100) 검증
- 범위 초과 예측값 클리핑 검증
- 모델 없을 때 Baseline 폴백 동작 검증
- Baseline 폴백 점수 공식 (60/25/15) 검증
- 추론 예외 발생 시 폴백 동작 검증
"""

import numpy as np
import pytest

from src.model_server import ModelServer


class MockModel:
    """정상 동작하는 모의 모델."""

    def predict(self, X):
        """입력에 관계없이 고정 점수 반환."""
        return np.array([72.5])


class MockModelOutOfRange:
    """범위를 벗어나는 예측값을 반환하는 모의 모델."""

    def __init__(self, value):
        self.value = value

    def predict(self, X):
        return np.array([self.value])


class MockModelException:
    """추론 시 예외를 발생시키는 모의 모델."""

    def predict(self, X):
        raise RuntimeError("Model inference failed")


@pytest.fixture
def percentile_tables():
    """테스트용 백분위 테이블."""
    vps_values = np.linspace(0, 10, 101).tolist()
    engagement_values = np.linspace(0, 0.5, 101).tolist()
    like_rate_values = np.linspace(0, 0.3, 101).tolist()

    return {
        "L_0_20": {
            "vps": vps_values,
            "engagement_rate": engagement_values,
            "like_rate": like_rate_values,
        },
        "M_0_20": {
            "vps": vps_values,
            "engagement_rate": engagement_values,
            "like_rate": like_rate_values,
        },
        "S_0_20": {
            "vps": vps_values,
            "engagement_rate": engagement_values,
            "like_rate": like_rate_values,
        },
    }


@pytest.fixture
def sample_video():
    """테스트용 영상 데이터."""
    return {
        "video_id": "test_video_001",
        "view_count": 150000,
        "like_count": 8500,
        "comment_count": 320,
        "subscriber_count": 250000,
        "duration_sec": 480,
        "category_id": "20",
        "is_short": False,
        "published_at": "2026-04-28T12:00:00Z",
    }


@pytest.fixture
def server_with_model(percentile_tables):
    """모델이 있는 ModelServer 인스턴스."""
    return ModelServer(
        s3_bucket="",
        model_key="",
        percentile_tables=percentile_tables,
        model=MockModel(),
        scaler_params=None,
    )


@pytest.fixture
def server_without_model(percentile_tables):
    """모델이 없는 ModelServer 인스턴스 (폴백 모드)."""
    return ModelServer(
        s3_bucket="",
        model_key="",
        percentile_tables=percentile_tables,
        model=None,
        scaler_params=None,
    )


class TestPredictReturnsCorrectFormat:
    """predict 반환 형식 검증."""

    def test_predict_returns_all_required_keys(self, server_with_model, sample_video):
        """predict 결과에 모든 필수 키가 포함되어야 한다."""
        result = server_with_model.predict(sample_video)

        required_keys = {
            "video_id",
            "score",
            "model_version",
            "comparison_group",
            "percentiles",
            "fallback_used",
        }
        assert required_keys == set(result.keys())

    def test_predict_percentiles_has_required_keys(
        self, server_with_model, sample_video
    ):
        """percentiles 딕셔너리에 vps, engagement, like_rate 키가 있어야 한다."""
        result = server_with_model.predict(sample_video)

        percentile_keys = {"vps", "engagement", "like_rate"}
        assert percentile_keys == set(result["percentiles"].keys())

    def test_predict_returns_correct_video_id(self, server_with_model, sample_video):
        """반환된 video_id가 입력과 일치해야 한다."""
        result = server_with_model.predict(sample_video)
        assert result["video_id"] == "test_video_001"

    def test_predict_returns_correct_types(self, server_with_model, sample_video):
        """반환값의 타입이 올바라야 한다."""
        result = server_with_model.predict(sample_video)

        assert isinstance(result["video_id"], str)
        assert isinstance(result["score"], float)
        assert isinstance(result["model_version"], str)
        assert isinstance(result["comparison_group"], str)
        assert isinstance(result["percentiles"], dict)
        assert isinstance(result["fallback_used"], bool)


class TestPredictScoreInRange:
    """predict 점수 범위 (0~100) 검증."""

    def test_normal_prediction_in_range(self, server_with_model, sample_video):
        """정상 예측값은 0~100 범위 내에 있어야 한다."""
        result = server_with_model.predict(sample_video)
        assert 0.0 <= result["score"] <= 100.0

    def test_fallback_score_in_range(self, server_without_model, sample_video):
        """폴백 점수도 0~100 범위 내에 있어야 한다."""
        result = server_without_model.predict(sample_video)
        assert 0.0 <= result["score"] <= 100.0


class TestPredictClipsOutOfRange:
    """범위 초과 예측값 클리핑 검증."""

    def test_clips_score_above_100(self, percentile_tables, sample_video):
        """모델이 100 초과 예측 시 100으로 클리핑되어야 한다."""
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=MockModelOutOfRange(150.0),
            scaler_params=None,
        )
        result = server.predict(sample_video)
        assert result["score"] == 100.0

    def test_clips_score_below_0(self, percentile_tables, sample_video):
        """모델이 0 미만 예측 시 0으로 클리핑되어야 한다."""
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=MockModelOutOfRange(-25.0),
            scaler_params=None,
        )
        result = server.predict(sample_video)
        assert result["score"] == 0.0

    def test_clips_extreme_positive(self, percentile_tables, sample_video):
        """극단적으로 큰 예측값도 100으로 클리핑되어야 한다."""
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=MockModelOutOfRange(99999.0),
            scaler_params=None,
        )
        result = server.predict(sample_video)
        assert result["score"] == 100.0

    def test_clips_extreme_negative(self, percentile_tables, sample_video):
        """극단적으로 작은 예측값도 0으로 클리핑되어야 한다."""
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=MockModelOutOfRange(-99999.0),
            scaler_params=None,
        )
        result = server.predict(sample_video)
        assert result["score"] == 0.0


class TestBaselineFallbackWhenModelNone:
    """모델이 None일 때 Baseline 폴백 동작 검증."""

    def test_fallback_used_is_true(self, server_without_model, sample_video):
        """모델이 없으면 fallback_used가 True여야 한다."""
        result = server_without_model.predict(sample_video)
        assert result["fallback_used"] is True

    def test_fallback_returns_all_keys(self, server_without_model, sample_video):
        """폴백 결과도 모든 필수 키를 포함해야 한다."""
        result = server_without_model.predict(sample_video)

        required_keys = {
            "video_id",
            "score",
            "model_version",
            "comparison_group",
            "percentiles",
            "fallback_used",
        }
        assert required_keys == set(result.keys())

    def test_fallback_score_in_valid_range(self, server_without_model, sample_video):
        """폴백 점수가 0~100 범위 내에 있어야 한다."""
        result = server_without_model.predict(sample_video)
        assert 0.0 <= result["score"] <= 100.0


class TestBaselineFallbackScoreFormula:
    """Baseline 폴백 점수 공식 (60/25/15) 검증."""

    def test_fallback_formula_with_known_percentiles(self):
        """알려진 백분위 값으로 60/25/15 공식을 검증한다."""
        # 백분위 테이블을 설정하여 특정 백분위가 나오도록 구성
        # VPS=5.0 → 50번째 백분위 (0.5)
        # engagement=0.25 → 50번째 백분위 (0.5)
        # like_rate=0.15 → 50번째 백분위 (0.5)
        vps_values = np.linspace(0, 10, 101).tolist()
        engagement_values = np.linspace(0, 0.5, 101).tolist()
        like_rate_values = np.linspace(0, 0.3, 101).tolist()

        percentile_tables = {
            "L_0_20": {
                "vps": vps_values,
                "engagement_rate": engagement_values,
                "like_rate": like_rate_values,
            },
        }

        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=None,
            scaler_params=None,
        )

        # subscriber_count=250000 → L tier, is_short=False → 0, category=20
        # → comparison_group = "L_0_20"
        # VPS = 500000 / 250000 = 2.0
        # 2.0 in linspace(0,10,101) → index ~20 → percentile = 0.20
        video_data = {
            "video_id": "test",
            "view_count": 500000,
            "like_count": 25000,
            "comment_count": 1000,
            "subscriber_count": 250000,
            "duration_sec": 300,
            "category_id": "20",
            "is_short": False,
            "published_at": "2026-01-01T00:00:00Z",
        }

        result = server._baseline_fallback(video_data)

        # 수동 계산:
        # VPS = 500000/250000 = 2.0
        # engagement = (25000+1000)/500000 = 0.052
        # like_rate = 25000/500000 = 0.05
        #
        # VPS percentile: searchsorted([0, 0.1, ..., 10], 2.0) → ~20 → 0.20
        # engagement percentile: searchsorted([0, 0.005, ..., 0.5], 0.052) → ~10 → 0.10 (approx)
        # like_rate percentile: searchsorted([0, 0.003, ..., 0.3], 0.05) → ~16 → 0.16 (approx)
        #
        # score = 0.20*60 + engagement_pct*25 + like_rate_pct*15

        # 검증: 공식이 올바르게 적용되었는지 확인
        vps_pct = result["percentiles"]["vps"]
        eng_pct = result["percentiles"]["engagement"]
        lr_pct = result["percentiles"]["like_rate"]

        expected_score = vps_pct * 60.0 + eng_pct * 25.0 + lr_pct * 15.0
        assert abs(result["score"] - expected_score) < 1e-10

    def test_fallback_max_score(self):
        """모든 백분위가 1.0일 때 점수가 100이어야 한다."""
        # 모든 값이 최대인 경우
        vps_values = np.linspace(0, 1, 101).tolist()
        engagement_values = np.linspace(0, 0.01, 101).tolist()
        like_rate_values = np.linspace(0, 0.01, 101).tolist()

        percentile_tables = {
            "S_0_1": {
                "vps": vps_values,
                "engagement_rate": engagement_values,
                "like_rate": like_rate_values,
            },
        }

        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=None,
            scaler_params=None,
        )

        # 모든 지표가 테이블 최대값을 초과하도록 설정
        video_data = {
            "video_id": "max_test",
            "view_count": 1000000,
            "like_count": 500000,
            "comment_count": 500000,
            "subscriber_count": 10000,  # S tier
            "duration_sec": 60,
            "category_id": "1",
            "is_short": False,
            "published_at": "2026-01-01T00:00:00Z",
        }

        result = server._baseline_fallback(video_data)

        # 모든 백분위가 1.0이면: 1.0*60 + 1.0*25 + 1.0*15 = 100
        assert result["score"] == 100.0

    def test_fallback_min_score(self):
        """모든 백분위가 0.0일 때 점수가 0이어야 한다."""
        # 모든 값이 0인 경우 (view_count=0이면 engagement/like_rate=0)
        vps_values = np.linspace(0.1, 10, 101).tolist()  # 최소값 > 0
        engagement_values = np.linspace(0.01, 0.5, 101).tolist()
        like_rate_values = np.linspace(0.01, 0.3, 101).tolist()

        percentile_tables = {
            "S_0_1": {
                "vps": vps_values,
                "engagement_rate": engagement_values,
                "like_rate": like_rate_values,
            },
        }

        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=None,
            scaler_params=None,
        )

        # view_count=0이면 VPS=0, engagement=0, like_rate=0
        # 모두 테이블 최소값보다 작으므로 백분위 = 0
        video_data = {
            "video_id": "min_test",
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "subscriber_count": 10000,  # S tier
            "duration_sec": 60,
            "category_id": "1",
            "is_short": False,
            "published_at": "2026-01-01T00:00:00Z",
        }

        result = server._baseline_fallback(video_data)

        # 모든 백분위가 0이면: 0*60 + 0*25 + 0*15 = 0
        assert result["score"] == 0.0


class TestPredictCatchesExceptionAndFallsBack:
    """추론 예외 발생 시 폴백 동작 검증."""

    def test_exception_triggers_fallback(self, percentile_tables, sample_video):
        """모델 추론 중 예외 발생 시 폴백을 사용해야 한다."""
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=MockModelException(),
            scaler_params=None,
        )
        result = server.predict(sample_video)
        assert result["fallback_used"] is True

    def test_exception_fallback_returns_valid_score(
        self, percentile_tables, sample_video
    ):
        """예외 폴백 시에도 유효한 점수를 반환해야 한다."""
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=MockModelException(),
            scaler_params=None,
        )
        result = server.predict(sample_video)
        assert 0.0 <= result["score"] <= 100.0

    def test_exception_fallback_returns_all_keys(
        self, percentile_tables, sample_video
    ):
        """예외 폴백 시에도 모든 필수 키를 반환해야 한다."""
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=MockModelException(),
            scaler_params=None,
        )
        result = server.predict(sample_video)

        required_keys = {
            "video_id",
            "score",
            "model_version",
            "comparison_group",
            "percentiles",
            "fallback_used",
        }
        assert required_keys == set(result.keys())
