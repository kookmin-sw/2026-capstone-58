"""Feature Engineer 모듈.

학습/추론 공통 피처 변환 파이프라인을 제공한다.
수치 피처(9개) + 범주형 One-Hot(18개) = 총 27차원 피처 벡터를 생성한다.
"""

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd


# 스케일링 대상 수치 피처 (log1p 변환 적용)
SCALABLE_FEATURES = [
    "vps_raw",
    "engagement_rate_raw",
    "like_rate_raw",
    "vs_channel_avg_raw",
    "daily_views_raw",
    "duration_sec",
    "days_since_upload",
    "subscriber_count",
]


# 구독자 구간 경계값
SUB_TIER_BOUNDARIES = {
    "S": (0, 50_000),
    "M": (50_000, 200_000),
    "L": (200_000, 500_000),
    "XL": (500_000, float("inf")),
}

# feature_config.json에 정의된 카테고리 ID 목록
CATEGORY_IDS = ["1", "2", "10", "15", "17", "20", "22", "23", "24", "25", "26", "28"]

# 피처 컬럼 순서 (총 31차원)
NUMERIC_FEATURES = [
    "vps_raw",
    "vps_percentile",
    "engagement_rate_raw",
    "engagement_percentile",
    "like_rate_raw",
    "like_rate_percentile",
    "vs_channel_avg_raw",
    "vs_channel_avg_percentile",
    "daily_views_raw",
    "daily_views_percentile",
    "duration_sec",
    "days_since_upload",
    "subscriber_count",
]

SUB_TIER_COLUMNS = ["sub_tier_S", "sub_tier_M", "sub_tier_L", "sub_tier_XL"]
IS_SHORT_COLUMNS = ["is_short_0", "is_short_1"]
CATEGORY_COLUMNS = [f"category_id_{cid}" for cid in CATEGORY_IDS]

ALL_FEATURE_COLUMNS = NUMERIC_FEATURES + SUB_TIER_COLUMNS + IS_SHORT_COLUMNS + CATEGORY_COLUMNS

TOTAL_FEATURE_DIM = 31


class FeatureEngineer:
    """학습/추론 공통 피처 변환 파이프라인.

    백분위 테이블과 스케일러 파라미터를 기반으로
    원시 영상 데이터를 ML 모델 입력 피처로 변환한다.
    """

    def __init__(self, percentile_tables: dict, scaler_params: dict = None):
        """FeatureEngineer 초기화.

        Args:
            percentile_tables: S3 latest.json의 tables 딕셔너리.
                각 Comparison Group별 백분위 배열을 포함.
                형식: {group_key: {"vps": [...], "engagement_rate": [...], "like_rate": [...]}}
            scaler_params: 학습 시 fit된 스케일러 파라미터 (추론 시 로드).
                None이면 스케일링 미적용.
        """
        self.percentile_tables = percentile_tables
        self.scaler_params = scaler_params

    def _determine_sub_tier(self, subscriber_count: int) -> str:
        """구독자 수로 구독자 구간(sub_tier)을 결정한다.

        Args:
            subscriber_count: 채널 구독자 수.

        Returns:
            구독자 구간 문자열 ("S", "M", "L", "XL").
        """
        if subscriber_count < 50_000:
            return "S"
        elif subscriber_count < 200_000:
            return "M"
        elif subscriber_count < 500_000:
            return "L"
        else:
            return "XL"

    def _compute_comparison_group(self, video_data: dict) -> str:
        """영상 데이터에서 Comparison Group 키를 생성한다.

        형식: {sub_tier}_{is_short_int}_{category_id}

        Args:
            video_data: 영상 원시 데이터 딕셔너리.

        Returns:
            Comparison Group 키 문자열 (예: "L_0_20").
        """
        sub_tier = self._determine_sub_tier(video_data["subscriber_count"])
        is_short_int = 1 if video_data.get("is_short", False) else 0
        category_id = str(video_data.get("category_id", "1"))
        return f"{sub_tier}_{is_short_int}_{category_id}"

    def _lookup_percentile(self, value: float, sorted_values: list) -> float:
        """정렬된 백분위 배열에서 값의 백분위를 계산한다.

        np.searchsorted를 사용하여 이진 탐색으로 위치를 찾고,
        0~1 범위의 백분위를 반환한다.

        Args:
            value: 조회할 값.
            sorted_values: 0번째~100번째 백분위에 해당하는 정렬된 값 배열 (101개).

        Returns:
            0~1 범위의 백분위 값.
        """
        arr = np.array(sorted_values)
        idx = np.searchsorted(arr, value, side="right")
        # idx는 0~101 범위. 101개 값이므로 백분위는 idx / 100
        percentile = min(idx, 100) / 100.0
        return percentile

    def _compute_days_since_upload(self, published_at: str) -> float:
        """업로드 후 경과일을 계산한다.

        Args:
            published_at: ISO 8601 형식의 업로드 일시 문자열.

        Returns:
            업로드 후 경과일 (float).
        """
        if published_at is None:
            return 0.0

        try:
            # ISO 8601 파싱
            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - pub_date
            return max(delta.total_seconds() / 86400.0, 0.0)
        except (ValueError, TypeError):
            return 0.0

    def _apply_scaling(self, feature_name: str, value: float) -> float:
        """스케일러 파라미터를 사용하여 단일 수치 피처에 클리핑 + log1p 변환을 적용한다.

        Args:
            feature_name: 피처 이름 (scaler_params의 키).
            value: 원시 피처 값.

        Returns:
            변환된 피처 값. scaler_params에 해당 피처가 없으면 원시값 반환.
        """
        scalers = self.scaler_params.get("scalers", {})
        if feature_name not in scalers:
            return value

        params = scalers[feature_name]
        clip_min = params.get("clip_min", 0.0)
        clip_max = params.get("clip_max", float("inf"))

        # 클리핑 후 log1p 적용
        clipped = np.clip(value, clip_min, clip_max)
        return float(np.log1p(clipped))

    def transform(self, video_data: dict) -> np.ndarray:
        """단일 영상 → 피처 벡터 변환 (추론용).

        Args:
            video_data: 영상 원시 데이터 딕셔너리.
                필수 키: view_count, like_count, comment_count,
                subscriber_count, duration_sec, category_id,
                is_short, published_at

        Returns:
            27차원 numpy 배열 (피처 벡터).
        """
        # 원시값 계산
        view_count = max(video_data.get("view_count", 0), 0)
        like_count = max(video_data.get("like_count", 0), 0)
        comment_count = max(video_data.get("comment_count", 0), 0)
        subscriber_count = max(video_data.get("subscriber_count", 1), 1)
        duration_sec = max(video_data.get("duration_sec", 0), 0)

        # VPS, Engagement Rate, Like Rate, vs_channel_avg, daily_views 계산
        vps_raw = view_count / subscriber_count
        engagement_rate_raw = (
            (like_count + comment_count) / view_count if view_count > 0 else 0.0
        )
        like_rate_raw = like_count / view_count if view_count > 0 else 0.0
        vs_channel_avg_raw = float(video_data.get("vs_channel_avg", 1.0))
        daily_views_raw = float(video_data.get("daily_views", 0.0))

        # Comparison Group 결정 및 백분위 계산
        group_key = self._compute_comparison_group(video_data)
        group_table = self.percentile_tables.get(group_key)

        if group_table is not None:
            vps_percentile = self._lookup_percentile(vps_raw, group_table["vps"])
            engagement_percentile = self._lookup_percentile(
                engagement_rate_raw, group_table["engagement_rate"]
            )
            like_rate_percentile = self._lookup_percentile(
                like_rate_raw, group_table["like_rate"]
            )
            vs_channel_avg_percentile = self._lookup_percentile(
                vs_channel_avg_raw, group_table.get("vs_channel_avg", [0, 1])
            )
            daily_views_percentile = self._lookup_percentile(
                daily_views_raw, group_table.get("daily_views", [0, 1])
            )
        else:
            # 그룹 테이블이 없으면 0.5 (중간값) 사용
            vps_percentile = 0.5
            engagement_percentile = 0.5
            like_rate_percentile = 0.5
            vs_channel_avg_percentile = 0.5
            daily_views_percentile = 0.5

        # days_since_upload 계산
        days_since_upload = self._compute_days_since_upload(
            video_data.get("published_at")
        )

        # 스케일링 적용 (scaler_params가 있을 때만)
        if self.scaler_params is not None:
            vps_raw = self._apply_scaling("vps_raw", vps_raw)
            engagement_rate_raw = self._apply_scaling(
                "engagement_rate_raw", engagement_rate_raw
            )
            like_rate_raw = self._apply_scaling("like_rate_raw", like_rate_raw)
            vs_channel_avg_raw = self._apply_scaling(
                "vs_channel_avg_raw", vs_channel_avg_raw
            )
            daily_views_raw = self._apply_scaling(
                "daily_views_raw", daily_views_raw
            )
            duration_sec = self._apply_scaling("duration_sec", float(duration_sec))
            days_since_upload = self._apply_scaling(
                "days_since_upload", days_since_upload
            )
            subscriber_count = self._apply_scaling(
                "subscriber_count", float(subscriber_count)
            )

        # 수치 피처 (13개)
        numeric = np.array(
            [
                vps_raw,
                vps_percentile,
                engagement_rate_raw,
                engagement_percentile,
                like_rate_raw,
                like_rate_percentile,
                vs_channel_avg_raw,
                vs_channel_avg_percentile,
                daily_views_raw,
                daily_views_percentile,
                float(duration_sec),
                days_since_upload,
                float(subscriber_count),
            ],
            dtype=np.float64,
        )

        # 범주형 피처: sub_tier One-Hot (4개)
        # sub_tier는 원래 subscriber_count 기반이므로 스케일링 전 값 사용
        original_subscriber_count = max(video_data.get("subscriber_count", 1), 1)
        sub_tier = self._determine_sub_tier(original_subscriber_count)
        sub_tier_onehot = np.array(
            [1.0 if t == sub_tier else 0.0 for t in ["S", "M", "L", "XL"]],
            dtype=np.float64,
        )

        # 범주형 피처: is_short One-Hot (2개)
        is_short_val = 1 if video_data.get("is_short", False) else 0
        is_short_onehot = np.array(
            [1.0 if v == is_short_val else 0.0 for v in [0, 1]],
            dtype=np.float64,
        )

        # 범주형 피처: category_id One-Hot (12개)
        category_id = str(video_data.get("category_id", ""))
        category_onehot = np.array(
            [1.0 if cid == category_id else 0.0 for cid in CATEGORY_IDS],
            dtype=np.float64,
        )

        # 전체 피처 벡터 결합 (27차원)
        feature_vector = np.concatenate(
            [numeric, sub_tier_onehot, is_short_onehot, category_onehot]
        )

        assert len(feature_vector) == TOTAL_FEATURE_DIM, (
            f"Expected {TOTAL_FEATURE_DIM} features, got {len(feature_vector)}"
        )

        return feature_vector

    def transform_batch(self, videos: list) -> pd.DataFrame:
        """영상 리스트 → 피처 DataFrame 변환 (학습용).

        Args:
            videos: 영상 원시 데이터 딕셔너리 리스트.

        Returns:
            피처 DataFrame (행: 영상, 열: 27개 피처).
        """
        rows = []
        for video in videos:
            feature_vector = self.transform(video)
            rows.append(feature_vector)

        df = pd.DataFrame(rows, columns=ALL_FEATURE_COLUMNS)
        return df

    def fit_scalers(self, videos: list) -> dict:
        """학습 데이터로 스케일러 파라미터 fit.

        각 스케일링 대상 수치 피처에 대해 학습 데이터의 실제 min/max를
        계산하여 클리핑 경계로 사용한다.

        Args:
            videos: 학습용 영상 데이터 리스트.

        Returns:
            스케일러 파라미터 딕셔너리 (JSON 저장용).
        """
        if not videos:
            return {
                "fitted_at": datetime.now(timezone.utc).isoformat(),
                "scalers": {},
            }

        # 각 피처의 원시값을 수집
        raw_values = {feat: [] for feat in SCALABLE_FEATURES}

        for video in videos:
            view_count = max(video.get("view_count", 0), 0)
            like_count = max(video.get("like_count", 0), 0)
            comment_count = max(video.get("comment_count", 0), 0)
            subscriber_count = max(video.get("subscriber_count", 1), 1)
            duration_sec = max(video.get("duration_sec", 0), 0)

            vps_raw = view_count / subscriber_count
            engagement_rate_raw = (
                (like_count + comment_count) / view_count if view_count > 0 else 0.0
            )
            like_rate_raw = like_count / view_count if view_count > 0 else 0.0
            days_since_upload = self._compute_days_since_upload(
                video.get("published_at")
            )

            raw_values["vps_raw"].append(vps_raw)
            raw_values["engagement_rate_raw"].append(engagement_rate_raw)
            raw_values["like_rate_raw"].append(like_rate_raw)
            raw_values["vs_channel_avg_raw"].append(float(video.get("vs_channel_avg", 1.0)))
            raw_values["daily_views_raw"].append(float(video.get("daily_views", 0.0)))
            raw_values["duration_sec"].append(float(duration_sec))
            raw_values["days_since_upload"].append(days_since_upload)
            raw_values["subscriber_count"].append(float(subscriber_count))

        # 각 피처별 clip_min, clip_max 계산 (실제 데이터의 min/max)
        scalers = {}
        for feat in SCALABLE_FEATURES:
            values = raw_values[feat]
            if values:
                scalers[feat] = {
                    "type": "log1p",
                    "clip_min": float(min(values)),
                    "clip_max": float(max(values)),
                }

        return {
            "fitted_at": datetime.now(timezone.utc).isoformat(),
            "scalers": scalers,
        }

    def clip_outliers(self, features: pd.DataFrame, group_key: str) -> pd.DataFrame:
        """Comparison Group 내 상위/하위 1% 클리핑 (윈저화).

        수치 피처(스케일링 대상)에 대해 해당 그룹의 1st/99th 백분위를
        계산하고, 모든 값을 [p1, p99] 범위로 클리핑한다.

        Args:
            features: 피처 DataFrame.
            group_key: Comparison Group 키 (예: "L_0_20").

        Returns:
            클리핑된 피처 DataFrame.
        """
        # 그룹이 백분위 테이블에 없으면 변환 없이 반환
        if group_key not in self.percentile_tables:
            return features

        result = features.copy()

        # 스케일링 대상 수치 피처만 클리핑 (백분위 피처, one-hot 피처 제외)
        for feat in SCALABLE_FEATURES:
            if feat in result.columns:
                col_values = result[feat]
                p1 = np.percentile(col_values, 1)
                p99 = np.percentile(col_values, 99)
                result[feat] = col_values.clip(lower=p1, upper=p99)

        return result
