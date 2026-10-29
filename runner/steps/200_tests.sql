-- two helpers; SQL SECURITY INVOKER so a test never runs with more rights than its caller
DELIMITER //
CREATE PROCEDURE sp_check(IN p_id VARCHAR(5), IN p_what VARCHAR(80),
                          IN p_expected VARCHAR(40), IN p_actual VARCHAR(40))
SQL SECURITY INVOKER
BEGIN
  SET @tests_pass = COALESCE(@tests_pass, 0) + (p_expected <=> p_actual);
  SET @tests_fail = COALESCE(@tests_fail, 0) + (NOT (p_expected <=> p_actual));
  SELECT p_id AS test, p_what AS checks, p_expected AS expected, p_actual AS actual,
         IF(p_expected <=> p_actual, 'PASS', 'FAIL') AS result;
END //

-- runs p_sql and compares the error number it raises (0 = no error) with p_errno
CREATE PROCEDURE sp_expect_error(IN p_id VARCHAR(5), IN p_what VARCHAR(80),
                                 IN p_sql TEXT, IN p_errno INT)
SQL SECURITY INVOKER
BEGIN
  DECLARE v_errno INT DEFAULT 0;
  BEGIN
    -- SQLWARNING too: strict mode raises some errors (e.g. 1265) with a warning-class SQLSTATE
    DECLARE EXIT HANDLER FOR SQLEXCEPTION, SQLWARNING
      GET DIAGNOSTICS CONDITION 1 v_errno = MYSQL_ERRNO;
    SET @sx_sql = p_sql;
    PREPARE sx_st FROM @sx_sql;
    EXECUTE sx_st;
  END;
  CALL sp_check(p_id, p_what, p_errno, v_errno);
END //
DELIMITER ;

GRANT EXECUTE ON PROCEDURE sentinelx.sp_check        TO 'sx_analyst', 'sx_viewer';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_expect_error TO 'sx_analyst', 'sx_viewer';

SET @tests_pass = 0, @tests_fail = 0;

CALL sp_check('T01', '16 tables plus incident_audit', '17',
  (SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'sentinelx' AND table_type = 'BASE TABLE'));
CALL sp_check('T02', 'network_log is fully loaded', '50021', (SELECT COUNT(*) FROM network_log));

CALL sp_expect_error('T03', 'CHECK rejects criticality 9',
  "INSERT INTO asset (hostname, ip_address, asset_type, criticality) VALUES ('t-03', '10.9.9.9', 'web', 9)", 3819);
CALL sp_expect_error('T04', 'UNIQUE rejects a second web-01',
  "INSERT INTO asset (hostname, ip_address, asset_type, criticality) VALUES ('web-01', '10.9.9.8', 'web', 3)", 1062);
CALL sp_expect_error('T05', 'FK rejects an unknown attack type',
  "INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked) VALUES (NOW(), '192.0.2.1', 'US', 1, 999, 5, 1)", 1452);
CALL sp_expect_error('T06', 'FK blocks deleting an attacked asset',
  "DELETE FROM asset WHERE asset_id = 1", 1451);
CALL sp_expect_error('T07', 'CHECK: CLOSED needs closed_at',
  "UPDATE incident SET status = 'CLOSED' WHERE incident_id = 6", 3819);
CALL sp_expect_error('T08', 'ENUM rejects priority URGENT (strict mode)',
  "UPDATE incident SET priority = 'URGENT' WHERE incident_id = 6", 1265);

START TRANSACTION;
DELETE FROM incident WHERE incident_id = 2;
CALL sp_check('T09', 'ON DELETE CASCADE clears incident_event', '0',
  (SELECT COUNT(*) FROM incident_event WHERE incident_id = 2));
ROLLBACK;

CALL sp_expect_error('T10', 'aggregated view is not updatable',
  "UPDATE v_asset_risk SET criticality = 5 WHERE asset_id = 2", 1288);

START TRANSACTION;
SET @n = (SELECT COUNT(*) FROM incident);
INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES ('2026-11-01 10:00:00', '192.0.2.10', 'US', 4, 1, 9, 0);
CALL sp_check('T11', 'severity 9 attack opens an incident', @n + 1, (SELECT COUNT(*) FROM incident));
INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES ('2026-11-01 10:10:00', '192.0.2.10', 'US', 4, 1, 8, 0);
CALL sp_check('T12', 'repeat within 1 hour joins that incident', @n + 1, (SELECT COUNT(*) FROM incident));
ROLLBACK;

CALL sp_check('T13', 'retro-hunt found 8 old logs for 198.51.100.77', '8',
  (SELECT logs_matched FROM v_retro_hunt_summary
    WHERE ioc_version_id = (SELECT MIN(ioc_version_id) FROM ioc WHERE ioc_value = '198.51.100.77')));
CALL sp_expect_error('T14', 'overlapping IOC version is rejected',
  "INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from) VALUES ('ip', '198.51.100.77', '2026-10-01', '2026-10-28 11:00:00')", 1644);
CALL sp_expect_error('T15', 'IOC history is append-only',
  "DELETE FROM ioc WHERE ioc_value = '198.51.100.77'", 1644);

START TRANSACTION;
UPDATE ioc SET recorded_to = NOW() WHERE ioc_value = '198.51.100.77' AND recorded_to IS NULL;
CALL sp_expect_error('T28', 'a closed IOC version can be replaced by a new one',
  "INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from) VALUES ('ip', '198.51.100.77', '2026-09-10', NOW())", 0);
ROLLBACK;
CALL sp_check('T16', 'fn_severity_label(9.8), (6.5)', 'CRITICAL/MEDIUM',
  CONCAT(fn_severity_label(9.8), '/', fn_severity_label(6.5)));
CALL sp_expect_error('T17', 'cannot assign a closed incident',
  "CALL sp_assign_incident(1, 4)", 1644);
CALL sp_expect_error('T18', 'cannot assign an incident to a viewer',
  "CALL sp_assign_incident(6, 5)", 1644);
CALL sp_expect_error('T19', 'bad log batch raises the FK error',
  "CALL sp_load_log_batch(99)", 1452);
CALL sp_check('T20', '... and leaves none of its rows behind', '0',
  (SELECT COUNT(*) FROM network_log WHERE src_ip = '203.0.113.7'));
CALL sp_check('T21', 'savepoint kept the IOC, undid the priority change', '1/CRITICAL',
  CONCAT((SELECT COUNT(*) FROM ioc WHERE ioc_value = 'kestrel-drop.example'), '/',
         (SELECT priority FROM incident WHERE incident_id = 3)));
CALL sp_check('T22', 'NOT IN over a NULL returns nothing', '0',
  (SELECT COUNT(*) FROM threat_actor WHERE actor_id NOT IN (SELECT actor_id FROM malware)));
CALL sp_check('T23', "audit trail names rahul for his claim of incident 8", 'rahul.mehta',
  (SELECT SUBSTRING_INDEX(changed_by, '@', 1) FROM incident_audit
    WHERE incident_id = 8 AND new_assigned_to = 2));
CALL sp_expect_error('T24', 'audit trail is append-only (DELETE)',
  "DELETE FROM incident_audit WHERE audit_id = 1", 1644);
CALL sp_expect_error('T25', 'audit trail is append-only (UPDATE)',
  "UPDATE incident_audit SET changed_by = 'nobody' WHERE audit_id = 1", 1644);
CALL sp_check('T26', 'injectable procedure was removed', '0',
  (SELECT COUNT(*) FROM information_schema.routines
    WHERE routine_schema = 'sentinelx' AND routine_name = 'sp_search_incidents_unsafe'));
CALL sp_check('T27', 'admin role has no CREATE/ALTER/DROP/TRIGGER', '0',
  (SELECT COUNT(*) FROM information_schema.schema_privileges
    WHERE grantee = "'sx_admin'@'%'" AND privilege_type IN ('CREATE', 'ALTER', 'DROP', 'TRIGGER')));

SELECT @tests_pass AS passed, @tests_fail AS failed;
