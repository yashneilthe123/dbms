SELECT cve_id, cvss,
       ROUND(cvss)                AS rounded,
       CEIL(cvss)                 AS ceiling,
       FLOOR(cvss)                AS floor_value,
       TRUNCATE(cvss * 10, 0)     AS pct_of_max,
       MOD(FLOOR(cvss * 10), 7)   AS bucket
FROM vulnerability
ORDER BY cvss DESC, cve_id;
