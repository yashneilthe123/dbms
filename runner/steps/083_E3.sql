SELECT src_ip FROM attack_event
INTERSECT
SELECT ioc_value FROM ioc WHERE ioc_type = 'ip'
ORDER BY src_ip;
