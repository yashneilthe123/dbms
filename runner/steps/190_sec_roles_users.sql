CREATE ROLE 'sx_admin', 'sx_analyst', 'sx_viewer';

-- the admin works with the data but cannot change the schema: no CREATE, ALTER, DROP,
-- TRIGGER or GRANT OPTION, so no TRUNCATE (needs DROP) and no dropping the audit triggers.
-- Schema changes stay with root, the DBA.
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE, SHOW VIEW ON sentinelx.* TO 'sx_admin';

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
