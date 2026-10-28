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
