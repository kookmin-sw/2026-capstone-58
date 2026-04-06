package com.capstone.crit.service;

import com.capstone.crit.form.RecommendForm;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class YoutubeAPIService {

    private static final String API_KEY = "AIzaSyAZmCz7C9UMAs9zYVq28EdiVIxxY9-7Shk";
    private static final int MAX_VIDEOS = 10; // 🔥 분석할 최근 영상 수

    // 🔥 채널 URL을 받도록 변경 (기존: 영상 URL)
    public RecommendForm getData(String channelUrl) {
        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper mapper = new ObjectMapper();

        try {
            // 🔥 1단계: 채널 URL에서 채널 ID 추출
            String channelId = resolveChannelId(channelUrl, restTemplate, mapper);

            // 🔥 2단계: 채널 기본 정보 조회 (채널명, 채널 설명)
            String channelInfoUrl = "https://www.googleapis.com/youtube/v3/channels"
                    + "?part=snippet"
                    + "&id=" + channelId
                    + "&key=" + API_KEY;

            ResponseEntity<String> channelResponse = restTemplate.getForEntity(channelInfoUrl, String.class);
            JsonNode channelRoot = mapper.readTree(channelResponse.getBody());
            JsonNode channelSnippet = channelRoot.path("items").get(0).path("snippet");

            String channelTitle = channelSnippet.path("title").asText();
            String channelDescription = channelSnippet.path("description").asText();

            // 🔥 3단계: playlistItems API로 최근 영상 ID 목록 조회 (search API 대비 쿼터 100배 절약)
            String uploadPlaylistId = channelId.replaceFirst("^UC", "UU"); // 🔥 UC→UU 변환으로 업로드 플레이리스트 ID 획득

            String playlistUrl = "https://www.googleapis.com/youtube/v3/playlistItems"
                    + "?part=contentDetails"
                    + "&playlistId=" + uploadPlaylistId
                    + "&maxResults=" + MAX_VIDEOS
                    + "&key=" + API_KEY;

            ResponseEntity<String> playlistResponse = restTemplate.getForEntity(playlistUrl, String.class);
            JsonNode playlistRoot = mapper.readTree(playlistResponse.getBody());

            // 🔥 파싱 경로: contentDetails.videoId (search API는 id.videoId였음)
            List<String> videoIds = new ArrayList<>();
            playlistRoot.path("items").forEach(item ->
                    videoIds.add(item.path("contentDetails").path("videoId").asText())
            );

            if (videoIds.isEmpty()) {
                return new RecommendForm(channelTitle, channelDescription,
                        Collections.emptyList(), Collections.emptyList(), Collections.emptyList());
            }

            // 🔥 4단계: videos API로 영상 상세 정보 일괄 조회
            String videoIdsParam = String.join(",", videoIds);
            String videosUrl = "https://www.googleapis.com/youtube/v3/videos"
                    + "?part=snippet,topicDetails"
                    + "&id=" + videoIdsParam
                    + "&key=" + API_KEY;

            ResponseEntity<String> videosResponse = restTemplate.getForEntity(videosUrl, String.class);
            JsonNode videosRoot = mapper.readTree(videosResponse.getBody());

            // 🔥 5단계: 영상들에서 태그 빈도 집계, 토픽/제목 수집
            Map<String, Integer> tagFrequency = new LinkedHashMap<>();
            Set<String> topicCategorySet = new LinkedHashSet<>();
            List<String> recentTitles = new ArrayList<>();

            videosRoot.path("items").forEach(item -> {
                JsonNode snippet = item.path("snippet");
                JsonNode topicDetails = item.path("topicDetails");

                // 영상 제목 수집
                String videoTitle = snippet.path("title").asText();
                if (!videoTitle.isBlank()) recentTitles.add(videoTitle);

                // 🔥 태그 빈도 집계 (여러 영상에서 자주 등장하는 태그가 채널 핵심 키워드)
                if (snippet.has("tags")) {
                    snippet.path("tags").forEach(tag -> {
                        String tagText = tag.asText().toLowerCase();
                        tagFrequency.merge(tagText, 1, Integer::sum);
                    });
                }

                // 토픽 카테고리 수집 (중복 제거)
                if (topicDetails.has("topicCategories")) {
                    topicDetails.path("topicCategories").forEach(topic ->
                            topicCategorySet.add(topic.asText())
                    );
                }
            });

            // 🔥 태그를 빈도 내림차순 정렬, 상위 20개만 추출
            List<String> sortedTags = tagFrequency.entrySet().stream()
                    .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                    .map(Map.Entry::getKey)
                    .limit(20)
                    .collect(Collectors.toList());

            return new RecommendForm(
                    channelTitle,
                    channelDescription,
                    sortedTags,
                    new ArrayList<>(topicCategorySet),
                    recentTitles  // 🔥 recentTitles 추가
            );

        } catch (JsonProcessingException e) {
            throw new RuntimeException("JSON 파싱 실패", e);
        }
    }

    // 채널 최신 썸네일 이미지 3개 다운로드
    public List<byte[]> getRecentThumbnailImages(String channelUrl) throws Exception {
        String channelId = resolveChannelId(channelUrl, new RestTemplate(), new com.fasterxml.jackson.databind.ObjectMapper());
        String searchUrl = "https://www.googleapis.com/youtube/v3/search"
                + "?channelId=" + channelId
                + "&part=snippet"
                + "&order=date"
                + "&maxResults=3"
                + "&type=video"
                + "&key=" + API_KEY;

        RestTemplate restTemplate = new RestTemplate();
        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        ResponseEntity<String> response = restTemplate.getForEntity(searchUrl, String.class);
        JsonNode items = mapper.readTree(response.getBody()).path("items");

        List<byte[]> images = new ArrayList<>();
        for (JsonNode item : items) {
            JsonNode thumbs = item.path("snippet").path("thumbnails");
            String url = thumbs.has("high") ? thumbs.path("high").path("url").asText()
                       : thumbs.path("medium").path("url").asText();
            try {
                images.add(restTemplate.getForObject(url, byte[].class));
            } catch (Exception ignored) {}
        }
        return images;
    }

    // 🔥 기존 extractVideoId 대신 채널 ID를 추출하는 메서드로 교체
    private String resolveChannelId(String channelUrl, RestTemplate restTemplate, ObjectMapper mapper) {
        try {
            // /channel/UC... 형식이면 바로 ID 추출
            if (channelUrl.contains("/channel/")) {
                return channelUrl.split("/channel/")[1].split("[/?]")[0];
            }

            // 🔥 @handle 형식이면 forHandle API로 채널 ID 조회
            if (channelUrl.contains("/@")) {
                String handle = channelUrl.split("/@")[1].split("[/?]")[0];

                String url = "https://www.googleapis.com/youtube/v3/channels"
                        + "?part=id"
                        + "&forHandle=" + handle
                        + "&key=" + API_KEY;

                ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
                JsonNode root = mapper.readTree(response.getBody());
                return root.path("items").get(0).path("id").asText();
            }

            throw new IllegalArgumentException("지원하지 않는 채널 URL 형식: " + channelUrl);

        } catch (JsonProcessingException e) {
            throw new RuntimeException("채널 ID 조회 실패", e);
        }
    }

    // 🔥 채널 URL로 최신 영상 URL 1개만 반환
    public String getLatestVideoUrl(String channelUrl) {
        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper mapper = new ObjectMapper();

        try {
            String channelId = resolveChannelId(channelUrl, restTemplate, mapper);
            String uploadPlaylistId = channelId.replaceFirst("^UC", "UU");

            // 🔥 10분 이하 영상을 찾기 위해 최근 10개 가져오기 (1개만 가져오면 10분 초과일 수 있음)
            String playlistUrl = "https://www.googleapis.com/youtube/v3/playlistItems"
                    + "?part=contentDetails"
                    + "&playlistId=" + uploadPlaylistId
                    + "&maxResults=10"
                    + "&key=" + API_KEY;

            ResponseEntity<String> response = restTemplate.getForEntity(playlistUrl, String.class);
            JsonNode root = mapper.readTree(response.getBody());

            // 🔥 videoId 목록 추출
            List<String> videoIds = new ArrayList<>();
            root.path("items").forEach(item ->
                    videoIds.add(item.path("contentDetails").path("videoId").asText())
            );

            // 🔥 contentDetails(duration 포함)로 영상 상세 조회
            String videoIdsParam = String.join(",", videoIds);
            String videosUrl = "https://www.googleapis.com/youtube/v3/videos"
                    + "?part=contentDetails"
                    + "&id=" + videoIdsParam
                    + "&key=" + API_KEY;

            ResponseEntity<String> videosResponse = restTemplate.getForEntity(videosUrl, String.class);
            JsonNode videosRoot = mapper.readTree(videosResponse.getBody());

            // 🔥 10분 이하인 가장 최근 영상 ID 반환
            for (JsonNode item : videosRoot.path("items")) {
                String iso8601 = item.path("contentDetails").path("duration").asText();
                int minutes = parseMinutes(iso8601);
                if (minutes <= 10) {
                    String videoId = item.path("id").asText();
                    return "https://www.youtube.com/watch?v=" + videoId;
                }
            }

            // 🔥 10분 이하 영상이 없으면 그냥 최신 영상 반환
            String fallbackId = root.path("items").get(0)
                    .path("contentDetails").path("videoId").asText();
            return "https://www.youtube.com/watch?v=" + fallbackId;

        } catch (JsonProcessingException e) {
            throw new RuntimeException("최신 영상 URL 조회 실패", e);
        }
    }

    // 🔥 ISO 8601 duration 파싱 (PT10M30S → 10분)
    private int parseMinutes(String iso8601) {
        try {
            return (int) java.time.Duration.parse(iso8601).toMinutes();
        } catch (Exception e) {
            return 999; // 파싱 실패시 필터 제외
        }
    }

    // 🔥 기획안과 유사한 영상 3개 검색 (URL + 제목)
    public List<Map<String, String>> getSimilarVideos(String conceptSummary, String keywords) {
        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper mapper = new ObjectMapper();
        List<Map<String, String>> similarVideos = new ArrayList<>();

        try {
            // 기획안 요약과 키워드를 조합하여 검색
            String searchQuery = keywords + " " + conceptSummary.substring(0, Math.min(50, conceptSummary.length()));
            
            String searchUrl = "https://www.googleapis.com/youtube/v3/search"
                    + "?part=snippet"
                    + "&q=" + java.net.URLEncoder.encode(searchQuery, "UTF-8")
                    + "&type=video"
                    + "&maxResults=3"
                    + "&order=relevance"
                    + "&key=" + API_KEY;

            ResponseEntity<String> response = restTemplate.getForEntity(searchUrl, String.class);
            JsonNode items = mapper.readTree(response.getBody()).path("items");

            for (JsonNode item : items) {
                if (similarVideos.size() >= 3) break;
                
                String videoId = item.path("id").path("videoId").asText();
                String title = item.path("snippet").path("title").asText();
                
                if (!videoId.isEmpty() && !title.isEmpty()) {
                    Map<String, String> video = new HashMap<>();
                    video.put("videoUrl", "https://www.youtube.com/watch?v=" + videoId);
                    video.put("videoTitle", title);
                    similarVideos.add(video);
                }
            }

        } catch (Exception e) {
            System.err.println("유사 영상 검색 실패: " + e.getMessage());
        }

        return similarVideos;
    }

    // 🔥 유사한 유튜버 2명 검색 (채널 URL + 유튜버 이름)
    public List<Map<String, String>> getSimilarCreators(String keywords, String category) {
        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper mapper = new ObjectMapper();
        List<Map<String, String>> similarCreators = new ArrayList<>();

        try {
            // 키워드와 카테고리를 조합하여 채널 검색
            String searchQuery = keywords + " " + category + " creator";
            
            String searchUrl = "https://www.googleapis.com/youtube/v3/search"
                    + "?part=snippet"
                    + "&q=" + java.net.URLEncoder.encode(searchQuery, "UTF-8")
                    + "&type=channel"
                    + "&maxResults=2"
                    + "&order=relevance"
                    + "&key=" + API_KEY;

            ResponseEntity<String> response = restTemplate.getForEntity(searchUrl, String.class);
            JsonNode items = mapper.readTree(response.getBody()).path("items");

            for (JsonNode item : items) {
                if (similarCreators.size() >= 2) break;
                
                String channelId = item.path("id").path("channelId").asText();
                String channelTitle = item.path("snippet").path("title").asText();
                
                if (!channelId.isEmpty() && !channelTitle.isEmpty()) {
                    Map<String, String> creator = new HashMap<>();
                    creator.put("channelUrl", "https://www.youtube.com/channel/" + channelId);
                    creator.put("creatorName", channelTitle);
                    similarCreators.add(creator);
                }
            }

        } catch (Exception e) {
            System.err.println("유사 유튜버 검색 실패: " + e.getMessage());
        }

        return similarCreators;
    }
}