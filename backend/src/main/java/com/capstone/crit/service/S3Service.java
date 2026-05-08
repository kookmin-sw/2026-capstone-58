package com.capstone.crit.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.util.Base64;
import java.util.UUID;

@Service
public class S3Service {

    private final S3Client s3Client;
    private final String bucket;

    public S3Service(
            @Value("${aws.region:us-east-1}") String region,
            @Value("${aws.s3.bucket}") String bucket) {
        this.s3Client = S3Client.builder()
                .region(Region.of(region))
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
        this.bucket = bucket;
    }

    public String uploadBase64Image(String base64, String prefix) {
        byte[] bytes = Base64.getDecoder().decode(base64);
        String key = prefix + "/" + UUID.randomUUID() + ".png";

        s3Client.putObject(
                PutObjectRequest.builder()
                        .bucket(bucket)
                        .key(key)
                        .contentType("image/png")
                        .build(),
                RequestBody.fromBytes(bytes));

        return "https://" + bucket + ".s3.amazonaws.com/" + key;
    }
}
