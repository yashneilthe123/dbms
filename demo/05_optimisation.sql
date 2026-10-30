-- Demo step 5 (root): one optimisation, before and after.
-- If a rehearsal stopped half-way and idx_src_time is already gone, skip the DROP line.
USE sentinelx;

ALTER TABLE network_log DROP INDEX idx_src_time;
ANALYZE TABLE network_log;
EXPLAIN SELECT log_id, log_time, dst_asset_id FROM network_log
WHERE src_ip = '198.51.100.77' AND log_time >= '2026-09-15' AND log_time < '2026-10-28'\G
-- type: ALL, rows: ~50,000  -> every row is read

CREATE INDEX idx_src_time ON network_log (src_ip, log_time);
ANALYZE TABLE network_log;
EXPLAIN SELECT log_id, log_time, dst_asset_id FROM network_log
WHERE src_ip = '198.51.100.77' AND log_time >= '2026-09-15' AND log_time < '2026-10-28'\G
-- type: range, key: idx_src_time, rows: 8

EXPLAIN ANALYZE SELECT log_id, log_time, dst_asset_id FROM network_log
WHERE src_ip = '198.51.100.77' AND log_time >= '2026-09-15' AND log_time < '2026-10-28';

-- an index that exists but is not used: a function on the column hides it
EXPLAIN SELECT COUNT(*) FROM network_log WHERE SUBSTRING_INDEX(src_ip, '.', 3) = '198.51.100'\G
EXPLAIN SELECT COUNT(*) FROM network_log WHERE src_ip LIKE '198.51.100.%'\G
