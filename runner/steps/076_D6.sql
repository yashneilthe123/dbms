SELECT a.hostname, e.event_id, e.severity
FROM attack_event e
JOIN asset a ON a.asset_id = e.asset_id
WHERE e.severity = (SELECT MAX(e2.severity)
                    FROM attack_event e2
                    WHERE e2.asset_id = e.asset_id)
ORDER BY a.hostname, e.event_id;
