SELECT event_id, event_time, src_ip, severity
FROM attack_event
WHERE event_time BETWEEN '2026-10-10 00:00:00' AND '2026-10-14 23:59:59'
ORDER BY event_time;
