// ScriptLogRepository.java
package com.capstone.crit.repository;

import com.capstone.crit.entity.ScriptLog;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ScriptLogRepository extends JpaRepository<ScriptLog, Long> {
}