-- SentinelX Review 2: Roles, users, GRANT, REVOKE and least-privilege tests
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- sec_roles_users ----
CREATE ROLE 'sx_admin', 'sx_analyst', 'sx_viewer';

-- the admin works with the data but cannot change the schema: no CREATE, ALTER, DROP,
-- TRIGGER or GRANT OPTION, so no TRUNCATE (needs DROP) and no dropping the audit triggers.
-- Schema changes stay with root, the DBA. Writes are granted per data table, so the admin
-- can only read incident_audit: the audit triggers write it with their definer's rights.
GRANT SELECT, EXECUTE, SHOW VIEW ON sentinelx.* TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.asset                TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.vulnerability        TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.asset_vulnerability  TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.network_log          TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.attack_type          TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.mitigation           TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.threat_actor         TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.malware              TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.attack_event         TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.analyst              TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.incident             TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.incident_event       TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.ioc                  TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.event_ioc            TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.retro_hunt_run       TO 'sx_admin';
GRANT INSERT, UPDATE, DELETE ON sentinelx.retro_hit            TO 'sx_admin';

-- analysts reach data only through views and procedures: no base table at all
GRANT SELECT ON sentinelx.v_attack_details     TO 'sx_analyst';
GRANT SELECT ON sentinelx.v_asset_risk         TO 'sx_analyst';
GRANT SELECT ON sentinelx.v_vulnerability      TO 'sx_analyst';
GRANT SELECT ON sentinelx.v_retro_hunt_summary TO 'sx_analyst';
GRANT SELECT ON sentinelx.v_ioc                TO 'sx_analyst';
GRANT SELECT, UPDATE ON sentinelx.v_my_incidents TO 'sx_analyst';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_assign_incident TO 'sx_analyst';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_attack_report   TO 'sx_analyst';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_report_ioc      TO 'sx_analyst';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_whoami          TO 'sx_analyst';

GRANT SELECT ON sentinelx.v_asset_risk        TO 'sx_viewer';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_attack_report TO 'sx_viewer';

-- 3 wrong passwords lock the account for 1 day (MySQL 8.0.19+)
CREATE USER 'ananya.rao'@'localhost'  IDENTIFIED BY 'Sx#Admin2026'   DEFAULT ROLE 'sx_admin'
  FAILED_LOGIN_ATTEMPTS 3 PASSWORD_LOCK_TIME 1;
CREATE USER 'rahul.mehta'@'localhost' IDENTIFIED BY 'Sx#Analyst2026' DEFAULT ROLE 'sx_analyst'
  FAILED_LOGIN_ATTEMPTS 3 PASSWORD_LOCK_TIME 1;
CREATE USER 'divya.iyer'@'localhost'  IDENTIFIED BY 'Sx#Viewer2026'  DEFAULT ROLE 'sx_viewer'
  FAILED_LOGIN_ATTEMPTS 3 PASSWORD_LOCK_TIME 1;

SELECT user, host, default_role_user AS default_role
FROM mysql.default_roles
WHERE user IN ('ananya.rao', 'rahul.mehta', 'divya.iyer')
ORDER BY user;


-- ---- sec_show_grants ----
SHOW GRANTS FOR 'sx_admin';
SHOW GRANTS FOR 'sx_analyst';
SHOW GRANTS FOR 'sx_viewer';
-- a user's own grants show only the role; USING expands what the role gives
SHOW GRANTS FOR 'rahul.mehta'@'localhost';
SHOW GRANTS FOR 'rahul.mehta'@'localhost' USING 'sx_analyst';
SHOW GRANTS FOR 'divya.iyer'@'localhost' USING 'sx_viewer';


-- ---- sec_revoke_1_grant ----
GRANT SELECT ON sentinelx.network_log TO 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';


-- ---- sec_revoke_2__as_divya ----
-- run while logged in as the divya test user
-- a new divya session while the extra grant exists
SELECT COUNT(*) AS log_lines FROM network_log;


-- ---- sec_revoke_3_revoke ----
REVOKE SELECT ON sentinelx.network_log FROM 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';


-- ---- sec_revoke_4__as_divya ----
-- run while logged in as the divya test user
-- a new divya session after the REVOKE
SELECT COUNT(*) AS log_lines FROM network_log;


-- ---- sec_viewer__as_divya ----
-- run while logged in as the divya test user
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

SELECT hostname, criticality, attacks, not_blocked, open_vulns
FROM v_asset_risk
ORDER BY not_blocked DESC
LIMIT 3;

CALL sp_attack_report('2026-10-20', '2026-10-28');

SELECT * FROM attack_event LIMIT 1;
DELETE FROM attack_event WHERE event_id = 1;
UPDATE v_asset_risk SET criticality = 1 WHERE asset_id = 1;


-- ---- sec_analyst__as_rahul ----
-- run while logged in as the rahul test user
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


-- ---- sec_admin__as_ananya ----
-- run while logged in as the ananya test user
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;
SELECT COUNT(*) AS incidents FROM incident;

-- the audit trail shows who changed which incident, including rahul's changes
-- made through the view and through the DEFINER procedure
SELECT audit_id, incident_id, changed_by, old_status, new_status,
       old_assigned_to, new_assigned_to
FROM incident_audit
ORDER BY audit_id;

-- the admin cannot erase or forge it: no DELETE or INSERT on it, no TRUNCATE (needs DROP), no DROP TRIGGER
DELETE FROM incident_audit WHERE audit_id = 1;
INSERT INTO incident_audit (incident_id, action, changed_by) VALUES (7, 'UPDATE', 'rahul.mehta@localhost');
TRUNCATE TABLE incident_audit;
DROP TRIGGER trg_audit_no_delete;


-- ---- sec_sqli_setup ----
-- SQL injection demo. Both procedures let an analyst search HIS incidents by title.
-- The unsafe one pastes the text into the SQL; the safe one passes it as a parameter.
DELIMITER //
CREATE PROCEDURE sp_search_incidents_unsafe(IN p_text VARCHAR(100))
BEGIN
  DECLARE v_me INT;
  SELECT analyst_id INTO v_me FROM analyst
   WHERE email = CONCAT(SUBSTRING_INDEX(USER(), '@', 1), '@sentinelx.in');
  SET @sql = CONCAT('SELECT incident_id, title, priority, status, assigned_to FROM incident ',
                    'WHERE assigned_to = ', COALESCE(v_me, -1),
                    ' AND title LIKE ''%', p_text, '%''');
  PREPARE st FROM @sql;
  EXECUTE st;
  DEALLOCATE PREPARE st;
END //

CREATE PROCEDURE sp_search_incidents(IN p_text VARCHAR(100))
BEGIN
  -- @me is a session variable the caller could set, so clear it and insist on a real analyst
  SET @me = NULL;
  SELECT analyst_id INTO @me FROM analyst
   WHERE email = CONCAT(SUBSTRING_INDEX(USER(), '@', 1), '@sentinelx.in');
  IF @me IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Caller is not a registered analyst';
  END IF;
  SET @text = p_text;
  PREPARE st FROM 'SELECT incident_id, title, priority, status, assigned_to FROM incident
                   WHERE assigned_to = ? AND title LIKE CONCAT(''%'', ?, ''%'')';
  EXECUTE st USING @me, @text;
  DEALLOCATE PREPARE st;
END //
DELIMITER ;

GRANT EXECUTE ON PROCEDURE sentinelx.sp_search_incidents_unsafe TO 'sx_analyst';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_search_incidents        TO 'sx_analyst';


-- ---- sec_sqli__as_rahul ----
-- run while logged in as the rahul test user
-- normal use: rahul's own incidents with 'Brute' in the title
CALL sp_search_incidents_unsafe('Brute');

-- tautology: the WHERE clause becomes (... AND title LIKE '%%') OR 1=1, so every incident comes back,
-- read with root's rights although rahul has no SELECT on incident
CALL sp_search_incidents_unsafe('%'' OR 1=1 -- ');

-- UNION: rows from another table he cannot read
CALL sp_search_incidents_unsafe('%'' UNION SELECT analyst_id, full_name, email, role, NULL FROM analyst -- ');

-- stacked statements are refused: PREPARE takes one statement only
CALL sp_search_incidents_unsafe('x''; DROP TABLE asset; -- ');

-- the safe procedure treats the same text as data: it only matches titles containing it
CALL sp_search_incidents('Brute');
CALL sp_search_incidents('%'' OR 1=1 -- ');


-- ---- sec_sqli_cleanup ----
-- the vulnerable procedure is removed once demonstrated
DROP PROCEDURE sp_search_incidents_unsafe;
SELECT routine_name, security_type FROM information_schema.routines
WHERE routine_schema = 'sentinelx' AND routine_name LIKE 'sp_search%';
