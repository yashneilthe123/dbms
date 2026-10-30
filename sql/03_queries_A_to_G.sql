-- SentinelX Review 2: Basic, aggregate, join, subquery, set, function and window queries
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- A1 ----
SELECT hostname, ip_address, asset_type, criticality
FROM asset
WHERE criticality >= 4
ORDER BY criticality DESC, hostname;


-- ---- A2 ----
SELECT DISTINCT src_country
FROM attack_event
ORDER BY src_country;


-- ---- A3 ----
SELECT event_id, event_time, src_ip, severity
FROM attack_event
WHERE event_time BETWEEN '2026-10-10 00:00:00' AND '2026-10-14 23:59:59'
ORDER BY event_time;


-- ---- A4 ----
SELECT hostname, asset_type, criticality
FROM asset
WHERE asset_type IN ('web', 'db', 'vpn')
ORDER BY asset_type, hostname;


-- ---- A5 ----
SELECT cve_id, cvss, published
FROM vulnerability
WHERE cve_id LIKE 'CVE-2023-%'
ORDER BY cvss DESC;


-- ---- A6 ----
SELECT incident_id, title, priority, status
FROM incident
WHERE assigned_to IS NULL;


-- ---- A7 ----
SELECT event_id, event_time, src_ip, severity
FROM attack_event
WHERE triage_priority IS NULL
ORDER BY event_id;


-- ---- B1 ----
SELECT t.type_name, COUNT(*) AS attacks
FROM attack_event e
JOIN attack_type t ON t.type_id = e.type_id
GROUP BY t.type_name
ORDER BY attacks DESC, t.type_name;


-- ---- B2 ----
SELECT a.hostname,
       COUNT(*)                   AS attacks,
       SUM(e.blocked)             AS blocked,
       ROUND(AVG(e.severity), 2)  AS avg_severity
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
GROUP BY a.hostname
ORDER BY attacks DESC, a.hostname;


-- ---- B3 ----
SELECT src_country,
       MIN(event_time) AS first_seen,
       MAX(event_time) AS last_seen,
       MAX(severity)   AS worst_severity
FROM attack_event
GROUP BY src_country
ORDER BY first_seen;


-- ---- B4 ----
SELECT src_ip, COUNT(*) AS attacks
FROM attack_event
GROUP BY src_ip
HAVING COUNT(*) > 3
ORDER BY attacks DESC, src_ip;


-- ---- B5 ----
SELECT a.hostname, COUNT(*) AS serious_attacks
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
WHERE e.severity >= 7          -- WHERE filters single rows before grouping
GROUP BY a.hostname
HAVING COUNT(*) >= 2           -- HAVING filters whole groups after grouping
ORDER BY serious_attacks DESC, a.hostname;


-- ---- B6 ----
SELECT YEAR(published)       AS year_published,
       COUNT(*)              AS cves,
       ROUND(AVG(cvss), 2)   AS avg_cvss,
       MIN(cvss)             AS min_cvss,
       MAX(cvss)             AS max_cvss
FROM vulnerability
GROUP BY YEAR(published)
ORDER BY year_published;


-- ---- C1 ----
SELECT e.event_id, e.event_time, a.hostname, t.type_name, e.severity
FROM attack_event e
INNER JOIN asset a       ON a.asset_id = e.asset_id
INNER JOIN attack_type t ON t.type_id  = e.type_id
WHERE e.severity >= 9
ORDER BY e.event_time;


-- ---- C2 ----
SELECT a.hostname, COUNT(e.event_id) AS attacks
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY attacks, a.hostname;


-- ---- C3 ----
SELECT an.full_name, an.role, i.incident_id, i.status
FROM incident i
RIGHT JOIN analyst an ON an.analyst_id = i.assigned_to
ORDER BY an.analyst_id, i.incident_id;


-- ---- C4 ----
SELECT t.actor_name, m.malware_name
FROM threat_actor t LEFT JOIN malware m ON m.actor_id = t.actor_id
UNION
SELECT t.actor_name, m.malware_name
FROM threat_actor t RIGHT JOIN malware m ON m.actor_id = t.actor_id
ORDER BY actor_name, malware_name;


-- ---- C5 ----
SELECT t.actor_name, m1.malware_name AS malware_1, m2.malware_name AS malware_2
FROM malware m1
JOIN malware m2     ON m2.actor_id = m1.actor_id
                   AND m2.malware_id > m1.malware_id
JOIN threat_actor t ON t.actor_id = m1.actor_id
ORDER BY t.actor_name, malware_1;


-- ---- C6 ----
SELECT a.hostname, t.type_name,
       (SELECT COUNT(*) FROM attack_event e
         WHERE e.asset_id = a.asset_id AND e.type_id = t.type_id) AS times_seen
FROM asset a
CROSS JOIN attack_type t
WHERE a.criticality = 5 AND t.base_severity >= 8
ORDER BY a.hostname, t.type_name;


-- ---- D1 ----
SELECT cve_id, cvss,
       (SELECT ROUND(AVG(cvss), 2) FROM vulnerability) AS avg_cvss
FROM vulnerability
WHERE cvss > (SELECT AVG(cvss) FROM vulnerability)
ORDER BY cvss DESC, cve_id;


-- ---- D2 ----
SELECT full_name, email
FROM analyst
WHERE analyst_id = (SELECT assigned_to
                    FROM incident
                    WHERE assigned_to IS NOT NULL
                    ORDER BY opened_at DESC
                    LIMIT 1);


-- ---- D3 ----
SELECT hostname, asset_type
FROM asset
WHERE asset_id IN (SELECT e.asset_id
                   FROM attack_event e
                   JOIN attack_type t ON t.type_id = e.type_id
                   WHERE t.type_name = 'Ransomware')
ORDER BY hostname;


-- ---- D4 ----
SELECT cve_id, cvss
FROM vulnerability
WHERE cvss > ALL (SELECT v.cvss
                  FROM asset_vulnerability av
                  JOIN vulnerability v ON v.cve_id = av.cve_id
                  WHERE av.asset_id IN (2, 4))
ORDER BY cve_id;


-- ---- D5 ----
SELECT cve_id, cvss
FROM vulnerability
WHERE cvss > ANY (SELECT v.cvss
                  FROM attack_event e
                  JOIN vulnerability v ON v.cve_id = e.cve_id
                  WHERE e.src_country = 'RU')
ORDER BY cvss DESC, cve_id;


-- ---- D6 ----
SELECT a.hostname, e.event_id, e.severity
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
WHERE e.severity = (SELECT MAX(e2.severity)
                    FROM attack_event e2
                    WHERE e2.asset_id = e.asset_id)
ORDER BY a.hostname, e.event_id;


-- ---- D7 ----
SELECT t.actor_name, t.motive
FROM threat_actor t
WHERE EXISTS (SELECT 1 FROM attack_event e
              WHERE e.actor_id = t.actor_id AND e.blocked = 0)
ORDER BY t.actor_name;


-- ---- D8 ----
SELECT hostname, asset_type, criticality
FROM asset a
WHERE NOT EXISTS (SELECT 1 FROM attack_event e
                  WHERE e.asset_id = a.asset_id);


-- ---- D9 ----
SELECT actor_name FROM threat_actor
WHERE actor_id NOT IN (SELECT actor_id FROM malware);

SELECT actor_name FROM threat_actor
WHERE actor_id NOT IN (SELECT actor_id FROM malware WHERE actor_id IS NOT NULL);


-- ---- E1 ----
SELECT src_country AS country FROM attack_event
UNION
SELECT origin_country FROM threat_actor WHERE origin_country IS NOT NULL
ORDER BY country;


-- ---- E2 ----
SELECT event_time AS seen_at, 'attack' AS source, asset_id, severity AS detail
FROM attack_event WHERE src_ip = '198.51.100.45'
UNION ALL
SELECT log_time, 'log', dst_asset_id, dst_port
FROM network_log WHERE src_ip = '198.51.100.45'
ORDER BY seen_at;


-- ---- E3 ----
SELECT src_ip FROM attack_event
INTERSECT
SELECT ioc_value FROM ioc WHERE ioc_type = 'ip'
ORDER BY src_ip;


-- ---- E4 ----
SELECT src_ip FROM attack_event
EXCEPT
SELECT ioc_value FROM ioc WHERE ioc_type = 'ip'
ORDER BY src_ip;


-- ---- F1 ----
SELECT cve_id, cvss,
       CASE WHEN cvss >= 9 THEN 'CRITICAL'
            WHEN cvss >= 7 THEN 'HIGH'
            WHEN cvss >= 4 THEN 'MEDIUM'
            ELSE 'LOW' END AS severity
FROM vulnerability
ORDER BY cvss DESC, cve_id;


-- ---- F2 ----
SELECT e.event_id, e.src_ip,
       COALESCE(t.actor_name, 'Unattributed') AS actor,
       COALESCE(m.malware_name, '-')          AS malware
FROM attack_event e
LEFT JOIN threat_actor t ON t.actor_id   = e.actor_id
LEFT JOIN malware m      ON m.malware_id = e.malware_id
WHERE e.event_time >= '2026-10-20'
ORDER BY e.event_id;


-- ---- F3 ----
SELECT a.hostname,
       COUNT(e.event_id) AS attacks,
       ROUND(100 * SUM(e.blocked) / NULLIF(COUNT(e.event_id), 0), 1) AS blocked_pct
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY blocked_pct DESC, a.hostname;


-- ---- F4 ----
SELECT incident_id,
       DATE_FORMAT(opened_at, '%d %b %Y %H:%i') AS opened,
       DAYNAME(opened_at) AS opened_on,
       TIMESTAMPDIFF(HOUR, opened_at, COALESCE(closed_at, '2026-10-28 12:00:00')) AS hours_open,
       DATEDIFF('2026-10-28', DATE(opened_at)) AS age_days
FROM incident
ORDER BY incident_id;


-- ---- F5 ----
SELECT LPAD(analyst_id, 4, '0')                    AS staff_no,
       UPPER(full_name)                             AS name_upper,
       CONCAT(LEFT(full_name, 1), '. ',
              SUBSTRING_INDEX(full_name, ' ', -1))  AS short_name,
       SUBSTRING_INDEX(email, '@', 1)               AS username,
       LENGTH(email)                                AS email_length
FROM analyst
ORDER BY analyst_id;


-- ---- F6 ----
SELECT cve_id, cvss,
       ROUND(cvss)                AS rounded,
       CEIL(cvss)                 AS ceiling,
       FLOOR(cvss)                AS floor_value,
       TRUNCATE(cvss * 10, 0)     AS pct_of_max,
       MOD(FLOOR(cvss * 10), 7)   AS bucket
FROM vulnerability
ORDER BY cvss DESC, cve_id;


-- ---- G1 ----
SELECT a.hostname,
       COUNT(e.event_id) AS attacks,
       RANK()       OVER (ORDER BY COUNT(e.event_id) DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY COUNT(e.event_id) DESC) AS dense_rnk,
       ROW_NUMBER() OVER (ORDER BY COUNT(e.event_id) DESC, a.hostname) AS row_no
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY row_no;


-- ---- G2 ----
SELECT DATE(event_time) AS day,
       COUNT(*) AS attacks,
       SUM(COUNT(*)) OVER (ORDER BY DATE(event_time)) AS running_total
FROM attack_event
WHERE event_time < '2026-10-11'
GROUP BY DATE(event_time)
ORDER BY day;


-- ---- G3 ----
SELECT src_ip, event_id, event_time,
       TIMESTAMPDIFF(MINUTE,
                     LAG(event_time) OVER w, event_time) AS mins_since_prev,
       LEAD(event_id) OVER w AS next_event
FROM attack_event
WHERE src_country = 'RU'
WINDOW w AS (PARTITION BY src_ip ORDER BY event_time)
ORDER BY src_ip, event_time;
