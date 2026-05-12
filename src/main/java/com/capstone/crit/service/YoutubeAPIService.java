package com.capstone.crit.service;

import com.capstone.crit.form.RecommendForm;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;
import java.util.stream.Collectors;

@Service
@Slf4j
public class YoutubeAPIService {

    @Value("${youtube.api.key}")
    private String apiKey;
    
    private static final int MAX_VIDEOS = 10;

    public RecommendForm getData(String channelUrl) {
        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper mapper = new ObjectMapper();

        try {
            String channelId = resolveChannelId(channelUrl, restTemplate, mapper);

            String channelInfoUrl = "https://www.googleapis.com/youtube/v3/channels"
                    + "?part=snippet"
                    + "&id=" + channelId
                    + "&key=" + apiKey;

            ResponseEntity<String> channelResponse = restTemplate.getForEntity(channelInfoUrl, String.class);
            JsonNode channelRoot = mapper.readTree(channelResponse.getBody());
            JsonNode channelSnippet = channelRoot.path("items").get(0).path("snippet");

            String channelTitle = channelSnippet.path("title").asText();
            String channelDescription = channelSnippet.path("description").asText();

            String uploadPlaylistId = channelId.replaceFirst("^UC", "UU");

            String playlistUrl = "https://www.googleapis.com/youtube/v3/playlistItems"
                    + "?part=contentDetails"
                    + "&playlistId=" + uploadPlaylistId
                    + "&maxResults=" + MAX_VIDEOS
                    + "&key=" + apiKey;

            ResponseEntity<String> playlistResponse = restTemplate.getForEntity(playlistUrl, String.class);
            JsonNode playlistRoot = mapper.readTree(playlistResponse.getBody());

            List<String> videoIds = new ArrayList<>();
            playlistRoot.path("items").forEach(item ->
                    videoIds.add(item.path("contentDetails").path("videoId").asText())
            );

            if (videoIds.isEmpty()) {
                return new RecommendForm(channelTitle, channelDescription,
                        Collections.emptyList(), Collections.emptyList(), Collections.emptyList());
            }

            String videoIdsParam = String.join(",", videoIds);
            String videosUrl = "https://www.googleapis.com/youtube/v3/videos"
                    + "?part=snippet,topicDetails"
                    + "&id=" + videoIdsParam
                    + "&key=" + apiKey;

            ResponseEntity<String> videosResponse = restTemplate.getForEntity(videosUrl, String.class);
            JsonNode videosRoot = mapper.readTree(videosResponse.getBody());

            Map<String, Integer> tagFrequency = new LinkedHashMap<>();
            Set<String> topicCategorySet = new LinkedHashSet<>();
            List<String> recentTitles = new ArrayList<>();

            videosRoot.path("items").forEach(item -> {
                JsonNode snippet = item.path("snippet");
                JsonNode topicDetails = item.path("topicDetails");

                String videoTitle = snippet.path("title").asText();
                if (!videoTitle.isBlank()) recentTitles.add(videoTitle);

                if (snippet.has("tags")) {
                    snippet.path("tags").forEach(tag -> {
                        String tagText = tag.asText().toLowerCase();
                        tagFrequency.merge(tagText, 1, Integer::sum);
                    });
                }

                if (topicDetails.has("topicCategories")) {
                    topicDetails.path("topicCategories").forEach(topic ->
                            topicCategorySet.add(topic.asText())
                    );
                }
            });

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
                    recentTitles
            );

        } catch (JsonProcessingException e) {
            throw new RuntimeException("JSON 파싱 실패", e);
        }
    }

    public List<byte[]> getRecentThumbnailImages(String channelUrl) throws Exception {
        String channelId = resolveChannelId(channelUrl, new RestTemplate(), new ObjectMapper());
        String searchUrl = "https://www.googleapis.com/youtube/v3/search"
                + "?channelId=" + channelId
                + "&part=snippet"
                + "&order=date"
                + "&maxResults=3"
                + "&type=video"
                + "&key=" + apiKey;

        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper mapper = new ObjectMapper();
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

    private String resolveChannelId(String channelUrl, RestTemplate restTemplate, ObjectMapper mapper) {
        try {
            if (channelUrl.contains("/channel/")) {
                return channelUrl.split("/channel/")[1].split("[/?]")[0];
            }

            if (channelUrl.contains("/@")) {
                String handle = channelUrl.split("/@")[1].split("[/?]")[0];

                String url = "https://www.googleapis.com/youtube/v3/channels"
                        + "?part=id"
                        + "&forHandle=" + handle
                        + "&key=" + apiKey;

                ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
                JsonNode root = mapper.readTree(response.getBody());
                return root.path("items").get(0).path("id").asText();
            }

            throw new IllegalArgumentException("지원하지 않는 채널 URL 형식: " + channelUrl);

        } catch (JsonProcessingException e) {
            throw new RuntimeException("채널 ID 조회 실패", e);
        }
    }

    public String getLatestVideoUrl(String channelUrl) {
        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper mapper = new ObjectMapper();

        try {
            String channelId = resolveChannelId(channelUrl, restTemplate, mapper);
            String uploadPlaylistId = channelId.replaceFirst("^UC", "UU");

            String playlistUrl = "https://www.googleapis.com/youtube/v3/playlistItems"
                    + "?part=contentDetails"
                    + "&playlistId=" + uploadPlaylistId
                    + "&maxResults=10"
                    + "&key=" + apiKey;

            ResponseEntity<String> response = restTemplate.getForEntity(playlistUrl, String.class);
            JsonNode root = mapper.readTree(response.getBody());

            List<String> videoIds = new ArrayList<>();
            root.path("items").forEach(item ->
                    videoIds.add(item.path("contentDetails").path("videoId").asText())
            );

            String videoIdsParam = String.join(",", videoIds);
            String videosUrl = "https://www.googleapis.com/youtube/v3/videos"
                    + "?part=contentDetails"
                    + "&id=" + videoIdsParam
                    + "&key=" + apiKey;

            ResponseEntity<String> videosResponse = restTemplate.getForEntity(videosUrl, String.class);
            JsonNode videosRoot = mapper.readTree(videosResponse.getBody());

            for (JsonNode item : videosRoot.path("items")) {
                String iso8601 = item.path("contentDetails").path("duration").asText();
                int minutes = parseMinutes(iso8601);
                if (minutes <= 10) {
                    String videoId = item.path("id").asText();
                    return "https://www.youtube.com/watch?v=" + videoId;
                }
            }

            String fallbackId = root.path("items").get(0)
                    .path("contentDetails").path("videoId").asText();
            return "https://www.youtube.com/watch?v=" + fallbackId;

        } catch (JsonProcessingException e) {
            throw new RuntimeException("최신 영상 URL 조회 실패", e);
        }
    }

    private int parseMinutes(String iso8601) {
        try {
            return (int) java.time.Duration.parse(iso8601).toMinutes();
        } catch (Exception e) {
            return 999;
        }
    }

    public List<Map<String, String>> getSimilarVideos(String conceptSummary, String keywords) {
        List<Map<String, String>> similarVideos = new ArrayList<>();

        try {
            String searchQuery = keywords;
            
            if (searchQuery == null || searchQuery.trim().isEmpty()) {
                if (conceptSummary != null && !conceptSummary.isEmpty()) {
                    String summary = conceptSummary.substring(0, Math.min(20, conceptSummary.length()));
                    summary = summary.replaceAll("[^가-힣a-zA-Z0-9\\s]", "").trim();
                    searchQuery = !summary.isEmpty() ? summary : "유튜브";
                } else {
                    searchQuery = "유튜브";
                }
            }
            
            String finalSearchQuery = searchQuery + " 리뷰";
            String encodedQuery = java.net.URLEncoder.encode(finalSearchQuery, "UTF-8");
            
            String searchUrl = "https://www.googleapis.com/youtube/v3/search"
                    + "?part=snippet"
                    + "&q=" + encodedQuery
                    + "&type=video"
                    + "&maxResults=3"
                    + "&order=relevance"
                    + "&key=" + apiKey;

            java.net.URL url = new java.net.URL(searchUrl);
            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(conn.getInputStream(), "UTF-8"));
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();
                
                ObjectMapper mapper = new ObjectMapper();
                JsonNode root = mapper.readTree(response.toString());
                JsonNode items = root.path("items");

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
            }
            
            conn.disconnect();

        } catch (Exception e) {
            log.error("유사 영상 검색 실패", e);
        }

        return similarVideos;
    }

    public List<Map<String, String>> getSimilarCreators(String keywords, String category) {
        List<Map<String, String>> similarCreators = new ArrayList<>();

        try {
            String searchQuery = keywords;
            
            if (category != null && !category.trim().isEmpty()) {
                String firstCategory = category.split(",")[0].trim();
                firstCategory = firstCategory.replaceAll("[^가-힣a-zA-Z0-9\\s]", "").trim();
                if (!firstCategory.isEmpty()) {
                    searchQuery = keywords + " " + firstCategory;
                }
            }
            
            if (searchQuery == null || searchQuery.trim().isEmpty()) {
                searchQuery = "유튜브 크리에이터";
            }
            
            String encodedQuery = java.net.URLEncoder.encode(searchQuery, "UTF-8");
            String searchUrl = "https://www.googleapis.com/youtube/v3/search"
                    + "?part=snippet"
                    + "&q=" + encodedQuery
                    + "&type=channel"
                    + "&maxResults=2"
                    + "&order=relevance"
                    + "&key=" + apiKey;

            java.net.URL url = new java.net.URL(searchUrl);
            java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(conn.getInputStream(), "UTF-8"));
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();
                
                ObjectMapper mapper = new ObjectMapper();
                JsonNode root = mapper.readTree(response.toString());
                JsonNode items = root.path("items");

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
            }
            
            conn.disconnect();

        } catch (Exception e) {
            log.error("유사 유튜버 검색 실패", e);
        }

        return similarCreators;
    }
}
