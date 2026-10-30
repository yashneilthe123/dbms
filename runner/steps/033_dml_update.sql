SELECT event_id, severity, blocked, triage_priority FROM attack_event WHERE event_id IN (25, 26);
UPDATE attack_event
   SET triage_priority = CASE event_id WHEN 25 THEN 'MEDIUM'   -- severity 7, but blocked
                                       WHEN 26 THEN 'LOW' END   -- severity 4, blocked
 WHERE event_id IN (25, 26);
SELECT event_id, severity, blocked, triage_priority FROM attack_event WHERE event_id IN (25, 26);
