-- Demo step 4 (root): triggers firing. Safe to run more than once.
USE sentinelx;

-- (a) a severity-9 attack opens an incident by itself
SELECT COUNT(*) AS incidents_before FROM incident;
INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES (NOW(), '203.0.113.66', 'US', 3, 3, 9, 0);
SELECT i.incident_id, i.title, i.priority, i.status
FROM incident i JOIN incident_event ie ON ie.incident_id = i.incident_id
WHERE ie.event_id = LAST_INSERT_ID();

-- (b) retro-hunt: internal host 172.16.3.4 turns out to be compromised. Reporting it makes
--     the database search 50,000 old log lines and open an incident if it finds any.
UPDATE ioc SET recorded_to = NOW() WHERE ioc_value = '172.16.3.4' AND recorded_to IS NULL;  -- close an earlier run's version
INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '172.16.3.4', '2026-10-01', NOW());
SELECT * FROM v_retro_hunt_summary WHERE ioc_version_id = LAST_INSERT_ID();
SELECT incident_id, title, priority FROM incident ORDER BY incident_id DESC LIMIT 1;

-- (c) the IOC rules
INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '172.16.3.4', '2026-10-05', NOW());                -- ERROR 1644: overlapping version
DELETE FROM ioc WHERE ioc_value = '172.16.3.4';                   -- ERROR 1644: append-only
