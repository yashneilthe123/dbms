SELECT a.hostname, t.type_name,
       (SELECT COUNT(*) FROM attack_event e
         WHERE e.asset_id = a.asset_id AND e.type_id = t.type_id) AS times_seen
FROM asset a
CROSS JOIN attack_type t
WHERE a.criticality = 5 AND t.base_severity >= 8
ORDER BY a.hostname, t.type_name;
