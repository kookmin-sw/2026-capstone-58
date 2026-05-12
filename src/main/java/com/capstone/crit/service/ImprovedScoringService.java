package com.capstone.crit.service;

import com.capstone.crit.entity.ChannelCache;
import com.capstone.crit.entity.VideoCache;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * 개선된 YouTube 성장 중심 점수 계산 서비스
 * 
 * 기존 알고리즘의 문제점:
 * - 대부분의 영상이 100점에 수렴
 * - 채널 성장 단계 미반영
 * - 실행 가능한 인사이트 부족
 * 
 * 개선 사항:
 * - 다층 점수 시스템 (도달, 참여, 유지, 성장)
 * - 채널 단계별 동적 가중치
 * - 카테고리별 벤치마크
 * - 시간 가중치 (최신 영상 우대)
 * - 실행 가능한 인사이트 생성
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ImprovedScoringService {

    /**
     * 채널 성장 단계 정의
     */
    public enum ChannelStage {
        EARLY(0, 1000, "초기 채널"),
        GROWTH(1000, 10000, "성장 채널"),
        MATURE(10000, 100000, "성숙 채널"),
        ESTABLISHED(100000, Long.MAX_VALUE, "대형 채널");

        private final long minSubscribers;
        private final long maxSubscribers;
        private final String label;

        ChannelStage(long minSubscribers, long maxSubscribers, String label) {
            this.minSubscribers = minSubscribers;
            this.maxSubscribers = maxSubscribers;
            this.label = label;
        }

        public static ChannelStage fromSubscribers(long subscribers) {
            for (ChannelStage stage : values()) {
                if (subscribers >= stage.minSubscribers && subscribers < stage.maxSubscribers) {
                    return stage;
                }
            }
            return ESTABLISHED;
        }

        public String getLabel() {
            return label;
        }
    }

    /**
     * 카테고리별 평균 참여도 (%)
     */
    private static final Map<String, Double> CATEGORY_AVG_ENGAGEMENT = Map.ofEntries(
            Map.entry("교육", 0.7),
            Map.entry("엔터테인먼트", 4.0),
            Map.entry("게임", 2.5),
            Map.entry("뷰티", 1.5),
            Map.entry("음악", 1.0),
            Map.entry("기술", 0.8),
            Map.entry("일상", 2.0),
            Map.entry("기타", 1.5)
    );

    /**
     * 채널 단계별 가중치
     * [도달, 참여, 유지, 성장]
     */
    private static final Map<ChannelStage, double[]> STAGE_WEIGHTS = Map.ofEntries(
            Map.entry(ChannelStage.EARLY, new double[]{0.30, 0.40, 0.20, 0.10}),
            Map.entry(ChannelStage.GROWTH, new double[]{0.40, 0.30, 0.10, 0.20}),
            Map.entry(ChannelStage.MATURE, new double[]{0.35, 0.25, 0.10, 0.30}),
            Map.entry(ChannelStage.ESTABLISHED, new double[]{0.30, 0.20, 0.10, 0.40})
    );

    /**
     * 종합 성장 점수 계산
     */
    public GrowthScoreResult calculateGrowthScore(
            VideoCache video,
            ChannelCache channel,
            List<VideoCache> channelVideos,
            String category) {

        // 1. 개별 점수 계산
        int reachScore = calculateReachScore(video.getViewCount());
        int engagementScore = calculateEngagementScore(video, channel, category);
        int retentionScore = calculateRetentionScore(video);
        int growthImpactScore = calculateGrowthImpactScore(video, channel, channelVideos);

        // 2. 채널 단계 결정
        ChannelStage stage = ChannelStage.fromSubscribers(channel.getSubscriberCount());
        double[] weights = STAGE_WEIGHTS.get(stage);

        // 3. 가중 평균 계산
        double weightedScore = reachScore * weights[0] +
                engagementScore * weights[1] +
                retentionScore * weights[2] +
                growthImpactScore * weights[3];

        // 4. 시간 가중치 적용
        double recencyWeight = calculateRecencyWeight(video.getFetchedAt());
        int finalScore = (int) Math.round(weightedScore * recencyWeight);

        // 5. 인사이트 생성
        List<String> insights = generateInsights(reachScore, engagementScore, retentionScore, growthImpactScore);

        return GrowthScoreResult.builder()
                .finalScore(Math.min(100, finalScore))
                .reachScore(reachScore)
                .engagementScore(engagementScore)
                .retentionScore(retentionScore)
                .growthImpactScore(growthImpactScore)
                .channelStage(stage.getLabel())
                .recencyWeight(recencyWeight)
                .insights(insights)
                .breakdown(new ScoreBreakdown(reachScore, engagementScore, retentionScore, growthImpactScore, weights))
                .build();
    }

    /**
     * 도달 점수 (0~40점)
     * 로그 스케일로 조회수 평가
     */
    private int calculateReachScore(long views) {
        if (views == 0) return 0;
        double logViews = Math.log10(views);
        return Math.min(40, (int) Math.round(logViews * 10));
    }

    /**
     * 참여 점수 (0~30점)
     * 채널 평균 대비 상대적 참여도 평가
     */
    private int calculateEngagementScore(VideoCache video, ChannelCache channel, String category) {
        if (video.getViewCount() == 0) return 0;

        double engagementRate = (double) (video.getLikeCount() + video.getCommentCount()) / video.getViewCount();

        // 카테고리별 벤치마크 적용
        double categoryAvgEngagement = CATEGORY_AVG_ENGAGEMENT.getOrDefault(category, 1.5) / 100.0;
        double relativeEngagement = engagementRate / Math.max(0.001, categoryAvgEngagement);

        return Math.min(30, (int) Math.round(relativeEngagement * 15));
    }

    /**
     * 유지 점수 (0~20점)
     * 댓글/좋아요 비율로 시청자 만족도 추정
     */
    private int calculateRetentionScore(VideoCache video) {
        if (video.getLikeCount() == 0) return 0;

        double commentToLikeRatio = (double) video.getCommentCount() / (video.getLikeCount() + 1);
        return Math.min(20, (int) Math.round(commentToLikeRatio * 100));
    }

    /**
     * 성장 점수 (0~10점)
     * 이 영상이 채널 성장에 얼마나 기여했는가?
     */
    private int calculateGrowthImpactScore(VideoCache video, ChannelCache channel, List<VideoCache> channelVideos) {
        if (channelVideos.isEmpty()) return 0;

        long totalChannelViews = channelVideos.stream()
                .mapToLong(VideoCache::getViewCount)
                .sum();

        if (totalChannelViews == 0) return 0;

        double videoViewRatio = (double) video.getViewCount() / totalChannelViews;
        return Math.min(10, (int) Math.round(videoViewRatio * 100));
    }

    /**
     * 시간 가중치 (Recency Weight)
     * 최신 영상에 더 높은 가중치 부여
     */
    private double calculateRecencyWeight(LocalDateTime uploadDate) {
        long daysSinceUpload = ChronoUnit.DAYS.between(uploadDate, LocalDateTime.now());

        if (daysSinceUpload < 0) daysSinceUpload = 0;
        if (daysSinceUpload > 30) return 1.0;

        return 1.0 + (1.0 - (double) daysSinceUpload / 30) * 0.3;
    }

    /**
     * 실행 가능한 인사이트 생성
     */
    private List<String> generateInsights(int reachScore, int engagementScore, int retentionScore, int growthImpactScore) {
        List<String> insights = new ArrayList<>();

        if (reachScore < 15) {
            insights.add("📌 조회수 부족: 썸네일과 제목을 개선하여 클릭률을 높이세요.");
        } else if (reachScore < 25) {
            insights.add("📌 조회수 개선 필요: SEO 최적화와 재생목록 활용을 고려하세요.");
        } else if (reachScore >= 35) {
            insights.add("✅ 도달 점수 우수: 현재의 썸네일/제목 전략을 유지하세요.");
        }

        if (engagementScore < 10) {
            insights.add("💬 참여도 낮음: 댓글 유도 질문을 추가하고 커뮤니티 탭을 활용하세요.");
        } else if (engagementScore < 20) {
            insights.add("💬 참여도 개선 필요: 시청자 피드백에 더 적극적으로 응답하세요.");
        } else if (engagementScore >= 25) {
            insights.add("✅ 참여도 우수: 시청자와의 상호작용이 잘 이루어지고 있습니다.");
        }

        if (retentionScore < 8) {
            insights.add("⏱️ 시청자 이탈 높음: 영상 길이를 5~10분으로 최적화하고 오프닝을 개선하세요.");
        } else if (retentionScore < 15) {
            insights.add("⏱️ 유지율 개선 필요: 자막을 추가하고 편집 속도를 높이세요.");
        } else if (retentionScore >= 18) {
            insights.add("✅ 유지율 우수: 시청자가 영상을 끝까지 보고 있습니다.");
        }

        if (growthImpactScore < 5) {
            insights.add("🚀 성장 기여도 낮음: 구독 유도 CTA를 추가하고 시리즈 콘텐츠를 제작하세요.");
        } else if (growthImpactScore < 8) {
            insights.add("🚀 성장 기여도 개선 필요: 채널 정체성을 강화하고 커뮤니티를 구축하세요.");
        } else if (growthImpactScore >= 9) {
            insights.add("✅ 성장 기여도 우수: 이 영상은 채널 성장에 크게 기여했습니다.");
        }

        return insights;
    }

    /**
     * 채널 평균 점수 계산
     */
    public ChannelAverageScore calculateChannelAverageScore(List<VideoCache> videos, ChannelCache channel, String category) {
        if (videos.isEmpty()) {
            return ChannelAverageScore.builder()
                    .avgReachScore(0)
                    .avgEngagementScore(0)
                    .avgRetentionScore(0)
                    .avgGrowthImpactScore(0)
                    .build();
        }

        double avgReach = 0;
        double avgEngagement = 0;
        double avgRetention = 0;
        double avgGrowthImpact = 0;

        for (VideoCache video : videos) {
            avgReach += calculateReachScore(video.getViewCount());
            avgEngagement += calculateEngagementScore(video, channel, category);
            avgRetention += calculateRetentionScore(video);
            avgGrowthImpact += calculateGrowthImpactScore(video, channel, videos);
        }

        int count = videos.size();
        return ChannelAverageScore.builder()
                .avgReachScore((int) (avgReach / count))
                .avgEngagementScore((int) (avgEngagement / count))
                .avgRetentionScore((int) (avgRetention / count))
                .avgGrowthImpactScore((int) (avgGrowthImpact / count))
                .build();
    }

    /**
     * 성장 점수 결과 DTO
     */
    public static class GrowthScoreResult {
        public int finalScore;
        public int reachScore;
        public int engagementScore;
        public int retentionScore;
        public int growthImpactScore;
        public String channelStage;
        public double recencyWeight;
        public List<String> insights;
        public ScoreBreakdown breakdown;

        public GrowthScoreResult(int finalScore, int reachScore, int engagementScore, int retentionScore,
                                int growthImpactScore, String channelStage, double recencyWeight,
                                List<String> insights, ScoreBreakdown breakdown) {
            this.finalScore = finalScore;
            this.reachScore = reachScore;
            this.engagementScore = engagementScore;
            this.retentionScore = retentionScore;
            this.growthImpactScore = growthImpactScore;
            this.channelStage = channelStage;
            this.recencyWeight = recencyWeight;
            this.insights = insights;
            this.breakdown = breakdown;
        }

        public static Builder builder() {
            return new Builder();
        }

        public static class Builder {
            private int finalScore;
            private int reachScore;
            private int engagementScore;
            private int retentionScore;
            private int growthImpactScore;
            private String channelStage;
            private double recencyWeight;
            private List<String> insights;
            private ScoreBreakdown breakdown;

            public Builder finalScore(int finalScore) {
                this.finalScore = finalScore;
                return this;
            }

            public Builder reachScore(int reachScore) {
                this.reachScore = reachScore;
                return this;
            }

            public Builder engagementScore(int engagementScore) {
                this.engagementScore = engagementScore;
                return this;
            }

            public Builder retentionScore(int retentionScore) {
                this.retentionScore = retentionScore;
                return this;
            }

            public Builder growthImpactScore(int growthImpactScore) {
                this.growthImpactScore = growthImpactScore;
                return this;
            }

            public Builder channelStage(String channelStage) {
                this.channelStage = channelStage;
                return this;
            }

            public Builder recencyWeight(double recencyWeight) {
                this.recencyWeight = recencyWeight;
                return this;
            }

            public Builder insights(List<String> insights) {
                this.insights = insights;
                return this;
            }

            public Builder breakdown(ScoreBreakdown breakdown) {
                this.breakdown = breakdown;
                return this;
            }

            public GrowthScoreResult build() {
                return new GrowthScoreResult(finalScore, reachScore, engagementScore, retentionScore,
                        growthImpactScore, channelStage, recencyWeight, insights, breakdown);
            }
        }
    }

    /**
     * 점수 구성 분석
     */
    public static class ScoreBreakdown {
        public int reachScore;
        public int engagementScore;
        public int retentionScore;
        public int growthImpactScore;
        public double[] weights;
        public double[] contributions;

        public ScoreBreakdown(int reachScore, int engagementScore, int retentionScore, int growthImpactScore, double[] weights) {
            this.reachScore = reachScore;
            this.engagementScore = engagementScore;
            this.retentionScore = retentionScore;
            this.growthImpactScore = growthImpactScore;
            this.weights = weights;
            this.contributions = new double[]{
                    reachScore * weights[0],
                    engagementScore * weights[1],
                    retentionScore * weights[2],
                    growthImpactScore * weights[3]
            };
        }
    }

    /**
     * 채널 평균 점수
     */
    public static class ChannelAverageScore {
        public int avgReachScore;
        public int avgEngagementScore;
        public int avgRetentionScore;
        public int avgGrowthImpactScore;

        public ChannelAverageScore(int avgReachScore, int avgEngagementScore, int avgRetentionScore, int avgGrowthImpactScore) {
            this.avgReachScore = avgReachScore;
            this.avgEngagementScore = avgEngagementScore;
            this.avgRetentionScore = avgRetentionScore;
            this.avgGrowthImpactScore = avgGrowthImpactScore;
        }

        public static Builder builder() {
            return new Builder();
        }

        public static class Builder {
            private int avgReachScore;
            private int avgEngagementScore;
            private int avgRetentionScore;
            private int avgGrowthImpactScore;

            public Builder avgReachScore(int avgReachScore) {
                this.avgReachScore = avgReachScore;
                return this;
            }

            public Builder avgEngagementScore(int avgEngagementScore) {
                this.avgEngagementScore = avgEngagementScore;
                return this;
            }

            public Builder avgRetentionScore(int avgRetentionScore) {
                this.avgRetentionScore = avgRetentionScore;
                return this;
            }

            public Builder avgGrowthImpactScore(int avgGrowthImpactScore) {
                this.avgGrowthImpactScore = avgGrowthImpactScore;
                return this;
            }

            public ChannelAverageScore build() {
                return new ChannelAverageScore(avgReachScore, avgEngagementScore, avgRetentionScore, avgGrowthImpactScore);
            }
        }
    }
}
