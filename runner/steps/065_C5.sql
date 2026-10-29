SELECT t.actor_name, m1.malware_name AS malware_1, m2.malware_name AS malware_2
FROM malware m1
JOIN malware m2     ON m2.actor_id = m1.actor_id
                   AND m2.malware_id > m1.malware_id
JOIN threat_actor t ON t.actor_id = m1.actor_id
ORDER BY t.actor_name, malware_1;
