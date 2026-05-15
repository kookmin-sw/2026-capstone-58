package com.capstone.crit.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import java.util.List;

@Getter
@NoArgsConstructor
public class AIScriptRequestDto {
    private String requestURL;
    private String title;
    private String concept;
    private String keywords;
    private String category;
    private int time;
}