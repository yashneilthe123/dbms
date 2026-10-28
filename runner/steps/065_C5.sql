SELECT m1.cluster_id, m1.malware_name AS malware_1, m2.malware_name AS malware_2
FROM malware m1
JOIN malware m2 ON m2.cluster_id = m1.cluster_id
               AND m2.malware_id > m1.malware_id
ORDER BY m1.cluster_id, malware_1;
