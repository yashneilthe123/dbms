CREATE INDEX idx_src_time ON network_log (src_ip, log_time);
ANALYZE TABLE network_log;

EXPLAIN SELECT log_id, log_time, dst_asset_id
FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28'\G

SELECT COUNT(*) AS hits FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28';
