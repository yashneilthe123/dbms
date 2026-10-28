-- SentinelX Review 2: Roles, users, GRANT, REVOKE and least-privilege tests
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- sec_roles_users ----
CREATE ROLE 'sx_admin', 'sx_analyst', 'sx_viewer';

GRANT ALL PRIVILEGES ON sentinelx.* TO 'sx_admin';

GRANT SELECT ON sentinelx.asset               TO 'sx_analyst';
GRANT SELECT ON sentinelx.vulnerability       TO 'sx_analyst';
GRANT SELECT ON sentinelx.asset_vulnerability TO 'sx_analyst';
GRANT SELECT ON sentinelx.attack_type         TO 'sx_analyst';
GRANT SELECT ON sentinelx.mitigation          TO 'sx_analyst';
GRANT SELECT ON sentinelx.threat_actor        TO 'sx_analyst';
GRANT SELECT ON sentinelx.malware             TO 'sx_analyst';
GRANT SELECT ON sentinelx.attack_event        TO 'sx_analyst';
GRANT SELECT ON sentinelx.event_ioc           TO 'sx_analyst';
GRANT SELECT, INSERT ON sentinelx.ioc         TO 'sx_analyst';
GRANT SELECT, UPDATE ON sentinelx.v_my_incidents TO 'sx_analyst';
GRANT SELECT ON sentinelx.v_attack_details    TO 'sx_analyst';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_assign_incident TO 'sx_analyst';

GRANT SELECT ON sentinelx.v_asset_risk        TO 'sx_viewer';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_attack_report TO 'sx_viewer';

CREATE USER 'ananya.rao'@'localhost'  IDENTIFIED BY 'Sx#Admin2026'   DEFAULT ROLE 'sx_admin';
CREATE USER 'rahul.mehta'@'localhost' IDENTIFIED BY 'Sx#Analyst2026' DEFAULT ROLE 'sx_analyst';
CREATE USER 'divya.iyer'@'localhost'  IDENTIFIED BY 'Sx#Viewer2026'  DEFAULT ROLE 'sx_viewer';

SELECT user, host, default_role_user AS default_role
FROM mysql.default_roles
WHERE user IN ('ananya.rao', 'rahul.mehta', 'divya.iyer')
ORDER BY user;


-- ---- sec_show_grants ----
SHOW GRANTS FOR 'sx_viewer';
SHOW GRANTS FOR 'sx_analyst';
SHOW GRANTS FOR 'divya.iyer'@'localhost' USING 'sx_viewer';


-- ---- sec_revoke ----
GRANT SELECT ON sentinelx.network_log TO 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';

REVOKE SELECT ON sentinelx.network_log FROM 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';


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
DROP TABLE asset;


-- ---- sec_admin__as_ananya ----
-- run while logged in as the ananya test user
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;
SELECT COUNT(*) AS incidents FROM incident;
