-- SentinelX Review 2: Views
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- view_attack_details ----
CREATE VIEW v_attack_details AS
SELECT e.event_id, e.event_time, e.src_ip, e.src_country,
       a.hostname, t.type_name,
       ta.actor_name, m.malware_name, e.cve_id,
       e.severity, e.blocked
FROM attack_event e
JOIN asset a             ON a.asset_id   = e.asset_id
JOIN attack_type t       ON t.type_id    = e.type_id
LEFT JOIN threat_actor ta ON ta.actor_id  = e.actor_id
LEFT JOIN malware m       ON m.malware_id = e.malware_id;

SELECT event_id, event_time, src_ip, type_name, actor_name, severity
FROM v_attack_details
WHERE hostname = 'web-01'
ORDER BY event_time;

DELETE FROM v_attack_details WHERE event_id = 3;


-- ---- view_asset_risk ----
CREATE VIEW v_asset_risk AS
SELECT a.asset_id, a.hostname, a.criticality,
       COUNT(e.event_id)               AS attacks,
       COALESCE(SUM(e.blocked = 0), 0) AS not_blocked,
       MAX(e.severity)                 AS worst_severity,
       (SELECT COUNT(*) FROM asset_vulnerability av
         WHERE av.asset_id = a.asset_id AND av.patched_at IS NULL) AS open_vulns
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.asset_id, a.hostname, a.criticality;

SELECT hostname, criticality, attacks, not_blocked, worst_severity, open_vulns
FROM v_asset_risk
ORDER BY not_blocked DESC, criticality DESC
LIMIT 5;

UPDATE v_asset_risk SET criticality = 5 WHERE asset_id = 2;


-- ---- view_my_incidents ----
CREATE VIEW v_my_incidents AS
SELECT incident_id, title, priority, status, assigned_to, opened_at, closed_at
FROM incident
WHERE assigned_to = (SELECT analyst_id FROM analyst
                     WHERE email = CONCAT(SUBSTRING_INDEX(USER(), '@', 1), '@sentinelx.in'))
WITH CHECK OPTION;

SELECT USER() AS logged_in_as, COUNT(*) AS rows_visible FROM v_my_incidents;

SELECT table_name, is_updatable
FROM information_schema.views
WHERE table_schema = 'sentinelx'
ORDER BY table_name;


-- ---- view_review1_views ----
CREATE VIEW v_vulnerability AS
SELECT cve_id, cvss, published,
       CASE WHEN cvss >= 9 THEN 'CRITICAL'
            WHEN cvss >= 7 THEN 'HIGH'
            WHEN cvss >= 4 THEN 'MEDIUM'
            ELSE 'LOW' END AS severity
FROM vulnerability;

CREATE VIEW v_retro_hunt_summary AS
SELECT r.run_id, r.ioc_version_id, r.started_at, r.incident_id,
       COUNT(h.log_id)                AS logs_matched,
       COUNT(DISTINCT l.dst_asset_id) AS assets_touched
FROM retro_hunt_run r
LEFT JOIN retro_hit   h ON h.run_id = r.run_id
LEFT JOIN network_log l ON l.log_id = h.log_id
GROUP BY r.run_id, r.ioc_version_id, r.started_at, r.incident_id;

SELECT * FROM v_retro_hunt_summary;


-- ---- view_ioc ----
-- the indicator versions we currently believe (not yet superseded); analysts read IOCs only through this
CREATE VIEW v_ioc AS
SELECT ioc_version_id, ioc_type, ioc_value, actor_id, malware_id,
       valid_from, valid_to, recorded_from
FROM ioc
WHERE recorded_to IS NULL;

SELECT ioc_type, COUNT(*) AS indicators FROM v_ioc GROUP BY ioc_type ORDER BY ioc_type;

-- updatable or not, for every view in the schema
SELECT table_name AS view_name, is_updatable
FROM information_schema.views WHERE table_schema = 'sentinelx' ORDER BY table_name;
