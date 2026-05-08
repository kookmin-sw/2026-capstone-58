package com.capstone.crit.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "script_log")
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ScriptLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "api_log_id")
    private com.capstone.crit.entity.ApiLog apiLog;

    // 사용자가 선택한 것
    private String selectedTitle;

    @Column(columnDefinition = "TEXT")
    private String selectedConcept;

    //private Integer requestedTime;

    // Gemini 결과물
    @Column(columnDefinition = "TEXT")
    private String resultTitles;   // suggestedTitles JSON

    @Column(columnDefinition = "TEXT")
    private String resultConcept;  // conceptSummary

    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        this.createdAt = LocalDateTime.now();
    }
}