"""ModelEvaluator 단위 테스트.

evaluate, compare_with_baseline, check_deployment_gate,
check_monotonic_increase 함수의 정확성을 검증한다.
"""

import numpy as np
import pytest

from src.model_evaluator import ModelEvaluator, check_monotonic_increase


class MockModel:
    """테스트용 모델. 고정된 예측값을 반환한다."""

    def __init__(self, predictions):
        self._predictions = np.asarray(predictions, dtype=float)

    def predict(self, X):
        return self._predictions


@pytest.fixture
def evaluator():
    return ModelEvaluator()


class TestEvaluateReturnsCorrectMetrics:
    """test_evaluate_returns_correct_metrics: 알려진 값으로 MAE, RMSE, Spearman 검증."""

    def test_known_values(self, evaluator):
        # predictions = [10, 20, 30, 40, 50], y_test = [12, 18, 33, 37, 55]
        predictions = [10, 20, 30, 40, 50]
        y_test = [12, 18, 33, 37, 55]
        model = MockModel(predictions)
        X_test = np.zeros((5, 3))  # dummy features

        result = evaluator.evaluate(model, X_test, np.array(y_test))

        # MAE = mean(|10-12|, |20-18|, |30-33|, |40-37|, |50-55|)
        #      = mean(2, 2, 3, 3, 5) = 15/5 = 3.0
        assert result["mae"] == pytest.approx(3.0)

        # RMSE = sqrt(mean(4, 4, 9, 9, 25)) = sqrt(51/5) = sqrt(10.2)
        assert result["rmse"] == pytest.approx(np.sqrt(10.2))

        # Spearman: both are monotonically increasing, so correlation = 1.0
        assert result["spearman"] == pytest.approx(1.0)

        # All required keys present
        assert "mae" in result
        assert "rmse" in result
        assert "spearman" in result
        assert "score_distribution" in result
        assert "monotonic_check" in result


class TestEvaluateScoreDistribution:
    """test_evaluate_score_distribution: 점수 분포 히스토그램 정확성 검증."""

    def test_distribution_bins(self, evaluator):
        # Predictions spread across all bins
        predictions = [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]
        y_test = list(range(10, 110, 10))  # dummy labels
        model = MockModel(predictions)
        X_test = np.zeros((10, 3))

        result = evaluator.evaluate(model, X_test, np.array(y_test))

        dist = result["score_distribution"]
        assert dist["0-20"] == 2   # 5, 15
        assert dist["20-40"] == 2  # 25, 35
        assert dist["40-60"] == 2  # 45, 55
        assert dist["60-80"] == 2  # 65, 75
        assert dist["80-100"] == 2  # 85, 95

    def test_all_in_one_bin(self, evaluator):
        predictions = [50, 51, 52, 53, 54]
        y_test = [50, 51, 52, 53, 54]
        model = MockModel(predictions)
        X_test = np.zeros((5, 3))

        result = evaluator.evaluate(model, X_test, np.array(y_test))

        dist = result["score_distribution"]
        assert dist["40-60"] == 5
        assert dist["0-20"] == 0
        assert dist["20-40"] == 0
        assert dist["60-80"] == 0
        assert dist["80-100"] == 0


class TestCompareWithBaselineImproved:
    """test_compare_with_baseline_improved: 모델이 Baseline보다 우수한 경우."""

    def test_all_metrics_improved(self, evaluator):
        model_metrics = {"mae": 8.0, "rmse": 11.0, "spearman": 0.92}
        baseline_metrics = {"mae": 12.0, "rmse": 16.0, "spearman": 0.82}

        result = evaluator.compare_with_baseline(model_metrics, baseline_metrics)

        assert result["improved"] is True
        assert "mae" in result["comparison_report"]["improvements"]
        assert "rmse" in result["comparison_report"]["improvements"]
        assert "spearman" in result["comparison_report"]["improvements"]
        assert result["comparison_report"]["mae_diff"] == pytest.approx(-4.0)
        assert result["comparison_report"]["rmse_diff"] == pytest.approx(-5.0)
        assert result["comparison_report"]["spearman_diff"] == pytest.approx(0.10)

    def test_only_spearman_improved(self, evaluator):
        model_metrics = {"mae": 13.0, "rmse": 17.0, "spearman": 0.85}
        baseline_metrics = {"mae": 12.0, "rmse": 16.0, "spearman": 0.82}

        result = evaluator.compare_with_baseline(model_metrics, baseline_metrics)

        # Primary criterion is Spearman
        assert result["improved"] is True
        assert "spearman" in result["comparison_report"]["improvements"]
        assert "mae" not in result["comparison_report"]["improvements"]
        assert "rmse" not in result["comparison_report"]["improvements"]


class TestCompareWithBaselineNotImproved:
    """test_compare_with_baseline_not_improved: 모델이 Baseline보다 열등한 경우."""

    def test_spearman_worse(self, evaluator):
        model_metrics = {"mae": 8.0, "rmse": 11.0, "spearman": 0.80}
        baseline_metrics = {"mae": 12.0, "rmse": 16.0, "spearman": 0.82}

        result = evaluator.compare_with_baseline(model_metrics, baseline_metrics)

        # Spearman is worse → not improved
        assert result["improved"] is False
        assert result["comparison_report"]["spearman_diff"] == pytest.approx(-0.02)

    def test_all_metrics_worse(self, evaluator):
        model_metrics = {"mae": 14.0, "rmse": 18.0, "spearman": 0.75}
        baseline_metrics = {"mae": 12.0, "rmse": 16.0, "spearman": 0.82}

        result = evaluator.compare_with_baseline(model_metrics, baseline_metrics)

        assert result["improved"] is False
        assert result["comparison_report"]["improvements"] == []


class TestCheckDeploymentGateAllows:
    """test_check_deployment_gate_allows: Spearman >= Baseline이면 배포 허용."""

    def test_spearman_higher(self, evaluator):
        model_metrics = {"spearman": 0.91}
        baseline_metrics = {"spearman": 0.85}

        assert evaluator.check_deployment_gate(model_metrics, baseline_metrics) is True

    def test_spearman_equal(self, evaluator):
        model_metrics = {"spearman": 0.85}
        baseline_metrics = {"spearman": 0.85}

        assert evaluator.check_deployment_gate(model_metrics, baseline_metrics) is True


class TestCheckDeploymentGateBlocks:
    """test_check_deployment_gate_blocks: Spearman < Baseline이면 배포 차단."""

    def test_spearman_lower(self, evaluator):
        model_metrics = {"spearman": 0.80}
        baseline_metrics = {"spearman": 0.85}

        assert evaluator.check_deployment_gate(model_metrics, baseline_metrics) is False

    def test_spearman_slightly_lower(self, evaluator):
        model_metrics = {"spearman": 0.849}
        baseline_metrics = {"spearman": 0.85}

        assert evaluator.check_deployment_gate(model_metrics, baseline_metrics) is False


class TestCheckMonotonicIncreaseTrue:
    """test_check_monotonic_increase_true: 평균 VPS가 단조 증가하는 경우."""

    def test_strictly_increasing(self):
        # Scores in bins: 0-20, 20-40, 40-60, 60-80, 80-100
        scores = np.array([10, 30, 50, 70, 90])
        vps_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        assert check_monotonic_increase(scores, vps_values) is True

    def test_non_decreasing_with_equal(self):
        scores = np.array([10, 30, 50, 70, 90])
        vps_values = np.array([1.0, 2.0, 2.0, 3.0, 5.0])

        assert check_monotonic_increase(scores, vps_values) is True

    def test_multiple_values_per_bin(self):
        # Multiple values per bin, mean VPS still increasing
        scores = np.array([5, 15, 25, 35, 45, 55, 65, 75, 85, 95])
        vps_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

        assert check_monotonic_increase(scores, vps_values) is True

    def test_empty_bins_skipped(self):
        # Only bins 0-20 and 80-100 have data, still monotonic
        scores = np.array([10, 15, 85, 90])
        vps_values = np.array([1.0, 2.0, 8.0, 9.0])

        assert check_monotonic_increase(scores, vps_values) is True


class TestCheckMonotonicIncreaseFalse:
    """test_check_monotonic_increase_false: 평균 VPS가 단조 증가하지 않는 경우."""

    def test_decreasing(self):
        scores = np.array([10, 30, 50, 70, 90])
        vps_values = np.array([5.0, 4.0, 3.0, 2.0, 1.0])

        assert check_monotonic_increase(scores, vps_values) is False

    def test_non_monotonic_middle(self):
        scores = np.array([10, 30, 50, 70, 90])
        vps_values = np.array([1.0, 3.0, 2.0, 4.0, 5.0])

        assert check_monotonic_increase(scores, vps_values) is False

    def test_last_bin_drops(self):
        scores = np.array([10, 30, 50, 70, 90])
        vps_values = np.array([1.0, 2.0, 3.0, 4.0, 3.5])

        assert check_monotonic_increase(scores, vps_values) is False
