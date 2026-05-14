"""통합 테스트 모듈.

전체 학습 파이프라인 end-to-end 실행, 메트릭 계산 정확성,
추론 성능 벤치마크, 재학습 Champion 아키텍처 검증,
버전 롤백 기능을 검증한다.

Requirements: 3.1, 4.1, 4.2, 5.1, 5.4, 6.1, 6.3
"""

import time

import numpy as np
import pytest
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge

from src.feature_engineer import FeatureEngineer, TOTAL_FEATURE_DIM
from src.label_generator import LabelGenerator
from src.model_evaluator import ModelEvaluator
from src.model_server import ModelServer
from src.model_trainer import ModelTrainer, TrainingConfig
from src.training_pipeline import PipelineConfig, TrainingPipeline


# ---------------------------------------------------------------------------
# Helper: 합성 영상 데이터 생성
# ---------------------------------------------------------------------------


def generate_synthetic_videos(n=100, seed=42):
    """소규모 합성 영상 데이터를 생성한다.

    Args:
        n: 생성할 영상 수.
        seed: 랜덤 시드.

    Returns:
        영상 딕셔너리 리스트.
    """
    rng = np.random.RandomState(seed)
    videos = []
    categories = ["1", "2", "10", "15", "17", "20"]
    for i in range(n):
        sub_count = rng.choice([10000, 80000, 300000, 600000])
        view_count = int(rng.exponential(50000))
        view_count = max(view_count, 100)
        like_count = int(view_count * rng.uniform(0.01, 0.1))
        comment_count = int(view_count * rng.uniform(0.001, 0.02))
        is_short = rng.random() < 0.4
        vps = view_count / sub_count
        vs_channel_avg = rng.uniform(0.2, 5.0)
        daily_views = view_count / max(rng.randint(1, 60), 1)
        videos.append(
            {
                "video_id": f"video_{i}",
                "channel_id": f"channel_{i % 20}",
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "subscriber_count": sub_count,
                "duration_sec": int(rng.uniform(30, 3600)),
                "category_id": rng.choice(categories),
                "is_short": is_short,
                "published_at": "2026-03-01T00:00:00Z",
                "comparison_group": None,  # will be computed below
                "vps": vps,
                "vs_channel_avg": vs_channel_avg,
                "daily_views": daily_views,
            }
        )
        # Compute comparison_group
        tier = (
            "S"
            if sub_count < 50000
            else "M" if sub_count < 200000 else "L" if sub_count < 500000 else "XL"
        )
        is_short_int = 1 if videos[-1]["is_short"] else 0
        videos[-1]["comparison_group"] = (
            f"{tier}_{is_short_int}_{videos[-1]['category_id']}"
        )
    return videos


def _build_percentile_tables(videos):
    """영상 데이터에서 간단한 백분위 테이블을 구축한다."""
    from collections import defaultdict

    groups = defaultdict(list)
    for v in videos:
        groups[v["comparison_group"]].append(v)

    tables = {}
    for group_key, group_videos in groups.items():
        vps_vals = sorted([v["vps"] for v in group_videos])
        eng_vals = sorted(
            [
                (v["like_count"] + v["comment_count"]) / max(v["view_count"], 1)
                for v in group_videos
            ]
        )
        like_vals = sorted(
            [v["like_count"] / max(v["view_count"], 1) for v in group_videos]
        )
        vca_vals = sorted([v.get("vs_channel_avg", 1.0) for v in group_videos])
        dv_vals = sorted([v.get("daily_views", 0.0) for v in group_videos])

        # 101개 백분위 포인트 생성
        def to_percentile_array(vals):
            if len(vals) < 2:
                return np.linspace(0, max(vals[0] if vals else 1, 0.001), 101).tolist()
            return np.percentile(vals, np.linspace(0, 100, 101)).tolist()

        tables[group_key] = {
            "vps": to_percentile_array(vps_vals),
            "engagement_rate": to_percentile_array(eng_vals),
            "like_rate": to_percentile_array(like_vals),
            "vs_channel_avg": to_percentile_array(vca_vals),
            "daily_views": to_percentile_array(dv_vals),
        }
    return tables


# ---------------------------------------------------------------------------
# TestEndToEndPipeline
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    """전체 학습 파이프라인 end-to-end 테스트.

    소규모 합성 데이터(100개 영상)로 FeatureEngineer → LabelGenerator →
    ModelTrainer(split, filter, train) → ModelEvaluator 전체 흐름을 검증한다.

    Validates: Requirements 3.1
    """

    def test_full_pipeline_completes(self):
        """100개 합성 영상으로 전체 파이프라인이 에러 없이 완료되는지 검증."""
        # 1. 합성 데이터 생성
        videos = generate_synthetic_videos(n=100, seed=42)

        # 2. 백분위 테이블 구축
        percentile_tables = _build_percentile_tables(videos)

        # 3. Feature Engineering
        fe = FeatureEngineer(percentile_tables=percentile_tables)
        feature_df = fe.transform_batch(videos)
        X = feature_df.values
        assert X.shape == (100, TOTAL_FEATURE_DIM), f"Expected (100, {TOTAL_FEATURE_DIM}), got {X.shape}"

        # 4. Label Generation
        lg = LabelGenerator()
        labels = lg.generate_labels(videos)
        assert len(labels) == 100
        assert np.all(labels >= 0) and np.all(labels <= 100)

        # 5. Data Split (채널 단위)
        channel_ids = np.array([v["channel_id"] for v in videos])
        trainer = ModelTrainer(TrainingConfig(random_state=42))
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(
            X, labels, channel_ids
        )
        assert len(X_train) + len(X_val) + len(X_test) == 100

        # 6. Train ridge model only (fast)
        ridge = Ridge()
        ridge.fit(X_train, y_train)
        models = {"ridge": ridge}

        # 7. Champion selection
        champion_name = trainer.select_champion(models, X_val, y_val)
        assert champion_name == "ridge"

        # 8. Evaluation
        evaluator = ModelEvaluator()
        metrics = evaluator.evaluate(ridge, X_test, y_test)

        assert "mae" in metrics
        assert "rmse" in metrics
        assert "spearman" in metrics
        assert metrics["mae"] >= 0
        assert metrics["rmse"] >= 0

    def test_pipeline_champion_metrics_computed(self):
        """Champion 선정 후 메트릭이 올바르게 계산되는지 검증."""
        videos = generate_synthetic_videos(n=100, seed=123)
        percentile_tables = _build_percentile_tables(videos)

        fe = FeatureEngineer(percentile_tables=percentile_tables)
        X = fe.transform_batch(videos).values
        lg = LabelGenerator()
        labels = lg.generate_labels(videos)

        channel_ids = np.array([v["channel_id"] for v in videos])
        trainer = ModelTrainer(TrainingConfig(random_state=123))
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(
            X, labels, channel_ids
        )

        ridge = Ridge()
        ridge.fit(X_train, y_train)

        evaluator = ModelEvaluator()
        metrics = evaluator.evaluate(ridge, X_test, y_test)

        # Spearman should be a valid correlation value
        assert -1.0 <= metrics["spearman"] <= 1.0
        # Score distribution should be present
        assert "score_distribution" in metrics


# ---------------------------------------------------------------------------
# TestMetricsAccuracy
# ---------------------------------------------------------------------------


class TestMetricsAccuracy:
    """메트릭 계산 정확성 검증.

    알려진 예측값과 실제값에 대해 MAE, RMSE, Spearman이
    수동 계산 결과와 일치하는지 검증한다.

    Validates: Requirements 4.1, 4.2
    """

    def test_mae_rmse_spearman_known_values(self):
        """알려진 값에 대한 MAE/RMSE/Spearman 정확성 검증."""
        # 알려진 예측값과 실제값
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        y_pred_values = np.array([12.0, 18.0, 33.0, 37.0, 52.0])

        # 수동 계산
        errors = np.abs(y_pred_values - y_true)
        expected_mae = np.mean(errors)  # (2+2+3+3+2)/5 = 2.4
        expected_rmse = np.sqrt(np.mean((y_pred_values - y_true) ** 2))
        expected_spearman, _ = spearmanr(y_pred_values, y_true)

        # Mock model that returns known predictions
        class MockModel:
            def predict(self, X):
                return y_pred_values

        model = MockModel()
        X_dummy = np.zeros((5, 3))  # dummy features

        evaluator = ModelEvaluator()
        metrics = evaluator.evaluate(model, X_dummy, y_true)

        assert abs(metrics["mae"] - expected_mae) < 1e-10
        assert abs(metrics["rmse"] - expected_rmse) < 1e-10
        assert abs(metrics["spearman"] - expected_spearman) < 1e-10

    def test_perfect_predictions(self):
        """완벽한 예측 시 MAE=0, RMSE=0, Spearman=1 검증."""
        y_true = np.array([10.0, 20.0, 30.0, 40.0, 50.0])

        class PerfectModel:
            def predict(self, X):
                return y_true

        model = PerfectModel()
        X_dummy = np.zeros((5, 3))

        evaluator = ModelEvaluator()
        metrics = evaluator.evaluate(model, X_dummy, y_true)

        assert metrics["mae"] == 0.0
        assert metrics["rmse"] == 0.0
        assert abs(metrics["spearman"] - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# TestInferencePerformance
# ---------------------------------------------------------------------------


class TestInferencePerformance:
    """추론 성능 벤치마크.

    ModelServer의 predict 호출이 평균 200ms 이내에 완료되는지 검증한다.

    Validates: Requirements 5.4
    """

    def test_predict_under_200ms(self):
        """100회 predict 호출 평균 시간이 200ms 미만인지 검증."""
        # 합성 데이터로 Ridge 모델 학습
        videos = generate_synthetic_videos(n=50, seed=99)
        percentile_tables = _build_percentile_tables(videos)

        fe = FeatureEngineer(percentile_tables=percentile_tables)
        X = fe.transform_batch(videos).values
        lg = LabelGenerator()
        y = lg.generate_labels(videos)

        ridge = Ridge()
        ridge.fit(X, y)

        # ModelServer에 학습된 모델 직접 주입
        server = ModelServer(
            s3_bucket="",
            model_key="",
            percentile_tables=percentile_tables,
            model=ridge,
        )

        # 벤치마크: 100회 predict 호출
        sample_video = videos[0]
        times = []
        for _ in range(100):
            start = time.perf_counter()
            result = server.predict(sample_video)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        avg_time_ms = np.mean(times) * 1000.0

        assert result["fallback_used"] is False
        assert 0 <= result["score"] <= 100
        assert avg_time_ms < 200.0, (
            f"Average inference time {avg_time_ms:.2f}ms exceeds 200ms limit"
        )


# ---------------------------------------------------------------------------
# TestRetrainChampionOnly
# ---------------------------------------------------------------------------


class TestRetrainChampionOnly:
    """재학습 시 Champion 아키텍처만 학습되는지 검증.

    TrainingPipeline.run_retrain이 champion_name으로 지정된
    아키텍처(Ridge)만 재학습하는지 확인한다.

    Validates: Requirements 6.1
    """

    def test_retrain_uses_champion_architecture(self):
        """run_retrain 결과 모델이 Ridge 인스턴스인지 검증."""
        # 합성 데이터 준비
        videos = generate_synthetic_videos(n=50, seed=77)
        percentile_tables = _build_percentile_tables(videos)

        fe = FeatureEngineer(percentile_tables=percentile_tables)
        X = fe.transform_batch(videos).values
        lg = LabelGenerator()
        y = lg.generate_labels(videos)

        # Train/Val 분할
        X_train, X_val = X[:35], X[35:]
        y_train, y_val = y[:35], y[35:]

        # TrainingPipeline 설정 (champion = ridge)
        config = PipelineConfig(champion_name="ridge")
        pipeline = TrainingPipeline(config)

        # 재학습 실행
        result = pipeline.run_retrain(
            new_data_key="",
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            current_metrics=None,
        )

        assert result["success"] is True
        assert result["deployed"] is True
        assert "mae" in result["metrics"]
        assert "spearman" in result["metrics"]

        # 재학습된 모델이 Ridge 인스턴스인지 확인
        assert isinstance(pipeline.current_model, Ridge)

    def test_retrain_does_not_train_other_models(self):
        """재학습 시 다른 모델(RF, XGBoost 등)이 학습되지 않는지 검증."""
        videos = generate_synthetic_videos(n=50, seed=88)
        percentile_tables = _build_percentile_tables(videos)

        fe = FeatureEngineer(percentile_tables=percentile_tables)
        X = fe.transform_batch(videos).values
        lg = LabelGenerator()
        y = lg.generate_labels(videos)

        X_train, X_val = X[:35], X[35:]
        y_train, y_val = y[:35], y[35:]

        config = PipelineConfig(champion_name="ridge")
        pipeline = TrainingPipeline(config)

        result = pipeline.run_retrain(
            new_data_key="",
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
        )

        assert result["success"] is True
        # current_model should only be Ridge, not RandomForest or XGBoost
        model = pipeline.current_model
        assert model is not None
        assert type(model).__name__ == "Ridge"


# ---------------------------------------------------------------------------
# TestVersionRollback
# ---------------------------------------------------------------------------


class TestVersionRollback:
    """모델 버전 관리 및 롤백 검증.

    save_version으로 버전을 저장하고, rollback으로 복원 가능한지 검증한다.

    Validates: Requirements 6.3
    """

    def test_save_and_rollback(self, tmp_path):
        """버전 저장 후 롤백이 올바른 메타데이터를 반환하는지 검증."""
        config = PipelineConfig(
            champion_name="ridge",
            versions_dir=str(tmp_path / "versions"),
        )
        pipeline = TrainingPipeline(config)

        # 모델 저장
        dummy_model = Ridge()
        metrics = {"mae": 8.5, "rmse": 12.0, "spearman": 0.90}
        version_label = "v1_20260501"

        meta_path = pipeline.save_version(dummy_model, metrics, version_label)

        # 메타데이터 파일 존재 확인
        import os

        assert os.path.exists(meta_path)

        # 롤백 실행
        rollback_result = pipeline.rollback(version_label)

        assert rollback_result["success"] is True
        assert rollback_result["version"] == version_label
        assert rollback_result["metadata"]["champion_name"] == "ridge"
        assert rollback_result["metadata"]["metrics"]["spearman"] == 0.90
        assert rollback_result["error"] is None

    def test_rollback_nonexistent_version(self, tmp_path):
        """존재하지 않는 버전 롤백 시 실패를 반환하는지 검증."""
        config = PipelineConfig(
            champion_name="ridge",
            versions_dir=str(tmp_path / "versions"),
        )
        pipeline = TrainingPipeline(config)

        rollback_result = pipeline.rollback("nonexistent_v99")

        assert rollback_result["success"] is False
        assert rollback_result["error"] is not None

    def test_multiple_versions_rollback(self, tmp_path):
        """여러 버전 저장 후 특정 버전으로 롤백 가능한지 검증."""
        config = PipelineConfig(
            champion_name="ridge",
            versions_dir=str(tmp_path / "versions"),
        )
        pipeline = TrainingPipeline(config)

        dummy_model = Ridge()

        # 버전 2개 저장
        pipeline.save_version(
            dummy_model, {"mae": 9.0, "spearman": 0.88}, "v1_20260501"
        )
        pipeline.save_version(
            dummy_model, {"mae": 8.0, "spearman": 0.92}, "v2_20260508"
        )

        # 첫 번째 버전으로 롤백
        result = pipeline.rollback("v1_20260501")
        assert result["success"] is True
        assert result["metadata"]["metrics"]["spearman"] == 0.88

        # 두 번째 버전으로 롤백
        result = pipeline.rollback("v2_20260508")
        assert result["success"] is True
        assert result["metadata"]["metrics"]["spearman"] == 0.92
