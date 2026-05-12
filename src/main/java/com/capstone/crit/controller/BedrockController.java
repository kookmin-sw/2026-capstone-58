package com.capstone.crit.controller;

import com.capstone.crit.dto.TrendRequest;
import com.capstone.crit.service.BedrockService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/ai")
@RequiredArgsConstructor
public class BedrockController {

    private final BedrockService bedrockService;

    //@PostMapping("/trend")
    //public ResponseEntity<Map<String, String>> analyzeTrend(@RequestBody TrendRequest request) {
    //    String result = bedrockService.analyzeTrend(request.getCategory(), request.getKeywords());
    //    return ResponseEntity.ok(Map.of("result", result));
    //}
}
