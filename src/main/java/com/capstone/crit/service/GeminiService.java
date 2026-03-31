package com.capstone.crit.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;

import java.util.List;
import java.util.Map;

@Service
public class GeminiService {

    @Value("${gemini.api.key}")
    private String apikey;

    private final RestTemplate restTemplate = new RestTemplate();
    private static final String MODEL_ID = "gemini-3.1-flash-lite-preview";

    public String analyzeVideo(String youtubeUrl, String category, String keywords) {
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
                    전문 영상 스크립트 작가 역할을 합니다.
                    입력된 영상(URL: %s)을 분석하여 다음 지시 사항에 따라 새로운 대본을 작성합니다.
                
                    1. 스타일 복제: 원본 영상의 말투, 진행 속도, 자막 스타일, 편집 호흡, 전체적인 분위기(톤앤매너)를 유지합니다.
                    2. 내용 차별화: '스타일'은 같지만, 내용은 원본과 완전히 다르게 구성합니다.
                    3. 분량: 약 5분 정도의 영상 촬영이 가능한 상세한 스크립트 형태로 작성합니다.
                
                    [출력 형식]
                    - 도입부 - 전개 - 결론 (영상 분량에 따라 단계 추가)
            """, cleanUrl);

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

            ResponseEntity<Map> responseEntity = restTemplate.exchange(url, HttpMethod.POST, entity, Map.class);
            return extractText(responseEntity.getBody());

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