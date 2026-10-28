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
