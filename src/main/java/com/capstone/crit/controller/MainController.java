package com.capstone.crit.controller;

import com.capstone.crit.form.RecommendForm;
import com.capstone.crit.service.AIService;
import com.capstone.crit.service.BedrockService;
import com.capstone.crit.service.GeminiService;
import com.capstone.crit.service.ImagenService;
import com.capstone.crit.service.S3Service;
import com.capstone.crit.service.YoutubeAPIService;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
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
    private ImagenService imagenService;
    private S3Service s3Service;

    @Operation(summary = "유튜브 기반 주제 추천", description = "유튜브 URL을 기반으로 AI가 새로운 콘텐츠 주제를 추천합니다.")
    @PostMapping("/ai_recommend")
    public ResponseEntity<List<Map<String, String>>> AIRecommend(@Parameter(description = "유튜브 채널 url", example = "https://youtube.com/@codingapple")
                                                                     @RequestParam String requestURL,

                                                                 @Parameter(description = "키워드", example = "유튜브 성장")
                                                                     @RequestParam String keywords,

                                                                 @Parameter(description = "카테고리", example = "교육")
                                                                     @RequestParam String category){

        RecommendForm recommendForm = youtubeAPIService.getData(requestURL); // 1 url 채널 정보 얻기
        log.info("recommendForm = {}", recommendForm);
        log.info("getTags = {}", recommendForm.getTags());
        log.info("getTopicCategories = {}", recommendForm.getTopicCategories());
        log.info("getTitle = {}", recommendForm.getTitle()); // 필드명은 네 코드에 맞게

        //2. 유튜브 정보로 3개의 주제 추천
        List<Map<String, String>> result = geminiService.recommendTopic(recommendForm, category, keywords);

        return ResponseEntity.ok(result); //❗ 왜 void로 하면 안되지?
    }
    @Operation(summary = "영상 기획 및 제목 생성", description = "유튜브 정보를 기반으로 5분짜리 콘텐츠 기획안과 제목을 생성합니다.")
    @PostMapping("/ai_script")
    public ResponseEntity<List<Map<String, Object>>> AIScript(@Parameter(description = "유튜브 채널 url")
                                                                  @RequestParam String requestURL,

                                                              @Parameter(description = "추천 영상 제목")
                                                                  @RequestParam String title,

                                                              @Parameter(description = "추천 기획 컨셉")
                                                                  @RequestParam String concept,

                                                              @Parameter(description = "키워드")
                                                                  @RequestParam String keywords,

                                                              @Parameter(description = "카테고리")
                                                                  @RequestParam List<String> category,

                                                            @Parameter(description = "시간")
                                                            @RequestParam int time){
        RecommendForm recommendForm = youtubeAPIService.getData(requestURL); //❗이거 두번 호출!!! redis에 저장하고 재사용하는 방식으로 바꾸든가 해야한다!!!!

        //2. 사용자 keyword, category, 유튜브 정보를 bedrock ai로 요청
        String latestVideoUrl = youtubeAPIService.getLatestVideoUrl(requestURL);
        log.info("최신 영상 URL = {}", latestVideoUrl);
        String categoryStr = String.join(", ", category);

        // 기존 writeScript 그대로 호출 (멀티모달 유지)
        List<Map<String, Object>> result = geminiService.writeScript(latestVideoUrl, recommendForm, title, concept, categoryStr, keywords, time);

        // 썸네일 생성
        String thumbnailImage = null;
        try {
            List<byte[]> thumbnailImages = youtubeAPIService.getRecentThumbnailImages(requestURL);
            String imagenPrompt = bedrockService.analyzeThumbnailsAndGeneratePrompt(thumbnailImages, title, concept);
            String base64 = imagenService.generateThumbnail(imagenPrompt);
            thumbnailImage = s3Service.uploadBase64Image(base64, "thumbnails");
        } catch (Exception e) {
            log.error("썸네일 생성 실패: {}", e.getMessage());
        }

        // 유사한 영상 3개 검색
        List<Map<String, String>> similarVideos = youtubeAPIService.getSimilarVideos(concept, keywords);
        
        // 유사한 유튜버 2명 검색
        List<Map<String, String>> similarCreators = youtubeAPIService.getSimilarCreators(keywords, categoryStr);

        // 응답 구조 변경: thumbnail 객체로 묶기 + 유사 영상/유튜버 추가
        if (thumbnailImage != null || !result.isEmpty()) {
            for (Map<String, Object> item : result) {
                Map<String, Object> thumbnail = new java.util.HashMap<>();
                if (thumbnailImage != null) {
                    thumbnail.put("thumbnailImage", thumbnailImage);
                }
                Object guide = item.remove("thumbnailGuide");
                if (guide != null) {
                    thumbnail.put("thumbnailGuide", guide);
                }
                item.put("thumbnail", thumbnail);
                
                // 유사 영상 및 유튜버 추가
                item.put("similarVideos", similarVideos);
                item.put("similarCreators", similarCreators);
            }
        }

        return ResponseEntity.ok(result);
    }
}
