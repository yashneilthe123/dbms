SELECT 'asset' AS table_name, COUNT(*) AS row_count FROM asset
UNION ALL SELECT 'vulnerability', COUNT(*) FROM vulnerability
UNION ALL SELECT 'asset_vulnerability', COUNT(*) FROM asset_vulnerability
UNION ALL SELECT 'network_log', COUNT(*) FROM network_log
UNION ALL SELECT 'attack_type', COUNT(*) FROM attack_type
UNION ALL SELECT 'mitigation', COUNT(*) FROM mitigation
UNION ALL SELECT 'threat_actor', COUNT(*) FROM threat_actor
UNION ALL SELECT 'malware', COUNT(*) FROM malware
UNION ALL SELECT 'attack_event', COUNT(*) FROM attack_event
UNION ALL SELECT 'analyst', COUNT(*) FROM analyst
UNION ALL SELECT 'incident', COUNT(*) FROM incident
UNION ALL SELECT 'incident_event', COUNT(*) FROM incident_event
UNION ALL SELECT 'ioc', COUNT(*) FROM ioc
UNION ALL SELECT 'event_ioc', COUNT(*) FROM event_ioc
UNION ALL SELECT 'retro_hunt_run', COUNT(*) FROM retro_hunt_run
UNION ALL SELECT 'retro_hit', COUNT(*) FROM retro_hit
UNION ALL SELECT 'incident_audit', COUNT(*) FROM incident_audit;
