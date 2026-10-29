-- SentinelX Review 2: Triggers and demonstrations
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- trg_auto_incident ----
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


-- ---- trg_ioc_rules ----
DELIMITER //
CREATE TRIGGER trg_ioc_no_overlap
BEFORE INSERT ON ioc
FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM ioc
             WHERE ioc_type = NEW.ioc_type
               AND ioc_value = NEW.ioc_value
               AND recorded_to IS NULL               -- versions closed with recorded_to are history
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

-- the only change allowed to a version is closing it: recorded_to from NULL to a time
CREATE TRIGGER trg_ioc_only_close
BEFORE UPDATE ON ioc
FOR EACH ROW
BEGIN
  IF NOT (NEW.ioc_version_id <=> OLD.ioc_version_id AND NEW.ioc_type <=> OLD.ioc_type
          AND NEW.ioc_value <=> OLD.ioc_value AND NEW.actor_id <=> OLD.actor_id
          AND NEW.malware_id <=> OLD.malware_id AND NEW.valid_from <=> OLD.valid_from
          AND NEW.valid_to <=> OLD.valid_to AND NEW.recorded_from <=> OLD.recorded_from
          AND OLD.recorded_to IS NULL AND NEW.recorded_to IS NOT NULL) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Indicator versions cannot be changed; only an open version can be closed';
  END IF;
END //

CREATE TRIGGER trg_ioc_retro_hunt
AFTER INSERT ON ioc
FOR EACH ROW
BEGIN
  DECLARE v_run, v_hits, v_assets INT;
  IF NEW.ioc_type = 'ip' THEN
    INSERT INTO retro_hunt_run (ioc_version_id, started_at)
    VALUES (NEW.ioc_version_id, SYSDATE());           -- when this search really ran
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


-- ---- trg_retro_hunt_demo ----
INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '198.51.100.77', '2026-09-15 00:00:00', '2026-10-28 10:00:00');

SELECT * FROM v_retro_hunt_summary WHERE ioc_version_id = LAST_INSERT_ID();

SELECT incident_id, title, priority, status, opened_at
FROM incident
WHERE title LIKE 'Retro-hunt: 198.51.100.77%';

INSERT INTO ioc (ioc_type, ioc_value, valid_from, recorded_from)
VALUES ('ip', '198.51.100.77', '2026-10-01 00:00:00', '2026-10-28 11:00:00');

DELETE FROM ioc WHERE ioc_value = '198.51.100.77';
UPDATE ioc SET ioc_value = '198.51.100.78' WHERE ioc_value = '198.51.100.77';


-- ---- trg_audit ----
-- every change to an incident is written to incident_audit by the database itself,
-- so it is recorded whether it came from a view, a procedure or a direct UPDATE
DELIMITER //
CREATE TRIGGER trg_incident_audit_update
AFTER UPDATE ON incident
FOR EACH ROW
BEGIN
  INSERT INTO incident_audit (incident_id, action, changed_by, changed_at,
                              old_status, new_status, old_priority, new_priority,
                              old_assigned_to, new_assigned_to)
  VALUES (OLD.incident_id, 'UPDATE', USER(),     -- USER(), not CURRENT_USER(): inside a trigger
          SYSDATE(6),                            -- CURRENT_USER() is the trigger's definer (root);
          OLD.status, NEW.status,                -- SYSDATE(), unlike NOW(), ignores SET timestamp
          OLD.priority, NEW.priority,
          OLD.assigned_to, NEW.assigned_to);
END //

CREATE TRIGGER trg_incident_audit_delete
AFTER DELETE ON incident
FOR EACH ROW
BEGIN
  INSERT INTO incident_audit (incident_id, action, changed_by, changed_at,
                              old_status, old_priority, old_assigned_to)
  VALUES (OLD.incident_id, 'DELETE', USER(), SYSDATE(6), OLD.status, OLD.priority, OLD.assigned_to);
END //

-- the trail itself is append-only
CREATE TRIGGER trg_audit_no_update
BEFORE UPDATE ON incident_audit
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The audit trail is append-only';
END //

CREATE TRIGGER trg_audit_no_delete
BEFORE DELETE ON incident_audit
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The audit trail is append-only';
END //
DELIMITER ;

UPDATE incident SET status = 'CONTAINED' WHERE incident_id = 4;
SELECT audit_id, incident_id, action, changed_by, old_status, new_status FROM incident_audit;

DELETE FROM incident_audit;
