SELECT a.hostname,
       COUNT(*)                   AS attacks,
       SUM(e.blocked)             AS blocked,
       ROUND(AVG(e.severity), 2)  AS avg_severity
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
GROUP BY a.hostname
ORDER BY attacks DESC, a.hostname;
