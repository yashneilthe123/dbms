SELECT table_name, index_name,
       GROUP_CONCAT(column_name ORDER BY seq_in_index) AS columns_in_index,
       IF(non_unique = 0, 'yes', 'no') AS is_unique
FROM information_schema.statistics
WHERE table_schema = 'sentinelx'
  AND table_name IN ('network_log', 'attack_event')
GROUP BY table_name, index_name, non_unique
ORDER BY table_name, index_name;
