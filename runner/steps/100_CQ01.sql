SELECT t.actor_name, t.motive,
       COUNT(*)                   AS serious_attacks,
       COUNT(DISTINCT e.asset_id) AS assets_hit,
       MAX(e.severity)            AS worst
FROM attack_event e
JOIN threat_actor t ON t.actor_id = e.actor_id
JOIN asset a        ON a.asset_id = e.asset_id
WHERE e.severity >= 8 AND a.criticality >= 4
GROUP BY t.actor_id, t.actor_name, t.motive
ORDER BY serious_attacks DESC, t.actor_name;
