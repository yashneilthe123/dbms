-- every change to an incident is written to incident_audit by the database itself,
-- so it is recorded whether it came from a view, a procedure or a direct UPDATE
DELIMITER //
CREATE TRIGGER trg_incident_audit_update
AFTER UPDATE ON incident
FOR EACH ROW
BEGIN
  INSERT INTO incident_audit (incident_id, action, changed_by,
                              old_status, new_status, old_priority, new_priority,
                              old_assigned_to, new_assigned_to)
  VALUES (OLD.incident_id, 'UPDATE', USER(),     -- USER(), not CURRENT_USER(): inside a trigger
          OLD.status, NEW.status,                -- CURRENT_USER() is the trigger's definer (root)
          OLD.priority, NEW.priority,
          OLD.assigned_to, NEW.assigned_to);
END //

CREATE TRIGGER trg_incident_audit_delete
AFTER DELETE ON incident
FOR EACH ROW
BEGIN
  INSERT INTO incident_audit (incident_id, action, changed_by,
                              old_status, old_priority, old_assigned_to)
  VALUES (OLD.incident_id, 'DELETE', USER(), OLD.status, OLD.priority, OLD.assigned_to);
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
