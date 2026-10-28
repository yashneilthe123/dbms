SELECT r.run_id, i.ioc_value, r.started_at,
       COUNT(h.log_id)                AS logs_matched,
       COUNT(DISTINCT l.dst_asset_id) AS assets_touched,
       MIN(l.log_time)                AS first_contact,
       inc.status                     AS incident_status
FROM retro_hunt_run r
JOIN ioc i            ON i.ioc_version_id = r.ioc_version_id
LEFT JOIN retro_hit h ON h.run_id  = r.run_id
LEFT JOIN network_log l ON l.log_id = h.log_id
LEFT JOIN incident inc  ON inc.incident_id = r.incident_id
GROUP BY r.run_id, i.ioc_value, r.started_at, inc.status
ORDER BY r.run_id;
