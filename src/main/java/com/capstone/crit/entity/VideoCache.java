package com.capstone.crit.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "video_cache")
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class VideoCache {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String channelId;

    private String videoId;
    private String title;
    private String thumbnailUrl;
    private Long viewCount;
    private Long likeCount;
    private Long commentCount;
    private Long durationSeconds;
    private Integer algorithmScore; // 계산된 알고리즘 점수
    private Integer videoRank;      // 1~10 순서

    @Column(nullable = false)
    private LocalDateTime fetchedAt;
}
