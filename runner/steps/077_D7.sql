SELECT t.actor_name, t.motive
FROM threat_actor t
WHERE EXISTS (SELECT 1 FROM attack_event e
              WHERE e.actor_id = t.actor_id AND e.blocked = 0)
ORDER BY t.actor_name;
