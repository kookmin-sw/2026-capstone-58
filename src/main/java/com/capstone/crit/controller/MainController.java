package com.capstone.crit.controller;

import com.capstone.crit.form.RecommendForm;
import com.capstone.crit.service.AIService;
import com.capstone.crit.service.BedrockService;
import com.capstone.crit.service.GeminiService;
import com.capstone.crit.service.YoutubeAPIService;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@AllArgsConstructor
@Slf4j
public class MainController {

    private AIService aiService;
    private YoutubeAPIService youtubeAPIService;
    private BedrockService bedrockService;
    private GeminiService geminiService;

    @PostMapping("/ai_recommend")
    public ResponseEntity<List<Map<String, String>>> AIRecommend(@RequestParam String requestURL, String keywords, String category){

        RecommendForm recommendForm = youtubeAPIService.getData(requestURL); // 1 url 영상 정보 얻기
        log.info("data.getTags = {}", recommendForm.getTags());
        log.info("data.getTopicCategories = {}", recommendForm.getTopicCategories());

        //2. 유튜브 정보로 3개의 주제 추천
        List<Map<String, String>> result = geminiService.recommendTopic(recommendForm, category, keywords);

        return ResponseEntity.ok(result); //❗ 왜 void로 하면 안되지?
    }

    @PostMapping("/ai_script")
    public ResponseEntity<List<Map<String, Object>>> AIScript(String requestURL, String title, String concept, String keywords, String category){

        //2. 사용자 keyword, category, 유튜브 정보를 bedrock ai로 요청
        List<Map<String, Object>> result = geminiService.writeScript(requestURL, title, concept, category, keywords); //이걸 제미나이 서비스로 바꿔보자

        return ResponseEntity.ok(result); //❗ 왜 void로 하면 안되지?
    }
}
