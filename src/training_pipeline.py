"""Training Pipeline 모듈.

재학습 파이프라인 오케스트레이션을 담당한다.
Champion Model 재학습, 성능 하락 감지, 모델 버전 관리를 수행한다.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.model_evaluator import ModelEvaluator
from src.model_trainer import ModelTrainer, TrainingConfig

logger = logging.getLogger(__name__)

# 구독자 구간 폴백 체인: S → M → L → XL
_SUB_TIER_FALLBACK = {"S": "M", "M": "L", "L": "XL", "XL": "XL"}


@dataclass
class PipelineConfig:
    """파이프라인 설정.

    Attributes:
        s3_bucket: S3 버킷 이름.
        model_prefix: 모델 아티팩트 S3 경로 프리픽스.
        champion_name: 현재 Champion 모델 이름.
        retrain_history_key: 재학습 이력 S3 키.
        max_consecutive_degradations: 연속 하락 허용 횟수 (기본 3).
        versions_dir: 모델 버전 이력 저장 디렉토리.
    """

    s3_bucket: str = ""
    model_prefix: str = "models/"
    champion_name: str = ""
    retrain_history_key: str = "training/retrain_history.json"
    max_consecutive_degradations: int = 3
    versions_dir: str = "versions/"


class TrainingPipeline:
    """재학습 파이프라인 오케스트레이터.

    Champion Model 재학습을 실행하고,
    성능 하락 감지 및 전체 모델 재선정 권고를 수행한다.
    """

    def __init__(self, config: PipelineConfig):
        """TrainingPipeline 초기화.

        Args:
            config: 파이프라인 설정 (S3 경로, Champion 정보, 성능 이력 등).
        """
        self.config = config
        self.evaluator = ModelEvaluator()
        self.trainer = ModelTrainer(TrainingConfig())
        self.retrain_history: list = []
        self.current_model = None

    def check_degradation(self, history: list) -> bool:
        """3회 연속 성능 하락 여부 확인.

        Args:
            history: 메트릭 딕셔너리 리스트 (각 항목에 "spearman" 키 포함),
                     시간순 정렬.

        Returns:
            True이면 마지막 3개 항목의 Spearman이 연속 감소, False이면 정상.
        """
        if len(history) < 3:
            return False

        return (
            history[-3]["spearman"] > history[-2]["spearman"]
            and history[-2]["spearman"] > history[-1]["spearman"]
        )

    def recommend_reselection(self) -> str:
        """전체 모델 재선정 권고 메시지.

        3회 연속 성능 하락 시 전체 후보 모델 재선정을 권고한다.

        Returns:
            권고 메시지 문자열.
        """
        return "Champion 모델의 성능이 3회 연속 하락했습니다. 전체 모델 재선정을 권고합니다."

    def run_retrain(
        self,
        new_data_key: str,
        X_train=None,
        y_train=None,
        X_val=None,
        y_val=None,
        current_metrics=None,
    ) -> dict:
        """Champion Model 재학습 실행.

        새 데이터를 병합하여 Champion 아키텍처로만 재학습하고,
        성능 비교 후 조건부 배포를 수행한다.

        Args:
            new_data_key: 새 학습 데이터의 S3 키 (현재 미사용, 향후 S3 연동용).
            X_train: 학습 피처 (직접 전달, 테스트 용이성).
            y_train: 학습 레이블.
            X_val: 검증 피처.
            y_val: 검증 레이블.
            current_metrics: 현재 배포 모델의 메트릭 딕셔너리
                             (spearman 키 포함).

        Returns:
            {
                "success": bool,
                "deployed": bool,
                "metrics": dict,
                "error": str | None
            }
        """
        try:
            # Champion 아키텍처로 재학습
            champion_name = self.config.champion_name
            new_model = self.trainer.retrain_champion(champion_name, X_train, y_train)

            # 새 모델 평가
            new_metrics = self.evaluator.evaluate(new_model, X_val, y_val)

            # 현재 모델과 성능 비교
            if current_metrics is not None:
                should_deploy = self.evaluator.check_deployment_gate(
                    new_metrics, current_metrics
                )
            else:
                # 현재 메트릭이 없으면 무조건 배포
                should_deploy = True

            if should_deploy:
                self.current_model = new_model

            # 이력에 기록
            self.retrain_history.append(new_metrics)

            return {
                "success": True,
                "deployed": should_deploy,
                "metrics": new_metrics,
                "error": None,
            }

        except Exception as e:
            logger.error(f"재학습 중 오류 발생: {e}")
            return {
                "success": False,
                "deployed": False,
                "metrics": {},
                "error": str(e),
            }

    def get_fallback_group(self, group_key: str) -> str:
        """소규모 그룹(< 20 샘플)에 대한 폴백 그룹 결정.

        구독자 구간(sub_tier)만 상위 구간으로 변경하여 폴백 그룹을 반환한다.
        그룹 키 형식: "{sub_tier}_{is_short}_{category_id}"
        폴백 체인: S → M → L → XL (XL이면 더 이상 폴백 없음)

        Args:
            group_key: 현재 그룹 키 (예: "S_0_20").

        Returns:
            폴백 그룹 키 (예: "M_0_20"). XL이면 동일 키 반환.
        """
        parts = group_key.split("_", 1)
        sub_tier = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        fallback_tier = _SUB_TIER_FALLBACK.get(sub_tier, sub_tier)

        if rest:
            return f"{fallback_tier}_{rest}"
        return fallback_tier

    def save_version(self, model, metrics: dict, version_label: str) -> str:
        """모델 버전을 versions/ 디렉토리에 저장.

        Args:
            model: 저장할 모델 객체.
            metrics: 모델 메트릭.
            version_label: 버전 라벨 (예: "v1_20260501").

        Returns:
            저장된 메타데이터 파일 경로.
        """
        versions_dir = self.config.versions_dir
        os.makedirs(versions_dir, exist_ok=True)

        meta_path = os.path.join(versions_dir, f"{version_label}_meta.json")
        metadata = {
            "version": version_label,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "champion_name": self.config.champion_name,
            "metrics": metrics,
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return meta_path

    def rollback(self, version_label: str) -> dict:
        """이전 버전으로 롤백.

        Args:
            version_label: 롤백할 버전 라벨.

        Returns:
            {"success": bool, "version": str, "error": str | None}
        """
        versions_dir = self.config.versions_dir
        meta_path = os.path.join(versions_dir, f"{version_label}_meta.json")

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            return {
                "success": True,
                "version": version_label,
                "metadata": metadata,
                "error": None,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "version": version_label,
                "metadata": None,
                "error": f"버전 '{version_label}'을 찾을 수 없습니다.",
            }
        except Exception as e:
            return {
                "success": False,
                "version": version_label,
                "metadata": None,
                "error": str(e),
            }
