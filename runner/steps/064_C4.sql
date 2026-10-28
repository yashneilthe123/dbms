SELECT t.actor_name, m.malware_name
FROM threat_actor t LEFT JOIN malware m ON m.actor_id = t.actor_id
UNION
SELECT t.actor_name, m.malware_name
FROM threat_actor t RIGHT JOIN malware m ON m.actor_id = t.actor_id
ORDER BY actor_name, malware_name;
