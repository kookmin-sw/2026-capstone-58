package com.capstone.crit.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "api_log")
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApiLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String clientIp;
    private String endpoint;
    private String category;
    private String keywords;
    private String channelUrl;
    private Integer responseMs;
    private Boolean isError;
    private Integer requestedTime; // 추가

    @Column(length = 500)
    private String errorMsg;

    private LocalDateTime calledAt;

    @OneToOne(mappedBy = "apiLog", cascade = CascadeType.ALL)
    private RecommendLog recommendLog;

    @OneToOne(mappedBy = "apiLog", cascade = CascadeType.ALL)
    private ScriptLog scriptLog;

    @PrePersist
    public void prePersist() {
        this.calledAt = LocalDateTime.now();
    }
}