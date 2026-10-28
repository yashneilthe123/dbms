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
