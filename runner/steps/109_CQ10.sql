SELECT DISTINCT a.hostname, av.cve_id, v.cvss, t.actor_name
FROM asset_vulnerability av
JOIN vulnerability v  ON v.cve_id   = av.cve_id
JOIN asset a          ON a.asset_id = av.asset_id
JOIN attack_event e   ON e.asset_id = av.asset_id
JOIN threat_actor t   ON t.actor_id = e.actor_id
WHERE av.patched_at IS NULL
  AND v.cvss >= 9
  AND t.motive = 'espionage'
ORDER BY v.cvss DESC, a.hostname;
