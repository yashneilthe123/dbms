SELECT hostname, asset_type, criticality
FROM asset
WHERE asset_type IN ('web', 'db', 'vpn')
ORDER BY asset_type, hostname;
