SET SESSION cte_max_recursion_depth = 60000;
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
WITH RECURSIVE seq (n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 50000)
SELECT TIMESTAMP('2026-09-01') + INTERVAL n * 100 SECOND,
       CONCAT('172.16.', n MOD 40, '.', 1 + n MOD 250),
       1 + n MOD 9,
       ELT(1 + n MOD 5, 443, 80, 53, 25, 22),
       IF(n MOD 5 = 2, 'UDP', 'TCP'),
       IF(n MOD 47 = 0, 'blocked', 'allowed')
FROM seq;
