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
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;

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

    @Operation(summary = "유튜브 기반 주제 추천", description = "유튜브 URL을 기반으로 AI가 새로운 콘텐츠 주제를 추천합니다.")
    @PostMapping("/ai_recommend")
    public ResponseEntity<List<Map<String, String>>> AIRecommend(@Parameter(description = "유튜브 영상 URL", example = "https://youtube.com/...")
                                                                     @RequestParam String requestURL,

                                                                 @Parameter(description = "키워드", example = "유튜브 성장")
                                                                     @RequestParam String keywords,

                                                                 @Parameter(description = "카테고리", example = "교육")
                                                                     @RequestParam String category){

        RecommendForm recommendForm = youtubeAPIService.getData(requestURL); // 1 url 영상 정보 얻기
        log.info("data.getTags = {}", recommendForm.getTags());
        log.info("data.getTopicCategories = {}", recommendForm.getTopicCategories());

        //2. 유튜브 정보로 3개의 주제 추천
        List<Map<String, String>> result = geminiService.recommendTopic(recommendForm, category, keywords);

        return ResponseEntity.ok(result); //❗ 왜 void로 하면 안되지?
    }
    @Operation(summary = "영상 기획 및 제목 생성", description = "유튜브 정보를 기반으로 5분짜리 콘텐츠 기획안과 제목을 생성합니다.")
    @PostMapping("/ai_script")
    public ResponseEntity<List<Map<String, Object>>> AIScript(@Parameter(description = "유튜브 URL")
                                                                  @RequestParam String requestURL,

                                                              @Parameter(description = "추천 영상 제목")
                                                                  @RequestParam String title,

                                                              @Parameter(description = "추천 기획 컨셉")
                                                                  @RequestParam String concept,

                                                              @Parameter(description = "키워드")
                                                                  @RequestParam String keywords,

                                                              @Parameter(description = "카테고리")
                                                                  @RequestParam String category){

        //2. 사용자 keyword, category, 유튜브 정보를 bedrock ai로 요청
        List<Map<String, Object>> result = geminiService.writeScript(requestURL, title, concept, category, keywords); //이걸 제미나이 서비스로 바꿔보자

        return ResponseEntity.ok(result); //❗ 왜 void로 하면 안되지?
    }
}
