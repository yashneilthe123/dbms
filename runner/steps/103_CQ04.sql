SELECT m.family,
       COUNT(*) AS attacks,
       GROUP_CONCAT(DISTINCT COALESCE(t.actor_name, 'Unknown')) AS used_by,
       ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM attack_event
                               WHERE malware_id IS NOT NULL), 1) AS pct_of_malware_attacks
FROM attack_event e
JOIN malware m           ON m.malware_id = e.malware_id
LEFT JOIN threat_actor t ON t.actor_id   = m.actor_id
GROUP BY m.family
ORDER BY attacks DESC, m.family;
