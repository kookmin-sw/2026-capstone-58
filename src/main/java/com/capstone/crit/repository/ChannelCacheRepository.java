package com.capstone.crit.repository;

import com.capstone.crit.entity.ChannelCache;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.transaction.annotation.Transactional;
import java.util.Optional;

public interface ChannelCacheRepository extends JpaRepository<ChannelCache, Long> {
    Optional<ChannelCache> findByChannelId(String channelId);

    @Modifying
    @Transactional
    @Query("UPDATE ChannelCache c SET c.guidesJson = :guidesJson WHERE c.id = :id")
    void updateGuidesJson(Long id, String guidesJson);

    @Modifying
    @Transactional
    @Query("UPDATE ChannelCache c SET c.percentileScore = :total, c.percentileVps = :vps, c.percentileEngagement = :eng, c.percentileLikeRate = :lr WHERE c.id = :id")
    void updatePercentileScore(Long id, int total, int vps, int eng, int lr);
}
