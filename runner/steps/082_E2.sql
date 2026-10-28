SELECT event_time AS seen_at, 'attack' AS source, asset_id, severity AS detail
FROM attack_event WHERE src_ip = '198.51.100.45'
UNION ALL
SELECT log_time, 'log', dst_asset_id, dst_port
FROM network_log WHERE src_ip = '198.51.100.45'
ORDER BY seen_at;
