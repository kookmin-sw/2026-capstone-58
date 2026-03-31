package com.capstone.crit.controller;

import com.capstone.crit.form.RecommendForm;
import com.capstone.crit.service.AIService;
import com.capstone.crit.service.BedrockService;
import com.capstone.crit.service.GeminiService;
import com.capstone.crit.service.YoutubeAPIService;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@AllArgsConstructor
@Slf4j
public class MainController {

    private AIService aiService;
    private YoutubeAPIService youtubeAPIService;
    private BedrockService bedrockService;
    private GeminiService geminiService;

    @PostMapping("/ai_recommend")
    public String main(@RequestParam String requestURL, String keywords, String category){

        RecommendForm data = youtubeAPIService.getData(requestURL); // 1 url 영상 정보 얻기
        log.info("data.title = {}", data.getTitle());
        log.info("data.body = {}", data.getDescription());

        //2. 사용자 keyword, category, 유튜브 정보를 bedrock ai로 요청
        String result = geminiService.analyzeVideo(requestURL, category, keywords); //이걸 제미나이 서비스로 바꿔보자

        return result; //❗ 왜 void로 하면 안되지?
    }
}
