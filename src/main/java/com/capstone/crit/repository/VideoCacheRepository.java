package com.capstone.crit.repository;

import com.capstone.crit.entity.VideoCache;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface VideoCacheRepository extends JpaRepository<VideoCache, Long> {
    List<VideoCache> findByChannelIdOrderByVideoRankAsc(String channelId);
    void deleteByChannelId(String channelId);
}
