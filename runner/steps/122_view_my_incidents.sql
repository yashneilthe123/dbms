CREATE VIEW v_my_incidents AS
SELECT incident_id, title, priority, status, assigned_to, opened_at, closed_at
FROM incident
WHERE assigned_to = (SELECT analyst_id FROM analyst
                     WHERE email = CONCAT(SUBSTRING_INDEX(USER(), '@', 1), '@sentinelx.in'))
WITH CHECK OPTION;

SELECT USER() AS logged_in_as, COUNT(*) AS rows_visible FROM v_my_incidents;

SELECT table_name, is_updatable
FROM information_schema.views
WHERE table_schema = 'sentinelx'
ORDER BY table_name;
