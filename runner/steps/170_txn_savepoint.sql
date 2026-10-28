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
