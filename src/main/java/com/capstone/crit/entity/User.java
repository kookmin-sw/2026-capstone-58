package com.capstone.crit.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "users")
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String googleId;

    @Column(unique = true)
    private String email;

    private String name;
    private String profileImage;

    // YouTube 채널 정보 (채널 없으면 null)
    private String youtubeChannelId;
    private String youtubeChannelTitle;

    @Column(length = 1000)
    private String youtubeChannelDescription;

    private Long subscriberCount;
    private Long videoCount;
    private String youtubeThumbnailUrl;

    // 추후 YouTube API 재호출을 위한 refresh token
    @Column(length = 500)
    private String googleRefreshToken;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @PrePersist
    public void prePersist() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    public void updateYoutubeInfo(String channelId, String channelTitle, String description,
                                  Long subscriberCount, Long videoCount, String thumbnailUrl) {
        this.youtubeChannelId = channelId;
        this.youtubeChannelTitle = channelTitle;
        this.youtubeChannelDescription = description;
        this.subscriberCount = subscriberCount;
        this.videoCount = videoCount;
        this.youtubeThumbnailUrl = thumbnailUrl;
    }

    public void updateRefreshToken(String refreshToken) {
        this.googleRefreshToken = refreshToken;
    }
}
