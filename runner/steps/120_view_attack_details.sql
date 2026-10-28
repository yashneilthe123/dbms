CREATE VIEW v_attack_details AS
SELECT e.event_id, e.event_time, e.src_ip, e.src_country,
       a.hostname, t.type_name,
       ta.actor_name, m.malware_name, e.cve_id,
       e.severity, e.blocked
FROM attack_event e
JOIN asset a             ON a.asset_id   = e.asset_id
JOIN attack_type t       ON t.type_id    = e.type_id
LEFT JOIN threat_actor ta ON ta.actor_id  = e.actor_id
LEFT JOIN malware m       ON m.malware_id = e.malware_id;

SELECT event_id, event_time, src_ip, type_name, actor_name, severity
FROM v_attack_details
WHERE hostname = 'web-01'
ORDER BY event_time;

DELETE FROM v_attack_details WHERE event_id = 3;
