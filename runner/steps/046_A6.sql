SELECT incident_id, title, priority, status
FROM incident
WHERE assigned_to IS NULL;
