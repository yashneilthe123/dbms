SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

SELECT incident_id, title, priority, status FROM v_my_incidents;

UPDATE v_my_incidents SET status = 'CONTAINED' WHERE incident_id = 7;
SELECT incident_id, status FROM v_my_incidents WHERE incident_id = 7;

UPDATE v_my_incidents SET assigned_to = 3 WHERE incident_id = 7;
SELECT * FROM incident LIMIT 1;
DROP TABLE asset;
