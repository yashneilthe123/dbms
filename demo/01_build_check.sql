-- Demo step 1, after the clean build: is everything there?
USE sentinelx;

SELECT 'asset' AS table_name, COUNT(*) AS row_count FROM asset
UNION ALL SELECT 'network_log',  COUNT(*) FROM network_log
UNION ALL SELECT 'attack_event', COUNT(*) FROM attack_event
UNION ALL SELECT 'ioc',          COUNT(*) FROM ioc
UNION ALL SELECT 'incident',     COUNT(*) FROM incident
UNION ALL SELECT 'analyst',      COUNT(*) FROM analyst;

SELECT COUNT(*) AS base_tables FROM information_schema.tables
WHERE table_schema = 'sentinelx' AND table_type = 'BASE TABLE';

SELECT routine_type, COUNT(*) AS how_many FROM information_schema.routines
WHERE routine_schema = 'sentinelx' GROUP BY routine_type
UNION ALL
SELECT 'TRIGGER', COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'sentinelx'
UNION ALL
SELECT 'VIEW', COUNT(*) FROM information_schema.views WHERE table_schema = 'sentinelx';
