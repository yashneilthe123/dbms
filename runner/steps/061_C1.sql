SELECT e.event_id, e.event_time, a.hostname, t.type_name, e.severity
FROM attack_event e
INNER JOIN asset a       ON a.asset_id = e.asset_id
INNER JOIN attack_type t ON t.type_id  = e.type_id
WHERE e.severity >= 9
ORDER BY e.event_time;
