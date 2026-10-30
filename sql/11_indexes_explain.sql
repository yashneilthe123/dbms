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


-- ---- idx_not_used ----
-- leftmost prefix: idx_src_time is (src_ip, log_time), so a filter on log_time alone
-- cannot seek it directly. Without skip scan this is a full index scan ...
EXPLAIN SELECT /*+ NO_SKIP_SCAN(network_log) */ COUNT(*) FROM network_log
WHERE log_time >= '2026-10-27' AND log_time < '2026-10-28'\G

-- ... MySQL 8.0.13+ instead does one range read per distinct src_ip (1,004 of them)
EXPLAIN SELECT COUNT(*) FROM network_log
WHERE log_time >= '2026-10-27' AND log_time < '2026-10-28'\G

-- a function on the indexed column hides it from the optimizer ...
EXPLAIN SELECT COUNT(*) FROM network_log
WHERE SUBSTRING_INDEX(src_ip, '.', 3) = '198.51.100'\G

-- ... the same filter written as a prefix LIKE becomes a range read
EXPLAIN SELECT COUNT(*) FROM network_log
WHERE src_ip LIKE '198.51.100.%'\G

-- actual time and rows, not estimates
EXPLAIN ANALYZE SELECT log_id, log_time, dst_asset_id
FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28';
