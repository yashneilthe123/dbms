SELECT a.hostname, COUNT(e.event_id) AS attacks
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY attacks, a.hostname;
