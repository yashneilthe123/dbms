-- SentinelX Review 2: Transactions
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- txn_savepoint ----
START TRANSACTION;
INSERT INTO ioc (ioc_type, ioc_value, actor_id, valid_from, recorded_from)
VALUES ('domain', 'kestrel-drop.example', 4, '2026-10-20 00:00:00', '2026-10-27 12:00:00');
SAVEPOINT after_ioc;
UPDATE incident SET priority = 'LOW' WHERE incident_id = 3;
SELECT incident_id, priority FROM incident WHERE incident_id = 3;
ROLLBACK TO SAVEPOINT after_ioc;
COMMIT;

SELECT ioc_version_id, ioc_type, ioc_value FROM ioc WHERE ioc_value = 'kestrel-drop.example';
SELECT incident_id, priority FROM incident WHERE incident_id = 3;


-- ---- txn_rollback ----
SELECT COUNT(*) AS logs_before FROM network_log;

START TRANSACTION;
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:00:00', '203.0.113.5', 1, 443, 'TCP', 'allowed');
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:00:01', '203.0.113.5', 99, 443, 'TCP', 'allowed');
ROLLBACK;

SELECT COUNT(*) AS logs_after FROM network_log;
