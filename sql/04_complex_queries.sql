-- SentinelX Review 2: Complex business queries CQ-01 to CQ-11
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- CQ01 ----
SELECT t.actor_name, t.motive,
       COUNT(*)                   AS serious_attacks,
       COUNT(DISTINCT e.asset_id) AS assets_hit,
       MAX(e.severity)            AS worst
FROM attack_event e
JOIN threat_actor t ON t.actor_id = e.actor_id
JOIN asset a        ON a.asset_id = e.asset_id
WHERE e.severity >= 8 AND a.criticality >= 4
GROUP BY t.actor_id, t.actor_name, t.motive
ORDER BY serious_attacks DESC, t.actor_name;


-- ---- CQ02 ----
SELECT i.incident_id, i.priority, i.status,
       COALESCE(an.full_name, 'Unassigned')      AS owner,
       COUNT(*)                                  AS attacks,
       MAX(e.severity)                           AS worst,
       GROUP_CONCAT(DISTINCT a.hostname ORDER BY a.hostname) AS assets
FROM incident i
JOIN incident_event ie ON ie.incident_id = i.incident_id
JOIN attack_event e    ON e.event_id     = ie.event_id
JOIN asset a           ON a.asset_id     = e.asset_id
LEFT JOIN analyst an   ON an.analyst_id  = i.assigned_to
WHERE i.status <> 'CLOSED'
GROUP BY i.incident_id, i.priority, i.status, an.full_name
ORDER BY FIELD(i.priority, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'), i.incident_id;


-- ---- CQ03 ----
SELECT a.hostname, e.event_id, e.cve_id, v.cvss, av.detected_at,
       DATEDIFF('2026-10-28', av.detected_at) AS days_unpatched
FROM attack_event e
JOIN asset_vulnerability av ON av.asset_id = e.asset_id
                           AND av.cve_id   = e.cve_id
                           AND av.patched_at IS NULL
JOIN vulnerability v ON v.cve_id   = e.cve_id
JOIN asset a         ON a.asset_id = e.asset_id
ORDER BY v.cvss DESC, a.hostname;


-- ---- CQ04 ----
SELECT m.family,
       COUNT(*) AS attacks,
       GROUP_CONCAT(DISTINCT COALESCE(t.actor_name, 'Unknown')) AS used_by,
       ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM attack_event
                               WHERE malware_id IS NOT NULL), 1) AS pct_of_malware_attacks
FROM attack_event e
JOIN malware m           ON m.malware_id = e.malware_id
LEFT JOIN threat_actor t ON t.actor_id   = m.actor_id
GROUP BY m.family
ORDER BY attacks DESC, m.family;


-- ---- CQ05 ----
SELECT CASE WHEN i.recorded_from <= e.event_time THEN 'known at attack time'
            ELSE 'recognised later' END                 AS knowledge,
       COUNT(*)                                          AS matches,
       COUNT(DISTINCT e.event_id)                        AS attacks,
       ROUND(AVG(CASE WHEN i.recorded_from > e.event_time
                      THEN TIMESTAMPDIFF(HOUR, e.event_time, i.recorded_from) / 24
                 END), 1)                                AS avg_days_late
FROM attack_event e
JOIN event_ioc ei ON ei.event_id      = e.event_id
JOIN ioc i        ON i.ioc_version_id = ei.ioc_version_id
GROUP BY knowledge
ORDER BY knowledge;


-- ---- CQ06 ----
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


-- ---- CQ07 ----
SELECT t.type_name, m.step_no, m.action
FROM mitigation m
JOIN attack_type t ON t.type_id = m.type_id
WHERE m.type_id = (SELECT e.type_id
                   FROM attack_event e
                   JOIN asset a ON a.asset_id = e.asset_id
                   WHERE a.hostname = 'web-01'
                   GROUP BY e.type_id
                   ORDER BY COUNT(*) DESC
                   LIMIT 1)
ORDER BY m.step_no;


-- ---- CQ08 ----
SELECT an.full_name,
       COUNT(i.incident_id)                          AS open_incidents,
       COALESCE(SUM(i.priority = 'CRITICAL'), 0)     AS critical,
       RANK() OVER (ORDER BY COUNT(i.incident_id) DESC) AS workload_rank
FROM analyst an
LEFT JOIN incident i ON i.assigned_to = an.analyst_id
                    AND i.status <> 'CLOSED'
WHERE an.role = 'analyst'
GROUP BY an.analyst_id, an.full_name
ORDER BY workload_rank, an.full_name;


-- ---- CQ09 ----
SELECT c.src_country, c.attacks,
       ROUND(100 * c.attacks / SUM(c.attacks) OVER (), 1) AS pct,
       (SELECT t.type_name
          FROM attack_event e2
          JOIN attack_type t ON t.type_id = e2.type_id
         WHERE e2.src_country = c.src_country
         GROUP BY t.type_name
         ORDER BY COUNT(*) DESC, t.type_name
         LIMIT 1) AS top_type
FROM (SELECT src_country, COUNT(*) AS attacks
      FROM attack_event
      GROUP BY src_country) AS c
ORDER BY c.attacks DESC, c.src_country;


-- ---- CQ10 ----
SELECT DISTINCT a.hostname, av.cve_id, v.cvss, t.actor_name
FROM asset_vulnerability av
JOIN vulnerability v  ON v.cve_id   = av.cve_id
JOIN asset a          ON a.asset_id = av.asset_id
JOIN attack_event e   ON e.asset_id = av.asset_id
JOIN threat_actor t   ON t.actor_id = e.actor_id
WHERE av.patched_at IS NULL
  AND v.cvss >= 9
  AND t.motive = 'espionage'
ORDER BY v.cvss DESC, a.hostname;


-- ---- CQ11 ----
SELECT src_ip, prev_event, event_id, gap_minutes, hostname
FROM (SELECT e.src_ip, e.event_id, a.hostname,
             LAG(e.event_id) OVER w AS prev_event,
             TIMESTAMPDIFF(MINUTE, LAG(e.event_time) OVER w, e.event_time) AS gap_minutes
      FROM attack_event e
      JOIN asset a ON a.asset_id = e.asset_id
      WINDOW w AS (PARTITION BY e.src_ip ORDER BY e.event_time)) AS x
WHERE gap_minutes <= 60
ORDER BY gap_minutes, src_ip;
