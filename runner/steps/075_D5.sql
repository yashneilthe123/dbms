SELECT cve_id, cvss
FROM vulnerability
WHERE cvss > ANY (SELECT v.cvss
                  FROM attack_event e
                  JOIN vulnerability v ON v.cve_id = e.cve_id
                  WHERE e.src_country = 'RU')
ORDER BY cvss DESC, cve_id;
