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

    private AIService aiService;
    private YoutubeAPIService youtubeAPIService;
    private BedrockService bedrockService;
    private GeminiService geminiService;
    private ApiLogRepository apiLogRepository;
    private RecommendLogRepository recommendLogRepository;
    private ScriptLogRepository scriptLogRepository;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Operation(summary = "유튜브 기반 주제 추천")
    @PostMapping("/ai_recommend")
    public ResponseEntity<List<Map<String, String>>> AIRecommend(
            @RequestParam String requestURL,
            @RequestParam String keywords,
            @RequestParam String category,
            HttpServletRequest request) {

        long start = System.currentTimeMillis();
        boolean isError = false;
        String errorMsg = null;
        String clientIp = getClientIp(request);
        List<Map<String, String>> result = null;

        try {
            RecommendForm recommendForm = youtubeAPIService.getData(requestURL);
            result = geminiService.recommendTopic(recommendForm, category, keywords);
            return ResponseEntity.ok(result);

        } catch (Exception e) {
            isError = true;
            errorMsg = e.getMessage();
            throw e;

        } finally {
            try {
                ApiLog apiLog = apiLogRepository.save(ApiLog.builder()
                        .clientIp(clientIp)
                        .endpoint("/ai_recommend")
                        .category(category)
                        .keywords(keywords)
                        .channelUrl(requestURL)
                        .responseMs((int)(System.currentTimeMillis() - start))
                        .isError(isError)
                        .errorMsg(errorMsg)
                        .build());

                // 성공했을 때만 결과 저장
                if (result != null) {
                    recommendLogRepository.save(RecommendLog.builder()
                            .apiLog(apiLog)
                            .recommendations(objectMapper.writeValueAsString(result))
                            .build());
                }
            } catch (Exception logEx) {
                log.error("로그 저장 실패: {}", logEx.getMessage());
            }
        }
    }

    @Operation(summary = "영상 기획 및 제목 생성")
    @PostMapping("/ai_script")
    public ResponseEntity<List<Map<String, Object>>> AIScript(
            @RequestParam String requestURL,
            @RequestParam String title,
            @RequestParam String concept,
            @RequestParam String keywords,
            @RequestParam List<String> category,
            @RequestParam int time,
            HttpServletRequest request) {

        long start = System.currentTimeMillis();
        boolean isError = false;
        String errorMsg = null;
        String clientIp = getClientIp(request);
        List<Map<String, Object>> result = null;

        try {
            RecommendForm recommendForm = youtubeAPIService.getData(requestURL);
            String latestVideoUrl = youtubeAPIService.getLatestVideoUrl(requestURL);
            String categoryStr = String.join(", ", category);
            result = geminiService.writeScript(latestVideoUrl, recommendForm, title, concept, categoryStr, keywords, time);
            return ResponseEntity.ok(result);

        } catch (Exception e) {
            isError = true;
            errorMsg = e.getMessage();
            throw e;

        } finally {
            try {
                ApiLog apiLog = apiLogRepository.save(ApiLog.builder()
                        .clientIp(clientIp)
                        .endpoint("/ai_script")
                        .category(String.join(", ", category))
                        .keywords(keywords)
                        .channelUrl(requestURL)
                        .responseMs((int)(System.currentTimeMillis() - start))
                        .requestedTime(time)
                        .isError(isError)
                        .errorMsg(errorMsg)
                        .build());

                // 성공했을 때만 결과 저장
                if (result != null && !result.isEmpty()) {
                    Map<String, Object> first = result.get(0);
                    Object titles = first.get("suggestedTitles");
                    Object conceptSummary = first.get("conceptSummary");

                    scriptLogRepository.save(ScriptLog.builder()
                            .apiLog(apiLog)
                            .selectedTitle(title)
                            .selectedConcept(concept)
                            .resultTitles(objectMapper.writeValueAsString(titles))
                            .resultConcept(conceptSummary != null ? conceptSummary.toString() : null)
                            .build());
                }
            } catch (Exception logEx) {
                log.error("로그 저장 실패: {}", logEx.getMessage());
            }
        }
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddr();
        }
        return ip.split(",")[0].trim();
    }
}