package com.capstone.crit.form;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter @Setter
@NoArgsConstructor // JSON 파싱 시 기본 생성자가 필요할 수 있음
@AllArgsConstructor
public class RecommendForm {

    // [기본 정보]
    private String title;          // 영상 제목
    private String description;    // 영상 설명 (요약해서 전달 권장)

    // [기능적 정보 - 제미나이 분석용]
    private List<String> tags;     // 크리에이터가 설정한 핵심 키워드 (가장 중요)
    private List<String> topicCategories; // 유튜브 알고리즘이 분류한 주제 URL 리스트

}