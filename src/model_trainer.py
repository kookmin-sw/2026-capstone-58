"""Model Trainer 모듈.

다중 모델 학습 및 Champion 선정을 담당한다.
Ridge, RandomForest, XGBoost, LightGBM, Stacking Ensemble을 학습하고
검증 세트 Spearman 기준으로 최적 모델을 선정한다.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging

import numpy as np
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """학습 설정.

    Attributes:
        train_ratio: 학습 데이터 비율 (기본 0.70).
        val_ratio: 검증 데이터 비율 (기본 0.15).
        test_ratio: 테스트 데이터 비율 (기본 0.15).
        min_group_size: Comparison Group 최소 샘플 수 (기본 20).
        random_state: 랜덤 시드.
        include_mlp: MLP 모델 포함 여부.
    """

    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    min_group_size: int = 20
    random_state: int = 42
    include_mlp: bool = False


class ModelTrainer:
    """다중 모델 학습 및 Champion 선정.

    후보 모델(Ridge, RF, XGBoost, LightGBM, Ensemble)을 학습하고,
    검증 세트 Spearman 기준으로 Champion을 선정한다.
    """

    def __init__(self, config: TrainingConfig):
        """ModelTrainer 초기화.

        Args:
            config: 학습 설정 (분할 비율, 최소 샘플 수 등).
        """
        self.config = config

    def split_data(self, X: np.ndarray, y: np.ndarray, channel_ids: np.ndarray) -> tuple:
        """채널 단위 Train/Val/Test 분할.

        같은 채널의 영상이 서로 다른 분할에 포함되지 않도록 보장한다.

        Args:
            X: 피처 매트릭스.
            y: 레이블 배열.
            channel_ids: 각 영상의 채널 ID 배열.

        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test) 튜플.
        """
        if len(X) == 0:
            empty_X = np.empty((0, X.shape[1] if X.ndim == 2 else 0))
            empty_y = np.empty((0,))
            return (empty_X, empty_X.copy(), empty_X.copy(),
                    empty_y, empty_y.copy(), empty_y.copy())

        # 고유 채널 목록 추출 및 셔플
        unique_channels = np.unique(channel_ids)
        rng = np.random.RandomState(self.config.random_state)
        rng.shuffle(unique_channels)

        # 채널을 train/val/test로 분할
        n_channels = len(unique_channels)
        n_train = int(np.round(n_channels * self.config.train_ratio))
        n_val = int(np.round(n_channels * self.config.val_ratio))

        train_channels = set(unique_channels[:n_train])
        val_channels = set(unique_channels[n_train:n_train + n_val])
        test_channels = set(unique_channels[n_train + n_val:])

        # 채널 분할을 영상 인덱스로 매핑
        train_mask = np.array([ch in train_channels for ch in channel_ids])
        val_mask = np.array([ch in val_channels for ch in channel_ids])
        test_mask = np.array([ch in test_channels for ch in channel_ids])

        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]
        X_test, y_test = X[test_mask], y[test_mask]

        return (X_train, X_val, X_test, y_train, y_val, y_test)

    def filter_by_group_size(self, X: np.ndarray, y: np.ndarray,
                             group_keys: np.ndarray,
                             min_size: int = None) -> tuple:
        """Comparison Group별 최소 샘플 수 필터링.

        min_size 미만의 샘플을 가진 그룹을 제거한다.

        Args:
            X: 피처 매트릭스.
            y: 레이블 배열.
            group_keys: 각 샘플의 Comparison Group 키 배열.
            min_size: 최소 샘플 수 (기본값: self.config.min_group_size).

        Returns:
            (X_filtered, y_filtered, group_keys_filtered, removed_groups) 튜플.
            removed_groups는 {group_key: sample_count} 딕셔너리.
        """
        if min_size is None:
            min_size = self.config.min_group_size

        if len(X) == 0:
            empty_X = np.empty((0, X.shape[1] if X.ndim == 2 else 0))
            empty_y = np.empty((0,))
            empty_groups = np.empty((0,), dtype=group_keys.dtype if len(group_keys) > 0 else object)
            return (empty_X, empty_y, empty_groups, {})

        # 그룹별 샘플 수 계산
        unique_groups, counts = np.unique(group_keys, return_counts=True)
        group_counts = dict(zip(unique_groups, counts))

        # 제거할 그룹 식별
        removed_groups = {g: int(c) for g, c in group_counts.items() if c < min_size}
        keep_groups = set(g for g, c in group_counts.items() if c >= min_size)

        # 필터링 마스크 생성
        keep_mask = np.array([g in keep_groups for g in group_keys])

        X_filtered = X[keep_mask]
        y_filtered = y[keep_mask]
        group_keys_filtered = group_keys[keep_mask]

        return (X_filtered, y_filtered, group_keys_filtered, removed_groups)

    def _create_model(self, model_name: str) -> object:
        """모델 이름으로 새 모델 인스턴스를 생성하는 팩토리 메서드.

        Args:
            model_name: 모델 이름 (ridge, random_forest, xgboost, lightgbm,
                        stacking_ensemble, mlp).

        Returns:
            초기화된 모델 인스턴스.

        Raises:
            ValueError: 알 수 없는 모델 이름인 경우.
        """
        if model_name == "ridge":
            from sklearn.linear_model import Ridge
            return Ridge()
        elif model_name == "random_forest":
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                random_state=self.config.random_state,
            )
        elif model_name == "xgboost":
            from xgboost import XGBRegressor
            return XGBRegressor(
                n_estimators=500,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.config.random_state,
            )
        elif model_name == "lightgbm":
            from lightgbm import LGBMRegressor
            return LGBMRegressor(
                n_estimators=500,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.config.random_state,
                verbose=-1,
            )
        elif model_name == "stacking_ensemble":
            from sklearn.linear_model import Ridge
            from sklearn.ensemble import RandomForestRegressor, StackingRegressor
            from xgboost import XGBRegressor
            base_estimators = [
                ("ridge", Ridge()),
                ("random_forest", RandomForestRegressor(
                    n_estimators=200,
                    max_depth=10,
                    random_state=self.config.random_state,
                )),
                ("xgboost", XGBRegressor(
                    n_estimators=500,
                    max_depth=6,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.config.random_state,
                )),
            ]
            return StackingRegressor(
                estimators=base_estimators,
                final_estimator=Ridge(),
            )
        elif model_name == "mlp":
            from sklearn.neural_network import MLPRegressor
            return MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                max_iter=500,
                random_state=self.config.random_state,
            )
        else:
            raise ValueError(f"알 수 없는 모델 이름: {model_name}")

    def train_all_candidates(self, X_train: np.ndarray, y_train: np.ndarray,
                             X_val: np.ndarray, y_val: np.ndarray) -> dict:
        """후보 모델 전부 학습.

        Ridge Regression, RandomForest, XGBoost, LightGBM,
        Stacking Ensemble을 학습한다. config.include_mlp이 True이면
        MLP도 추가로 학습한다.

        Args:
            X_train: 학습 피처.
            y_train: 학습 레이블.
            X_val: 검증 피처.
            y_val: 검증 레이블.

        Returns:
            {model_name: trained_model} 딕셔너리.
        """
        candidate_names = [
            "ridge",
            "random_forest",
            "xgboost",
            "lightgbm",
            "stacking_ensemble",
        ]

        if self.config.include_mlp:
            candidate_names.append("mlp")

        trained_models = {}
        for name in candidate_names:
            try:
                model = self._create_model(name)
                model.fit(X_train, y_train)
                trained_models[name] = model
                logger.info(f"모델 '{name}' 학습 완료.")
            except Exception as e:
                logger.warning(f"모델 '{name}' 학습 실패: {e}")

        return trained_models

    def select_champion(self, models: dict, X_val: np.ndarray, y_val: np.ndarray) -> str:
        """검증 세트 기준 최고 성능 모델 선정.

        Spearman 순위 상관계수가 가장 높은 모델을 Champion으로 선정한다.
        모든 모델이 음수 또는 NaN 상관계수를 가지면 가장 높은(덜 음수인) 값을 선택한다.

        Args:
            models: {model_name: trained_model} 딕셔너리.
            X_val: 검증 피처.
            y_val: 검증 레이블.

        Returns:
            Champion 모델 이름.
        """
        best_name = None
        best_spearman = -np.inf

        for name, model in models.items():
            try:
                y_pred = model.predict(X_val)
                corr, _ = spearmanr(y_pred, y_val)

                # NaN 처리: NaN은 -inf로 취급
                if np.isnan(corr):
                    corr = -np.inf

                if corr > best_spearman:
                    best_spearman = corr
                    best_name = name
            except Exception as e:
                logger.warning(f"모델 '{name}' 예측 실패: {e}")

        if best_name is None:
            # 모든 모델이 예측 실패한 경우 첫 번째 모델 반환
            best_name = next(iter(models))

        return best_name

    def retrain_champion(self, champion_name: str, X_train: np.ndarray,
                         y_train: np.ndarray) -> object:
        """Champion 아키텍처로만 재학습.

        Args:
            champion_name: Champion 모델 이름.
            X_train: 학습 피처 (train + val 합산 가능).
            y_train: 학습 레이블.

        Returns:
            재학습된 모델 객체.
        """
        model = self._create_model(champion_name)
        model.fit(X_train, y_train)
        return model

    def save_metadata(self, models: dict, champion_name: str, metrics: dict) -> dict:
        """모델 메타데이터를 JSON 직렬화 가능한 딕셔너리로 생성.

        Args:
            models: {model_name: trained_model} 딕셔너리.
            champion_name: Champion 모델 이름.
            metrics: 평가 메트릭 딕셔너리 (예: {"mae": 8.2, "rmse": 11.5, "spearman": 0.91}).

        Returns:
            JSON 직렬화 가능한 메타데이터 딕셔너리.
        """
        champion_model = models.get(champion_name)

        # 하이퍼파라미터 추출
        hyperparameters = {}
        if champion_model is not None and hasattr(champion_model, "get_params"):
            params = champion_model.get_params(deep=False)
            # JSON 직렬화 가능한 값만 포함
            for key, value in params.items():
                if isinstance(value, (int, float, str, bool, type(None))):
                    hyperparameters[key] = value
                elif isinstance(value, (list, tuple)):
                    # 리스트/튜플 내부에 객체가 있으면 문자열로 변환
                    try:
                        json.dumps(value)
                        hyperparameters[key] = list(value)
                    except (TypeError, ValueError):
                        hyperparameters[key] = str(value)

        metadata = {
            "model_name": champion_name,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "hyperparameters": hyperparameters,
            "metrics": metrics,
        }

        # JSON 직렬화 가능 여부 검증
        json.dumps(metadata)

        return metadata
