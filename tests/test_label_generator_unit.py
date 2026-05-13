"""LabelGenerator 단위 테스트.

generate_labels 및 validate_distribution의 핵심 동작과 엣지 케이스를 검증한다.
"""

import numpy as np
import pytest

from src.label_generator import LabelGenerator


@pytest.fixture
def label_generator():
    """LabelGenerator 인스턴스."""
    return LabelGenerator()


class TestGenerateLabelsBasic:
    """generate_labels 기본 동작 테스트."""

    def test_empty_videos_returns_empty_array(self, label_generator):
        """빈 리스트 입력 시 빈 배열 반환."""
        result = label_generator.generate_labels([])
        assert isinstance(result, np.ndarray)
        assert len(result) == 0

    def test_single_video_group_returns_50(self, label_generator):
        """단일 영상 그룹은 레이블 50.0 반환."""
        videos = [{"vps": 1.0, "comparison_group": "L_0_20"}]
        result = label_generator.generate_labels(videos)
        assert result[0] == 50.0

    def test_two_videos_same_group(self, label_generator):
        """2개 영상 그룹: 낮은 VPS → 0.0, 높은 VPS → 100.0."""
        videos = [
            {"vps": 0.5, "vs_channel_avg": 0.5, "daily_views": 50.0, "comparison_group": "L_0_20"},
            {"vps": 1.5, "vs_channel_avg": 1.5, "daily_views": 150.0, "comparison_group": "L_0_20"},
        ]
        result = label_generator.generate_labels(videos)
        assert result[0] == 0.0
        assert result[1] == 100.0

    def test_three_videos_same_group(self, label_generator):
        """3개 영상 그룹: 순위에 따라 0, 50, 100."""
        videos = [
            {"vps": 3.0, "vs_channel_avg": 3.0, "daily_views": 300.0, "comparison_group": "M_0_20"},
            {"vps": 1.0, "vs_channel_avg": 1.0, "daily_views": 100.0, "comparison_group": "M_0_20"},
            {"vps": 2.0, "vs_channel_avg": 2.0, "daily_views": 200.0, "comparison_group": "M_0_20"},
        ]
        result = label_generator.generate_labels(videos)
        # 모든 지표에서 동일 순서이므로 결과도 동일
        assert result[0] == 100.0
        assert result[1] == 0.0
        assert result[2] == 50.0

    def test_labels_in_original_order(self, label_generator):
        """레이블은 입력 videos와 동일한 순서로 반환."""
        videos = [
            {"vps": 5.0, "vs_channel_avg": 5.0, "daily_views": 500.0, "comparison_group": "S_0_20"},
            {"vps": 1.0, "vs_channel_avg": 1.0, "daily_views": 100.0, "comparison_group": "S_0_20"},
            {"vps": 3.0, "vs_channel_avg": 3.0, "daily_views": 300.0, "comparison_group": "S_0_20"},
            {"vps": 4.0, "vs_channel_avg": 4.0, "daily_views": 400.0, "comparison_group": "S_0_20"},
            {"vps": 2.0, "vs_channel_avg": 2.0, "daily_views": 200.0, "comparison_group": "S_0_20"},
        ]
        result = label_generator.generate_labels(videos)
        # 모든 지표가 동일 순서이므로 VPS 순위와 동일
        np.testing.assert_array_almost_equal(
            result, [100.0, 0.0, 50.0, 75.0, 25.0]
        )

    def test_multiple_groups_independent(self, label_generator):
        """서로 다른 그룹은 독립적으로 순위 산출."""
        videos = [
            {"vps": 1.0, "vs_channel_avg": 1.0, "daily_views": 100.0, "comparison_group": "L_0_20"},
            {"vps": 2.0, "vs_channel_avg": 2.0, "daily_views": 200.0, "comparison_group": "L_0_20"},
            {"vps": 10.0, "vs_channel_avg": 10.0, "daily_views": 1000.0, "comparison_group": "M_0_20"},
            {"vps": 20.0, "vs_channel_avg": 20.0, "daily_views": 2000.0, "comparison_group": "M_0_20"},
        ]
        result = label_generator.generate_labels(videos)
        assert result[0] == 0.0
        assert result[1] == 100.0
        assert result[2] == 0.0
        assert result[3] == 100.0


class TestGenerateLabelsTiedVPS:
    """동점 VPS 처리 테스트."""

    def test_tied_vps_average_rank(self, label_generator):
        """동일 VPS 값은 평균 순위(average rank) 사용."""
        videos = [
            {"vps": 1.0, "vs_channel_avg": 1.0, "daily_views": 100.0, "comparison_group": "L_0_20"},
            {"vps": 1.0, "vs_channel_avg": 1.0, "daily_views": 100.0, "comparison_group": "L_0_20"},
            {"vps": 2.0, "vs_channel_avg": 2.0, "daily_views": 200.0, "comparison_group": "L_0_20"},
        ]
        result = label_generator.generate_labels(videos)
        # 모든 지표가 동일 순서이므로 동점 처리도 동일
        np.testing.assert_array_almost_equal(result, [25.0, 25.0, 100.0])

    def test_all_same_vps(self, label_generator):
        """모든 VPS가 동일하면 모두 같은 레이블."""
        videos = [
            {"vps": 5.0, "vs_channel_avg": 5.0, "daily_views": 500.0, "comparison_group": "L_0_20"},
            {"vps": 5.0, "vs_channel_avg": 5.0, "daily_views": 500.0, "comparison_group": "L_0_20"},
            {"vps": 5.0, "vs_channel_avg": 5.0, "daily_views": 500.0, "comparison_group": "L_0_20"},
        ]
        result = label_generator.generate_labels(videos)
        np.testing.assert_array_almost_equal(result, [50.0, 50.0, 50.0])


class TestGenerateLabelsRange:
    """레이블 범위 검증."""

    def test_labels_within_0_100(self, label_generator):
        """모든 레이블이 [0, 100] 범위 내."""
        videos = [
            {"vps": float(i), "vs_channel_avg": float(i), "daily_views": float(i * 100), "comparison_group": "L_0_20"}
            for i in range(20)
        ]
        result = label_generator.generate_labels(videos)
        assert np.all(result >= 0.0)
        assert np.all(result <= 100.0)

    def test_order_preservation(self, label_generator):
        """VPS가 높은 영상의 레이블 >= VPS가 낮은 영상의 레이블."""
        videos = [
            {"vps": float(i), "vs_channel_avg": float(i), "daily_views": float(i * 100), "comparison_group": "L_0_20"}
            for i in range(10)
        ]
        result = label_generator.generate_labels(videos)
        # 모든 지표가 동일 순서이므로 레이블도 단조 증가
        for i in range(len(result) - 1):
            assert result[i] <= result[i + 1]


class TestMultiMetricStrategy:
    """다중 지표 가중 순위 전략 테스트."""

    def test_multi_metric_basic(self, label_generator):
        """multi_metric 전략 기본 동작."""
        videos = [
            {
                "vps": 1.0,
                "vs_channel_avg": 1.0,
                "daily_views": 100.0,
                "comparison_group": "L_0_20",
            },
            {
                "vps": 2.0,
                "vs_channel_avg": 2.0,
                "daily_views": 200.0,
                "comparison_group": "L_0_20",
            },
        ]
        weights = {"vps": 0.4, "vs_channel_avg": 0.4, "daily_views": 0.2}
        result = label_generator.generate_labels(
            videos, strategy="multi_metric", weights=weights
        )
        # 모든 지표에서 두 번째 영상이 높으므로 0, 100
        assert result[0] == 0.0
        assert result[1] == 100.0

    def test_multi_metric_conflicting_metrics(self, label_generator):
        """지표 간 순위가 다를 때 가중합으로 결정."""
        videos = [
            {
                "vps": 3.0,
                "vs_channel_avg": 0.5,
                "daily_views": 50.0,
                "comparison_group": "L_0_20",
            },
            {
                "vps": 1.0,
                "vs_channel_avg": 3.0,
                "daily_views": 500.0,
                "comparison_group": "L_0_20",
            },
        ]
        weights = {"vps": 0.4, "vs_channel_avg": 0.4, "daily_views": 0.2}
        result = label_generator.generate_labels(
            videos, strategy="multi_metric", weights=weights
        )
        # video 0: vps rank=2, vca rank=1, dv rank=1
        #   weighted = 2*0.4 + 1*0.4 + 1*0.2 = 1.4
        # video 1: vps rank=1, vca rank=2, dv rank=2
        #   weighted = 1*0.4 + 2*0.4 + 2*0.2 = 1.6
        # final_ranks: video0 gets rank 1, video1 gets rank 2
        # percent_ranks: video0 = (1-1)/1 = 0.0, video1 = (2-1)/1 = 1.0
        # VPS와 vs_channel_avg 가중치가 동일하므로 video 1 (높은 vca+dv)이 더 높은 레이블
        assert result[0] == 0.0
        assert result[1] == 100.0

    def test_multi_metric_single_video(self, label_generator):
        """multi_metric 단일 영상 그룹은 50.0."""
        videos = [
            {
                "vps": 1.0,
                "vs_channel_avg": 1.0,
                "daily_views": 100.0,
                "comparison_group": "L_0_20",
            },
        ]
        weights = {"vps": 0.4, "vs_channel_avg": 0.4, "daily_views": 0.2}
        result = label_generator.generate_labels(
            videos, strategy="multi_metric", weights=weights
        )
        assert result[0] == 50.0

    def test_multi_metric_uses_default_weights_when_none(self, label_generator):
        """multi_metric 전략에 weights 미지정 시 DEFAULT_WEIGHTS(40/40/20) 사용."""
        videos = [
            {
                "vps": 1.0,
                "vs_channel_avg": 1.0,
                "daily_views": 100.0,
                "comparison_group": "L_0_20",
            },
            {
                "vps": 2.0,
                "vs_channel_avg": 2.0,
                "daily_views": 200.0,
                "comparison_group": "L_0_20",
            },
        ]
        result = label_generator.generate_labels(videos, strategy="multi_metric")
        # weights 미지정 시 DEFAULT_WEIGHTS 사용, 모든 지표에서 두 번째가 높으므로
        assert result[0] == 0.0
        assert result[1] == 100.0

    def test_multi_metric_empty_videos(self, label_generator):
        """multi_metric 빈 리스트 입력 시 빈 배열 반환."""
        weights = {"vps": 0.4, "vs_channel_avg": 0.4, "daily_views": 0.2}
        result = label_generator.generate_labels(
            [], strategy="multi_metric", weights=weights
        )
        assert len(result) == 0


class TestValidateDistribution:
    """validate_distribution 테스트."""

    def test_uniform_distribution(self, label_generator):
        """균등 분포 시 is_uniform=True."""
        # 각 구간에 동일한 수의 레이블 배치
        labels = np.array([10, 30, 50, 70, 90], dtype=np.float64)
        result = label_generator.validate_distribution(labels)
        assert result["is_uniform"] is True
        assert result["concentration_warning"] is None

    def test_concentrated_distribution_warning(self, label_generator):
        """특정 구간 80% 초과 집중 시 경고."""
        # 90%가 [0, 20) 구간에 집중
        labels = np.array(
            [5, 10, 12, 15, 18, 3, 7, 11, 14, 50], dtype=np.float64
        )
        # 10개 중 9개가 [0,20) → 90% > 80%
        result = label_generator.validate_distribution(labels)
        assert result["is_uniform"] is False
        assert result["concentration_warning"] is not None
        assert "[0,20)" in result["concentration_warning"]

    def test_exactly_80_percent_is_uniform(self, label_generator):
        """정확히 80%는 경고 미발생 (> 80% 조건)."""
        # 10개 중 8개가 [0,20) → 80% (초과가 아님)
        labels = np.array(
            [5, 10, 12, 15, 18, 3, 7, 11, 50, 70], dtype=np.float64
        )
        result = label_generator.validate_distribution(labels)
        assert result["is_uniform"] is True
        assert result["concentration_warning"] is None

    def test_concentration_in_last_bin(self, label_generator):
        """마지막 구간 [80,100] 집중 시 경고."""
        # 10개 중 9개가 [80, 100]
        labels = np.array(
            [85, 90, 92, 95, 98, 83, 87, 91, 100, 50], dtype=np.float64
        )
        result = label_generator.validate_distribution(labels)
        assert result["is_uniform"] is False
        assert result["concentration_warning"] is not None
        assert "[80,100]" in result["concentration_warning"]

    def test_empty_labels(self, label_generator):
        """빈 레이블 배열 시 is_uniform=True."""
        result = label_generator.validate_distribution(np.array([]))
        assert result["is_uniform"] is True
        assert result["concentration_warning"] is None

    def test_warning_issued(self, label_generator):
        """경고 발생 시 warnings.warn 호출 확인."""
        labels = np.array(
            [5, 10, 12, 15, 18, 3, 7, 11, 14, 50], dtype=np.float64
        )
        with pytest.warns(UserWarning):
            label_generator.validate_distribution(labels)

    def test_all_labels_in_middle_bin(self, label_generator):
        """모든 레이블이 [40,60) 구간에 집중."""
        labels = np.array([45, 50, 55, 42, 58], dtype=np.float64)
        result = label_generator.validate_distribution(labels)
        assert result["is_uniform"] is False
        assert "[40,60)" in result["concentration_warning"]
