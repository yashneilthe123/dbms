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
