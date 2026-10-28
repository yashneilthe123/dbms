SELECT a.hostname, e.event_id, e.cve_id, v.cvss, av.detected_at,
       DATEDIFF('2026-10-28', av.detected_at) AS days_unpatched
FROM attack_event e
JOIN asset_vulnerability av ON av.asset_id = e.asset_id
                           AND av.cve_id   = e.cve_id
                           AND av.patched_at IS NULL
JOIN vulnerability v ON v.cve_id   = e.cve_id
JOIN asset a         ON a.asset_id = e.asset_id
ORDER BY v.cvss DESC, a.hostname;
