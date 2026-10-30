SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;
SELECT COUNT(*) AS incidents FROM incident;

-- the audit trail shows who changed which incident, including rahul's changes
-- made through the view and through the DEFINER procedure
SELECT audit_id, incident_id, changed_by, old_status, new_status,
       old_assigned_to, new_assigned_to
FROM incident_audit
ORDER BY audit_id;

-- the admin cannot erase or forge it: no DELETE or INSERT on it, no TRUNCATE (needs DROP), no DROP TRIGGER
DELETE FROM incident_audit WHERE audit_id = 1;
INSERT INTO incident_audit (incident_id, action, changed_by) VALUES (7, 'UPDATE', 'rahul.mehta@localhost');
TRUNCATE TABLE incident_audit;
DROP TRIGGER trg_audit_no_delete;
