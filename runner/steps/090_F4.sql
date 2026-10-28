SELECT incident_id,
       DATE_FORMAT(opened_at, '%d %b %Y %H:%i') AS opened,
       DAYNAME(opened_at) AS opened_on,
       TIMESTAMPDIFF(HOUR, opened_at, COALESCE(closed_at, '2026-10-28 12:00:00')) AS hours_open,
       DATEDIFF('2026-10-28', DATE(opened_at)) AS age_days
FROM incident
ORDER BY incident_id;
