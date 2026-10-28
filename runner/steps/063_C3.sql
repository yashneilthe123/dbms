SELECT an.full_name, an.role, i.incident_id, i.status
FROM incident i
RIGHT JOIN analyst an ON an.analyst_id = i.assigned_to
ORDER BY an.analyst_id, i.incident_id;
