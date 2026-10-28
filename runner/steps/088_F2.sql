SELECT e.event_id, e.src_ip,
       COALESCE(t.actor_name, 'Unattributed') AS actor,
       COALESCE(m.malware_name, '-')          AS malware
FROM attack_event e
LEFT JOIN threat_actor t ON t.actor_id   = e.actor_id
LEFT JOIN malware m      ON m.malware_id = e.malware_id
WHERE e.event_time >= '2026-10-20'
ORDER BY e.event_id;
