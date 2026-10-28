SELECT hostname, asset_type, criticality
FROM asset a
WHERE NOT EXISTS (SELECT 1 FROM attack_event e
                  WHERE e.asset_id = a.asset_id);
