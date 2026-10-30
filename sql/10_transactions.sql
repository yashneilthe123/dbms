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


-- ---- txn_handler_rollback ----
-- a failed statement does NOT roll back the transaction: COMMIT keeps the good row
START TRANSACTION;
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:05:00', '203.0.113.6', 1, 443, 'TCP', 'allowed');
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:05:01', '203.0.113.6', 99, 443, 'TCP', 'allowed');
COMMIT;
SELECT COUNT(*) AS kept_after_commit FROM network_log WHERE src_ip = '203.0.113.6';
DELETE FROM network_log WHERE src_ip = '203.0.113.6';

-- the loader therefore rolls back the whole batch itself
DELIMITER //
CREATE PROCEDURE sp_load_log_batch(IN p_last_asset INT)
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;
  INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
  VALUES ('2026-10-28 09:10:00', '203.0.113.7', 1, 22, 'TCP', 'blocked'),
         ('2026-10-28 09:10:01', '203.0.113.7', 2, 22, 'TCP', 'blocked');
  INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
  VALUES ('2026-10-28 09:10:02', '203.0.113.7', p_last_asset, 22, 'TCP', 'blocked');
  COMMIT;
END //
DELIMITER ;

CALL sp_load_log_batch(99);
SELECT COUNT(*) AS rows_after_failed_batch FROM network_log WHERE src_ip = '203.0.113.7';

CALL sp_load_log_batch(3);
SELECT COUNT(*) AS rows_after_good_batch FROM network_log WHERE src_ip = '203.0.113.7';
DELETE FROM network_log WHERE src_ip = '203.0.113.7';
