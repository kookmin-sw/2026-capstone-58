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

    @Operation(summary = "채널 분석", description = "채널 ID, @handle, 또는 유튜브 채널 URL로 분석합니다. 30일 캐싱 적용.")
    @GetMapping("/channel")
    public ResponseEntity<Map<String, Object>> analyzeChannel(
            @Parameter(description = "채널 ID / @handle / 유튜브 URL", example = "@codingapple")
            @RequestParam String channel) {
        return ResponseEntity.ok(channelAnalyzeService.analyzeByInput(channel));
    }

    @Operation(summary = "영상 상세 분석", description = "영상 ID로 상세 분석 정보를 반환합니다.")
    @GetMapping("/video/{videoId}")
    public ResponseEntity<Map<String, Object>> analyzeVideo(
            @Parameter(description = "유튜브 영상 ID", example = "dQw4w9WgXcQ")
            @PathVariable String videoId) {
        return ResponseEntity.ok(channelAnalyzeService.getVideoDetail(videoId));
    }
}
