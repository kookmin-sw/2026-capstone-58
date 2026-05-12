package com.capstone.crit.service;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

@Service
@Slf4j
public class TrendingKeywordsService {

    private final S3Client s3Client;
    private final String bucket;
    private final String key;
    private volatile String cachedJson = "[]";

    public TrendingKeywordsService(
            @Value("${aws.region:us-east-1}") String region,
            @Value("${aws.s3.trending-bucket:pj-kmucd1-08-s3-trending-keywords}") String bucket,
            @Value("${aws.s3.trending-key:words.json}") String key) {
        this.s3Client = S3Client.builder()
                .region(Region.of(region))
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
        this.bucket = bucket;
        this.key = key;
    }

    @PostConstruct
    public void init() {
        refresh();
    }

    @Scheduled(fixedRate = 3600000)
    public void refresh() {
        try {
            InputStream is = s3Client.getObject(GetObjectRequest.builder()
                    .bucket(bucket).key(key).build());
            cachedJson = new String(is.readAllBytes(), StandardCharsets.UTF_8);
            is.close();
            log.info("트렌드 키워드 로드 완료 ({}bytes)", cachedJson.length());
        } catch (Exception e) {
            log.warn("트렌드 키워드 로드 실패: {}", e.getMessage());
        }
    }

    public String getKeywords() {
        return cachedJson;
    }
}
