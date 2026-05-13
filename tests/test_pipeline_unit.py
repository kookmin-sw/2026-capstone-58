"""Training Pipeline 단위 테스트.

TrainingPipeline 클래스의 핵심 메서드를 검증한다.
- check_degradation: 3회 연속 성능 하락 감지
- recommend_reselection: 재선정 권고 메시지
- run_retrain: 재학습 성공/실패/배포 여부
- get_fallback_group: 소규모 그룹 폴백 로직
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from src.training_pipeline import TrainingPipeline, PipelineConfig


@pytest.fixture
def pipeline():
    """기본 TrainingPipeline 인스턴스."""
    config = PipelineConfig(
        s3_bucket="test-bucket",
        champion_name="ridge",
        versions_dir="test_versions/",
    )
    return TrainingPipeline(config)


@pytest.fixture
def simple_training_data():
    """간단한 학습/검증 데이터."""
    rng = np.random.RandomState(42)
    X_train = rng.randn(50, 5)
    y_train = rng.rand(50) * 100
    X_val = rng.randn(20, 5)
    y_val = rng.rand(20) * 100
    return X_train, y_train, X_val, y_val


class TestCheckDegradation:
    """check_degradation 메서드 테스트."""

    def test_check_degradation_true(self, pipeline):
        """3회 연속 Spearman 감소 시 True 반환."""
        history = [
            {"spearman": 0.90},
            {"spearman": 0.85},
            {"spearman": 0.80},
        ]
        assert pipeline.check_degradation(history) is True

    def test_check_degradation_false(self, pipeline):
        """연속 감소가 아닌 경우 False 반환."""
        # 중간에 증가가 있는 경우
        history = [
            {"spearman": 0.90},
            {"spearman": 0.85},
            {"spearman": 0.88},
        ]
        assert pipeline.check_degradation(history) is False

    def test_check_degradation_less_than_3_entries(self, pipeline):
        """3개 미만 항목이면 False 반환."""
        history_empty = []
        history_one = [{"spearman": 0.90}]
        history_two = [{"spearman": 0.90}, {"spearman": 0.85}]

        assert pipeline.check_degradation(history_empty) is False
        assert pipeline.check_degradation(history_one) is False
        assert pipeline.check_degradation(history_two) is False


class TestRecommendReselection:
    """recommend_reselection 메서드 테스트."""

    def test_recommend_reselection_message(self, pipeline):
        """올바른 권고 메시지 반환."""
        message = pipeline.recommend_reselection()
        assert message == "Champion 모델의 성능이 3회 연속 하락했습니다. 전체 모델 재선정을 권고합니다."


class TestRunRetrain:
    """run_retrain 메서드 테스트."""

    def test_run_retrain_success_deployed(self, pipeline, simple_training_data):
        """새 모델이 기존보다 우수하면 deployed=True."""
        X_train, y_train, X_val, y_val = simple_training_data

        # 현재 메트릭을 매우 낮게 설정하여 새 모델이 항상 우수하도록
        current_metrics = {"spearman": -1.0, "mae": 100.0, "rmse": 100.0}

        result = pipeline.run_retrain(
            new_data_key="s3://test/new_data.csv",
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            current_metrics=current_metrics,
        )

        assert result["success"] is True
        assert result["deployed"] is True
        assert "spearman" in result["metrics"]
        assert result["error"] is None

    def test_run_retrain_success_not_deployed(self, pipeline, simple_training_data):
        """새 모델이 기존보다 열등하면 deployed=False."""
        X_train, y_train, X_val, y_val = simple_training_data

        # 현재 메트릭을 매우 높게 설정하여 새 모델이 항상 열등하도록
        current_metrics = {"spearman": 1.0, "mae": 0.0, "rmse": 0.0}

        result = pipeline.run_retrain(
            new_data_key="s3://test/new_data.csv",
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            current_metrics=current_metrics,
        )

        assert result["success"] is True
        assert result["deployed"] is False
        assert "spearman" in result["metrics"]
        assert result["error"] is None

    def test_run_retrain_failure(self, pipeline):
        """학습 중 예외 발생 시 기존 모델 유지."""
        # None 데이터를 전달하여 예외 유발
        result = pipeline.run_retrain(
            new_data_key="s3://test/new_data.csv",
            X_train=None,
            y_train=None,
            X_val=None,
            y_val=None,
            current_metrics={"spearman": 0.9},
        )

        assert result["success"] is False
        assert result["deployed"] is False
        assert result["metrics"] == {}
        assert result["error"] is not None
        assert len(result["error"]) > 0


class TestGetFallbackGroup:
    """get_fallback_group 메서드 테스트."""

    def test_get_fallback_group_s_to_m(self, pipeline):
        """S 구간은 M으로 폴백."""
        assert pipeline.get_fallback_group("S_0_20") == "M_0_20"

    def test_get_fallback_group_m_to_l(self, pipeline):
        """M 구간은 L로 폴백."""
        assert pipeline.get_fallback_group("M_0_20") == "L_0_20"

    def test_get_fallback_group_l_to_xl(self, pipeline):
        """L 구간은 XL로 폴백."""
        assert pipeline.get_fallback_group("L_0_20") == "XL_0_20"

    def test_get_fallback_group_xl_stays_xl(self, pipeline):
        """XL 구간은 더 이상 폴백 없이 동일 그룹 반환."""
        assert pipeline.get_fallback_group("XL_0_20") == "XL_0_20"

    def test_get_fallback_group_with_short_flag(self, pipeline):
        """is_short=1인 그룹도 올바르게 폴백."""
        assert pipeline.get_fallback_group("S_1_20") == "M_1_20"
