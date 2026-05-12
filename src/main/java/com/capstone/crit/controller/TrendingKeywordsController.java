package com.capstone.crit.controller;

import com.capstone.crit.service.TrendingKeywordsService;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
public class TrendingKeywordsController {

    private final TrendingKeywordsService trendingKeywordsService;

    @Operation(summary = "트렌드 키워드 TOP 100", description = "S3에 저장된 실시간 트렌드 키워드를 반환합니다.")
    @GetMapping("/keywords")
    public ResponseEntity<String> getKeywords() {
        return ResponseEntity.ok()
                .header("Content-Type", "application/json")
                .body(trendingKeywordsService.getKeywords());
    }
}
