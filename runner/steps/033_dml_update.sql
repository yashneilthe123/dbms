SELECT event_id, severity, predicted_severity FROM attack_event WHERE event_id IN (25, 26);
UPDATE attack_event
   SET predicted_severity = CASE WHEN severity >= 9 THEN 'CRITICAL'
                                 WHEN severity >= 7 THEN 'HIGH'
                                 WHEN severity >= 4 THEN 'MEDIUM'
                                 ELSE 'LOW' END
 WHERE event_id IN (25, 26);
SELECT event_id, severity, predicted_severity FROM attack_event WHERE event_id IN (25, 26);
