-- SentinelX Review 2: Indexes and EXPLAIN
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- idx_list ----
SELECT table_name, index_name,
       GROUP_CONCAT(column_name ORDER BY seq_in_index) AS columns_in_index,
       IF(non_unique = 0, 'yes', 'no') AS is_unique
FROM information_schema.statistics
WHERE table_schema = 'sentinelx'
  AND table_name IN ('network_log', 'attack_event')
GROUP BY table_name, index_name, non_unique
ORDER BY table_name, index_name;


-- ---- idx_explain_before ----
ALTER TABLE network_log DROP INDEX idx_src_time;
ANALYZE TABLE network_log;

EXPLAIN SELECT log_id, log_time, dst_asset_id
FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28'\G

SELECT COUNT(*) AS hits FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28';


-- ---- idx_explain_after ----
CREATE INDEX idx_src_time ON network_log (src_ip, log_time);
ANALYZE TABLE network_log;

EXPLAIN SELECT log_id, log_time, dst_asset_id
FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28'\G

SELECT COUNT(*) AS hits FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28';
