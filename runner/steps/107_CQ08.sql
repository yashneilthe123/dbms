SELECT an.full_name,
       COUNT(i.incident_id)                          AS open_incidents,
       COALESCE(SUM(i.priority = 'CRITICAL'), 0)     AS critical,
       RANK() OVER (ORDER BY COUNT(i.incident_id) DESC) AS workload_rank
FROM analyst an
LEFT JOIN incident i ON i.assigned_to = an.analyst_id
                    AND i.status <> 'CLOSED'
WHERE an.role = 'analyst'
GROUP BY an.analyst_id, an.full_name
ORDER BY workload_rank, an.full_name;
