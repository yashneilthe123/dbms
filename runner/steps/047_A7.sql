SELECT event_id, event_time, src_ip, severity
FROM attack_event
WHERE triage_priority IS NULL
ORDER BY event_id;
