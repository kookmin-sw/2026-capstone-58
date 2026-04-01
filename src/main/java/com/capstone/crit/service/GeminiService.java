package com.capstone.crit.service;

import com.capstone.crit.form.RecommendForm;
import com.fasterxml.jackson.core.type.TypeReference;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;

import java.util.List;
import java.util.Map;

@Service
public class GeminiService {

    @Value("${gemini.api.key}")
    private String apikey;

    private final RestTemplate restTemplate = new RestTemplate();
    private static final String MODEL_ID = "gemini-3.1-flash-lite-preview";

    public List<Map<String, String>> recommendTopic(RecommendForm recommendForm, String category, String keywords) {
        try {
            String url = String.format(
                    "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s",
                    MODEL_ID,
                    apikey
            );

            // ✅ 1. 프롬프트 수정: 데이터 기반 분석 및 JSON 출력 지시
            String prompt = String.format("""
                            당신은 유튜브 기획자입니다.\s
                                        원본 영상의 데이터를 분석하되, 내용에 얽매이지 말고 '완전히 새로운' 기획안 3개를 작성하세요.
                            
                                        [원본 데이터 참고용]
                                        - 제목: %s
                                        - 태그: %s
                                        - 카테고리: %s / 사용자 요청: %s
                                        - 키워드: %s
                            
                                        [기획 지시 사항]
                                        1. 창의성 우선: 원본 데이터의 내용 써도 되고 관련 된 다른 키워드로 작성 해도 됩니다.
                                        2. 무조건 원본 데이터와 연관된 다른 키워드로 확장하거나 더 깊은 내요을 다루거나 합니다.
                                        3. 형식: 반드시 아래의 JSON 배열 형식으로만 답변하세요. (Markdown 기호 제외)
                            
                                        [
                                          {
                                            "suggestedTitle": "예측 불가능하고 자극적인 새 영상 제목",
                                            "conceptSummary": "기존의 틀을 깨는 창의적인 기획 의도 한 줄"
                                          },
                                          {
                                            "suggestedTitle": "두 번째 파격적인 추천 제목",
                                            "conceptSummary": "두 번째 기획 의도 한 줄"
                                          },
                                          {
                                            "suggestedTitle": "세 번째 혁신적인 추천 제목",
                                            "conceptSummary": "세 번째 기획 의도 한 줄"
                                          }
                                        ]
                """,
                    recommendForm.getTitle(),
                    recommendForm.getTags(),
                    recommendForm.getTopicCategories(),
                    category,
                    keywords);

            // ✅ 2. 요청 바디 구성 (영상 분석이 아닌 데이터 분석이므로 textPart만 사용하거나 프롬프트에 URL 포함)
            Map<String, Object> textPart = Map.of("text", prompt);
            Map<String, Object> requestBody = Map.of(
                    "contents", List.of(Map.of("parts", List.of(textPart)))
            );

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            // ✅ 3. API 호출 및 응답 파싱
            ResponseEntity<Map> responseEntity = restTemplate.exchange(url, HttpMethod.POST, entity, Map.class);
            String rawJson = extractText(responseEntity.getBody());

            // ✨ 4. JSON 문자열을 List<Map>으로 변환하여 리턴 (Jackson 이용)
            ObjectMapper mapper = new ObjectMapper();
            String cleanJson = rawJson.trim().replaceAll("^```[a-zA-Z]*\\n?", "").replaceAll("```$", "").trim();
            return mapper.readValue(cleanJson, new TypeReference<List<Map<String, String>>>() {});

        } catch (Exception e) {
            throw new RuntimeException("Gemini 추천 생성 실패: " + e.getMessage());
        }
    }

    public List<Map<String, Object>> writeScript(String youtubeUrl, String title,String concept,String category, String keywords) {
        try {
            // 1. URL 정규화 (추가 파라미터 제거)
            String cleanUrl = normalizeYoutubeUrl(youtubeUrl);

            String url = String.format(
                    "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s",
                    MODEL_ID,
                    apikey
            );

            // 2. 프롬프트 준비
            String prompt = String.format("""
                    String youtubeUrl, String title, String concept, String category, String keywords
                    
                         당신은 유튜브 콘텐츠 기획 전문가입니다.
                         youtubeUrl을 기반으로 영상의 핵심 흐름과 패턴을 분석하되, 기존 내용에 얽매이지 말고 확장된 새로운 기획을 제안하세요.
                    
                         [원본 데이터 참고용]
                         - URL: %s
                         - 제목: %s
                         - 컨셉: %s
                         - 카테고리: %s
                         - 키워드: %s
                    
                         [기획 지시 사항]
                         1. URL 영상의 구조(주제, 흐름, 포인트)를 참고하되 완전히 새로운 방향으로 재해석하세요.
                         2. 기존 키워드를 확장하거나 트렌디한 요소를 추가하세요.
                         3. 결과 기획안은 **약 5분 분량의 영상 구성**을 기준으로 작성하세요. (초반 훅 → 전개 → 클라이맥스 → 마무리 흐름 포함)
                         4. 작성한 기획안과 관련된 새로운 제목을 생성하세요.
                         5. 결과는 반드시 아래 JSON 형식으로만 출력하세요. (Markdown 금지)
                    
                         [
                           {
                             "conceptSummary": "5분 영상 기준으로 구성된 새로운 기획안",
                             "suggestedTitles": [
                               "자극적인 제목 1",
                               "자극적인 제목 2",
                               "자극적인 제목 3",
                               "자극적인 제목 4",
                               "자극적인 제목 5"
                             ]
                           }
                         ]
            """, cleanUrl,
                    title,
                    concept,
                    category,
                    keywords);

            // 3. JSON 구성 (유효성 검사 통과를 위해 정규화된 cleanUrl 사용)
            Map<String, Object> videoPart = Map.of(
                    "file_data", Map.of(
                            "mime_type", "video/mp4",
                            "file_uri", cleanUrl
                    )
            );

            Map<String, Object> textPart = Map.of("text", prompt);

            Map<String, Object> requestBody = Map.of(
                    "contents", List.of(
                            Map.of("parts", List.of(videoPart, textPart))
                    )
            );

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

            // ✅ 3. API 호출 및 응답 파싱
            ResponseEntity<Map> responseEntity = restTemplate.exchange(url, HttpMethod.POST, entity, Map.class);
            String rawJson = extractText(responseEntity.getBody());

            // ✨ 4. JSON 문자열을 List<Map>으로 변환하여 리턴 (Jackson 이용)
            ObjectMapper mapper = new ObjectMapper();
            String cleanJson = rawJson.trim().replaceAll("^```[a-zA-Z]*\\n?", "").replaceAll("```$", "").trim();
            return mapper.readValue(cleanJson, new TypeReference<List<Map<String, Object>>>() {});

        } catch (Exception e) {
            System.err.println("에러 상세: " + e.getMessage());
            throw new RuntimeException("Gemini 시청 분석 실패: " + e.getMessage());
        }
    }

    /**
     * 유튜브 URL에서 불필요한 파라미터(list, index, start_radio 등)를 제거하고
     * 표준 형태(https://www.youtube.com/watch?v=VIDEO_ID)로 변환합니다.
     */
    private String normalizeYoutubeUrl(String url) {
        if (url == null || !url.contains("v=")) return url;
        try {
            String videoId = url.split("v=")[1].split("&")[0];
            return "https://www.youtube.com/watch?v=" + videoId;
        } catch (Exception e) {
            return url; // 파싱 실패 시 원본 반환
        }
    }

    private String extractText(Map response) {
        try {
            List candidates = (List) response.get("candidates");
            Map first = (Map) candidates.get(0);
            Map content = (Map) first.get("content");
            List parts = (List) content.get("parts");
            return (String) ((Map) parts.get(0)).get("text");
        } catch (Exception e) {
            return "응답 처리 중 오류: " + e.getMessage();
        }
    }
}