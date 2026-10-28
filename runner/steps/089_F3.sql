SELECT a.hostname,
       COUNT(e.event_id) AS attacks,
       ROUND(100 * SUM(e.blocked) / NULLIF(COUNT(e.event_id), 0), 1) AS blocked_pct
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY blocked_pct DESC, a.hostname;
