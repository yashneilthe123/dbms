SELECT t.type_name, m.step_no, m.action
FROM mitigation m
JOIN attack_type t ON t.type_id = m.type_id
WHERE m.type_id = (SELECT e.type_id
                   FROM attack_event e
                   JOIN asset a ON a.asset_id = e.asset_id
                   WHERE a.hostname = 'web-01'
                   GROUP BY e.type_id
                   ORDER BY COUNT(*) DESC
                   LIMIT 1)
ORDER BY m.step_no;
