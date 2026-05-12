package com.capstone.crit.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "recommend_log")
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RecommendLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "api_log_id")
    private com.capstone.crit.entity.ApiLog apiLog;

    @Column(columnDefinition = "TEXT")
    private String recommendations; // Gemini 추천 3개 JSON 통째로

    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        this.createdAt = LocalDateTime.now();
    }
}