SELECT src_ip, prev_event, event_id, gap_minutes, hostname
FROM (SELECT e.src_ip, e.event_id, a.hostname,
             LAG(e.event_id) OVER w AS prev_event,
             TIMESTAMPDIFF(MINUTE, LAG(e.event_time) OVER w, e.event_time) AS gap_minutes
      FROM attack_event e
      JOIN asset a ON a.asset_id = e.asset_id
      WINDOW w AS (PARTITION BY e.src_ip ORDER BY e.event_time)) AS x
WHERE gap_minutes <= 60
ORDER BY gap_minutes, src_ip;
