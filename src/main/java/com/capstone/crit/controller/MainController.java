package com.capstone.crit.controller;

import com.capstone.crit.entity.ApiLog;
import com.capstone.crit.entity.RecommendLog;
import com.capstone.crit.entity.ScriptLog;
import com.capstone.crit.form.RecommendForm;
import com.capstone.crit.repository.ApiLogRepository;
import com.capstone.crit.repository.RecommendLogRepository;
import com.capstone.crit.repository.ScriptLogRepository;
import com.capstone.crit.service.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequiredArgsConstructor
@Slf4j
public class MainController {

    private final AIService aiService;
    private final YoutubeAPIService youtubeAPIService;
    private final BedrockService bedrockService;
    private final GeminiService geminiService;
    private final ImagenService imagenService;
    private final S3Service s3Service;
    private final ApiLogRepository apiLogRepository;
    private final RecommendLogRepository recommendLogRepository;
    private final ScriptLogRepository scriptLogRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Operation(summary = "유튜브 기반 주제 추천", description = "유튜브 URL을 기반으로 AI가 새로운 콘텐츠 주제를 추천합니다.")
    @PostMapping("/ai_recommend")
    public ResponseEntity<List<Map<String, String>>> AIRecommend(
            @Parameter(description = "유튜브 채널 url", example = "https://youtube.com/@codingapple")
            @RequestParam String requestURL,
            @Parameter(description = "키워드", example = "유튜브 성장")
            @RequestParam String keywords,
            @Parameter(description = "카테고리", example = "교육")
            @RequestParam String category,
            HttpServletRequest request) {

        long start = System.currentTimeMillis();
        boolean isError = false;
        String errorMsg = null;
        List<Map<String, String>> result = null;

        try {
            RecommendForm recommendForm = youtubeAPIService.getData(requestURL);
            log.info("recommendForm = {}", recommendForm);
            result = geminiService.recommendTopic(recommendForm, category, keywords);
        } catch (Exception e) {
            isError = true;
            errorMsg = e.getMessage();
            throw e;
        } finally {
            int responseMs = (int) (System.currentTimeMillis() - start);

            ApiLog apiLog = ApiLog.builder()
                    .clientIp(request.getRemoteAddr())
                    .endpoint("/ai_recommend")
                    .category(category)
                    .keywords(keywords)
                    .channelUrl(requestURL)
                    .responseMs(responseMs)
                    .isError(isError)
                    .errorMsg(errorMsg)
                    .build();
            apiLogRepository.save(apiLog);

            if (!isError && result != null) {
                try {
                    String resultJson = objectMapper.writeValueAsString(result);
                    RecommendLog recommendLog = RecommendLog.builder()
                            .apiLog(apiLog)
                            .recommendations(resultJson)
                            .build();
                    recommendLogRepository.save(recommendLog);
                } catch (Exception e) {
                    log.warn("RecommendLog 저장 실패: {}", e.getMessage());
                }
            }
        }

        return ResponseEntity.ok(result);
    }

    @Operation(summary = "영상 기획 및 제목 생성", description = "유튜브 정보를 기반으로 5분짜리 콘텐츠 기획안과 제목을 생성합니다.")
    @PostMapping("/ai_script")
    public ResponseEntity<List<Map<String, Object>>> AIScript(
            @Parameter(description = "유튜브 채널 url")
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
            @RequestParam int time,
            HttpServletRequest request) {

        long start = System.currentTimeMillis();
        boolean isError = false;
        String errorMsg = null;
        List<Map<String, Object>> result = null;
        String categoryStr = String.join(", ", category);

        try {
            RecommendForm recommendForm = youtubeAPIService.getData(requestURL);
            String latestVideoUrl = youtubeAPIService.getLatestVideoUrl(requestURL);
            log.info("최신 영상 URL = {}", latestVideoUrl);

            result = geminiService.writeScript(latestVideoUrl, recommendForm, title, concept, categoryStr, keywords, time);

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

            List<Map<String, String>> similarVideos = youtubeAPIService.getSimilarVideos(concept, keywords);
            List<Map<String, String>> similarCreators = youtubeAPIService.getSimilarCreators(keywords, categoryStr);

            if (thumbnailImage != null || !result.isEmpty()) {
                for (Map<String, Object> item : result) {
                    Map<String, Object> thumbnail = new java.util.HashMap<>();
                    if (thumbnailImage != null) thumbnail.put("thumbnailImage", thumbnailImage);
                    Object guide = item.remove("thumbnailGuide");
                    if (guide != null) thumbnail.put("thumbnailGuide", guide);
                    item.put("thumbnail", thumbnail);
                    item.put("similarVideos", similarVideos);
                    item.put("similarCreators", similarCreators);
                }
            }

        } catch (Exception e) {
            isError = true;
            errorMsg = e.getMessage();
            throw e;
        } finally {
            int responseMs = (int) (System.currentTimeMillis() - start);

            ApiLog apiLog = ApiLog.builder()
                    .clientIp(request.getRemoteAddr())
                    .endpoint("/ai_script")
                    .category(categoryStr)
                    .keywords(keywords)
                    .channelUrl(requestURL)
                    .responseMs(responseMs)
                    .isError(isError)
                    .errorMsg(errorMsg)
                    .requestedTime(time)
                    .build();
            apiLogRepository.save(apiLog);

            if (!isError && result != null) {
                try {
                    String resultTitles = null;
                    String resultConcept = null;
                    if (!result.isEmpty()) {
                        Map<String, Object> first = result.get(0);
                        Object titlesObj = first.get("suggestedTitles");
                        Object conceptObj = first.get("conceptSummary");
                        if (titlesObj != null) resultTitles = objectMapper.writeValueAsString(titlesObj);
                        if (conceptObj != null) resultConcept = conceptObj.toString();
                    }

                    ScriptLog scriptLog = ScriptLog.builder()
                            .apiLog(apiLog)
                            .selectedTitle(title)
                            .selectedConcept(concept)
                            .resultTitles(resultTitles)
                            .resultConcept(resultConcept)
                            .build();
                    scriptLogRepository.save(scriptLog);
                } catch (Exception e) {
                    log.warn("ScriptLog 저장 실패: {}", e.getMessage());
                }
            }
        }

        return ResponseEntity.ok(result);
    }
}