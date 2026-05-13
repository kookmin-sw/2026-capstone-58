"""Label Generator 모듈.

Comparison Group 내 VPS 순위 기반으로 학습 레이블을 자동 생성한다.
"""

import warnings
from collections import defaultdict

import numpy as np
from scipy.stats import rankdata


class LabelGenerator:
    """Comparison Group 내 VPS 순위 기반 레이블 생성.

    각 그룹 내에서 VPS 순위를 산출하고,
    percent_rank * 100으로 0~100 연속 점수를 생성한다.
    """

    # 기본 레이블 가중치 (40/40/20 공식)
    DEFAULT_WEIGHTS = {"vps": 0.4, "vs_channel_avg": 0.4, "daily_views": 0.2}

    def generate_labels(
        self,
        videos: list,
        strategy: str = "multi_metric",
        weights: dict | None = None,
    ) -> np.ndarray:
        """Comparison Group별 다중 지표 가중 순위 기반 레이블 생성.

        각 Comparison Group 내에서 지표별 순위를 산출하고,
        가중합 순위를 percent_rank * 100으로 0~100 연속 점수 변환.

        Args:
            videos: 영상 데이터 딕셔너리 리스트.
                각 영상은 'vps', 'vs_channel_avg', 'daily_views',
                'comparison_group' 키를 포함해야 함.
            strategy: 레이블 전략.
                - "vps_rank": VPS 단일 지표 순위
                - "multi_metric": 다중 지표 가중 순위 (기본값)
            weights: 다중 지표 가중치 딕셔너리.
                None이면 DEFAULT_WEIGHTS(40/40/20) 사용.
                예: {"vps": 0.4, "vs_channel_avg": 0.4, "daily_views": 0.2}

        Returns:
            0~100 범위의 레이블 배열 (입력 videos와 동일 순서).
        """
        if len(videos) == 0:
            return np.array([], dtype=np.float64)

        if strategy == "multi_metric":
            if weights is None:
                weights = self.DEFAULT_WEIGHTS
            return self._generate_multi_metric_labels(videos, weights)

        return self._generate_vps_rank_labels(videos)

    def _generate_vps_rank_labels(self, videos: list) -> np.ndarray:
        """VPS 단일 지표 기반 순위 레이블 생성."""
        labels = np.zeros(len(videos), dtype=np.float64)

        # Group videos by comparison_group
        groups: dict[str, list[int]] = defaultdict(list)
        for idx, video in enumerate(videos):
            groups[video["comparison_group"]].append(idx)

        for _group_key, indices in groups.items():
            group_size = len(indices)

            if group_size == 1:
                # 단일 영상 그룹: percent_rank = 0.5
                labels[indices[0]] = 50.0
                continue

            # VPS 값 추출
            vps_values = np.array(
                [videos[i]["vps"] for i in indices], dtype=np.float64
            )

            # 평균 순위 (동점 처리: method='average')
            ranks = rankdata(vps_values, method="average")

            # percent_rank = (rank - 1) / (group_size - 1)
            percent_ranks = (ranks - 1) / (group_size - 1)

            # 0~100 변환
            for i, idx in enumerate(indices):
                labels[idx] = percent_ranks[i] * 100.0

        return labels

    def _generate_multi_metric_labels(
        self, videos: list, weights: dict
    ) -> np.ndarray:
        """다중 지표 가중 순위 기반 레이블 생성.

        각 그룹 내에서 각 지표별 순위를 산출하고,
        가중합으로 종합 순위를 계산한 뒤 percent_rank * 100으로 변환.
        """
        labels = np.zeros(len(videos), dtype=np.float64)

        # Group videos by comparison_group
        groups: dict[str, list[int]] = defaultdict(list)
        for idx, video in enumerate(videos):
            groups[video["comparison_group"]].append(idx)

        for _group_key, indices in groups.items():
            group_size = len(indices)

            if group_size == 1:
                labels[indices[0]] = 50.0
                continue

            # 각 지표별 순위 산출 후 가중합
            weighted_ranks = np.zeros(group_size, dtype=np.float64)

            for metric, weight in weights.items():
                metric_values = np.array(
                    [videos[i][metric] for i in indices], dtype=np.float64
                )
                ranks = rankdata(metric_values, method="average")
                weighted_ranks += ranks * weight

            # 가중합 순위를 다시 순위로 변환 (최종 순위)
            final_ranks = rankdata(weighted_ranks, method="average")

            # percent_rank = (rank - 1) / (group_size - 1)
            percent_ranks = (final_ranks - 1) / (group_size - 1)

            for i, idx in enumerate(indices):
                labels[idx] = percent_ranks[i] * 100.0

        return labels

    def validate_distribution(self, labels: np.ndarray) -> dict:
        """레이블 분포 검증.

        0~100을 5개 구간으로 나누어 분포를 확인하고,
        특정 구간에 80% 이상 집중되면 경고를 발생시킨다.

        Args:
            labels: 레이블 배열.

        Returns:
            {"is_uniform": bool, "concentration_warning": str | None}
        """
        if len(labels) == 0:
            return {"is_uniform": True, "concentration_warning": None}

        total = len(labels)

        # 5개 구간: [0,20), [20,40), [40,60), [60,80), [80,100]
        bin_edges = [0, 20, 40, 60, 80, 100]
        bin_labels = ["[0,20)", "[20,40)", "[40,60)", "[60,80)", "[80,100]"]

        for i in range(5):
            lower = bin_edges[i]
            upper = bin_edges[i + 1]

            if i < 4:
                # [lower, upper)
                count = np.sum((labels >= lower) & (labels < upper))
            else:
                # [80, 100] (마지막 구간은 100 포함)
                count = np.sum((labels >= lower) & (labels <= upper))

            concentration = count / total

            if concentration > 0.80:
                warning_msg = (
                    f"레이블의 {concentration * 100:.1f}%가 "
                    f"{bin_labels[i]} 구간에 집중되어 있습니다."
                )
                warnings.warn(warning_msg, stacklevel=2)
                return {
                    "is_uniform": False,
                    "concentration_warning": warning_msg,
                }

        return {"is_uniform": True, "concentration_warning": None}
