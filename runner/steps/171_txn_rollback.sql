SELECT COUNT(*) AS logs_before FROM network_log;

START TRANSACTION;
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:00:00', '203.0.113.5', 1, 443, 'TCP', 'allowed');
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:00:01', '203.0.113.5', 99, 443, 'TCP', 'allowed');
ROLLBACK;

SELECT COUNT(*) AS logs_after FROM network_log;
