SELECT actor_name FROM threat_actor
WHERE actor_id NOT IN (SELECT actor_id FROM malware);

SELECT actor_name FROM threat_actor
WHERE actor_id NOT IN (SELECT actor_id FROM malware WHERE actor_id IS NOT NULL);
