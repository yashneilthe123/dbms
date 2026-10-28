SELECT src_country,
       MIN(event_time) AS first_seen,
       MAX(event_time) AS last_seen,
       MAX(severity)   AS worst_severity
FROM attack_event
GROUP BY src_country
ORDER BY first_seen;
