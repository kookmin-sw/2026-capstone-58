package com.capstone.crit.controller;

import com.capstone.crit.service.ChannelAnalyzeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/analyze")
public class AnalyzeController {

    private final ChannelAnalyzeService channelAnalyzeService;

    @Operation(summary = "채널 분석", description = "채널 ID로 유튜브 채널을 분석합니다. 30일 캐싱 적용.")
    @GetMapping("/channel")
    public ResponseEntity<Map<String, Object>> analyzeChannel(
            @Parameter(description = "유튜브 채널 ID", example = "UCxxxxxx")
            @RequestParam String channelId) {
        return ResponseEntity.ok(channelAnalyzeService.analyze(channelId));
    }
}
