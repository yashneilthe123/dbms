-- Demo step 2d, logged in as ananya (admin): who changed what, and the trail cannot be erased or forged.
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

SELECT audit_id, incident_id, action, changed_by, changed_at,
       old_status, new_status, old_priority, new_priority, old_assigned_to, new_assigned_to
FROM incident_audit ORDER BY audit_id DESC LIMIT 8;

DELETE FROM incident_audit WHERE audit_id = 1;   -- ERROR 1142: the admin may only read the audit trail
INSERT INTO incident_audit (incident_id, action, changed_by)
VALUES (7, 'UPDATE', 'rahul.mehta@localhost');  -- ERROR 1142: no forged rows either
TRUNCATE TABLE incident_audit;                   -- ERROR 1142: TRUNCATE needs DROP, which admins do not have
DROP TRIGGER trg_audit_no_delete;                -- ERROR 1142: no TRIGGER privilege
