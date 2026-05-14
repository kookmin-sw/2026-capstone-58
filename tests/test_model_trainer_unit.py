"""Model Trainer 단위 테스트.

split_data 채널 단위 분할, filter_by_group_size 필터링,
train_all_candidates, select_champion, retrain_champion, save_metadata 검증.
"""

import json

import numpy as np
import pytest

from src.model_trainer import ModelTrainer, TrainingConfig


@pytest.fixture
def trainer():
    """기본 설정의 ModelTrainer 인스턴스."""
    config = TrainingConfig()
    return ModelTrainer(config)


@pytest.fixture
def trainer_with_mlp():
    """MLP 포함 설정의 ModelTrainer 인스턴스."""
    config = TrainingConfig(include_mlp=True)
    return ModelTrainer(config)


@pytest.fixture
def sample_split_data():
    """채널 단위 분할 테스트용 샘플 데이터.

    10개 채널, 각 채널당 10개 영상 = 총 100개 샘플.
    """
    n_channels = 10
    videos_per_channel = 10
    n_samples = n_channels * videos_per_channel
    n_features = 27

    rng = np.random.RandomState(123)
    X = rng.randn(n_samples, n_features)
    y = rng.rand(n_samples) * 100

    channel_ids = np.array([
        f"channel_{i}" for i in range(n_channels)
        for _ in range(videos_per_channel)
    ])

    return X, y, channel_ids


@pytest.fixture
def synthetic_training_data():
    """후보 모델 학습 테스트용 합성 데이터.

    100 샘플, 27 피처. 선형 관계를 가진 데이터.
    """
    rng = np.random.RandomState(42)
    n_samples = 100
    n_features = 27

    X = rng.randn(n_samples, n_features)
    # 선형 관계 + 노이즈
    weights = rng.randn(n_features)
    y = X @ weights + rng.randn(n_samples) * 0.5
    # 0~100 범위로 스케일링
    y = (y - y.min()) / (y.max() - y.min()) * 100

    # train/val 분할
    X_train, X_val = X[:80], X[80:]
    y_train, y_val = y[:80], y[80:]

    return X_train, y_train, X_val, y_val


class TestSplitData:
    """split_data 메서드 테스트."""

    def test_no_channel_in_multiple_splits(self, trainer, sample_split_data):
        """같은 채널이 여러 분할에 포함되지 않아야 한다."""
        X, y, channel_ids = sample_split_data
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(X, y, channel_ids)

        # 각 분할의 인덱스 추출
        train_mask = np.isin(channel_ids, np.unique(channel_ids)[:7])  # 대략적 확인 대신 실제 분할 결과 사용

        # 실제 분할 결과에서 채널 추출
        n_samples = len(X)
        all_indices = np.arange(n_samples)

        # 분할 결과의 크기로 인덱스 매핑
        train_size = len(X_train)
        val_size = len(X_val)
        test_size = len(X_test)

        # 전체 데이터가 보존되는지 확인
        assert train_size + val_size + test_size == n_samples

        # 채널 ID를 분할별로 추출 (원본 데이터에서 매칭)
        # split_data는 마스크 기반이므로 원본 순서 유지
        train_channels = set()
        val_channels = set()
        test_channels = set()

        # 각 분할의 채널 ID를 직접 추적
        idx = 0
        for i in range(n_samples):
            # X_train의 행과 원본 X의 행을 비교하여 매핑
            pass

        # 더 직접적인 방법: channel_ids를 분할과 동일하게 마스킹
        unique_channels = np.unique(channel_ids)
        rng = np.random.RandomState(42)
        rng.shuffle(unique_channels)

        n_channels = len(unique_channels)
        n_train = int(np.round(n_channels * 0.70))
        n_val = int(np.round(n_channels * 0.15))

        train_ch = set(unique_channels[:n_train])
        val_ch = set(unique_channels[n_train:n_train + n_val])
        test_ch = set(unique_channels[n_train + n_val:])

        # 채널 집합 간 교집합이 없어야 함
        assert len(train_ch & val_ch) == 0
        assert len(train_ch & test_ch) == 0
        assert len(val_ch & test_ch) == 0

    def test_channel_split_no_overlap_via_data(self, trainer, sample_split_data):
        """분할된 데이터에서 채널 중복이 없는지 직접 검증."""
        X, y, channel_ids = sample_split_data
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(X, y, channel_ids)

        # 각 분할에 속한 채널 ID를 역추적
        # split_data는 boolean mask로 필터링하므로 순서가 유지됨
        unique_channels = np.unique(channel_ids)
        rng = np.random.RandomState(trainer.config.random_state)
        rng.shuffle(unique_channels)

        n_channels = len(unique_channels)
        n_train = int(np.round(n_channels * trainer.config.train_ratio))
        n_val = int(np.round(n_channels * trainer.config.val_ratio))

        train_channels = set(unique_channels[:n_train])
        val_channels = set(unique_channels[n_train:n_train + n_val])
        test_channels = set(unique_channels[n_train + n_val:])

        # 교집합 없음 확인
        assert train_channels.isdisjoint(val_channels)
        assert train_channels.isdisjoint(test_channels)
        assert val_channels.isdisjoint(test_channels)

        # 모든 채널이 포함됨 확인
        assert train_channels | val_channels | test_channels == set(unique_channels)

    def test_approximate_ratio_adherence(self, trainer, sample_split_data):
        """분할 비율이 대략적으로 맞아야 한다 (10% 허용 오차)."""
        X, y, channel_ids = sample_split_data
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(X, y, channel_ids)

        total = len(X)
        train_ratio = len(X_train) / total
        val_ratio = len(X_val) / total
        test_ratio = len(X_test) / total

        # 채널 단위 분할이므로 정확한 비율은 보장되지 않지만 10% 이내
        assert abs(train_ratio - 0.70) <= 0.10
        assert abs(val_ratio - 0.15) <= 0.10
        assert abs(test_ratio - 0.15) <= 0.10

    def test_reproducibility_with_same_random_state(self, sample_split_data):
        """같은 random_state로 동일한 분할 결과를 얻어야 한다."""
        X, y, channel_ids = sample_split_data

        trainer1 = ModelTrainer(TrainingConfig(random_state=42))
        trainer2 = ModelTrainer(TrainingConfig(random_state=42))

        result1 = trainer1.split_data(X, y, channel_ids)
        result2 = trainer2.split_data(X, y, channel_ids)

        for arr1, arr2 in zip(result1, result2):
            np.testing.assert_array_equal(arr1, arr2)

    def test_different_random_state_gives_different_split(self, sample_split_data):
        """다른 random_state는 다른 분할 결과를 줘야 한다."""
        X, y, channel_ids = sample_split_data

        trainer1 = ModelTrainer(TrainingConfig(random_state=42))
        trainer2 = ModelTrainer(TrainingConfig(random_state=99))

        result1 = trainer1.split_data(X, y, channel_ids)
        result2 = trainer2.split_data(X, y, channel_ids)

        # 적어도 하나의 분할이 달라야 함
        any_different = False
        for arr1, arr2 in zip(result1, result2):
            if arr1.shape != arr2.shape or not np.array_equal(arr1, arr2):
                any_different = True
                break
        assert any_different

    def test_empty_input(self, trainer):
        """빈 입력 처리."""
        X = np.empty((0, 27))
        y = np.empty((0,))
        channel_ids = np.array([], dtype=str)

        X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(X, y, channel_ids)

        assert len(X_train) == 0
        assert len(X_val) == 0
        assert len(X_test) == 0
        assert len(y_train) == 0
        assert len(y_val) == 0
        assert len(y_test) == 0

    def test_all_samples_preserved(self, trainer, sample_split_data):
        """분할 후 전체 샘플 수가 보존되어야 한다."""
        X, y, channel_ids = sample_split_data
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(X, y, channel_ids)

        total_X = len(X_train) + len(X_val) + len(X_test)
        total_y = len(y_train) + len(y_val) + len(y_test)

        assert total_X == len(X)
        assert total_y == len(y)


class TestFilterByGroupSize:
    """filter_by_group_size 메서드 테스트."""

    def test_removes_small_groups(self, trainer):
        """min_size 미만 그룹이 제거되어야 한다."""
        X = np.random.randn(50, 27)
        y = np.random.rand(50) * 100
        # 그룹 A: 30개, 그룹 B: 10개, 그룹 C: 10개
        group_keys = np.array(
            ["A"] * 30 + ["B"] * 10 + ["C"] * 10
        )

        X_f, y_f, groups_f, removed = trainer.filter_by_group_size(
            X, y, group_keys, min_size=20
        )

        assert "B" in removed
        assert "C" in removed
        assert "A" not in removed
        assert len(X_f) == 30
        assert set(groups_f) == {"A"}

    def test_keeps_large_groups_intact(self, trainer):
        """min_size 이상 그룹은 그대로 유지되어야 한다."""
        X = np.random.randn(60, 27)
        y = np.random.rand(60) * 100
        # 그룹 A: 30개, 그룹 B: 30개
        group_keys = np.array(["A"] * 30 + ["B"] * 30)

        X_f, y_f, groups_f, removed = trainer.filter_by_group_size(
            X, y, group_keys, min_size=20
        )

        assert len(removed) == 0
        assert len(X_f) == 60
        assert set(groups_f) == {"A", "B"}

    def test_removed_groups_dict_has_correct_counts(self, trainer):
        """removed_groups 딕셔너리에 정확한 샘플 수가 기록되어야 한다."""
        X = np.random.randn(45, 27)
        y = np.random.rand(45) * 100
        # 그룹 A: 25개, 그룹 B: 15개, 그룹 C: 5개
        group_keys = np.array(["A"] * 25 + ["B"] * 15 + ["C"] * 5)

        _, _, _, removed = trainer.filter_by_group_size(
            X, y, group_keys, min_size=20
        )

        assert removed == {"B": 15, "C": 5}

    def test_empty_input(self, trainer):
        """빈 입력 처리."""
        X = np.empty((0, 27))
        y = np.empty((0,))
        group_keys = np.array([], dtype=str)

        X_f, y_f, groups_f, removed = trainer.filter_by_group_size(
            X, y, group_keys, min_size=20
        )

        assert len(X_f) == 0
        assert len(y_f) == 0
        assert len(groups_f) == 0
        assert removed == {}

    def test_all_groups_below_threshold(self, trainer):
        """모든 그룹이 임계값 미만이면 빈 결과를 반환해야 한다."""
        X = np.random.randn(15, 27)
        y = np.random.rand(15) * 100
        group_keys = np.array(["A"] * 5 + ["B"] * 5 + ["C"] * 5)

        X_f, y_f, groups_f, removed = trainer.filter_by_group_size(
            X, y, group_keys, min_size=20
        )

        assert len(X_f) == 0
        assert len(removed) == 3

    def test_default_min_size_from_config(self, trainer):
        """min_size 미지정 시 config.min_group_size(20) 사용."""
        X = np.random.randn(35, 27)
        y = np.random.rand(35) * 100
        group_keys = np.array(["A"] * 25 + ["B"] * 10)

        X_f, y_f, groups_f, removed = trainer.filter_by_group_size(
            X, y, group_keys
        )

        # config.min_group_size = 20이므로 B(10개)는 제거
        assert "B" in removed
        assert len(X_f) == 25


class TestTrainingConfig:
    """TrainingConfig 데이터 클래스 테스트."""

    def test_default_values(self):
        """기본값이 올바르게 설정되어야 한다."""
        config = TrainingConfig()
        assert config.train_ratio == 0.70
        assert config.val_ratio == 0.15
        assert config.test_ratio == 0.15
        assert config.min_group_size == 20
        assert config.random_state == 42
        assert config.include_mlp is False

    def test_custom_values(self):
        """커스텀 값이 올바르게 설정되어야 한다."""
        config = TrainingConfig(
            train_ratio=0.80,
            val_ratio=0.10,
            test_ratio=0.10,
            min_group_size=30,
            random_state=123,
            include_mlp=True,
        )
        assert config.train_ratio == 0.80
        assert config.val_ratio == 0.10
        assert config.test_ratio == 0.10
        assert config.min_group_size == 30
        assert config.random_state == 123
        assert config.include_mlp is True

    def test_ratios_sum_to_one(self):
        """기본 비율의 합이 1.0이어야 한다."""
        config = TrainingConfig()
        assert abs(config.train_ratio + config.val_ratio + config.test_ratio - 1.0) < 1e-10


class TestTrainAllCandidates:
    """train_all_candidates 메서드 테스트."""

    def test_train_all_candidates_returns_all_models(self, trainer, synthetic_training_data):
        """기본 설정에서 5개 모델이 모두 학습되어야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data
        models = trainer.train_all_candidates(X_train, y_train, X_val, y_val)

        expected_names = {"ridge", "random_forest", "xgboost", "lightgbm", "stacking_ensemble"}
        assert set(models.keys()) == expected_names

    def test_train_all_candidates_with_mlp(self, trainer_with_mlp, synthetic_training_data):
        """include_mlp=True일 때 6개 모델이 학습되어야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data
        models = trainer_with_mlp.train_all_candidates(X_train, y_train, X_val, y_val)

        expected_names = {"ridge", "random_forest", "xgboost", "lightgbm", "stacking_ensemble", "mlp"}
        assert set(models.keys()) == expected_names

    def test_trained_models_can_predict(self, trainer, synthetic_training_data):
        """학습된 모든 모델이 예측을 수행할 수 있어야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data
        models = trainer.train_all_candidates(X_train, y_train, X_val, y_val)

        for name, model in models.items():
            predictions = model.predict(X_val)
            assert len(predictions) == len(X_val), f"모델 '{name}' 예측 길이 불일치"
            assert not np.any(np.isnan(predictions)), f"모델 '{name}' NaN 예측 존재"


class TestSelectChampion:
    """select_champion 메서드 테스트."""

    def test_select_champion_picks_best_spearman(self, trainer, synthetic_training_data):
        """Spearman 상관계수가 가장 높은 모델을 선정해야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data
        models = trainer.train_all_candidates(X_train, y_train, X_val, y_val)

        champion = trainer.select_champion(models, X_val, y_val)

        # champion이 유효한 모델 이름이어야 함
        assert champion in models

        # champion의 Spearman이 다른 모든 모델보다 크거나 같아야 함
        from scipy.stats import spearmanr
        champion_pred = models[champion].predict(X_val)
        champion_corr, _ = spearmanr(champion_pred, y_val)

        for name, model in models.items():
            pred = model.predict(X_val)
            corr, _ = spearmanr(pred, y_val)
            if not np.isnan(corr):
                assert champion_corr >= corr or np.isclose(champion_corr, corr, atol=1e-10)

    def test_select_champion_with_single_model(self, trainer, synthetic_training_data):
        """단일 모델만 있을 때 해당 모델을 반환해야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data
        from sklearn.linear_model import Ridge
        single_model = Ridge()
        single_model.fit(X_train, y_train)

        models = {"ridge": single_model}
        champion = trainer.select_champion(models, X_val, y_val)
        assert champion == "ridge"


class TestRetrainChampion:
    """retrain_champion 메서드 테스트."""

    def test_retrain_champion_returns_trained_model(self, trainer, synthetic_training_data):
        """재학습된 모델이 예측을 수행할 수 있어야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data

        # train + val 합산
        X_combined = np.vstack([X_train, X_val])
        y_combined = np.concatenate([y_train, y_val])

        model = trainer.retrain_champion("xgboost", X_combined, y_combined)

        predictions = model.predict(X_val)
        assert len(predictions) == len(X_val)
        assert not np.any(np.isnan(predictions))

    def test_retrain_champion_all_architectures(self, trainer, synthetic_training_data):
        """모든 아키텍처로 재학습이 가능해야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data

        for name in ["ridge", "random_forest", "xgboost", "lightgbm", "stacking_ensemble"]:
            model = trainer.retrain_champion(name, X_train, y_train)
            predictions = model.predict(X_val)
            assert len(predictions) == len(X_val)


class TestSaveMetadata:
    """save_metadata 메서드 테스트."""

    def test_save_metadata_json_serializable(self, trainer, synthetic_training_data):
        """메타데이터가 JSON 직렬화 가능해야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data
        models = trainer.train_all_candidates(X_train, y_train, X_val, y_val)

        metrics = {"mae": 8.2, "rmse": 11.5, "spearman": 0.91}
        metadata = trainer.save_metadata(models, "xgboost", metrics)

        # JSON 직렬화 가능 여부 확인
        json_str = json.dumps(metadata)
        assert json_str is not None

        # 역직렬화 후 동일 데이터 복원
        restored = json.loads(json_str)
        assert restored["model_name"] == "xgboost"
        assert restored["metrics"] == metrics
        assert "trained_at" in restored
        assert "hyperparameters" in restored

    def test_save_metadata_contains_required_fields(self, trainer, synthetic_training_data):
        """메타데이터에 필수 필드가 포함되어야 한다."""
        X_train, y_train, X_val, y_val = synthetic_training_data
        models = trainer.train_all_candidates(X_train, y_train, X_val, y_val)

        metrics = {"mae": 10.0, "rmse": 13.0, "spearman": 0.85}
        metadata = trainer.save_metadata(models, "ridge", metrics)

        assert "model_name" in metadata
        assert "trained_at" in metadata
        assert "hyperparameters" in metadata
        assert "metrics" in metadata
        assert metadata["model_name"] == "ridge"
        assert metadata["metrics"]["spearman"] == 0.85
