SELECT hostname, asset_type
FROM asset
WHERE asset_id IN (SELECT e.asset_id
                   FROM attack_event e
                   JOIN attack_type t ON t.type_id = e.type_id
                   WHERE t.type_name = 'Ransomware')
ORDER BY hostname;
