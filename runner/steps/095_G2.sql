SELECT DATE(event_time) AS day,
       COUNT(*) AS attacks,
       SUM(COUNT(*)) OVER (ORDER BY DATE(event_time)) AS running_total
FROM attack_event
WHERE event_time < '2026-10-11'
GROUP BY DATE(event_time)
ORDER BY day;
