SELECT src_ip, event_id, event_time,
       TIMESTAMPDIFF(MINUTE,
                     LAG(event_time) OVER w, event_time) AS mins_since_prev,
       LEAD(event_id) OVER w AS next_event
FROM attack_event
WHERE src_country = 'RU'
WINDOW w AS (PARTITION BY src_ip ORDER BY event_time)
ORDER BY src_ip, event_time;
