package com.capstone.crit.service;

import com.capstone.crit.form.RecommendForm;
import com.fasterxml.jackson.core.JsonProcessingException;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.List;

@Service
public class YoutubeAPIService { // test 용 수정

    private static final String API_KEY = "AIzaSyAZmCz7C9UMAs9zYVq28EdiVIxxY9-7Shk";

    public RecommendForm getData(String url){
        // 여기에 url이랑 토큰 이용해서 데이터 가져오는 코드 작성
        // 토큰 값은 일단 하드 코딩

        String videoId = extractVideoId(url);

        String apiURL = "https://www.googleapis.com/youtube/v3/videos"
                + "?part=snippet, topicDetails"
                + "&id=" + videoId
                + "&key=" + API_KEY; //

        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.getForEntity(apiURL, String.class);

        //response 파싱
        ObjectMapper objectMapper = new ObjectMapper();
        try{
            JsonNode root = objectMapper.readTree(response.getBody());


            JsonNode item = root.path("items").get(0);
            JsonNode topicDetails = item.path("topicDetails");
            JsonNode snippet = item.path("snippet");

            String title = snippet.path("title").asText();
            String description  = snippet.path("description").asText();

// ✨ [추가] Tags 리스트 파싱 로직
            List<String> tags = new ArrayList<>();
            if (snippet.has("tags")) {
                snippet.path("tags").forEach(tag -> tags.add(tag.asText()));
            }

            // ✨ [추가] TopicCategories 리스트 파싱 로직
            List<String> topicCategories = new ArrayList<>();
            if (topicDetails.has("topicCategories")) {
                topicDetails.path("topicCategories").forEach(topic -> topicCategories.add(topic.asText()));
            }

            // ✅ 수정된 RecommendForm 생성자(필드 4개)에 맞춰 반환
            return new RecommendForm(title, description, tags, topicCategories);
        }

        catch(JsonProcessingException e){
            throw new RuntimeException("JSON 파싱 실패", e);
        }



    }

    private String extractVideoId(String url) {

        return url.split("v=")[1].split("&")[0];
    }

} ////
