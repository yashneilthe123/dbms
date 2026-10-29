-- SentinelX demo preflight. Run as root 5 minutes before the demo:
--   mysql --login-path=sx_root --table < demo/00_preflight.sql      (cmd)
--   mysql --login-path=sx_root --table -e "source demo/00_preflight.sql"   (PowerShell)
-- Every row should say OK.

USE sentinelx;

SELECT 'MySQL 8.0.31 or later'  AS check_item,
       IF(VERSION() >= '8.0.31', 'OK', CONCAT('TOO OLD: ', VERSION())) AS result
UNION ALL
SELECT 'binary log is on (needed for point-in-time recovery)',
       IF(@@log_bin = 1, 'OK', 'OFF')
UNION ALL
SELECT 'strict sql_mode (CHECK/ENUM errors depend on it)',
       IF(@@sql_mode LIKE '%STRICT_TRANS_TABLES%', 'OK', @@sql_mode)
UNION ALL
SELECT '17 base tables',
       IF(COUNT(*) = 17, 'OK', COUNT(*))
  FROM information_schema.tables WHERE table_schema = 'sentinelx' AND table_type = 'BASE TABLE'
UNION ALL
SELECT '50,021+ log lines',
       IF(COUNT(*) >= 50021, 'OK', COUNT(*)) FROM network_log
UNION ALL
SELECT 'idx_src_time exists',
       IF(COUNT(*) > 0, 'OK', 'MISSING: CREATE INDEX idx_src_time ON network_log (src_ip, log_time)')
  FROM information_schema.statistics
 WHERE table_schema = 'sentinelx' AND table_name = 'network_log' AND index_name = 'idx_src_time'
UNION ALL
SELECT 'demo accounts exist and are unlocked',
       IF(SUM(account_locked = 'N') = 3, 'OK', 'RUN demo/00_reset_accounts.sql')
  FROM mysql.user WHERE user IN ('ananya.rao', 'rahul.mehta', 'divya.iyer')
UNION ALL
SELECT 'injectable procedure is NOT installed (it is created only for its demo)',
       IF(COUNT(*) = 0, 'OK', 'DROP PROCEDURE sp_search_incidents_unsafe')
  FROM information_schema.routines
 WHERE routine_schema = 'sentinelx' AND routine_name = 'sp_search_incidents_unsafe'
UNION ALL
SELECT 'no open transactions holding locks',
       IF(COUNT(*) = 0, 'OK', CONCAT(COUNT(*), ' open: see information_schema.innodb_trx'))
  FROM information_schema.innodb_trx
 WHERE trx_mysql_thread_id <> CONNECTION_ID();          -- not this preflight's own read
