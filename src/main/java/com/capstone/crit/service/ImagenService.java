package com.capstone.crit.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Jwts;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.time.Instant;
import java.util.Base64;
import java.util.Date;
import java.util.List;
import java.util.Map;

@Service
public class ImagenService {

    private static final String IMAGEN_MODEL = "imagen-4.0-generate-001";
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final String gcpKeyPath;

    public ImagenService(@Value("${gcp.key-path}") String gcpKeyPath) {
        this.gcpKeyPath = gcpKeyPath;
    }

    public String generateThumbnail(String prompt) {
        try {
            JsonNode key = objectMapper.readTree(Files.readString(Paths.get(gcpKeyPath)));
            String projectId = key.get("project_id").asText();
            String token = getAccessToken(key);

            Map<String, Object> body = Map.of(
                "instances", List.of(Map.of("prompt", prompt)),
                "parameters", Map.of("sampleCount", 1, "aspectRatio", "16:9",
                    "outputOptions", Map.of("mimeType", "image/png"))
            );

            String response = WebClient.builder()
                .baseUrl("https://us-central1-aiplatform.googleapis.com")
                .codecs(c -> c.defaultCodecs().maxInMemorySize(10 * 1024 * 1024))
                .build()
                .post()
                .uri("/v1/projects/{p}/locations/us-central1/publishers/google/models/{m}:predict",
                    projectId, IMAGEN_MODEL)
                .header("Authorization", "Bearer " + token)
                .header("Content-Type", "application/json")
                .bodyValue(objectMapper.writeValueAsString(body))
                .retrieve()
                .bodyToMono(String.class)
                .block();

            return objectMapper.readTree(response)
                .path("predictions").get(0)
                .path("bytesBase64Encoded").asText();
        } catch (Exception e) {
            throw new RuntimeException("Imagen 호출 실패: " + e.getMessage(), e);
        }
    }

    private String getAccessToken(JsonNode key) throws Exception {
        String privateKeyPem = key.get("private_key").asText()
            .replace("-----BEGIN PRIVATE KEY-----", "")
            .replace("-----END PRIVATE KEY-----", "")
            .replaceAll("\\s", "");

        PrivateKey privateKey = KeyFactory.getInstance("RSA")
            .generatePrivate(new PKCS8EncodedKeySpec(Base64.getDecoder().decode(privateKeyPem)));

        String clientEmail = key.get("client_email").asText();
        Instant now = Instant.now();

        String jwt = Jwts.builder()
            .issuer(clientEmail)
            .subject(clientEmail)
            .claim("aud", "https://oauth2.googleapis.com/token")
            .claim("scope", "https://www.googleapis.com/auth/cloud-platform")
            .issuedAt(Date.from(now))
            .expiration(Date.from(now.plusSeconds(3600)))
            .signWith(privateKey)
            .compact();

        String tokenResponse = WebClient.create("https://oauth2.googleapis.com")
            .post()
            .uri("/token")
            .header("Content-Type", "application/x-www-form-urlencoded")
            .bodyValue("grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=" + jwt)
            .retrieve()
            .bodyToMono(String.class)
            .block();

        return objectMapper.readTree(tokenResponse).get("access_token").asText();
    }
}
