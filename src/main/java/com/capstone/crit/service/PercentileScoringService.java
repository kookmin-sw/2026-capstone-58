package com.capstone.crit.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;

import java.io.InputStream;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * S3에 저장된 백분위 테이블을 기반으로 영상 점수를 계산하는 서비스.
 * 비교 그룹 = 구독자 구간 × 숏폼/롱폼 × 카테고리
 * 점수 = VPS 백분위 × 0.40 + 채널평균대비 백분위 × 0.40 + 일평균조회수 백분위 × 0.20
 */
@Service
@Slf4j
public class PercentileScoringService {

    private final S3Client s3Client;
    private final String bucket;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // 그룹키 → 지표별 백분위 배열 (101개 경계값)
    private final Map<String, Map<String, double[]>> tables = new ConcurrentHashMap<>();
    private String collectedAt;

    public PercentileScoringService(
            @Value("${aws.region:us-east-1}") String region,
            @Value("${aws.s3.scoring-bucket}") String bucket) {
        this.s3Client = S3Client.builder()
                .region(Region.of(region))
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
        this.bucket = bucket;
    }

    @PostConstruct
    public void init() {
        loadFromS3();
    }

    /** 1시간마다 S3에서 최신 테이블 갱신 */
    @Scheduled(fixedRate = 3600000)
    public void refresh() {
        loadFromS3();
    }

    private void loadFromS3() {
        try {
            InputStream is = s3Client.getObject(GetObjectRequest.builder()
                    .bucket(bucket).key("latest.json").build());
            JsonNode root = objectMapper.readTree(is);
            is.close();

            this.collectedAt = root.path("collected_at").asText();
            JsonNode tablesNode = root.path("tables");

            Map<String, Map<String, double[]>> newTables = new HashMap<>();
            tablesNode.fieldNames().forEachRemaining(key -> {
                JsonNode group = tablesNode.get(key);
                Map<String, double[]> metrics = new HashMap<>();
                for (String metric : List.of("vps", "engagement", "like_rate", "vs_channel_avg", "daily_views")) {
                    JsonNode arr = group.path(metric);
                    if (arr.isArray()) {
                        double[] vals = new double[arr.size()];
                        for (int i = 0; i < arr.size(); i++) vals[i] = arr.get(i).asDouble();
                        metrics.put(metric, vals);
                    }
                }
                newTables.put(key, metrics);
            });

            this.tables.clear();
            this.tables.putAll(newTables);
            log.info("백분위 테이블 로드 완료: {}개 그룹, 수집일: {}", tables.size(), collectedAt);
        } catch (Exception e) {
            log.warn("S3 백분위 테이블 로드 실패: {}", e.getMessage());
        }
    }

    /**
     * 영상 점수 계산 (0~100)
     * @param viewCount 조회수
     * @param subscriberCount 구독자수
     * @param channelAvgViews 채널 평균 조회수
     * @param daysSinceUpload 업로드 후 경과일
     * @param durationSec 영상 길이(초)
     * @param categoryId 카테고리 ID
     */
    public ScoreResult score(long viewCount, long subscriberCount,
                             double channelAvgViews, long daysSinceUpload,
                             long durationSec, String categoryId) {
        if (viewCount == 0) {
            return new ScoreResult(0, 0, 0, 0, false);
        }

        long effectiveSubscribers = Math.max(1, subscriberCount);
        double vps = (double) viewCount / effectiveSubscribers;
        double vsChannelAvg = channelAvgViews > 0 ? (double) viewCount / channelAvgViews : 1.0;
        double dailyViews = (double) viewCount / Math.max(1, daysSinceUpload);
        boolean isShort = durationSec < 60;

        String key = subTier(subscriberCount) + "_" + (isShort ? "1" : "0") + "_" + categoryId;
        Map<String, double[]> group = tables.get(key);

        // fallback: 카테고리 무시하고 같은 구간+형식
        if (group == null) {
            for (String k : tables.keySet()) {
                if (k.startsWith(subTier(subscriberCount) + "_" + (isShort ? "1" : "0") + "_")) {
                    group = tables.get(k);
                    break;
                }
            }
        }

        if (group == null) {
            return new ScoreResult(50, 50, 50, 50, false);
        }

        int vpsScore = percentile(vps, group.get("vps"));
        int vsChAvgScore = percentile(vsChannelAvg, group.get("vs_channel_avg"));
        int dailyViewsScore = percentile(dailyViews, group.get("daily_views"));
        int total = (int) Math.round(vpsScore * 0.40 + vsChAvgScore * 0.40 + dailyViewsScore * 0.20);

        return new ScoreResult(total, vpsScore, vsChAvgScore, dailyViewsScore, true);
    }

    private int percentile(double value, double[] thresholds) {
        if (thresholds == null) return 50;
        for (int i = 0; i < thresholds.length; i++) {
            if (value <= thresholds[i]) return i;
        }
        return 100;
    }

    private String subTier(long subscribers) {
        if (subscribers < 50000) return "S";
        if (subscribers < 200000) return "M";
        if (subscribers < 500000) return "L";
        return "XL";
    }

    public boolean isLoaded() {
        return !tables.isEmpty();
    }

    public String getCollectedAt() {
        return collectedAt;
    }

    public record ScoreResult(int totalScore, int vpsScore, int vsChannelAvgScore, int dailyViewsScore, boolean matched) {}
}
