-- Demo step 3 (root): a transactional workflow with a deliberate failure.
USE sentinelx;

-- (a) the trap: a failed statement does NOT roll back the transaction
SELECT COUNT(*) AS logs_before FROM network_log;
START TRANSACTION;
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES (NOW(), '203.0.113.6', 1, 443, 'TCP', 'allowed');
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES (NOW(), '203.0.113.6', 99, 443, 'TCP', 'allowed');      -- ERROR 1452: no asset 99
COMMIT;
SELECT COUNT(*) AS kept_after_commit FROM network_log WHERE src_ip = '203.0.113.6';   -- 1: half a batch
DELETE FROM network_log WHERE src_ip = '203.0.113.6';

-- (b) the fix: the loader's exit handler rolls back the whole batch and re-raises the error
CALL sp_load_log_batch(99);                                     -- ERROR 1452
SELECT COUNT(*) AS rows_after_failed_batch FROM network_log WHERE src_ip = '203.0.113.7';   -- 0
CALL sp_load_log_batch(3);
SELECT COUNT(*) AS rows_after_good_batch FROM network_log WHERE src_ip = '203.0.113.7';     -- 3
DELETE FROM network_log WHERE src_ip = '203.0.113.7';

-- (c) savepoint: keep the first change, undo the second
START TRANSACTION;
UPDATE incident SET status = 'INVESTIGATING' WHERE incident_id = 6;
SAVEPOINT after_status;
UPDATE incident SET priority = 'LOW' WHERE incident_id = 6;
ROLLBACK TO SAVEPOINT after_status;
COMMIT;
SELECT incident_id, status, priority FROM incident WHERE incident_id = 6;
