SELECT cve_id, cvss,
       CASE WHEN cvss >= 9 THEN 'CRITICAL'
            WHEN cvss >= 7 THEN 'HIGH'
            WHEN cvss >= 4 THEN 'MEDIUM'
            ELSE 'LOW' END AS severity
FROM vulnerability
ORDER BY cvss DESC, cve_id;
