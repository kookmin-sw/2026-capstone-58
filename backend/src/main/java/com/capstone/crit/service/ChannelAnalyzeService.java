package com.capstone.crit.service;

import com.capstone.crit.entity.ChannelCache;
import com.capstone.crit.entity.VideoCache;
import com.capstone.crit.repository.ChannelCacheRepository;
import com.capstone.crit.repository.UserRepository;
import com.capstone.crit.repository.VideoCacheRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import org.springframework.http.MediaType;
import com.capstone.crit.service.ImprovedScoringService;

@Service
@RequiredArgsConstructor
@Slf4j
public class ChannelAnalyzeService {

    private final ChannelCacheRepository channelCacheRepository;
    private final VideoCacheRepository videoCacheRepository;
    private final UserRepository userRepository;
    private final BedrockService bedrockService;
    private final ImprovedScoringService improvedScoringService;
    private final PercentileScoringService percentileScoringService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${youtube.api.key}")
    private String youtubeApiKey;

    @Value("${spring.security.oauth2.client.registration.google.client-id}")
    private String googleClientId;

    @Value("${spring.security.oauth2.client.registration.google.client-secret}")
    private String googleClientSecret;

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

        double growthRate = calculateGrowthRate(channel);

        // 가이드: DB에 저장된 게 없으면 생성 후 저장
        List<Map<String, String>> guides = getOrGenerateGuides(channel, videos);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("channel", Map.of(
                "channelId", channel.getChannelId(),
                "name", channel.getChannelName(),
                "handle", channel.getHandle() != null ? channel.getHandle() : "",
                "profileImageUrl", channel.getProfileImageUrl(),
                "subscriberCount", channel.getSubscriberCount()
        ));
        // channelScore는 백분위 계산 후 여기에 삽입 (아래에서 처리)
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("avgViewCount", channel.getAvgViewCount());
        summary.put("avgViewCountChange", calcChangePercent(channel.getAvgViewCount(), channel.getPreviousAvgViewCount()));
        summary.put("uploadFrequencyPerWeek", channel.getUploadFrequencyPerWeek());
        summary.put("uploadFrequencyChange", calcChangePercent(channel.getUploadFrequencyPerWeek(), channel.getPreviousUploadFrequencyPerWeek()));
        summary.put("avgWatchDurationSeconds", channel.getAvgWatchDurationSeconds());
        summary.put("avgWatchDurationChange", null);
        Long prevSubs = channel.getPreviousSubscriberCount();
        Long currSubs = channel.getSubscriberCount();
        summary.put("subscriberChange", prevSubs != null ? currSubs - prevSubs : null);
        summary.put("subscriberChangePercent", prevSubs != null && prevSubs > 0 ?
                Math.round((double)(currSubs - prevSubs) / prevSubs * 1000.0) / 10.0 : null);
        result.put("summary", summary);
        result.put("guides", guides);

        // 백분위 기반 점수 계산
        List<PercentileScoringService.ScoreResult> scoreResults = new ArrayList<>();
        List<Map<String, Object>> percentileVideoScores = new ArrayList<>();
        for (VideoCache video : videos) {
            PercentileScoringService.ScoreResult sr = percentileScoringService.score(
                    video.getViewCount(), video.getLikeCount(), video.getCommentCount(),
                    video.getDurationSeconds(), channel.getSubscriberCount(),
                    video.getCategoryId() != null ? video.getCategoryId() : "0"
            );
            scoreResults.add(sr);
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("videoId", video.getVideoId());
            entry.put("title", video.getTitle());
            entry.put("thumbnailUrl", video.getThumbnailUrl());
            entry.put("percentileScore", sr.totalScore());
            entry.put("reason", generateVideoReason(sr));
            percentileVideoScores.add(entry);
        }
        result.put("percentileVideoAnalysis", percentileVideoScores);
        result.put("percentileDataCollectedAt", percentileScoringService.getCollectedAt());

        // 채널 평균 백분위 점수 계산
        int avgTotal = (int) Math.round(scoreResults.stream()
                .mapToInt(PercentileScoringService.ScoreResult::totalScore).average().orElse(0));
        int avgVps = (int) Math.round(scoreResults.stream()
                .mapToInt(PercentileScoringService.ScoreResult::vpsScore).average().orElse(0));
        int avgEng = (int) Math.round(scoreResults.stream()
                .mapToInt(PercentileScoringService.ScoreResult::engagementScore).average().orElse(0));
        int avgLr = (int) Math.round(scoreResults.stream()
                .mapToInt(PercentileScoringService.ScoreResult::likeRateScore).average().orElse(0));

        // 이전 점수 비교 코멘트 생성
        String comment = generateScoreComment(channel, avgTotal, avgVps, avgEng, avgLr);

        // 현재 점수를 DB에 저장 (다음 분석 시 비교용)
        savePercentileScore(channel, avgTotal, avgVps, avgEng, avgLr);

        Map<String, Object> channelScoreMap = new LinkedHashMap<>();
        channelScoreMap.put("overall", avgTotal);
        channelScoreMap.put("topPercent", 100 - avgTotal);
        channelScoreMap.put("comment", comment);
        channelScoreMap.put("factors", List.of(
                Map.of("name", "도달력", "score", avgVps, "weight", 60, "description", "구독자 대비 조회수"),
                Map.of("name", "시청자 반응", "score", avgEng, "weight", 25, "description", "좋아요+댓글 비율"),
                Map.of("name", "콘텐츠 만족도", "score", avgLr, "weight", 15, "description", "좋아요 비율")
        ));

        // channelScore를 channel 바로 다음에 삽입
        Map<String, Object> ordered = new LinkedHashMap<>();
        ordered.put("channel", result.get("channel"));
        ordered.put("channelScore", channelScoreMap);
        result.remove("channel");
        result.forEach(ordered::put);

        return ordered;
    }

    private ChannelCache getOrFetchChannel(String channelId) {
        Optional<ChannelCache> cached = channelCacheRepository.findByChannelId(channelId);
        if (cached.isPresent() && cached.get().getFetchedAt().isAfter(LocalDateTime.now().minusDays(CACHE_DAYS))) {
            return cached.get();
        }

        Long previousSubscriberCount = cached.map(ChannelCache::getSubscriberCount).orElse(null);
        Double previousAvgViewCount = cached.map(ChannelCache::getAvgViewCount).orElse(null);
        Double previousUploadFreq = cached.map(ChannelCache::getUploadFrequencyPerWeek).orElse(null);
        ChannelCache fresh = fetchChannelFromYoutube(channelId, previousSubscriberCount);
        fresh = ChannelCache.builder()
                .channelId(fresh.getChannelId())
                .channelName(fresh.getChannelName())
                .handle(fresh.getHandle())
                .profileImageUrl(fresh.getProfileImageUrl())
                .subscriberCount(fresh.getSubscriberCount())
                .previousSubscriberCount(previousSubscriberCount)
                .totalVideoCount(fresh.getTotalVideoCount())
                .avgViewCount(fresh.getAvgViewCount())
                .previousAvgViewCount(previousAvgViewCount)
                .uploadFrequencyPerWeek(fresh.getUploadFrequencyPerWeek())
                .previousUploadFrequencyPerWeek(previousUploadFreq)
                .avgWatchDurationSeconds(fresh.getAvgWatchDurationSeconds())
                .fetchedAt(fresh.getFetchedAt())
                .build();
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

            Double avgWatchDuration = null;
            try {
                String refreshToken = userRepository.findByYoutubeChannelId(channelId)
                        .map(u -> u.getGoogleRefreshToken()).orElse(null);
                if (refreshToken != null) {
                    String accessToken = refreshGoogleAccessToken(refreshToken);
                    avgWatchDuration = fetchAvgWatchDurationFromAnalytics(accessToken);
                }
            } catch (Exception e) {
                log.warn("Analytics API 평균 시청 지속 시간 조회 실패: {} - {}", e.getClass().getSimpleName(), e.getMessage(), e);
            }

            return ChannelCache.builder()
                    .channelId(channelId)
                    .channelName(snippet.path("title").asText())
                    .handle(snippet.path("customUrl").asText(null))
                    .profileImageUrl(snippet.path("thumbnails").path("default").path("url").asText())
                    .subscriberCount(subscriberCount)
                    .previousSubscriberCount(previousSubscriberCount)
                    .totalVideoCount(totalVideos)
                    .avgViewCount(stats.path("viewCount").asDouble() / Math.max(1, totalVideos))
                    .uploadFrequencyPerWeek(Math.round(uploadFreq * 10.0) / 10.0)
                    .avgWatchDurationSeconds(avgWatchDuration)
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

                String publishedAtStr = item.path("snippet").path("publishedAt").asText(null);
                LocalDate publishedAt = null;
                if (publishedAtStr != null && !publishedAtStr.isEmpty()) {
                    try { publishedAt = java.time.OffsetDateTime.parse(publishedAtStr).toLocalDate(); } catch (Exception ignored) {}
                }

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
                        .categoryId(item.path("snippet").path("categoryId").asText("0"))
                        .publishedAt(publishedAt)
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

    // 영상 알고리즘 점수 계산 (0~100)
    private int calculateVideoScore(long views, long likes, long comments, long durationSec, long subscribers) {
        if (subscribers == 0) return 0;
        double engagementRate = (double) (likes + comments) / Math.max(1, views);
        double viewRatio = (double) views / subscribers;
        double durationBonus = (durationSec >= 180 && durationSec <= 900) ? 1.2 : 1.0;
        double raw = (viewRatio * 40 + engagementRate * 100 * 40) * durationBonus;
        return Math.min(100, (int) Math.round(raw + 20));
    }

    // 채널 전체 알고리즘 점수: 영상 점수 평균
    private int calculateChannelScore(ChannelCache channel, List<VideoCache> videos) {
        if (videos.isEmpty()) return 0;
        return (int) Math.round(videos.stream().mapToInt(VideoCache::getAlgorithmScore).average().orElse(0));
    }

    // 백분위 점수 DB 저장
    private void savePercentileScore(ChannelCache channel, int total, int vps, int eng, int lr) {
        try {
            channelCacheRepository.updatePercentileScore(channel.getId(), total, vps, eng, lr);
        } catch (Exception e) {
            log.warn("백분위 점수 저장 실패: {}", e.getMessage());
        }
    }

    // 변화율 계산 (%)
    private Double calcChangePercent(Double current, Double previous) {
        if (current == null || previous == null || previous == 0) return null;
        return Math.round((current - previous) / previous * 1000.0) / 10.0;
    }

    // 영상별 점수 이유 생성 (템플릿)
    private String generateVideoReason(PercentileScoringService.ScoreResult sr) {
        int vps = sr.vpsScore(), eng = sr.engagementScore(), lr = sr.likeRateScore();

        String strongName, weakName;
        int strongScore, weakScore;

        if (vps >= eng && vps >= lr) { strongName = "도달력"; strongScore = vps; }
        else if (eng >= lr) { strongName = "시청자 반응"; strongScore = eng; }
        else { strongName = "콘텐츠 만족도"; strongScore = lr; }

        if (vps <= eng && vps <= lr) { weakName = "도달력"; weakScore = vps; }
        else if (eng <= lr) { weakName = "시청자 반응"; weakScore = eng; }
        else { weakName = "콘텐츠 만족도"; weakScore = lr; }

        String strongPart = String.format("%s이(가) 상위 %d%%로 뛰어나요.", strongName, 100 - strongScore);
        String weakPart = weakScore < 50 ?
                String.format("%s을(를) 개선하면 점수가 올라갈 수 있어요.", weakName) :
                String.format("전반적으로 균형 잡힌 성과를 보이고 있어요.");

        return strongPart + " " + weakPart;
    }

    // AI 영상 한 줄 분석 생성
    private String generateVideoInsight(String title, PercentileScoringService.ScoreResult sr, List<Map<String, Object>> factors) {
        try {
            StringBuilder factorDesc = new StringBuilder();
            for (Map<String, Object> f : factors) {
                factorDesc.append(String.format("- %s: %d점 (%s)\n",
                        f.get("name"), f.get("score"), f.get("rawValue")));
            }
            String prompt = String.format(
                    "유튜브 영상 분석 결과를 AI 한 줄 분석으로 작성해.\n" +
                    "영상 제목: %s\n" +
                    "종합 점수: %d/100\n" +
                    "%s" +
                    "규칙: 2문장 이내. 강점과 약점을 자연스럽게 연결. 한국어.\n" +
                    "예시: '클릭을 유도하는 썸네일과 제목 덕분에 유입이 높았고, 안정적인 시청 유지율로 추천 확장까지 잘 이루어진 영상입니다.'",
                    title, sr.totalScore(), factorDesc.toString());
            return bedrockService.invokeModelPublic(prompt).trim();
        } catch (Exception e) {
            log.warn("AI 영상 인사이트 생성 실패: {}", e.getMessage());
            return generateVideoReason(sr);
        }
    }

    // AI 개선 포인트 + 추천 액션 생성
    private Map<String, List<Map<String, String>>> generateImprovementsAndActions(
            String title, PercentileScoringService.ScoreResult sr, List<Map<String, Object>> factors) {
        try {
            StringBuilder factorDesc = new StringBuilder();
            for (Map<String, Object> f : factors) {
                factorDesc.append(String.format("- %s: %d점 (%s)\n",
                        f.get("name"), f.get("score"), f.get("rawValue")));
            }
            String prompt = String.format(
                    "유튜브 영상 분석 결과를 바탕으로 개선 포인트 2개와 추천 액션 3개를 작성해.\n" +
                    "영상 제목: %s\n" +
                    "종합 점수: %d/100\n" +
                    "%s" +
                    "규칙: 각 항목은 title(10자 이내)과 description(25자 이내). 약점 기반 개선, 강점 기반 액션.\n" +
                    "반드시 아래 JSON 형식으로만 답변. 다른 텍스트 없이.\n" +
                    "{\"improvements\":[{\"title\":\"...\",\"description\":\"...\"}],\"actions\":[{\"title\":\"...\",\"description\":\"...\"}]}",
                    title, sr.totalScore(), factorDesc.toString());
            String raw = bedrockService.invokeModelPublic(prompt).trim();
            int start = raw.indexOf('{');
            int end = raw.lastIndexOf('}') + 1;
            if (start >= 0 && end > start) {
                JsonNode root = objectMapper.readTree(raw.substring(start, end));
                List<Map<String, String>> improvements = new ArrayList<>();
                List<Map<String, String>> actions = new ArrayList<>();
                for (JsonNode node : root.path("improvements")) {
                    improvements.add(Map.of("title", node.path("title").asText(), "description", node.path("description").asText()));
                }
                for (JsonNode node : root.path("actions")) {
                    actions.add(Map.of("title", node.path("title").asText(), "description", node.path("description").asText()));
                }
                return Map.of("improvements", improvements, "actions", actions);
            }
        } catch (Exception e) {
            log.warn("AI 개선 포인트/추천 액션 생성 실패: {}", e.getMessage());
        }
        return Map.of("improvements", List.of(), "actions", List.of());
    }

    // AI 코멘트 생성 (점수 이유 25~30자)
    private String generateScoreComment(ChannelCache channel, int currentTotal, int avgVps, int avgEng, int avgLr) {
        try {
            String weak = avgVps <= avgEng && avgVps <= avgLr ? "도달력" :
                          avgEng <= avgLr ? "시청자반응" : "콘텐츠만족도";
            String prompt = String.format(
                    "유튜브 채널 점수 코멘트를 한 줄로 작성해.\n" +
                    "채널: %s (구독자 %d명)\n" +
                    "종합 %d점 (도달력 %d, 시청자반응 %d, 만족도 %d). 약점: %s.\n" +
                    "규칙: 한 줄, 한 문장. 채널 규모에 맞는 표현. 약점이 점수에 미친 영향을 설명.\n" +
                    "예시: '구독자 대비 조회수가 낮아 도달력이 점수를 끌어내렸어요'",
                    channel.getChannelName(), channel.getSubscriberCount(),
                    currentTotal, avgVps, avgEng, avgLr, weak);
            return bedrockService.invokeModelPublic(prompt).trim();
        } catch (Exception e) {
            log.warn("AI 코멘트 생성 실패: {}", e.getMessage());
            String weak = avgVps <= avgEng && avgVps <= avgLr ? "도달력" :
                          avgEng <= avgLr ? "시청자 반응" : "콘텐츠 만족도";
            return String.format("%s이(가) 부족해 점수가 낮아졌어요.", weak);
        }
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
            // 평균 영상 길이 계산
            double avgDuration = videos.stream().mapToLong(VideoCache::getDurationSeconds).average().orElse(0);
            String avgDurStr = avgDuration < 60 ? String.format("%.0f초", avgDuration) :
                               String.format("%.0f분", avgDuration / 60);

            String prompt = String.format(
                    "당신은 유튜브 채널 성장 전문가입니다. 반드시 정확히 3개의 가이드를 제시하세요.\n" +
                    "채널 정보:\n" +
                    "- 채널명: %s\n" +
                    "- 구독자 수: %d명\n" +
                    "- 주 업로드 빈도: %.1f회\n" +
                    "- 평균 조회수: %.0f회\n" +
                    "- 평균 영상 길이: %s\n" +
                    "- 최근 영상 수: %d개\n" +
                    "- 점수: 도달력 %d점, 시청자반응 %d점, 콘텐츠만족도 %d점 (각 100점 만점)\n\n" +
                    "각 가이드는 구체적인 수치와 행동을 포함해야 합니다.\n" +
                    "예시: {\"title\": \"업로드 주기 늘리기\", \"description\": \"주 2회 업로드 시 성장률이 20%% 높아져요!\"}\n" +
                    "반드시 아래 JSON 배열 형식으로만 답변하세요. 정확히 3개. 다른 텍스트는 포함하지 마세요.\n" +
                    "[{\"title\": \"가이드 제목\", \"description\": \"구체적인 설명\"}]",
                    channel.getChannelName(),
                    channel.getSubscriberCount(),
                    channel.getUploadFrequencyPerWeek(),
                    channel.getAvgViewCount(),
                    avgDurStr,
                    videos.size(),
                    channel.getPercentileVps() != null ? channel.getPercentileVps() : 50,
                    channel.getPercentileEngagement() != null ? channel.getPercentileEngagement() : 50,
                    channel.getPercentileLikeRate() != null ? channel.getPercentileLikeRate() : 50
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

    public Map<String, Object> getVideoDetail(String videoId) {
        VideoCache video = videoCacheRepository.findByVideoId(videoId)
                .orElseThrow(() -> new RuntimeException("영상 정보를 찾을 수 없습니다: " + videoId));

        ChannelCache channel = channelCacheRepository.findByChannelId(video.getChannelId())
                .orElseThrow(() -> new RuntimeException("채널 정보를 찾을 수 없습니다"));

        List<VideoCache> allVideos = videoCacheRepository.findByChannelIdOrderByVideoRankAsc(video.getChannelId());

        PercentileScoringService.ScoreResult sr = percentileScoringService.score(
                video.getViewCount(), video.getLikeCount(), video.getCommentCount(),
                video.getDurationSeconds(), channel.getSubscriberCount(),
                video.getCategoryId() != null ? video.getCategoryId() : "0"
        );

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("videoId", video.getVideoId());
        result.put("title", video.getTitle());
        result.put("thumbnailUrl", video.getThumbnailUrl());
        result.put("viewCount", video.getViewCount());
        result.put("likeCount", video.getLikeCount());
        result.put("commentCount", video.getCommentCount());
        result.put("durationSeconds", video.getDurationSeconds());
        result.put("channelId", video.getChannelId());
        result.put("channelName", channel.getChannelName());
        result.put("category", resolveCategoryName(video.getCategoryId()));
        result.put("score", Map.of(
                "overall", sr.totalScore(),
                "topPercent", 100 - sr.totalScore()
        ));

        // Analytics API로 CTR, 시청 지속 시간, 추천 확장성 조회
        List<Map<String, Object>> factors = new ArrayList<>();
        Map<String, Object> audienceRetention = new LinkedHashMap<>();
        double videoCtr = 0, videoAvgWatchSec = 0, channelAvgCtr = 0;
        List<Map<String, Object>> videoGrowth = new ArrayList<>();
        List<Map<String, Object>> channelAvgGrowth = new ArrayList<>();
        try {
            String refreshToken = userRepository.findByYoutubeChannelId(video.getChannelId())
                    .map(u -> u.getGoogleRefreshToken()).orElse(null);
            if (refreshToken != null) {
                String accessToken = refreshGoogleAccessToken(refreshToken);
                VideoFactorsResult fr = fetchVideoFactors(accessToken, video.getVideoId(), video.getDurationSeconds());
                factors = fr.factors();
                videoCtr = fr.ctr();
                videoAvgWatchSec = fr.avgWatchSec();
                try { channelAvgCtr = fetchChannelAvgCtr(accessToken); } catch (Exception e) { log.warn("채널 평균 CTR 조회 실패: {}", e.getMessage()); }
                try { audienceRetention = fetchAudienceRetention(accessToken, video.getVideoId(), video.getDurationSeconds()); } catch (Exception e) { log.warn("시청자 유지율 조회 실패: {}", e.getMessage()); }
                if (video.getPublishedAt() != null) {
                    try { videoGrowth = fetchViewGrowthData(accessToken, video.getVideoId(), video.getPublishedAt()); } catch (Exception e) { log.warn("영상 조회수 성장 조회 실패: {}", e.getMessage()); }
                    try { channelAvgGrowth = fetchChannelAvgViewGrowth(accessToken, video.getPublishedAt(), allVideos.size()); } catch (Exception e) { log.warn("채널 평균 성장 조회 실패: {}", e.getMessage()); }
                }
            }
        } catch (Exception e) {
            log.warn("영상 Analytics 조회 실패: {}", e.getMessage());
        }
        result.put("factors", factors);
        result.put("audienceRetention", audienceRetention);
        result.put("insight", generateVideoInsight(video.getTitle(), sr, factors));

        Map<String, List<Map<String, String>>> improvementsAndActions =
                generateImprovementsAndActions(video.getTitle(), sr, factors);
        result.put("improvements", improvementsAndActions.get("improvements"));
        result.put("recommendedActions", improvementsAndActions.get("actions"));

        result.put("scoreBasis", buildScoreBasis(videoCtr, channelAvgCtr, videoAvgWatchSec, channel, videoGrowth, channelAvgGrowth));
        result.put("viewGrowthData", Map.of("video", videoGrowth, "channelAvg", channelAvgGrowth));

        // 채널 내 상대 순위
        long betterThanCount = allVideos.stream()
                .filter(v -> percentileScoringService.score(
                        v.getViewCount(), v.getLikeCount(), v.getCommentCount(),
                        v.getDurationSeconds(), channel.getSubscriberCount(),
                        v.getCategoryId() != null ? v.getCategoryId() : "0"
                ).totalScore() < sr.totalScore())
                .count();
        result.put("channelRank", Map.of(
                "rank", video.getVideoRank(),
                "total", allVideos.size(),
                "betterThanPercent", allVideos.size() > 1
                        ? (int) Math.round((double) betterThanCount / (allVideos.size() - 1) * 100) : 100
        ));

        return result;
    }

    private record VideoFactorsResult(List<Map<String, Object>> factors, double ctr, double avgWatchSec, double recommendPct) {}

    private VideoFactorsResult fetchVideoFactors(String accessToken, String videoId, long durationSeconds) throws Exception {
        String endDate   = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        String startDate = LocalDate.now().minusYears(2).format(DateTimeFormatter.ISO_LOCAL_DATE);
        String filter    = "video%3D%3D" + videoId;

        String metricsResp = WebClient.create().get()
                .uri("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel%3D%3DMINE"
                        + "&startDate=" + startDate + "&endDate=" + endDate
                        + "&metrics=impressionsClickThroughRate,averageViewDuration"
                        + "&filters=" + filter)
                .header("Authorization", "Bearer " + accessToken)
                .retrieve().bodyToMono(String.class).block();

        JsonNode metricsRows = objectMapper.readTree(metricsResp).path("rows");
        double ctr = 0, avgWatchSec = 0;
        if (!metricsRows.isEmpty()) {
            ctr         = metricsRows.get(0).get(0).asDouble();
            avgWatchSec = metricsRows.get(0).get(1).asDouble();
        }

        String trafficResp = WebClient.create().get()
                .uri("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel%3D%3DMINE"
                        + "&startDate=" + startDate + "&endDate=" + endDate
                        + "&metrics=views&dimensions=insightTrafficSourceType"
                        + "&filters=" + filter)
                .header("Authorization", "Bearer " + accessToken)
                .retrieve().bodyToMono(String.class).block();

        JsonNode trafficRows = objectMapper.readTree(trafficResp).path("rows");
        double totalViews = 0, suggestedViews = 0;
        for (JsonNode row : trafficRows) {
            double views = row.get(1).asDouble();
            totalViews += views;
            if ("SUGGESTED_VIDEOS".equals(row.get(0).asText())) suggestedViews = views;
        }
        double recommendPct = totalViews > 0 ? suggestedViews / totalViews : 0;

        int ctrScore       = calcCtrScore(ctr);
        int watchScore     = calcWatchDurationScore(avgWatchSec, durationSeconds);
        int recommendScore = calcRecommendScore(recommendPct);

        List<Map<String, Object>> factors = new ArrayList<>();
        factors.add(new LinkedHashMap<>(Map.of(
                "name", "CTR",
                "score", ctrScore,
                "rawValue", String.format("%.1f%%", ctr * 100),
                "description", "노출 대비 클릭률"
        )));
        factors.add(new LinkedHashMap<>(Map.of(
                "name", "시청 지속 시간",
                "score", watchScore,
                "rawValue", String.format("%.0f초 (유지율 %.0f%%)", avgWatchSec,
                        durationSeconds > 0 ? avgWatchSec / durationSeconds * 100 : 0),
                "description", "평균 시청 유지율"
        )));
        factors.add(new LinkedHashMap<>(Map.of(
                "name", "추천 확장성",
                "score", recommendScore,
                "rawValue", String.format("%.1f%%", recommendPct * 100),
                "description", "추천 알고리즘을 통한 유입 비율"
        )));
        return new VideoFactorsResult(factors, ctr, avgWatchSec, recommendPct);
    }

    private double fetchChannelAvgCtr(String accessToken) throws Exception {
        String endDate   = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        String startDate = LocalDate.now().minusMonths(3).format(DateTimeFormatter.ISO_LOCAL_DATE);
        String resp = WebClient.create().get()
                .uri("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel%3D%3DMINE"
                        + "&startDate=" + startDate + "&endDate=" + endDate
                        + "&metrics=impressionsClickThroughRate")
                .header("Authorization", "Bearer " + accessToken)
                .retrieve().bodyToMono(String.class).block();
        JsonNode rows = objectMapper.readTree(resp).path("rows");
        return rows.isEmpty() ? 0 : rows.get(0).get(0).asDouble();
    }

    private List<Map<String, Object>> fetchViewGrowthData(String accessToken, String videoId, LocalDate publishedAt) throws Exception {
        LocalDate endDate = publishedAt.plusDays(6);
        if (endDate.isAfter(LocalDate.now())) endDate = LocalDate.now();
        String filter = "video%3D%3D" + videoId;
        String resp = WebClient.create().get()
                .uri("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel%3D%3DMINE"
                        + "&startDate=" + publishedAt.format(DateTimeFormatter.ISO_LOCAL_DATE)
                        + "&endDate=" + endDate.format(DateTimeFormatter.ISO_LOCAL_DATE)
                        + "&metrics=views&dimensions=day&filters=" + filter + "&sort=day")
                .header("Authorization", "Bearer " + accessToken)
                .retrieve().bodyToMono(String.class).block();
        JsonNode rows = objectMapper.readTree(resp).path("rows");
        List<Map<String, Object>> result = new ArrayList<>();
        long cumulative = 0;
        for (JsonNode row : rows) {
            cumulative += row.get(1).asLong();
            int day = (int) java.time.temporal.ChronoUnit.DAYS.between(publishedAt, LocalDate.parse(row.get(0).asText()));
            result.add(Map.of("day", day, "views", cumulative));
        }
        return result;
    }

    private List<Map<String, Object>> fetchChannelAvgViewGrowth(String accessToken, LocalDate publishedAt, int videoCount) throws Exception {
        LocalDate endDate = publishedAt.plusDays(6);
        if (endDate.isAfter(LocalDate.now())) endDate = LocalDate.now();
        String resp = WebClient.create().get()
                .uri("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel%3D%3DMINE"
                        + "&startDate=" + publishedAt.format(DateTimeFormatter.ISO_LOCAL_DATE)
                        + "&endDate=" + endDate.format(DateTimeFormatter.ISO_LOCAL_DATE)
                        + "&metrics=views&dimensions=day&sort=day")
                .header("Authorization", "Bearer " + accessToken)
                .retrieve().bodyToMono(String.class).block();
        JsonNode rows = objectMapper.readTree(resp).path("rows");
        List<Map<String, Object>> result = new ArrayList<>();
        long cumulative = 0;
        int count = Math.max(1, videoCount);
        for (JsonNode row : rows) {
            cumulative += row.get(1).asLong();
            int day = (int) java.time.temporal.ChronoUnit.DAYS.between(publishedAt, LocalDate.parse(row.get(0).asText()));
            result.add(Map.of("day", day, "avgViews", cumulative / count));
        }
        return result;
    }

    private List<String> buildScoreBasis(double videoCtr, double channelAvgCtr, double videoAvgWatchSec,
                                          ChannelCache channel, List<Map<String, Object>> videoGrowth,
                                          List<Map<String, Object>> channelGrowth) {
        List<String> basis = new ArrayList<>();
        if (videoCtr > 0 && channelAvgCtr > 0) {
            double diff = (videoCtr - channelAvgCtr) * 100;
            basis.add(String.format("CTR이 채널 평균(%.1f%%) 대비 %.1f%% %s. (%.1f%%)",
                    channelAvgCtr * 100, Math.abs(diff), diff >= 0 ? "높습니다" : "낮습니다", videoCtr * 100));
        }
        if (videoAvgWatchSec > 0 && channel.getAvgWatchDurationSeconds() != null) {
            long channelAvgSec = channel.getAvgWatchDurationSeconds().longValue();
            long diff = Math.round(videoAvgWatchSec) - channelAvgSec;
            basis.add(String.format("평균 시청 지속 시간이 채널 평균(%s) 대비 %d초 %s.(%s)",
                    formatSeconds(channelAvgSec), Math.abs(diff), diff >= 0 ? "더 깁니다" : "더 짧습니다",
                    formatSeconds(Math.round(videoAvgWatchSec))));
        }
        if (!videoGrowth.isEmpty() && !channelGrowth.isEmpty()) {
            long videoDay0 = ((Number) videoGrowth.get(0).get("views")).longValue();
            long channelDay0 = ((Number) channelGrowth.get(0).get("avgViews")).longValue();
            if (channelDay0 > 0) {
                double growthDiff = (double)(videoDay0 - channelDay0) / channelDay0 * 100;
                basis.add(String.format("업로드 후 24시간 동안 조회수 성장률이 채널 평균 대비 %.0f%% %s.",
                        Math.abs(growthDiff), growthDiff >= 0 ? "높습니다" : "낮습니다"));
            }
        }
        return basis;
    }

    private String formatSeconds(long seconds) {
        return String.format("%d:%02d", seconds / 60, seconds % 60);
    }

    private Map<String, Object> fetchAudienceRetention(String accessToken, String videoId, long durationSeconds) throws Exception {
        String endDate = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        String startDate = LocalDate.now().minusYears(2).format(DateTimeFormatter.ISO_LOCAL_DATE);
        String filter = "video%3D%3D" + videoId;

        String retentionResp = WebClient.create().get()
                .uri("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel%3D%3DMINE"
                        + "&startDate=" + startDate + "&endDate=" + endDate
                        + "&metrics=audienceWatched"
                        + "&dimensions=elapsedVideoTimeRatio"
                        + "&filters=" + filter
                        + "&sort=elapsedVideoTimeRatio")
                .header("Authorization", "Bearer " + accessToken)
                .retrieve().bodyToMono(String.class).block();

        JsonNode rows = objectMapper.readTree(retentionResp).path("rows");
        if (rows.isEmpty()) return new LinkedHashMap<>();

        int n = rows.size();
        double[] retentionPcts = new double[n];
        long[] timeSecs = new long[n];

        double baseVal = rows.get(0).get(1).asDouble();
        if (baseVal <= 0) baseVal = 1.0;

        List<Map<String, Object>> curve = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            double ratio = rows.get(i).get(0).asDouble();
            double watched = rows.get(i).get(1).asDouble();
            retentionPcts[i] = watched / baseVal * 100;
            timeSecs[i] = Math.round(ratio * durationSeconds);

            Map<String, Object> point = new LinkedHashMap<>();
            point.put("timeSeconds", timeSecs[i]);
            point.put("retentionPercent", Math.round(retentionPcts[i] * 10.0) / 10.0);
            curve.add(point);
        }

        // 가장 급격한 이탈 구간 탐지 (슬라이딩 윈도우)
        int windowSize = Math.max(2, n / 20);
        int dropStart = 0;
        double maxDrop = Double.MIN_VALUE;
        for (int i = 0; i + windowSize < n; i++) {
            double drop = retentionPcts[i] - retentionPcts[i + windowSize];
            if (drop > maxDrop) {
                maxDrop = drop;
                dropStart = i;
            }
        }
        long dropStartSec = timeSecs[dropStart];
        long dropEndSec = timeSecs[Math.min(dropStart + windowSize, n - 1)];

        String tip;
        double startRatio = durationSeconds > 0 ? (double) dropStartSec / durationSeconds : 0;
        if (startRatio < 0.1) {
            tip = "초반 후킹을 강화하면 더 많은 시청자를 붙잡을 수 있어요.";
        } else if (startRatio < 0.5) {
            tip = "중반부 흐름을 더 긴장감 있게 구성하면 이탈을 줄일 수 있어요.";
        } else {
            tip = "마무리 구성을 강화하면 완주율을 높일 수 있어요.";
        }

        // 평균 유지율 = avgWatchSeconds / durationSeconds
        String avgWatchResp = WebClient.create().get()
                .uri("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel%3D%3DMINE"
                        + "&startDate=" + startDate + "&endDate=" + endDate
                        + "&metrics=averageViewDuration"
                        + "&filters=" + filter)
                .header("Authorization", "Bearer " + accessToken)
                .retrieve().bodyToMono(String.class).block();

        JsonNode avgRows = objectMapper.readTree(avgWatchResp).path("rows");
        long avgWatchSeconds = 0;
        if (!avgRows.isEmpty()) {
            avgWatchSeconds = Math.round(avgRows.get(0).get(0).asDouble());
        }
        int avgRetentionPercent = durationSeconds > 0
                ? (int) Math.round((double) avgWatchSeconds / durationSeconds * 100) : 0;

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("curve", curve);
        result.put("avgWatchSeconds", avgWatchSeconds);
        result.put("avgRetentionPercent", avgRetentionPercent);
        Map<String, Object> dropOffSegment = new LinkedHashMap<>();
        dropOffSegment.put("startSeconds", dropStartSec);
        dropOffSegment.put("endSeconds", dropEndSec);
        dropOffSegment.put("tip", tip);
        result.put("mainDropOffSegment", dropOffSegment);
        return result;
    }

    private int calcCtrScore(double ctr) {
        double pct = ctr * 100;
        if (pct >= 10) return 95;
        if (pct >= 7)  return (int)(80 + (pct - 7)  / 3  * 15);
        if (pct >= 5)  return (int)(65 + (pct - 5)  / 2  * 15);
        if (pct >= 3)  return (int)(40 + (pct - 3)  / 2  * 25);
        if (pct >= 1)  return (int)(10 + (pct - 1)  / 2  * 30);
        return (int)(pct * 10);
    }

    private int calcWatchDurationScore(double avgWatchSec, long durationSeconds) {
        if (durationSeconds <= 0) return 50;
        double retention = avgWatchSec / durationSeconds * 100;
        if (retention >= 70) return 95;
        if (retention >= 50) return (int)(75 + (retention - 50) / 20 * 20);
        if (retention >= 35) return (int)(55 + (retention - 35) / 15 * 20);
        if (retention >= 20) return (int)(30 + (retention - 20) / 15 * 25);
        return (int)(retention / 20 * 30);
    }

    private int calcRecommendScore(double recommendPct) {
        double pct = recommendPct * 100;
        if (pct >= 50) return 95;
        if (pct >= 30) return (int)(75 + (pct - 30) / 20 * 20);
        if (pct >= 15) return (int)(50 + (pct - 15) / 15 * 25);
        if (pct >= 5)  return (int)(20 + (pct - 5)  / 10 * 30);
        return (int)(pct / 5 * 20);
    }

    private String resolveCategoryName(String categoryId) {
        if (categoryId == null) return "기타";
        return switch (categoryId) {
            case "1"  -> "영화/애니메이션";
            case "2"  -> "자동차/교통";
            case "10" -> "음악";
            case "15" -> "반려동물";
            case "17" -> "스포츠";
            case "19" -> "여행/이벤트";
            case "20" -> "게임";
            case "22" -> "인물/블로그";
            case "23" -> "코미디";
            case "24" -> "엔터테인먼트";
            case "25" -> "뉴스/정치";
            case "26" -> "노하우/스타일";
            case "27" -> "교육";
            case "28" -> "과학/기술";
            case "29" -> "비영리/사회활동";
            default   -> "기타";
        };
    }

    private String refreshGoogleAccessToken(String refreshToken) throws Exception {
        String body = "grant_type=refresh_token"
                + "&client_id=" + googleClientId
                + "&client_secret=" + googleClientSecret
                + "&refresh_token=" + refreshToken;

        String response = WebClient.create()
                .post()
                .uri("https://oauth2.googleapis.com/token")
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(String.class)
                .block();

        String accessToken = objectMapper.readTree(response).path("access_token").asText(null);
        if (accessToken == null || accessToken.isEmpty()) {
            throw new RuntimeException("access_token 재발급 실패");
        }
        return accessToken;
    }

    private Double fetchAvgWatchDurationFromAnalytics(String accessToken) throws Exception {
        String endDate   = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        String startDate = LocalDate.now().minusDays(28).format(DateTimeFormatter.ISO_LOCAL_DATE);

        String response = WebClient.create()
                .get()
                .uri(java.net.URI.create("https://youtubeanalytics.googleapis.com/v2/reports"
                        + "?ids=channel==MINE"
                        + "&startDate=" + startDate
                        + "&endDate=" + endDate
                        + "&metrics=averageViewDuration"))
                .header("Authorization", "Bearer " + accessToken)
                .retrieve()
                .bodyToMono(String.class)
                .block();

        JsonNode rows = objectMapper.readTree(response).path("rows");
        if (rows.isEmpty()) return null;
        return rows.get(0).get(0).asDouble();
    }
}
