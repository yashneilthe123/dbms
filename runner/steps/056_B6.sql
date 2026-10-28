SELECT YEAR(published)       AS year_published,
       COUNT(*)              AS cves,
       ROUND(AVG(cvss), 2)   AS avg_cvss,
       MIN(cvss)             AS min_cvss,
       MAX(cvss)             AS max_cvss
FROM vulnerability
GROUP BY YEAR(published)
ORDER BY year_published;
