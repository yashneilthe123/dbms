SELECT i.incident_id, i.priority, i.status,
       COALESCE(an.full_name, 'Unassigned')      AS owner,
       COUNT(*)                                  AS attacks,
       MAX(e.severity)                           AS worst,
       GROUP_CONCAT(DISTINCT a.hostname ORDER BY a.hostname) AS assets
FROM incident i
JOIN incident_event ie ON ie.incident_id = i.incident_id
JOIN attack_event e    ON e.event_id     = ie.event_id
JOIN asset a           ON a.asset_id     = e.asset_id
LEFT JOIN analyst an   ON an.analyst_id  = i.assigned_to
WHERE i.status <> 'CLOSED'
GROUP BY i.incident_id, i.priority, i.status, an.full_name
ORDER BY FIELD(i.priority, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'), i.incident_id;
