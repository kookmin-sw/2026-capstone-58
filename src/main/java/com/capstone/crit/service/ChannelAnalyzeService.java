package com.capstone.crit.service;

import com.capstone.crit.entity.ChannelCache;
import com.capstone.crit.entity.VideoCache;
import com.capstone.crit.repository.ChannelCacheRepository;
import com.capstone.crit.repository.VideoCacheRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.LocalDateTime;
import java.util.*;
import com.capstone.crit.service.ImprovedScoringService;

@Service
@RequiredArgsConstructor
@Slf4j
public class ChannelAnalyzeService {

    private final ChannelCacheRepository channelCacheRepository;
    private final VideoCacheRepository videoCacheRepository;
    private final BedrockService bedrockService;
    private final ImprovedScoringService improvedScoringService;
    private final PercentileScoringService percentileScoringService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${youtube.api.key}")
    private String youtubeApiKey;

    private static final int CACHE_DAYS = 30;
    private static final String YT_API = "https://www.googleapis.com/youtube/v3";

    public Map<String, Object> analyzeByInput(String input) {
        String channelId = resolveChannelId(input.trim());
        return analyze(channelId);
    }

    // 입력값 → 채널 ID 변환
    private String resolveChannelId(String input) {
        // 이미 채널 ID 형식 (UC로 시작, 24자)
        if (input.startsWith("UC") && input.length() == 24) {
            return input;
        }

        // URL에서 handle 또는 채널 ID 추출
        String handle = input;
        if (input.contains("youtube.com/channel/")) {
            // https://www.youtube.com/channel/UCxxxxxx
            String id = input.substring(input.indexOf("/channel/") + 9).split("[/?]")[0];
            if (id.startsWith("UC")) return id;
        } else if (input.contains("youtube.com/@")) {
            // https://www.youtube.com/@handle
            handle = "@" + input.substring(input.indexOf("/@") + 2).split("[/?]")[0];
        }

        // @handle → 채널 ID 변환 (YouTube API 호출)
        String forHandle = handle.startsWith("@") ? handle.substring(1) : handle;
        try {
            String url = YT_API + "/channels?part=id&forHandle=" + forHandle + "&key=" + youtubeApiKey;
            String resp = WebClient.create().get().uri(url).retrieve().bodyToMono(String.class).block();
            JsonNode items = objectMapper.readTree(resp).path("items");
            if (items.isEmpty()) throw new RuntimeException("채널을 찾을 수 없습니다: " + input);
            return items.get(0).path("id").asText();
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException("채널 ID 조회 실패: " + e.getMessage(), e);
        }
    }

    @Transactional
    public Map<String, Object> analyze(String channelId) {
        ChannelCache channel = getOrFetchChannel(channelId);
        List<VideoCache> videos = getOrFetchVideos(channelId, channel);

        int channelScore = calculateChannelScore(channel, videos);
        double growthRate = calculateGrowthRate(channel);

        // 가이드: DB에 저장된 게 없으면 생성 후 저장
        List<Map<String, String>> guides = getOrGenerateGuides(channel, videos);

        // 개선된 알고리즘으로 각 영상의 성장 점수 계산
        List<Map<String, Object>> improvedVideoScores = new ArrayList<>();
        for (VideoCache video : videos) {
            ImprovedScoringService.GrowthScoreResult scoreResult = improvedScoringService.calculateGrowthScore(
                    video, channel, videos, "기타"
            );
            improvedVideoScores.add(Map.of(
                    "videoId", video.getVideoId(),
                    "title", video.getTitle(),
                    "thumbnailUrl", video.getThumbnailUrl(),
                    "growthScore", scoreResult.finalScore,
                    "reachScore", scoreResult.reachScore,
                    "engagementScore", scoreResult.engagementScore,
                    "retentionScore", scoreResult.retentionScore,
                    "growthImpactScore", scoreResult.growthImpactScore,
                    "channelStage", scoreResult.channelStage,
                    "insights", scoreResult.insights
            ));
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("channel", Map.of(
                "channelId", channel.getChannelId(),
                "name", channel.getChannelName(),
                "profileImageUrl", channel.getProfileImageUrl(),
                "subscriberCount", channel.getSubscriberCount()
        ));
        result.put("algorithmScore", channelScore);
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("avgViewCount", channel.getAvgViewCount());
        summary.put("uploadFrequencyPerWeek", channel.getUploadFrequencyPerWeek());
        summary.put("avgWatchDurationSeconds", channel.getAvgWatchDurationSeconds());
        summary.put("subscriberGrowthRate", growthRate);
        result.put("summary", summary);
        result.put("guides", guides);
        result.put("recentVideos", videos.stream().map(v -> Map.of(
                "videoId", v.getVideoId(),
                "title", v.getTitle(),
                "thumbnailUrl", v.getThumbnailUrl(),
                "algorithmScore", v.getAlgorithmScore()
        )).toList());
        // 개선된 알고리즘 결과 추가
        result.put("improvedVideoAnalysis", improvedVideoScores);

        // 백분위 기반 점수 계산
        List<Map<String, Object>> percentileVideoScores = new ArrayList<>();
        for (VideoCache video : videos) {
            PercentileScoringService.ScoreResult sr = percentileScoringService.score(
                    video.getViewCount(), video.getLikeCount(), video.getCommentCount(),
                    video.getDurationSeconds(), channel.getSubscriberCount(), "0"
            );
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("videoId", video.getVideoId());
            entry.put("title", video.getTitle());
            entry.put("thumbnailUrl", video.getThumbnailUrl());
            entry.put("percentileScore", sr.totalScore());
            entry.put("vpsScore", sr.vpsScore());
            entry.put("engagementScore", sr.engagementScore());
            entry.put("likeRateScore", sr.likeRateScore());
            entry.put("isShort", video.getDurationSeconds() < 60);
            entry.put("matched", sr.matched());
            percentileVideoScores.add(entry);
        }
        result.put("percentileVideoAnalysis", percentileVideoScores);
        result.put("percentileDataCollectedAt", percentileScoringService.getCollectedAt());

        return result;
    }

    private ChannelCache getOrFetchChannel(String channelId) {
        Optional<ChannelCache> cached = channelCacheRepository.findByChannelId(channelId);
        if (cached.isPresent() && cached.get().getFetchedAt().isAfter(LocalDateTime.now().minusDays(CACHE_DAYS))) {
            return cached.get();
        }

        Long previousSubscriberCount = cached.map(ChannelCache::getSubscriberCount).orElse(null);
        ChannelCache fresh = fetchChannelFromYoutube(channelId, previousSubscriberCount);
        cached.ifPresent(c -> channelCacheRepository.deleteById(c.getId()));
        return channelCacheRepository.save(fresh);
    }

    private List<Map<String, String>> getOrGenerateGuides(ChannelCache channel, List<VideoCache> videos) {
        // DB에 저장된 가이드가 있으면 바로 반환
        if (channel.getGuidesJson() != null) {
            try {
                JsonNode arr = objectMapper.readTree(channel.getGuidesJson());
                List<Map<String, String>> guides = new ArrayList<>();
                for (JsonNode node : arr) {
                    guides.add(Map.of("title", node.path("title").asText(), "description", node.path("description").asText()));
                }
                return guides;
            } catch (Exception e) {
                log.warn("가이드 파싱 실패, 재생성: {}", e.getMessage());
            }
        }

        // 없으면 Bedrock으로 생성 후 DB에 저장
        List<Map<String, String>> guides = generateGuides(channel, videos);
        try {
            String json = objectMapper.writeValueAsString(guides);
            channelCacheRepository.updateGuidesJson(channel.getId(), json);
        } catch (Exception e) {
            log.warn("가이드 저장 실패: {}", e.getMessage());
        }
        return guides;
    }

    private List<VideoCache> getOrFetchVideos(String channelId, ChannelCache channel) {
        List<VideoCache> cached = videoCacheRepository.findByChannelIdOrderByVideoRankAsc(channelId);
        if (!cached.isEmpty() && cached.get(0).getFetchedAt().isAfter(LocalDateTime.now().minusDays(CACHE_DAYS))) {
            return cached;
        }

        videoCacheRepository.deleteByChannelId(channelId);
        List<VideoCache> fresh = fetchVideosFromYoutube(channelId, channel);
        return videoCacheRepository.saveAll(fresh);
    }

    private ChannelCache fetchChannelFromYoutube(String channelId, Long previousSubscriberCount) {
        try {
            String url = YT_API + "/channels?part=snippet,statistics,contentDetails&id=" + channelId + "&key=" + youtubeApiKey;
            String response = WebClient.create().get().uri(url).retrieve().bodyToMono(String.class).block();
            JsonNode item = objectMapper.readTree(response).path("items").get(0);

            JsonNode snippet = item.path("snippet");
            JsonNode stats = item.path("statistics");

            long subscriberCount = stats.path("subscriberCount").asLong();
            long totalVideos = stats.path("videoCount").asLong();

            // 업로드 빈도: 전체 영상 수 / 채널 개설 이후 주 수
            String publishedAt = snippet.path("publishedAt").asText();
            long channelAgeWeeks = Math.max(1, java.time.temporal.ChronoUnit.WEEKS.between(
                    java.time.OffsetDateTime.parse(publishedAt).toLocalDate(), java.time.LocalDate.now()));
            double uploadFreq = (double) totalVideos / channelAgeWeeks;

            return ChannelCache.builder()
                    .channelId(channelId)
                    .channelName(snippet.path("title").asText())
                    .profileImageUrl(snippet.path("thumbnails").path("default").path("url").asText())
                    .subscriberCount(subscriberCount)
                    .previousSubscriberCount(previousSubscriberCount)
                    .totalVideoCount(totalVideos)
                    .avgViewCount(stats.path("viewCount").asDouble() / Math.max(1, totalVideos))
                    .uploadFrequencyPerWeek(Math.round(uploadFreq * 10.0) / 10.0)
                    .avgWatchDurationSeconds(null) // YouTube Analytics API 보류
                    .fetchedAt(LocalDateTime.now())
                    .build();
        } catch (Exception e) {
            throw new RuntimeException("YouTube 채널 정보 조회 실패: " + e.getMessage(), e);
        }
    }

    private List<VideoCache> fetchVideosFromYoutube(String channelId, ChannelCache channel) {
        try {
            // UC → UU 변환으로 업로드 플레이리스트 ID 생성 (1 유닛)
            String uploadPlaylistId = "UU" + channelId.substring(2);
            String playlistUrl = YT_API + "/playlistItems?part=contentDetails&playlistId=" + uploadPlaylistId
                    + "&maxResults=10&key=" + youtubeApiKey;
            String playlistResp = WebClient.create().get().uri(playlistUrl).retrieve().bodyToMono(String.class).block();
            JsonNode playlistItems = objectMapper.readTree(playlistResp).path("items");

            List<String> videoIds = new ArrayList<>();
            for (JsonNode item : playlistItems) {
                videoIds.add(item.path("contentDetails").path("videoId").asText());
            }

            // 영상 상세 통계 조회
            String ids = String.join(",", videoIds);
            String videoUrl = YT_API + "/videos?part=snippet,statistics,contentDetails&id=" + ids + "&key=" + youtubeApiKey;
            String videoResp = WebClient.create().get().uri(videoUrl).retrieve().bodyToMono(String.class).block();
            JsonNode videoItems = objectMapper.readTree(videoResp).path("items");

            List<VideoCache> result = new ArrayList<>();
            int rank = 1;
            for (JsonNode item : videoItems) {
                JsonNode stats = item.path("statistics");
                long viewCount = stats.path("viewCount").asLong();
                long likeCount = stats.path("likeCount").asLong();
                long commentCount = stats.path("commentCount").asLong();
                long duration = parseDuration(item.path("contentDetails").path("duration").asText());

                int score = calculateVideoScore(viewCount, likeCount, commentCount, duration, channel.getSubscriberCount());

                result.add(VideoCache.builder()
                        .channelId(channelId)
                        .videoId(item.path("id").asText())
                        .title(item.path("snippet").path("title").asText())
                        .thumbnailUrl(item.path("snippet").path("thumbnails").path("medium").path("url").asText())
                        .viewCount(viewCount)
                        .likeCount(likeCount)
                        .commentCount(commentCount)
                        .durationSeconds(duration)
                        .algorithmScore(score)
                        .videoRank(rank++)
                        .fetchedAt(LocalDateTime.now())
                        .build());
            }
            return result;
        } catch (Exception e) {
            throw new RuntimeException("YouTube 영상 정보 조회 실패: " + e.getMessage(), e);
        }
    }

    // ISO 8601 duration (PT4M13S) → 초 변환
    private long parseDuration(String duration) {
        if (duration == null || duration.isEmpty()) return 0;
        java.time.Duration d = java.time.Duration.parse(duration);
        return d.getSeconds();
    }

    // 영상 알고리즘 점수 계산 (0~100) - 추후 정교화 가능
    private int calculateVideoScore(long views, long likes, long comments, long durationSec, long subscribers) {
        if (subscribers == 0) return 0;
        double engagementRate = (double) (likes + comments) / Math.max(1, views);
        double viewRatio = (double) views / subscribers;
        // 적정 영상 길이 보너스 (3~15분)
        double durationBonus = (durationSec >= 180 && durationSec <= 900) ? 1.2 : 1.0;
        double raw = (viewRatio * 40 + engagementRate * 100 * 40) * durationBonus;
        return Math.min(100, (int) Math.round(raw + 20)); // 기본 20점
    }

    // 채널 전체 알고리즘 점수: 영상 점수 평균
    private int calculateChannelScore(ChannelCache channel, List<VideoCache> videos) {
        if (videos.isEmpty()) return 0;
        return (int) Math.round(videos.stream().mapToInt(VideoCache::getAlgorithmScore).average().orElse(0));
    }

    // 구독자 성장률: (현재 - 이전) / 이전 * 100
    private double calculateGrowthRate(ChannelCache channel) {
        if (channel.getPreviousSubscriberCount() == null || channel.getPreviousSubscriberCount() == 0) return 0.0;
        double rate = (double) (channel.getSubscriberCount() - channel.getPreviousSubscriberCount())
                / channel.getPreviousSubscriberCount() * 100;
        return Math.round(rate * 10.0) / 10.0;
    }

    // Bedrock으로 채널 방향 가이드 생성
    private List<Map<String, String>> generateGuides(ChannelCache channel, List<VideoCache> videos) {
        try {
            String prompt = String.format(
                    "당신은 유튜브 채널 성장 전문가입니다.\n" +
                    "채널 정보:\n" +
                    "- 구독자 수: %d명\n" +
                    "- 주 업로드 빈도: %.1f회\n" +
                    "- 평균 조회수: %.0f회\n" +
                    "- 최근 영상 수: %d개\n\n" +
                    "위 데이터를 바탕으로 채널 성장을 위한 구체적인 가이드를 2~3개 제시해주세요.\n" +
                    "반드시 아래 JSON 배열 형식으로만 답변하세요. 다른 텍스트는 포함하지 마세요.\n" +
                    "[{\"title\": \"가이드 제목\", \"description\": \"구체적인 설명\"}]",
                    channel.getSubscriberCount(),
                    channel.getUploadFrequencyPerWeek(),
                    channel.getAvgViewCount(),
                    videos.size()
            );

            String raw = bedrockService.invokeModelPublic(prompt);
            // JSON 배열 파싱
            int start = raw.indexOf('[');
            int end = raw.lastIndexOf(']') + 1;
            if (start >= 0 && end > start) {
                JsonNode arr = objectMapper.readTree(raw.substring(start, end));
                List<Map<String, String>> guides = new ArrayList<>();
                for (JsonNode node : arr) {
                    guides.add(Map.of(
                            "title", node.path("title").asText(),
                            "description", node.path("description").asText()
                    ));
                }
                return guides;
            }
        } catch (Exception e) {
            log.warn("가이드 생성 실패: {}", e.getMessage());
        }
        return List.of();
    }
}
