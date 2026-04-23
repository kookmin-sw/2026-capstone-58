package com.capstone.crit.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "channel_cache")
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ChannelCache {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String channelId;

    private String channelName;
    private String profileImageUrl;
    private Long subscriberCount;
    private Long previousSubscriberCount; // 성장률 계산용
    private Long totalVideoCount;
    private Double avgViewCount;
    private Double uploadFrequencyPerWeek;   // 주 업로드 빈도
    private Double avgWatchDurationSeconds;  // 평균 시청 지속 시간(초)

    @Column(nullable = false)
    private LocalDateTime fetchedAt;
}
