package com.capstone.crit.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class TrendRequest {
    private String category;  // 분석할 카테고리 (예: "게임", "요리", "여행")
    private String keywords;  // 추가 키워드 (선택)
}
