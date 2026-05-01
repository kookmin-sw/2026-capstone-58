package com.capstone.crit.service;

import com.capstone.crit.form.RecommendForm;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.bedrockruntime.BedrockRuntimeClient;
import software.amazon.awssdk.services.bedrockruntime.model.InvokeModelRequest;
import software.amazon.awssdk.services.bedrockruntime.model.InvokeModelResponse;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class BedrockService {

    private final BedrockRuntimeClient bedrockClient;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${aws.bedrock.model-id:anthropic.claude-3-5-sonnet-20241022-v2:0}")
    private String modelId;

    private static final String VISION_MODEL = "us.anthropic.claude-sonnet-4-20250514-v1:0";

    public BedrockService(@Value("${aws.region:us-east-1}") String region) {
        this.bedrockClient = BedrockRuntimeClient.builder()
                .region(Region.of(region))
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
    }

    public String analyzeTrend(RecommendForm recommendForm, String category, String keywords) {
        String prompt = buildTrendPrompt(recommendForm, category, keywords);
        return invokeModel(prompt);
    }

    private String buildTrendPrompt(RecommendForm recommendForm, String category, String keywords) {
        return String.format(
            "당신은 YouTube 콘텐츠 전략 전문가입니다.\n" +
                    "영상 제목: %s\n"+
                    "영상 설명: %s\n"+
            "카테고리: %s\n" +
            "키워드: %s\n\n" +
            "위 정보를 바탕으로 다음을 제공해주세요:\n" +
            "1. 현재 트렌드 분석 (3가지)\n" +
            "2. 추천 콘텐츠 주제 (5가지, 제목 포함)\n" +
            "3. 각 주제의 예상 타겟 시청자\n" +
            "한국어로 답변해주세요.",
            recommendForm.getTitle(), recommendForm.getDescription(),
            category, keywords != null ? keywords : "없음"
        );
    }

    public String analyzeThumbnailsAndGeneratePrompt(List<byte[]> thumbnailImages, String topic, String concept) {
        try {
            List<Map<String, Object>> content = new ArrayList<>();
            for (byte[] img : thumbnailImages) {
                content.add(Map.of("type", "image", "source", Map.of(
                    "type", "base64",
                    "media_type", "image/jpeg",
                    "data", java.util.Base64.getEncoder().encodeToString(img)
                )));
            }
            content.add(Map.of("type", "text", "text",
                String.format("위 %d개의 YouTube 썸네일을 분석해서 색상 팔레트, 텍스트 스타일, 레이아웃, 분위기를 파악해줘.\n" +
                    "그리고 이 채널 스타일을 유지하면서 아래 주제의 썸네일을 만들기 위한 Imagen 프롬프트를 영어로 작성해줘.\n" +
                    "주제: %s\n설명: %s\n\n" +
                    "중요: 텍스트, 글자, 문자는 일절 포함하지 말 것. 색상, 레이아웃, 인물/오브젝트 구성, 분위기만 표현해줘.\n" +
                    "프롬프트는 \"IMAGEN_PROMPT:\" 로 시작해줘.",
                    thumbnailImages.size(), topic, concept)));

            Map<String, Object> body = Map.of(
                "anthropic_version", "bedrock-2023-05-31",
                "max_tokens", 1024,
                "messages", List.of(Map.of("role", "user", "content", content))
            );

            InvokeModelRequest request = InvokeModelRequest.builder()
                .modelId(VISION_MODEL)
                .contentType("application/json")
                .accept("application/json")
                .body(SdkBytes.fromUtf8String(objectMapper.writeValueAsString(body)))
                .build();

            InvokeModelResponse response = bedrockClient.invokeModel(request);
            Map<?, ?> responseBody = objectMapper.readValue(response.body().asUtf8String(), Map.class);
            List<?> responseContent = (List<?>) responseBody.get("content");
            String text = (String) ((Map<?, ?>) responseContent.get(0)).get("text");

            if (text.contains("IMAGEN_PROMPT:")) {
                return text.substring(text.indexOf("IMAGEN_PROMPT:") + "IMAGEN_PROMPT:".length()).trim();
            }
            return text.trim();
        } catch (Exception e) {
            throw new RuntimeException("썸네일 분석 실패: " + e.getMessage(), e);
        }
    }

    private String invokeModel(String prompt) {        try {
            Map<String, Object> body = Map.of(
                "anthropic_version", "bedrock-2023-05-31",
                "max_tokens", 1024,
                "messages", List.of(
                    Map.of("role", "user", "content", prompt)
                )
            );

            String bodyJson = objectMapper.writeValueAsString(body);

            InvokeModelRequest request = InvokeModelRequest.builder()
                    .modelId(modelId)
                    .contentType("application/json")
                    .accept("application/json")
                    .body(SdkBytes.fromUtf8String(bodyJson))
                    .build();

            InvokeModelResponse response = bedrockClient.invokeModel(request);
            Map<?, ?> responseBody = objectMapper.readValue(
                response.body().asUtf8String(), Map.class
            );

            // Claude 응답 파싱
            List<?> content = (List<?>) responseBody.get("content");
            Map<?, ?> firstContent = (Map<?, ?>) content.get(0);
            return (String) firstContent.get("text");

        } catch (Exception e) {
            throw new RuntimeException("Bedrock 호출 실패: " + e.getMessage(), e);
        }
    }
}
