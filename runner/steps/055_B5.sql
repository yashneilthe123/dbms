SELECT a.hostname, COUNT(*) AS serious_attacks
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
WHERE e.severity >= 7          -- WHERE filters single rows before grouping
GROUP BY a.hostname
HAVING COUNT(*) >= 2           -- HAVING filters whole groups after grouping
ORDER BY serious_attacks DESC, a.hostname;
