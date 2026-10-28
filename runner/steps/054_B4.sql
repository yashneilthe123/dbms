SELECT src_ip, COUNT(*) AS attacks
FROM attack_event
GROUP BY src_ip
HAVING COUNT(*) > 3
ORDER BY attacks DESC, src_ip;
