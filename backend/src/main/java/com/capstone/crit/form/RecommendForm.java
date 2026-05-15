package com.capstone.crit.form;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
public class RecommendForm {

    private String title;                 // 채널명
    private String description;           // 채널 설명
    private List<String> tags;            // 🔥 영상들 태그 빈도순 집계
    private List<String> topicCategories; // 🔥 영상들 토픽 카테고리 중복제거
    private List<String> recentTitles;    // 🔥 최근 영상 제목 목록 (말투/트렌드 파악용) 추가
}