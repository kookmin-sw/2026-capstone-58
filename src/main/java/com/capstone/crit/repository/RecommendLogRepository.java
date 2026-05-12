// RecommendLogRepository.java
package com.capstone.crit.repository;

import com.capstone.crit.entity.RecommendLog;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RecommendLogRepository extends JpaRepository<RecommendLog, Long> {
}