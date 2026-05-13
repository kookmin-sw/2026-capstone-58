"""Model Server 모듈.

모델 로드 및 추론 서빙을 담당한다.
S3에서 모델 아티팩트를 로드하고, 영상 점수를 추론한다.
모델 로드 실패 시 Baseline 폴백을 제공한다.
"""

import numpy as np

from src.feature_engineer import FeatureEngineer


class ModelServer:
    """모델 로드 및 추론.

    S3에서 Champion 모델을 로드하고,
    영상 원시 데이터를 입력받아 0~100 범위의 점수를 반환한다.
    """

    def __init__(
        self,
        s3_bucket: str,
        model_key: str,
        percentile_tables: dict = None,
        model=None,
        scaler_params: dict = None,
    ):
        """ModelServer 초기화.

        S3에서 모델 아티팩트(champion_model.joblib, scaler_params.json,
        feature_config.json)를 로드한다.
        테스트 시에는 model, percentile_tables, scaler_params를 직접 주입할 수 있다.

        Args:
            s3_bucket: S3 버킷 이름.
            model_key: 모델 아티팩트 경로 프리픽스.
            percentile_tables: 백분위 테이블 딕셔너리 (직접 주입용).
            model: 학습된 모델 객체 (직접 주입용).
            scaler_params: 스케일러 파라미터 딕셔너리 (직접 주입용).
        """
        self.s3_bucket = s3_bucket
        self.model_key = model_key
        self.model = model
        self.model_version = "v1"

        # 직접 주입된 값이 없고 s3_bucket이 제공된 경우 S3에서 로드 시도
        if model is None and s3_bucket:
            try:
                self._load_from_s3()
            except Exception:
                # 모델 로드 실패 시 fallback 모드로 동작
                self.model = None

        # FeatureEngineer 초기화
        if percentile_tables is None:
            percentile_tables = {}
        self.feature_engineer = FeatureEngineer(
            percentile_tables=percentile_tables,
            scaler_params=scaler_params,
        )
        self.percentile_tables = percentile_tables

    def _load_from_s3(self):
        """S3에서 모델 아티팩트를 로드한다.

        champion_model.joblib, scaler_params.json, feature_config.json을 로드.
        현재는 placeholder로, 실제 S3 연동은 통합 테스트에서 구현.

        Raises:
            Exception: S3 로드 실패 시.
        """
        import boto3
        import joblib
        import json
        import io

        s3_client = boto3.client("s3")

        # 모델 로드
        model_obj = s3_client.get_object(
            Bucket=self.s3_bucket,
            Key=f"{self.model_key}/champion_model.joblib",
        )
        model_bytes = model_obj["Body"].read()
        self.model = joblib.load(io.BytesIO(model_bytes))

        # 메타데이터에서 버전 정보 로드
        try:
            meta_obj = s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=f"{self.model_key}/champion_meta.json",
            )
            meta = json.loads(meta_obj["Body"].read().decode("utf-8"))
            self.model_version = meta.get("version", "v1")
        except Exception:
            self.model_version = "v1"

    def predict(self, video_data: dict) -> dict:
        """단일 영상 점수 추론.

        Feature Engineer로 피처 변환 후 모델 추론을 수행한다.
        결과는 0~100 범위로 클리핑된다.
        모델이 없거나 추론 실패 시 Baseline 폴백을 사용한다.

        Args:
            video_data: 영상 원시 데이터 딕셔너리.

        Returns:
            추론 결과 딕셔너리:
                - video_id: 영상 ID
                - score: 0~100 범위의 점수
                - model_version: 모델 버전
                - comparison_group: Comparison Group 키
                - percentiles: VPS, engagement, like_rate 백분위
                - fallback_used: 폴백 사용 여부
        """
        if self.model is None:
            return self._baseline_fallback(video_data)

        try:
            # 피처 변환
            feature_vector = self.feature_engineer.transform(video_data)

            # 모델 추론 (2D 배열로 reshape)
            raw_score = self.model.predict(feature_vector.reshape(1, -1))[0]

            # 0~100 클리핑
            score = float(np.clip(raw_score, 0.0, 100.0))

            # Comparison Group 및 백분위 계산
            comparison_group = self.feature_engineer._compute_comparison_group(
                video_data
            )
            percentiles = self._compute_percentiles(video_data, comparison_group)

            return {
                "video_id": video_data.get("video_id", ""),
                "score": score,
                "model_version": self.model_version,
                "comparison_group": comparison_group,
                "percentiles": percentiles,
                "fallback_used": False,
            }

        except Exception:
            # 추론 실패 시 Baseline 폴백
            return self._baseline_fallback(video_data)

    def _baseline_fallback(self, video_data: dict) -> dict:
        """수동 가중치(60/25/15) 기반 점수 계산.

        모델 추론 실패 시 기존 수동 가중치 방식으로 점수를 계산한다.
        VPS 백분위 × 60 + 참여율 백분위 × 25 + 좋아요율 백분위 × 15
        (각 백분위는 0~1 범위이므로 결과는 0~100 범위)

        Args:
            video_data: 영상 원시 데이터 딕셔너리.

        Returns:
            폴백 결과 딕셔너리 (predict와 동일한 형식, fallback_used=True).
        """
        # Comparison Group 결정
        comparison_group = self.feature_engineer._compute_comparison_group(video_data)

        # 백분위 계산
        percentiles = self._compute_percentiles(video_data, comparison_group)

        # 수동 가중치 점수 계산: VPS*60 + engagement*25 + like_rate*15
        vps_pct = percentiles["vps"]
        engagement_pct = percentiles["engagement"]
        like_rate_pct = percentiles["like_rate"]

        score = vps_pct * 60.0 + engagement_pct * 25.0 + like_rate_pct * 15.0

        # 0~100 클리핑 (백분위가 0~1이므로 최대 100)
        score = float(np.clip(score, 0.0, 100.0))

        return {
            "video_id": video_data.get("video_id", ""),
            "score": score,
            "model_version": self.model_version,
            "comparison_group": comparison_group,
            "percentiles": percentiles,
            "fallback_used": True,
        }

    def _compute_percentiles(self, video_data: dict, comparison_group: str) -> dict:
        """영상 데이터의 VPS, engagement, like_rate 백분위를 계산한다.

        Args:
            video_data: 영상 원시 데이터 딕셔너리.
            comparison_group: Comparison Group 키.

        Returns:
            백분위 딕셔너리: {"vps": float, "engagement": float, "like_rate": float}
            각 값은 0~1 범위.
        """
        view_count = max(video_data.get("view_count", 0), 0)
        like_count = max(video_data.get("like_count", 0), 0)
        comment_count = max(video_data.get("comment_count", 0), 0)
        subscriber_count = max(video_data.get("subscriber_count", 1), 1)

        # 원시값 계산
        vps_raw = view_count / subscriber_count
        engagement_rate_raw = (
            (like_count + comment_count) / view_count if view_count > 0 else 0.0
        )
        like_rate_raw = like_count / view_count if view_count > 0 else 0.0

        # 백분위 테이블에서 조회
        group_table = self.percentile_tables.get(comparison_group)

        if group_table is not None:
            vps_pct = self.feature_engineer._lookup_percentile(
                vps_raw, group_table["vps"]
            )
            engagement_pct = self.feature_engineer._lookup_percentile(
                engagement_rate_raw, group_table["engagement_rate"]
            )
            like_rate_pct = self.feature_engineer._lookup_percentile(
                like_rate_raw, group_table["like_rate"]
            )
        else:
            # 그룹 테이블이 없으면 0.5 (중간값) 사용
            vps_pct = 0.5
            engagement_pct = 0.5
            like_rate_pct = 0.5

        return {
            "vps": vps_pct,
            "engagement": engagement_pct,
            "like_rate": like_rate_pct,
        }
