SELECT cve_id, cvss
FROM vulnerability
WHERE cvss > ALL (SELECT v.cvss
                  FROM asset_vulnerability av
                  JOIN vulnerability v ON v.cve_id = av.cve_id
                  WHERE av.asset_id IN (2, 4))
ORDER BY cve_id;
