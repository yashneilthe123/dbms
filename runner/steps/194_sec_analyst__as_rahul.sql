SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

SELECT incident_id, title, priority, status FROM v_my_incidents;

UPDATE v_my_incidents SET status = 'CONTAINED' WHERE incident_id = 7;
SELECT incident_id, status FROM v_my_incidents WHERE incident_id = 7;

UPDATE v_my_incidents SET assigned_to = 3 WHERE incident_id = 7;
SELECT * FROM incident LIMIT 1;
SELECT * FROM attack_event LIMIT 1;
DROP TABLE asset;

-- the procedure runs as root, so it must check the caller itself
CALL sp_whoami();
CALL sp_assign_incident(7, 3);
CALL sp_assign_incident(6, 2);
CALL sp_assign_incident(8, 2);

-- no direct writes to ioc; a compromised internal host is reported through the procedure,
-- and the retro-hunt trigger searches its past traffic
INSERT INTO ioc (ioc_type, ioc_value, valid_from) VALUES ('ip', '172.16.7.8', '2026-10-01');
CALL sp_report_ioc('ip', '172.16.7.8', '2026-10-01', NULL, NULL);
SELECT ioc_version_id, logs_matched, assets_touched, incident_id
FROM v_retro_hunt_summary
WHERE ioc_version_id = (SELECT MAX(ioc_version_id) FROM v_ioc);
