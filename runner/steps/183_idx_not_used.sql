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
