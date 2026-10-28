INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '198.51.100.77', '2026-09-15 00:00:00', '2026-10-28 10:00:00');

SELECT * FROM v_retro_hunt_summary WHERE ioc_version_id = LAST_INSERT_ID();

SELECT incident_id, title, priority, status, opened_at
FROM incident
WHERE title LIKE 'Retro-hunt: 198.51.100.77%';

INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '198.51.100.77', '2026-10-01 00:00:00', '2026-10-28 11:00:00');

DELETE FROM ioc WHERE ioc_value = '198.51.100.77';
