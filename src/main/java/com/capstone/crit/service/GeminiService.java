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
        당신은 유튜브 콘텐츠 기획자입니다.
        아래 채널 정보를 참고하여 이 유튜버가 다음에 올릴 만한 영상 주제 3개를 추천하세요.

        [채널 참고 정보 - 방향성 파악용]
        - 채널명: %s
        - 채널 설명: %s
        - 최근 영상 제목들: %s
        - 자주 사용한 태그: %s
        - 주요 카테고리: %s

        [사용자 요청 조건 - 반드시 반영]
        - 카테고리: %s
        - 키워드: %s

        [기획 지시 사항]
        1. 채널 정보는 이 유튜버의 스타일과 방향성을 파악하는 참고용입니다. 내용에 종속될 필요 없습니다.
        2. 사용자가 요청한 카테고리와 키워드는 반드시 주제에 반영하세요.
        3. 결과는 반드시 아래 JSON 배열 형식으로만 답변하세요. (Markdown 기호 제외)

        [
          {
            "suggestedTitle": "다음 영상 후보 제목 1",
            "conceptSummary": "기획 의도 한 줄"
          },
          {
            "suggestedTitle": "다음 영상 후보 제목 2",
            "conceptSummary": "기획 의도 한 줄"
          },
          {
            "suggestedTitle": "다음 영상 후보 제목 3",
            "conceptSummary": "기획 의도 한 줄"
          }
        ]
        """,
                    recommendForm.getTitle(),
                    recommendForm.getDescription(),
                    recommendForm.getRecentTitles(),
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

    public List<Map<String, Object>> writeScript(String youtubeUrl, RecommendForm recommendForm, String title,String concept,String category, String keywords, int time) {
        try {
            // 1. URL 정규화 (추가 파라미터 제거)
            String cleanUrl = normalizeYoutubeUrl(youtubeUrl);

            String url = String.format(
                    "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s",
                    MODEL_ID,
                    apikey
            );


            String duration = time + "분";

            // 🔥 프롬프트 수정: time 반영, 채널 최신 영상 분석 기준으로 변경
            String prompt = String.format("""
        당신은 유튜브 콘텐츠 기획 전문가입니다.
        아래 유튜브 영상을 직접 시청하고, 발화자의 말투·톤·특성을 파악한 뒤
        그 스타일을 살려 완전히 새로운 기획안을 작성하세요.

        [채널 정보 - 스타일 파악용]
        - 채널명: %s
        - 채널 설명: %s
        - 최근 영상 제목들: %s
        - 자주 사용한 태그: %s
        - 주요 카테고리: %s

        [채널 최신 영상 - 직접 분석 대상]
        - URL: %s
        - 선택된 기획 제목: %s
        - 컨셉: %s
        - 사용자 요청 카테고리: %s
        - 키워드: %s
        - 목표 영상 길이: %s

        [기획 지시 사항]
        1. 위 영상을 직접 시청하여 발화자의 말투, 톤, 편집 스타일, 콘텐츠 흐름을 파악하세요.
        2. 채널 정보(태그, 최근 제목들)로 채널 특성을 파악하고 기획안에 반영하세요.
        3. 파악한 발화자 특성을 기획안 전체에 반영하세요. (말투, 구성 방식 등)
        4. 기획안은 %s 분량 기준으로 작성하세요. (훅 → 전개 → 클라이맥스 → 마무리)
        5. 기존 키워드/카테고리에서 확장하거나 트렌디한 요소를 추가하세요.
        6. 기획안에 맞는 제목 5개를 생성하세요.
        7. 반드시 아래 JSON 형식으로만 출력하세요. (Markdown 기호 절대 금지)
        8. thumbnailGuide 내용은 공백 포함 100자 이내로 출력되게 하세요

        [
          {
            "conceptSummary": "위 조건을 반영한 새로운 기획안 (발화자 말투 포함)",
            "suggestedTitles": [
              "제목 1",
              "제목 2",
              "제목 3",
              "제목 4",
              "제목 5"
            ],
            "thumbnailGuide": "썸네일 구성 가이드 (색상, 레이아웃, 분위기 등)"
          }
        ]
        """,
                    // 🔥 채널 정보 (recommendForm)
                    recommendForm.getTitle(),           // 1 채널명
                    recommendForm.getDescription(),     // 2 채널 설명
                    recommendForm.getRecentTitles(),    // 3 최근 영상 제목들
                    recommendForm.getTags(),            // 4 태그
                    recommendForm.getTopicCategories(), // 5 토픽 카테고리

                    // 영상 + 사용자 요청 정보
                    cleanUrl,                           // 6 영상 URL
                    title,                              // 7 선택된 기획 제목
                    concept,                            // 8 컨셉
                    category,                           // 9 사용자 요청 카테고리
                    keywords,                           // 10 키워드
                    duration,                           // 11 목표 영상 길이
                    duration                            // 12 기획 지시 사항 4번
            );



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
            if (cleanJson.startsWith("{")) {
                cleanJson = "[" + cleanJson + "]";
            }
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