SELECT cve_id, cvss, published
FROM vulnerability
WHERE cve_id LIKE 'CVE-2023-%'
ORDER BY cvss DESC;
