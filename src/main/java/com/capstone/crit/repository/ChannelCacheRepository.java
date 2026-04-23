package com.capstone.crit.repository;

import com.capstone.crit.entity.ChannelCache;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ChannelCacheRepository extends JpaRepository<ChannelCache, Long> {
    Optional<ChannelCache> findByChannelId(String channelId);
}
