-- SentinelX Review 3: Test cases (PASS/FAIL), run after 01 to 12
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- tests ----
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
CALL sp_check('T29', 'all three accounts lock after 3 failed logins', '3',
  (SELECT COUNT(*) FROM mysql.user WHERE user IN ('ananya.rao', 'rahul.mehta', 'divya.iyer')
     AND JSON_EXTRACT(user_attributes, '$.Password_locking.failed_login_attempts') = 3));
CALL sp_check('T30', 'escalation cursor raised incident 6 from MEDIUM to HIGH', '1',
  (SELECT COUNT(*) FROM incident_audit WHERE incident_id = 6 AND old_priority = 'MEDIUM'
     AND new_priority = 'HIGH' AND changed_by LIKE 'root@%'));
CALL sp_check('T31', 'fn_asset_risk matches its formula for every asset', '0',
  (SELECT COUNT(*) FROM asset a
    WHERE fn_asset_risk(a.asset_id) <> a.criticality * 10
          + 5 * (SELECT COUNT(*) FROM asset_vulnerability av WHERE av.asset_id = a.asset_id AND av.patched_at IS NULL)
          + 2 * (SELECT COUNT(*) FROM attack_event e WHERE e.asset_id = a.asset_id AND e.blocked = 0)));
CALL sp_expect_error('T32', 'an IOC version cannot be rewritten',
  "UPDATE ioc SET ioc_value = '198.51.100.99' WHERE ioc_version_id = 1", 1644);
START TRANSACTION;
UPDATE ioc SET recorded_to = SYSDATE() WHERE ioc_version_id = 12;
CALL sp_expect_error('T33', 'a closed IOC version cannot be reopened',
  "UPDATE ioc SET recorded_to = NULL WHERE ioc_version_id = 12", 1644);
ROLLBACK;
CALL sp_check('T34', 'admin has no write privilege on incident_audit', '0',
  (SELECT COUNT(*) FROM information_schema.table_privileges
    WHERE grantee = "'sx_admin'@'%'" AND table_name = 'incident_audit'));
SET @me = 2;  -- pretend to be rahul by setting the session variable the procedure uses
CALL sp_expect_error('T35', 'search procedure ignores a forged @me (root is no analyst)',
  "CALL sp_search_incidents('Brute')", 1644);

SELECT @tests_pass AS passed, @tests_fail AS failed;


-- ---- tests__as_rahul ----
-- run while logged in as the rahul test user
SET @tests_pass = 0, @tests_fail = 0;
CALL sp_expect_error('S01', 'analyst cannot read a base table',
  "DO (SELECT COUNT(*) FROM attack_event)", 1142);
CALL sp_expect_error('S02', 'analyst can read through the view',
  "DO (SELECT COUNT(*) FROM v_attack_details)", 0);
CALL sp_expect_error('S03', 'analyst cannot run DDL',
  "DROP TABLE asset", 1142);
CALL sp_check('S04', 'v_my_incidents shows only his own rows', '0',
  (SELECT COUNT(*) FROM v_my_incidents WHERE assigned_to <> 2));
CALL sp_expect_error('S05', 'WITH CHECK OPTION blocks handing an incident over',
  "UPDATE v_my_incidents SET assigned_to = 3 WHERE incident_id = 7", 1369);
CALL sp_expect_error('S06', 'procedure blocks giving his incident away',
  "CALL sp_assign_incident(7, 3)", 1644);
CALL sp_expect_error('S07', "procedure blocks taking a colleague's incident",
  "CALL sp_assign_incident(6, 2)", 1644);
CALL sp_expect_error('S08', 'procedure lets him claim an unassigned incident',
  "CALL sp_assign_incident(9, 2)", 0);
CALL sp_expect_error('S09', 'analyst cannot write the ioc table directly',
  "INSERT INTO ioc (ioc_type, ioc_value, valid_from) VALUES ('ip', '192.0.2.200', '2026-10-01')", 1142);
CALL sp_expect_error('S10', 'analyst reports an IOC through the procedure',
  "CALL sp_report_ioc('ip', '192.0.2.200', '2026-10-01', NULL, NULL)", 0);
CALL sp_expect_error('S11', 'analyst cannot read the audit trail',
  "DO (SELECT COUNT(*) FROM incident_audit)", 1142);
-- try to backdate an indicator by moving this session's clock
SET timestamp = UNIX_TIMESTAMP('2026-01-01 00:00:00');
CALL sp_report_ioc('ip', '192.0.2.201', '2026-10-01', NULL, NULL);
SET timestamp = DEFAULT;
CALL sp_check('S12', 'SET timestamp cannot backdate a reported IOC', '0',
  (SELECT COUNT(*) FROM v_ioc WHERE ioc_value = '192.0.2.201' AND recorded_from < '2026-02-01'));
SELECT @tests_pass AS passed, @tests_fail AS failed;


-- ---- tests__as_divya ----
-- run while logged in as the divya test user
SET @tests_pass = 0, @tests_fail = 0;
CALL sp_expect_error('V01', 'viewer can read the risk view',
  "DO (SELECT COUNT(*) FROM v_asset_risk)", 0);
CALL sp_expect_error('V02', 'viewer cannot read a base table',
  "DO (SELECT COUNT(*) FROM attack_event)", 1142);
CALL sp_expect_error('V03', 'viewer cannot delete',
  "DELETE FROM attack_event WHERE event_id = 1", 1142);
CALL sp_expect_error('V04', 'viewer cannot run the assign procedure',
  "CALL sp_assign_incident(9, 5)", 1370);
CALL sp_expect_error('V05', 'viewer cannot update the risk view',
  "UPDATE v_asset_risk SET criticality = 1 WHERE asset_id = 1", 1142);
SELECT @tests_pass AS passed, @tests_fail AS failed;


-- ---- tests__as_ananya ----
-- run while logged in as the ananya test user
SET @tests_pass = 0, @tests_fail = 0;
CALL sp_expect_error('A01', 'admin can change incident data',
  "UPDATE incident SET priority = 'HIGH' WHERE incident_id = 9", 0);
CALL sp_check('A02', '... and the audit trail names the admin', 'ananya.rao',
  (SELECT SUBSTRING_INDEX(changed_by, '@', 1) FROM incident_audit ORDER BY audit_id DESC LIMIT 1));
CALL sp_expect_error('A03', 'admin cannot delete audit rows',
  "DELETE FROM incident_audit WHERE audit_id = 1", 1142);
CALL sp_expect_error('A04', 'admin cannot TRUNCATE the audit trail',
  "TRUNCATE TABLE incident_audit", 1142);
CALL sp_expect_error('A05', 'admin cannot change the schema',
  "ALTER TABLE incident ADD COLUMN note VARCHAR(10)", 1142);
CALL sp_expect_error('A06', 'admin cannot forge an audit row',
  "INSERT INTO incident_audit (incident_id, action, changed_by) VALUES (7, 'UPDATE', 'rahul.mehta@localhost')", 1142);
CALL sp_expect_error('A07', 'admin cannot edit an audit row',
  "UPDATE incident_audit SET changed_by = 'nobody' WHERE audit_id = 1", 1142);
SELECT @tests_pass AS passed, @tests_fail AS failed;
