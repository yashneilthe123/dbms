SELECT cve_id, cvss,
       (SELECT ROUND(AVG(cvss), 2) FROM vulnerability) AS avg_cvss
FROM vulnerability
WHERE cvss > (SELECT AVG(cvss) FROM vulnerability)
ORDER BY cvss DESC, cve_id;
