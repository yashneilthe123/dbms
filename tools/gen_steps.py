import os, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
from gen_seed import asset_insert, seed_rest, NOISE_SQL

OUT = os.path.join(HERE, '..', 'runner', 'steps')
STEPS = {}

def step(name, sql):
    STEPS[name] = sql.strip() + '\n'

# ---------------- reset ----------------
step('000_reset', """
DROP DATABASE IF EXISTS sentinelx;
DROP USER IF EXISTS 'ananya.rao'@'localhost', 'rahul.mehta'@'localhost', 'divya.iyer'@'localhost';
DROP ROLE IF EXISTS 'sx_admin', 'sx_analyst', 'sx_viewer';
CREATE DATABASE sentinelx;
""")
step('001_version', "SELECT VERSION() AS mysql_version, @@sql_mode AS sql_mode;")

# ---------------- DDL (one file per table, from the Review 1 script) ----------------
ddl = open(os.path.join(HERE, '..', 'sql', 'sentinelx_schema.sql')).read()
tables = re.findall(r'(CREATE TABLE (\w+) \(.*?\n\);)', ddl, re.S)
for i, (stmt, name) in enumerate(tables):
    step(f'{10 + i:03d}_ddl_{name}', stmt)
step('029_ddl_show_tables', "SHOW TABLES;")

# ---------------- DML ----------------
step('030_dml_insert_asset', asset_insert())
step('031_dml_seed_data', seed_rest())
step('032_dml_insert_noise_logs', NOISE_SQL)
step('033_dml_update', """
SELECT event_id, severity, predicted_severity FROM attack_event WHERE event_id IN (25, 26);
UPDATE attack_event
   SET predicted_severity = CASE WHEN severity >= 9 THEN 'CRITICAL'
                                 WHEN severity >= 7 THEN 'HIGH'
                                 WHEN severity >= 4 THEN 'MEDIUM'
                                 ELSE 'LOW' END
 WHERE event_id IN (25, 26);
SELECT event_id, severity, predicted_severity FROM attack_event WHERE event_id IN (25, 26);
""")
step('034_dml_delete', """
INSERT INTO asset (hostname, ip_address, asset_type, criticality) VALUES ('tmp-scan-01', '10.0.9.99', 'workstation', 1);
SELECT asset_id, hostname FROM asset WHERE hostname = 'tmp-scan-01';
DELETE FROM asset WHERE hostname = 'tmp-scan-01';
SELECT COUNT(*) AS assets_left FROM asset;
""")
step('035_dml_constraints', """
INSERT INTO asset (hostname, ip_address, asset_type, criticality) VALUES ('web-03', '10.0.1.12', 'web', 9);
INSERT INTO asset (hostname, ip_address, asset_type, criticality) VALUES ('web-01', '10.0.1.99', 'web', 3);
INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES ('2026-10-27 10:00:00', '203.0.113.5', 'US', 1, 99, 5, 1);
DELETE FROM asset WHERE asset_id = 1;
INSERT INTO incident (title, priority, status, closed_at) VALUES ('Test', 'LOW', 'OPEN', '2026-10-27 10:00:00');
""")
step('036_dml_row_counts', """
SELECT 'asset' AS table_name, COUNT(*) AS row_count FROM asset
UNION ALL SELECT 'vulnerability', COUNT(*) FROM vulnerability
UNION ALL SELECT 'asset_vulnerability', COUNT(*) FROM asset_vulnerability
UNION ALL SELECT 'network_log', COUNT(*) FROM network_log
UNION ALL SELECT 'attack_type', COUNT(*) FROM attack_type
UNION ALL SELECT 'mitigation', COUNT(*) FROM mitigation
UNION ALL SELECT 'threat_actor', COUNT(*) FROM threat_actor
UNION ALL SELECT 'malware', COUNT(*) FROM malware
UNION ALL SELECT 'attack_event', COUNT(*) FROM attack_event
UNION ALL SELECT 'analyst', COUNT(*) FROM analyst
UNION ALL SELECT 'incident', COUNT(*) FROM incident
UNION ALL SELECT 'incident_event', COUNT(*) FROM incident_event
UNION ALL SELECT 'ioc', COUNT(*) FROM ioc
UNION ALL SELECT 'event_ioc', COUNT(*) FROM event_ioc
UNION ALL SELECT 'retro_hunt_run', COUNT(*) FROM retro_hunt_run
UNION ALL SELECT 'retro_hit', COUNT(*) FROM retro_hit;
""")

# ---------------- A. Basic ----------------
Q = {}
Q['A1'] = ("Critical assets (criticality 4 or 5), most critical first",
"""SELECT hostname, ip_address, asset_type, criticality
FROM asset
WHERE criticality >= 4
ORDER BY criticality DESC, hostname;""")
Q['A2'] = ("Countries that attacks came from (DISTINCT)",
"""SELECT DISTINCT src_country
FROM attack_event
ORDER BY src_country;""")
Q['A3'] = ("Attacks between 10 and 14 October (BETWEEN)",
"""SELECT event_id, event_time, src_ip, severity
FROM attack_event
WHERE event_time BETWEEN '2026-10-10 00:00:00' AND '2026-10-14 23:59:59'
ORDER BY event_time;""")
Q['A4'] = ("Internet-facing servers: web, db and vpn assets (IN)",
"""SELECT hostname, asset_type, criticality
FROM asset
WHERE asset_type IN ('web', 'db', 'vpn')
ORDER BY asset_type, hostname;""")
Q['A5'] = ("CVEs published in 2023 (LIKE)",
"""SELECT cve_id, cvss, published
FROM vulnerability
WHERE cve_id LIKE 'CVE-2023-%'
ORDER BY cvss DESC;""")
Q['A6'] = ("Incidents nobody owns yet (IS NULL)",
"""SELECT incident_id, title, priority, status
FROM incident
WHERE assigned_to IS NULL;""")
Q['A7'] = ("Attacks the ML job has not scored yet (IS NULL)",
"""SELECT event_id, event_time, src_ip, severity
FROM attack_event
WHERE predicted_severity IS NULL
ORDER BY event_id;""")

# ---------------- B. Aggregate ----------------
Q['B1'] = ("Number of attacks per attack type (COUNT, GROUP BY)",
"""SELECT t.type_name, COUNT(*) AS attacks
FROM attack_event e
JOIN attack_type t ON t.type_id = e.type_id
GROUP BY t.type_name
ORDER BY attacks DESC, t.type_name;""")
Q['B2'] = ("Attacks, blocked attacks and average severity per asset (SUM, AVG)",
"""SELECT a.hostname,
       COUNT(*)                   AS attacks,
       SUM(e.blocked)             AS blocked,
       ROUND(AVG(e.severity), 2)  AS avg_severity
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
GROUP BY a.hostname
ORDER BY attacks DESC, a.hostname;""")
Q['B3'] = ("First and last attack and worst severity per source country (MIN, MAX)",
"""SELECT src_country,
       MIN(event_time) AS first_seen,
       MAX(event_time) AS last_seen,
       MAX(severity)   AS worst_severity
FROM attack_event
GROUP BY src_country
ORDER BY first_seen;""")
Q['B4'] = ("Source IPs with more than 3 attacks (HAVING)",
"""SELECT src_ip, COUNT(*) AS attacks
FROM attack_event
GROUP BY src_ip
HAVING COUNT(*) > 3
ORDER BY attacks DESC, src_ip;""")
Q['B5'] = ("WHERE vs HAVING: assets with 2 or more serious attacks",
"""SELECT a.hostname, COUNT(*) AS serious_attacks
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
WHERE e.severity >= 7          -- WHERE filters single rows before grouping
GROUP BY a.hostname
HAVING COUNT(*) >= 2           -- HAVING filters whole groups after grouping
ORDER BY serious_attacks DESC, a.hostname;""")
Q['B6'] = ("CVSS statistics by year of publication",
"""SELECT YEAR(published)       AS year_published,
       COUNT(*)              AS cves,
       ROUND(AVG(cvss), 2)   AS avg_cvss,
       MIN(cvss)             AS min_cvss,
       MAX(cvss)             AS max_cvss
FROM vulnerability
GROUP BY YEAR(published)
ORDER BY year_published;""")

# ---------------- C. Joins ----------------
Q['C1'] = ("INNER JOIN: attacks of severity 9 or more with asset and attack type",
"""SELECT e.event_id, e.event_time, a.hostname, t.type_name, e.severity
FROM attack_event e
INNER JOIN asset a       ON a.asset_id = e.asset_id
INNER JOIN attack_type t ON t.type_id  = e.type_id
WHERE e.severity >= 9
ORDER BY e.event_time;""")
Q['C2'] = ("LEFT JOIN: every asset with its number of attacks, including assets never attacked",
"""SELECT a.hostname, COUNT(e.event_id) AS attacks
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY attacks, a.hostname;""")
Q['C3'] = ("RIGHT JOIN: every analyst with the incidents they own, including analysts with none",
"""SELECT an.full_name, an.role, i.incident_id, i.status
FROM incident i
RIGHT JOIN analyst an ON an.analyst_id = i.assigned_to
ORDER BY an.analyst_id, i.incident_id;""")
Q['C4'] = ("FULL OUTER JOIN emulation: threat actors and malware, keeping both unmatched sides",
"""SELECT t.actor_name, m.malware_name
FROM threat_actor t LEFT JOIN malware m ON m.actor_id = t.actor_id
UNION
SELECT t.actor_name, m.malware_name
FROM threat_actor t RIGHT JOIN malware m ON m.actor_id = t.actor_id
ORDER BY actor_name, malware_name;""")
Q['C5'] = ("SELF JOIN: pairs of malware that the ML job put in the same cluster",
"""SELECT m1.cluster_id, m1.malware_name AS malware_1, m2.malware_name AS malware_2
FROM malware m1
JOIN malware m2 ON m2.cluster_id = m1.cluster_id
               AND m2.malware_id > m1.malware_id
ORDER BY m1.cluster_id, malware_1;""")
Q['C6'] = ("CROSS JOIN: hardening checklist of every criticality-5 asset against every severe attack type",
"""SELECT a.hostname, t.type_name,
       (SELECT COUNT(*) FROM attack_event e
         WHERE e.asset_id = a.asset_id AND e.type_id = t.type_id) AS times_seen
FROM asset a
CROSS JOIN attack_type t
WHERE a.criticality = 5 AND t.base_severity >= 8
ORDER BY a.hostname, t.type_name;""")

# ---------------- D. Subqueries ----------------
Q['D1'] = ("Scalar subquery: CVEs scoring above the average CVSS",
"""SELECT cve_id, cvss,
       (SELECT ROUND(AVG(cvss), 2) FROM vulnerability) AS avg_cvss
FROM vulnerability
WHERE cvss > (SELECT AVG(cvss) FROM vulnerability)
ORDER BY cvss DESC, cve_id;""")
Q['D2'] = ("Single-row subquery: the analyst who owns the most recently opened incident",
"""SELECT full_name, email
FROM analyst
WHERE analyst_id = (SELECT assigned_to
                    FROM incident
                    WHERE assigned_to IS NOT NULL
                    ORDER BY opened_at DESC
                    LIMIT 1);""")
Q['D3'] = ("Multi-row subquery with IN: assets that have been hit by ransomware",
"""SELECT hostname, asset_type
FROM asset
WHERE asset_id IN (SELECT e.asset_id
                   FROM attack_event e
                   JOIN attack_type t ON t.type_id = e.type_id
                   WHERE t.type_name = 'Ransomware')
ORDER BY hostname;""")
Q['D4'] = ("Multi-row subquery with ALL: CVEs scoring higher than every CVE on web-02 and mail-01",
"""SELECT cve_id, cvss
FROM vulnerability
WHERE cvss > ALL (SELECT v.cvss
                  FROM asset_vulnerability av
                  JOIN vulnerability v ON v.cve_id = av.cve_id
                  WHERE av.asset_id IN (2, 4))
ORDER BY cve_id;""")
Q['D5'] = ("Multi-row subquery with ANY: CVEs scoring higher than at least one CVE used by Russian sources",
"""SELECT cve_id, cvss
FROM vulnerability
WHERE cvss > ANY (SELECT v.cvss
                  FROM attack_event e
                  JOIN vulnerability v ON v.cve_id = e.cve_id
                  WHERE e.src_country = 'RU')
ORDER BY cvss DESC, cve_id;""")
Q['D6'] = ("Correlated subquery: the worst attack(s) on each asset",
"""SELECT a.hostname, e.event_id, e.severity
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
WHERE e.severity = (SELECT MAX(e2.severity)
                    FROM attack_event e2
                    WHERE e2.asset_id = e.asset_id)
ORDER BY a.hostname, e.event_id;""")
Q['D7'] = ("EXISTS: threat actors with at least one attack that was not blocked",
"""SELECT t.actor_name, t.motive
FROM threat_actor t
WHERE EXISTS (SELECT 1 FROM attack_event e
              WHERE e.actor_id = t.actor_id AND e.blocked = 0)
ORDER BY t.actor_name;""")
Q['D8'] = ("NOT EXISTS: assets that have never been attacked",
"""SELECT hostname, asset_type, criticality
FROM asset a
WHERE NOT EXISTS (SELECT 1 FROM attack_event e
                  WHERE e.asset_id = a.asset_id);""")
Q['D9'] = ("NOT IN and the NULL pitfall: threat actors with no malware",
"""SELECT actor_name FROM threat_actor
WHERE actor_id NOT IN (SELECT actor_id FROM malware);

SELECT actor_name FROM threat_actor
WHERE actor_id NOT IN (SELECT actor_id FROM malware WHERE actor_id IS NOT NULL);""")

# ---------------- E. Set operations ----------------
Q['E1'] = ("UNION: every country we know about, as an attack source or as an attacker's origin",
"""SELECT src_country AS country FROM attack_event
UNION
SELECT origin_country FROM threat_actor WHERE origin_country IS NOT NULL
ORDER BY country;""")
Q['E2'] = ("UNION ALL: full activity timeline of 198.51.100.45 across attacks and raw logs",
"""SELECT event_time AS seen_at, 'attack' AS source, asset_id, severity AS detail
FROM attack_event WHERE src_ip = '198.51.100.45'
UNION ALL
SELECT log_time, 'log', dst_asset_id, dst_port
FROM network_log WHERE src_ip = '198.51.100.45'
ORDER BY seen_at;""")
Q['E3'] = ("INTERSECT: attack sources that are also known bad IPs",
"""SELECT src_ip FROM attack_event
INTERSECT
SELECT ioc_value FROM ioc WHERE ioc_type = 'ip'
ORDER BY src_ip;""")
Q['E4'] = ("EXCEPT: attack sources that are not on the indicator list yet",
"""SELECT src_ip FROM attack_event
EXCEPT
SELECT ioc_value FROM ioc WHERE ioc_type = 'ip'
ORDER BY src_ip;""")

# ---------------- F. Advanced functions ----------------
Q['F1'] = ("CASE: severity label from CVSS score",
"""SELECT cve_id, cvss,
       CASE WHEN cvss >= 9 THEN 'CRITICAL'
            WHEN cvss >= 7 THEN 'HIGH'
            WHEN cvss >= 4 THEN 'MEDIUM'
            ELSE 'LOW' END AS severity
FROM vulnerability
ORDER BY cvss DESC, cve_id;""")
Q['F2'] = ("COALESCE: recent attacks with 'Unattributed' instead of a missing actor",
"""SELECT e.event_id, e.src_ip,
       COALESCE(t.actor_name, 'Unattributed') AS actor,
       COALESCE(m.malware_name, '-')          AS malware
FROM attack_event e
LEFT JOIN threat_actor t ON t.actor_id   = e.actor_id
LEFT JOIN malware m      ON m.malware_id = e.malware_id
WHERE e.event_time >= '2026-10-20'
ORDER BY e.event_id;""")
Q['F3'] = ("NULLIF: share of blocked attacks per asset without dividing by zero",
"""SELECT a.hostname,
       COUNT(e.event_id) AS attacks,
       ROUND(100 * SUM(e.blocked) / NULLIF(COUNT(e.event_id), 0), 1) AS blocked_pct
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY blocked_pct DESC, a.hostname;""")
Q['F4'] = ("Date and time functions: how long each incident has been or was open",
"""SELECT incident_id,
       DATE_FORMAT(opened_at, '%d %b %Y %H:%i') AS opened,
       DAYNAME(opened_at) AS opened_on,
       TIMESTAMPDIFF(HOUR, opened_at, COALESCE(closed_at, '2026-10-28 12:00:00')) AS hours_open,
       DATEDIFF('2026-10-28', DATE(opened_at)) AS age_days
FROM incident
ORDER BY incident_id;""")
Q['F5'] = ("String functions: analyst user names and short names",
"""SELECT LPAD(analyst_id, 4, '0')                    AS staff_no,
       UPPER(full_name)                             AS name_upper,
       CONCAT(LEFT(full_name, 1), '. ',
              SUBSTRING_INDEX(full_name, ' ', -1))  AS short_name,
       SUBSTRING_INDEX(email, '@', 1)               AS username,
       LENGTH(email)                                AS email_length
FROM analyst
ORDER BY analyst_id;""")
Q['F6'] = ("Numeric functions on CVSS scores",
"""SELECT cve_id, cvss,
       ROUND(cvss)                AS rounded,
       CEIL(cvss)                 AS ceiling,
       FLOOR(cvss)                AS floor_value,
       TRUNCATE(cvss * 10, 0)     AS pct_of_max,
       MOD(FLOOR(cvss * 10), 7)   AS bucket
FROM vulnerability
ORDER BY cvss DESC, cve_id;""")

# ---------------- G. Window ----------------
Q['G1'] = ("RANK, DENSE_RANK and ROW_NUMBER: assets ranked by number of attacks",
"""SELECT a.hostname,
       COUNT(e.event_id) AS attacks,
       RANK()       OVER (ORDER BY COUNT(e.event_id) DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY COUNT(e.event_id) DESC) AS dense_rnk,
       ROW_NUMBER() OVER (ORDER BY COUNT(e.event_id) DESC, a.hostname) AS row_no
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY row_no;""")
Q['G2'] = ("Running total of attacks per day for the first ten days of October",
"""SELECT DATE(event_time) AS day,
       COUNT(*) AS attacks,
       SUM(COUNT(*)) OVER (ORDER BY DATE(event_time)) AS running_total
FROM attack_event
WHERE event_time < '2026-10-11'
GROUP BY DATE(event_time)
ORDER BY day;""")
Q['G3'] = ("LAG and LEAD: minutes between attacks from the same Russian source IP",
"""SELECT src_ip, event_id, event_time,
       TIMESTAMPDIFF(MINUTE,
                     LAG(event_time) OVER w, event_time) AS mins_since_prev,
       LEAD(event_id) OVER w AS next_event
FROM attack_event
WHERE src_country = 'RU'
WINDOW w AS (PARTITION BY src_ip ORDER BY event_time)
ORDER BY src_ip, event_time;""")

order = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
base = {'A': 40, 'B': 50, 'C': 60, 'D': 70, 'E': 80, 'F': 86, 'G': 93}
for k, (title, sql) in Q.items():
    n = base[k[0]] + int(k[1:])
    step(f'{n:03d}_{k}', sql)

# ---------------- Complex queries ----------------
CQ = {}
CQ['CQ-01'] = ("Which threat actor is behind the most serious attacks (severity 8+) on our important assets (criticality 4+)?",
"""SELECT t.actor_name, t.motive,
       COUNT(*)                   AS serious_attacks,
       COUNT(DISTINCT e.asset_id) AS assets_hit,
       MAX(e.severity)            AS worst
FROM attack_event e
JOIN threat_actor t ON t.actor_id = e.actor_id
JOIN asset a        ON a.asset_id = e.asset_id
WHERE e.severity >= 8 AND a.criticality >= 4
GROUP BY t.actor_id, t.actor_name, t.motive
ORDER BY serious_attacks DESC, t.actor_name;""")
CQ['CQ-02'] = ("What does the board of incidents that are still not closed look like?",
"""SELECT i.incident_id, i.priority, i.status,
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
ORDER BY FIELD(i.priority, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'), i.incident_id;""")
CQ['CQ-03'] = ("Which assets were attacked through a CVE they still have not patched?",
"""SELECT a.hostname, e.event_id, e.cve_id, v.cvss, av.detected_at,
       DATEDIFF('2026-10-28', av.detected_at) AS days_unpatched
FROM attack_event e
JOIN asset_vulnerability av ON av.asset_id = e.asset_id
                           AND av.cve_id   = e.cve_id
                           AND av.patched_at IS NULL
JOIN vulnerability v ON v.cve_id   = e.cve_id
JOIN asset a         ON a.asset_id = e.asset_id
ORDER BY v.cvss DESC, a.hostname;""")
CQ['CQ-04'] = ("Which malware families cause the most attacks, and who uses them?",
"""SELECT m.family,
       COUNT(*) AS attacks,
       GROUP_CONCAT(DISTINCT COALESCE(t.actor_name, 'Unknown')) AS used_by,
       ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM attack_event
                               WHERE malware_id IS NOT NULL), 1) AS pct_of_malware_attacks
FROM attack_event e
JOIN malware m           ON m.malware_id = e.malware_id
LEFT JOIN threat_actor t ON t.actor_id   = m.actor_id
GROUP BY m.family
ORDER BY attacks DESC, m.family;""")
CQ['CQ-05'] = ("Time machine: how many attacks matched an indicator we already knew about at the time, and how late were we for the rest?",
"""SELECT CASE WHEN i.recorded_from <= e.event_time THEN 'known at attack time'
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
ORDER BY knowledge;""")
CQ['CQ-06'] = ("What did each retro-hunt find, and what happened to the incident it opened?",
"""SELECT r.run_id, i.ioc_value, r.started_at,
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
ORDER BY r.run_id;""")
CQ['CQ-07'] = ("What is the response playbook for the attack type that hits web-01 most often?",
"""SELECT t.type_name, m.step_no, m.action
FROM mitigation m
JOIN attack_type t ON t.type_id = m.type_id
WHERE m.type_id = (SELECT e.type_id
                   FROM attack_event e
                   JOIN asset a ON a.asset_id = e.asset_id
                   WHERE a.hostname = 'web-01'
                   GROUP BY e.type_id
                   ORDER BY COUNT(*) DESC
                   LIMIT 1)
ORDER BY m.step_no;""")
CQ['CQ-08'] = ("How is the open-incident workload spread across analysts?",
"""SELECT an.full_name,
       COUNT(i.incident_id)                          AS open_incidents,
       COALESCE(SUM(i.priority = 'CRITICAL'), 0)     AS critical,
       RANK() OVER (ORDER BY COUNT(i.incident_id) DESC) AS workload_rank
FROM analyst an
LEFT JOIN incident i ON i.assigned_to = an.analyst_id
                    AND i.status <> 'CLOSED'
WHERE an.role = 'analyst'
GROUP BY an.analyst_id, an.full_name
ORDER BY workload_rank, an.full_name;""")
CQ['CQ-09'] = ("Which countries do attacks come from, what share does each have, and what is each country's most common attack type?",
"""SELECT c.src_country, c.attacks,
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
ORDER BY c.attacks DESC, c.src_country;""")
CQ['CQ-10'] = ("Which assets with an unpatched critical CVE (CVSS 9+) have been attacked by an espionage group?",
"""SELECT DISTINCT a.hostname, av.cve_id, v.cvss, t.actor_name
FROM asset_vulnerability av
JOIN vulnerability v  ON v.cve_id   = av.cve_id
JOIN asset a          ON a.asset_id = av.asset_id
JOIN attack_event e   ON e.asset_id = av.asset_id
JOIN threat_actor t   ON t.actor_id = e.actor_id
WHERE av.patched_at IS NULL
  AND v.cvss >= 9
  AND t.motive = 'espionage'
ORDER BY v.cvss DESC, a.hostname;""")
CQ['CQ-11'] = ("Which source IPs launched a follow-up attack within one hour (attack bursts)?",
"""SELECT src_ip, prev_event, event_id, gap_minutes, hostname
FROM (SELECT e.src_ip, e.event_id, a.hostname,
             LAG(e.event_id) OVER w AS prev_event,
             TIMESTAMPDIFF(MINUTE, LAG(e.event_time) OVER w, e.event_time) AS gap_minutes
      FROM attack_event e
      JOIN asset a ON a.asset_id = e.asset_id
      WINDOW w AS (PARTITION BY e.src_ip ORDER BY e.event_time)) AS x
WHERE gap_minutes <= 60
ORDER BY gap_minutes, src_ip;""")
for i, (k, (q, sql)) in enumerate(CQ.items()):
    step(f'{100 + i:03d}_{k.replace("-", "")}', sql)

# ---------------- Views ----------------
step('120_view_attack_details', """
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
""")
step('121_view_asset_risk', """
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
""")
step('122_view_my_incidents', """
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
""")
step('123_view_review1_views', """
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
""")

# ---------------- Functions ----------------
step('130_func_severity_label', """
DELIMITER //
CREATE FUNCTION fn_severity_label(p_cvss DECIMAL(3,1))
RETURNS VARCHAR(8)
DETERMINISTIC NO SQL
BEGIN
  RETURN CASE WHEN p_cvss >= 9 THEN 'CRITICAL'
              WHEN p_cvss >= 7 THEN 'HIGH'
              WHEN p_cvss >= 4 THEN 'MEDIUM'
              ELSE 'LOW' END;
END //
DELIMITER ;

SELECT cve_id, cvss, fn_severity_label(cvss) AS label
FROM vulnerability
ORDER BY cvss DESC, cve_id;
""")
step('131_func_asset_risk', """
DELIMITER //
CREATE FUNCTION fn_asset_risk(p_asset INT)
RETURNS INT
READS SQL DATA
BEGIN
  DECLARE v_crit, v_open, v_hits INT DEFAULT 0;
  SELECT criticality INTO v_crit FROM asset WHERE asset_id = p_asset;
  SELECT COUNT(*) INTO v_open FROM asset_vulnerability
   WHERE asset_id = p_asset AND patched_at IS NULL;
  SELECT COUNT(*) INTO v_hits FROM attack_event
   WHERE asset_id = p_asset AND blocked = 0;
  RETURN v_crit * 10 + v_open * 5 + v_hits * 2;
END //
DELIMITER ;

SELECT hostname, criticality, fn_asset_risk(asset_id) AS risk_score
FROM asset
ORDER BY risk_score DESC, hostname
LIMIT 5;
""")

# ---------------- Procedures ----------------
step('140_proc_assign_incident', """
DELIMITER //
CREATE PROCEDURE sp_assign_incident(IN p_incident INT, IN p_analyst INT)
BEGIN
  DECLARE v_status VARCHAR(15);
  DECLARE v_role   VARCHAR(10);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;
  SELECT status INTO v_status FROM incident
   WHERE incident_id = p_incident FOR UPDATE;
  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No such incident';
  ELSEIF v_status = 'CLOSED' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Incident is already closed';
  END IF;

  SELECT role INTO v_role FROM analyst WHERE analyst_id = p_analyst;
  IF v_role IS NULL OR v_role = 'viewer' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only analysts or admins can own incidents';
  END IF;

  UPDATE incident
     SET assigned_to = p_analyst,
         status = IF(status = 'OPEN', 'INVESTIGATING', status)
   WHERE incident_id = p_incident;
  COMMIT;

  SELECT incident_id, status, assigned_to FROM incident WHERE incident_id = p_incident;
END //
DELIMITER ;

CALL sp_assign_incident(5, 6);
CALL sp_assign_incident(1, 4);
CALL sp_assign_incident(6, 5);
""")
step('141_proc_attack_report', """
DELIMITER //
CREATE PROCEDURE sp_attack_report(IN p_from DATE, IN p_to DATE)
READS SQL DATA
BEGIN
  SELECT t.type_name,
         COUNT(*)        AS attacks,
         SUM(e.blocked)  AS blocked,
         MAX(e.severity) AS worst
  FROM attack_event e
  JOIN attack_type t ON t.type_id = e.type_id
  WHERE e.event_time >= p_from
    AND e.event_time <  p_to + INTERVAL 1 DAY
  GROUP BY t.type_name
  ORDER BY attacks DESC, t.type_name;
END //
DELIMITER ;

CALL sp_attack_report('2026-10-01', '2026-10-15');
""")

# ---------------- Triggers ----------------
step('150_trg_auto_incident', """
DELIMITER //
CREATE TRIGGER trg_attack_auto_incident
AFTER INSERT ON attack_event
FOR EACH ROW
BEGIN
  DECLARE v_inc INT;
  IF NEW.severity >= 8 THEN
    -- reuse an open incident for the same asset and attack type from the last hour
    SET v_inc = (SELECT ie.incident_id
                 FROM incident_event ie
                 JOIN attack_event e ON e.event_id    = ie.event_id
                 JOIN incident i     ON i.incident_id = ie.incident_id
                 WHERE e.asset_id = NEW.asset_id
                   AND e.type_id  = NEW.type_id
                   AND i.status  <> 'CLOSED'
                   AND e.event_time >= NEW.event_time - INTERVAL 1 HOUR
                 ORDER BY i.opened_at DESC
                 LIMIT 1);
    IF v_inc IS NULL THEN
      INSERT INTO incident (title, priority, status, opened_at)
      VALUES (CONCAT((SELECT type_name FROM attack_type WHERE type_id = NEW.type_id),
                     ' on ', (SELECT hostname FROM asset WHERE asset_id = NEW.asset_id),
                     ' from ', NEW.src_ip),
              IF(NEW.severity >= 9, 'CRITICAL', 'HIGH'), 'OPEN', NEW.event_time);
      SET v_inc = LAST_INSERT_ID();
    END IF;
    INSERT INTO incident_event (incident_id, event_id) VALUES (v_inc, NEW.event_id);
  END IF;
END //
DELIMITER ;

SELECT COUNT(*) AS incidents_before FROM incident;

INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES ('2026-10-27 22:00:00', '203.0.113.66', 'US', 3, 3, 9, 0);
INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES ('2026-10-27 22:20:00', '203.0.113.66', 'US', 3, 3, 8, 0);
INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES ('2026-10-27 22:30:00', '203.0.113.66', 'US', 3, 4, 3, 1);

SELECT i.incident_id, i.title, i.priority, i.status, COUNT(ie.event_id) AS attacks
FROM incident i
JOIN incident_event ie ON ie.incident_id = i.incident_id
WHERE i.incident_id > 7
GROUP BY i.incident_id, i.title, i.priority, i.status;
""")
step('151_trg_ioc_rules', """
DELIMITER //
CREATE TRIGGER trg_ioc_no_overlap
BEFORE INSERT ON ioc
FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM ioc
             WHERE ioc_type = NEW.ioc_type
               AND ioc_value = NEW.ioc_value
               AND (valid_to IS NULL OR valid_to > NEW.valid_from)
               AND (NEW.valid_to IS NULL OR NEW.valid_to > valid_from)) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'An overlapping version of this indicator already exists';
  END IF;
END //

CREATE TRIGGER trg_ioc_no_delete
BEFORE DELETE ON ioc
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Indicator history is append-only; close it with recorded_to instead';
END //

CREATE TRIGGER trg_ioc_retro_hunt
AFTER INSERT ON ioc
FOR EACH ROW
BEGIN
  DECLARE v_run, v_hits, v_assets INT;
  IF NEW.ioc_type = 'ip' THEN
    INSERT INTO retro_hunt_run (ioc_version_id, started_at)
    VALUES (NEW.ioc_version_id, NEW.recorded_from);
    SET v_run = LAST_INSERT_ID();

    -- every old log line from this IP while it was hostile but not yet known
    INSERT INTO retro_hit (run_id, log_id)
    SELECT v_run, log_id
    FROM network_log
    WHERE src_ip = NEW.ioc_value
      AND log_time >= NEW.valid_from
      AND log_time <  NEW.recorded_from
      AND (NEW.valid_to IS NULL OR log_time < NEW.valid_to);
    SET v_hits = ROW_COUNT();

    IF v_hits > 0 THEN
      SET v_assets = (SELECT COUNT(DISTINCT l.dst_asset_id)
                      FROM retro_hit h JOIN network_log l ON l.log_id = h.log_id
                      WHERE h.run_id = v_run);
      INSERT INTO incident (title, priority, status, opened_at)
      VALUES (CONCAT('Retro-hunt: ', NEW.ioc_value, ' hit ', v_assets,
                     ' assets ', v_hits, ' times'),
              IF(v_assets >= 3, 'CRITICAL', 'HIGH'), 'OPEN', NEW.recorded_from);
      UPDATE retro_hunt_run SET incident_id = LAST_INSERT_ID() WHERE run_id = v_run;
    END IF;
  END IF;
END //
DELIMITER ;

SHOW TRIGGERS;
""")
step('152_trg_retro_hunt_demo', """
INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '198.51.100.77', '2026-09-15 00:00:00', '2026-10-28 10:00:00');

SELECT * FROM v_retro_hunt_summary WHERE ioc_version_id = LAST_INSERT_ID();

SELECT incident_id, title, priority, status, opened_at
FROM incident
WHERE title LIKE 'Retro-hunt: 198.51.100.77%';

INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '198.51.100.77', '2026-10-01 00:00:00', '2026-10-28 11:00:00');

DELETE FROM ioc WHERE ioc_value = '198.51.100.77';
""")

# ---------------- Cursors ----------------
step('160_cursor_escalate', """
DELIMITER //
CREATE PROCEDURE sp_escalate_incidents()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_id INT;
  DECLARE v_pri VARCHAR(8);
  DECLARE v_max TINYINT;
  DECLARE cur CURSOR FOR
    SELECT i.incident_id, i.priority, MAX(e.severity)
    FROM incident i
    JOIN incident_event ie ON ie.incident_id = i.incident_id
    JOIN attack_event e    ON e.event_id     = ie.event_id
    WHERE i.status <> 'CLOSED'
    GROUP BY i.incident_id, i.priority
    ORDER BY i.incident_id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  DROP TEMPORARY TABLE IF EXISTS escalation_log;
  CREATE TEMPORARY TABLE escalation_log (
    incident_id INT, old_priority VARCHAR(8), new_priority VARCHAR(8), worst_severity TINYINT);

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO v_id, v_pri, v_max;
    IF done THEN LEAVE read_loop; END IF;
    IF v_max >= 10 AND v_pri <> 'CRITICAL' THEN
      UPDATE incident SET priority = 'CRITICAL' WHERE incident_id = v_id;
      INSERT INTO escalation_log VALUES (v_id, v_pri, 'CRITICAL', v_max);
    ELSEIF v_max >= 8 AND v_pri IN ('LOW', 'MEDIUM') THEN
      UPDATE incident SET priority = 'HIGH' WHERE incident_id = v_id;
      INSERT INTO escalation_log VALUES (v_id, v_pri, 'HIGH', v_max);
    END IF;
  END LOOP;
  CLOSE cur;

  SELECT * FROM escalation_log;
END //
DELIMITER ;

CALL sp_escalate_incidents();
""")
step('161_cursor_asset_risk', """
DELIMITER //
CREATE PROCEDURE sp_asset_risk_report()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_id INT;
  DECLARE v_host VARCHAR(63);
  DECLARE v_score INT;
  DECLARE cur CURSOR FOR SELECT asset_id, hostname FROM asset ORDER BY asset_id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  DROP TEMPORARY TABLE IF EXISTS risk_report;
  CREATE TEMPORARY TABLE risk_report (hostname VARCHAR(63), risk_score INT, band VARCHAR(8));

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO v_id, v_host;
    IF done THEN LEAVE read_loop; END IF;
    SET v_score = fn_asset_risk(v_id);
    INSERT INTO risk_report VALUES (v_host, v_score,
      CASE WHEN v_score >= 60 THEN 'HIGH' WHEN v_score >= 30 THEN 'MEDIUM' ELSE 'LOW' END);
  END LOOP;
  CLOSE cur;

  SELECT * FROM risk_report ORDER BY risk_score DESC, hostname;
END //
DELIMITER ;

CALL sp_asset_risk_report();
""")

# ---------------- Transactions ----------------
step('170_txn_savepoint', """
START TRANSACTION;
INSERT INTO ioc (ioc_type, ioc_value, actor_id, valid_from, recorded_from)
VALUES ('domain', 'kestrel-drop.example', 4, '2026-10-20 00:00:00', '2026-10-27 12:00:00');
SAVEPOINT after_ioc;
UPDATE incident SET priority = 'LOW' WHERE incident_id = 3;
SELECT incident_id, priority FROM incident WHERE incident_id = 3;
ROLLBACK TO SAVEPOINT after_ioc;
COMMIT;

SELECT ioc_version_id, ioc_type, ioc_value FROM ioc WHERE ioc_value = 'kestrel-drop.example';
SELECT incident_id, priority FROM incident WHERE incident_id = 3;
""")
step('171_txn_rollback', """
SELECT COUNT(*) AS logs_before FROM network_log;

START TRANSACTION;
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:00:00', '203.0.113.5', 1, 443, 'TCP', 'allowed');
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
VALUES ('2026-10-28 09:00:01', '203.0.113.5', 99, 443, 'TCP', 'allowed');
ROLLBACK;

SELECT COUNT(*) AS logs_after FROM network_log;
""")

# ---------------- Indexes ----------------
step('180_idx_list', """
SELECT table_name, index_name,
       GROUP_CONCAT(column_name ORDER BY seq_in_index) AS columns_in_index,
       IF(non_unique = 0, 'yes', 'no') AS is_unique
FROM information_schema.statistics
WHERE table_schema = 'sentinelx'
  AND table_name IN ('network_log', 'attack_event')
GROUP BY table_name, index_name, non_unique
ORDER BY table_name, index_name;
""")
step('181_idx_explain_before', """
ALTER TABLE network_log DROP INDEX idx_src_time;
ANALYZE TABLE network_log;

EXPLAIN SELECT log_id, log_time, dst_asset_id
FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28'\\G

SELECT COUNT(*) AS hits FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28';
""")
step('182_idx_explain_after', """
CREATE INDEX idx_src_time ON network_log (src_ip, log_time);
ANALYZE TABLE network_log;

EXPLAIN SELECT log_id, log_time, dst_asset_id
FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28'\\G

SELECT COUNT(*) AS hits FROM network_log
WHERE src_ip = '198.51.100.77'
  AND log_time >= '2026-09-15' AND log_time < '2026-10-28';
""")

# ---------------- Security ----------------
step('190_sec_roles_users', """
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
""")
step('191_sec_show_grants', """
SHOW GRANTS FOR 'sx_viewer';
SHOW GRANTS FOR 'sx_analyst';
SHOW GRANTS FOR 'divya.iyer'@'localhost' USING 'sx_viewer';
""")
step('192_sec_revoke', """
GRANT SELECT ON sentinelx.network_log TO 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';

REVOKE SELECT ON sentinelx.network_log FROM 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';
""")
step('193_sec_viewer__as_divya', """
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

SELECT hostname, criticality, attacks, not_blocked, open_vulns
FROM v_asset_risk
ORDER BY not_blocked DESC
LIMIT 3;

CALL sp_attack_report('2026-10-20', '2026-10-28');

SELECT * FROM attack_event LIMIT 1;
DELETE FROM attack_event WHERE event_id = 1;
UPDATE v_asset_risk SET criticality = 1 WHERE asset_id = 1;
""")
step('194_sec_analyst__as_rahul', """
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

SELECT incident_id, title, priority, status FROM v_my_incidents;

UPDATE v_my_incidents SET status = 'CONTAINED' WHERE incident_id = 7;
SELECT incident_id, status FROM v_my_incidents WHERE incident_id = 7;

UPDATE v_my_incidents SET assigned_to = 3 WHERE incident_id = 7;
SELECT * FROM incident LIMIT 1;
DROP TABLE asset;
""")
step('195_sec_admin__as_ananya', """
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;
SELECT COUNT(*) AS incidents FROM incident;
""")

if __name__ == '__main__':
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for n, s in STEPS.items():
        with open(os.path.join(OUT, n + '.sql'), 'w', newline='\r\n') as f:
            f.write(s)
    print(len(STEPS), 'steps')
