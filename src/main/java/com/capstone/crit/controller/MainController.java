package com.capstone.crit.controller;

import com.capstone.crit.form.RecommendForm;
import com.capstone.crit.service.AIService;
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

    @PostMapping("/ai_recommend")
    public RecommendForm main(@RequestParam String requestURL){

        RecommendForm data = youtubeAPIService.getData(requestURL);
        log.info("data.title = {}", data.getTitle());
        log.info("data.body = {}", data.getDescription());
        return data; //❗ 왜 void로 하면 안되지?
    }
}
