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

import java.util.List;
import java.util.Map;

@Service
public class BedrockService {

    private final BedrockRuntimeClient bedrockClient;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${aws.bedrock.model-id:anthropic.claude-3-5-sonnet-20241022-v2:0}")
    private String modelId;

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

    private String invokeModel(String prompt) {
        try {
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
