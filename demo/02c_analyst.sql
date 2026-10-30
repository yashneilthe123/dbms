-- Demo step 2c, logged in as rahul (analyst): views and procedures only.
SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

-- row-level security: only his own incidents
SELECT incident_id, title, priority, status FROM v_my_incidents;

-- ERROR 1142: no base tables at all
SELECT * FROM incident LIMIT 1;

-- ERROR 1369: WITH CHECK OPTION stops him handing an incident to someone else through the view
UPDATE v_my_incidents SET assigned_to = 3 WHERE incident_id = 7;

-- the procedure runs with root's rights, so it checks the caller itself
CALL sp_whoami();
CALL sp_assign_incident(6, 2);   -- ERROR 1644: incident 6 belongs to Priya
