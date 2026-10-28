CREATE VIEW v_asset_risk AS
SELECT a.asset_id, a.hostname, a.criticality,
       COUNT(e.event_id)               AS attacks,
       COALESCE(SUM(e.blocked = 0), 0) AS not_blocked,
       MAX(e.severity)                 AS worst_severity,
       (SELECT COUNT(*) FROM asset_vulnerability av
         WHERE av.asset_id = a.asset_id AND av.patched_at IS NULL) AS open_vulns
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.asset_id, a.hostname, a.criticality;

SELECT hostname, criticality, attacks, not_blocked, worst_severity, open_vulns
FROM v_asset_risk
ORDER BY not_blocked DESC, criticality DESC
LIMIT 5;

UPDATE v_asset_risk SET criticality = 5 WHERE asset_id = 2;
