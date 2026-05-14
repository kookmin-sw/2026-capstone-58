"""Model Evaluator 모듈.

모델 성능 평가 및 Baseline 비교를 담당한다.
MAE, RMSE, Spearman 순위 상관계수를 산출하고,
배포 게이트 판단을 수행한다.
"""

import numpy as np
from scipy import stats


def check_monotonic_increase(scores: np.ndarray, vps_values: np.ndarray) -> bool:
    """점수 구간별 평균 VPS 단조 증가 검증.

    Args:
        scores: 예측 점수 배열.
        vps_values: 실제 VPS 값 배열.

    Returns:
        True이면 비어있지 않은 구간들의 평균 VPS가 단조 비감소(non-decreasing).
    """
    scores = np.asarray(scores, dtype=float)
    vps_values = np.asarray(vps_values, dtype=float)

    bins = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    mean_vps_per_bin = []

    for low, high in bins:
        if high == 100:
            mask = (scores >= low) & (scores <= high)
        else:
            mask = (scores >= low) & (scores < high)

        if np.any(mask):
            mean_vps_per_bin.append(np.mean(vps_values[mask]))

    if len(mean_vps_per_bin) <= 1:
        return True

    for i in range(1, len(mean_vps_per_bin)):
        if mean_vps_per_bin[i] < mean_vps_per_bin[i - 1]:
            return False

    return True


class ModelEvaluator:
    """모델 평가 및 배포 게이트.

    학습된 모델의 성능을 평가하고,
    Baseline(수동 가중치 60/25/15) 대비 개선 여부를 판단한다.
    """

    def evaluate(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        vps_values: np.ndarray = None,
    ) -> dict:
        """모델 성능 평가.

        Args:
            model: 학습된 모델 객체 (predict 메서드 필요).
            X_test: 테스트 피처.
            y_test: 테스트 레이블.
            vps_values: 실제 VPS 값 (단조 증가 검증용, 선택).

        Returns:
            {
                "mae": float,
                "rmse": float,
                "spearman": float,
                "score_distribution": dict,
                "monotonic_check": bool
            }
        """
        predictions = model.predict(X_test)
        predictions = np.asarray(predictions, dtype=float)
        y_test = np.asarray(y_test, dtype=float)

        # MAE
        mae = float(np.mean(np.abs(predictions - y_test)))

        # RMSE
        rmse = float(np.sqrt(np.mean((predictions - y_test) ** 2)))

        # Spearman rank correlation
        spearman_corr, _ = stats.spearmanr(predictions, y_test)
        spearman = float(spearman_corr)

        # Score distribution: count predictions in 5 bins
        score_distribution = {
            "0-20": int(np.sum((predictions >= 0) & (predictions < 20))),
            "20-40": int(np.sum((predictions >= 20) & (predictions < 40))),
            "40-60": int(np.sum((predictions >= 40) & (predictions < 60))),
            "60-80": int(np.sum((predictions >= 60) & (predictions < 80))),
            "80-100": int(np.sum((predictions >= 80) & (predictions <= 100))),
        }

        # Monotonic check
        if vps_values is not None:
            monotonic_check = check_monotonic_increase(predictions, vps_values)
        else:
            monotonic_check = True  # Skip if no VPS values provided

        return {
            "mae": mae,
            "rmse": rmse,
            "spearman": spearman,
            "score_distribution": score_distribution,
            "monotonic_check": monotonic_check,
        }

    def compare_with_baseline(
        self, model_metrics: dict, baseline_metrics: dict
    ) -> dict:
        """Baseline 대비 개선 여부 판단.

        Args:
            model_metrics: 모델 평가 메트릭 (mae, rmse, spearman 키 포함).
            baseline_metrics: Baseline 평가 메트릭 (mae, rmse, spearman 키 포함).

        Returns:
            {
                "improved": bool,
                "comparison_report": {
                    "mae_diff": float,
                    "rmse_diff": float,
                    "spearman_diff": float,
                    "improvements": list
                }
            }
        """
        mae_diff = model_metrics["mae"] - baseline_metrics["mae"]
        rmse_diff = model_metrics["rmse"] - baseline_metrics["rmse"]
        spearman_diff = model_metrics["spearman"] - baseline_metrics["spearman"]

        improvements = []
        # MAE: lower is better
        if mae_diff < 0:
            improvements.append("mae")
        # RMSE: lower is better
        if rmse_diff < 0:
            improvements.append("rmse")
        # Spearman: higher is better
        if spearman_diff > 0:
            improvements.append("spearman")

        # Primary criterion: Spearman improvement
        improved = spearman_diff > 0

        return {
            "improved": improved,
            "comparison_report": {
                "mae_diff": float(mae_diff),
                "rmse_diff": float(rmse_diff),
                "spearman_diff": float(spearman_diff),
                "improvements": improvements,
            },
        }

    def check_deployment_gate(
        self, model_metrics: dict, baseline_metrics: dict
    ) -> bool:
        """배포 게이트 판단.

        Spearman이 Baseline보다 낮으면 배포를 차단한다.

        Args:
            model_metrics: 모델 평가 메트릭 (spearman 키 포함).
            baseline_metrics: Baseline 평가 메트릭 (spearman 키 포함).

        Returns:
            True이면 배포 허용, False이면 배포 차단.
        """
        return model_metrics["spearman"] >= baseline_metrics["spearman"]
