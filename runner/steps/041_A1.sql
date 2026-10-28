SELECT hostname, ip_address, asset_type, criticality
FROM asset
WHERE criticality >= 4
ORDER BY criticality DESC, hostname;
