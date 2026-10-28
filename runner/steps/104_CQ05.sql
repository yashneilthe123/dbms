SELECT CASE WHEN i.recorded_from <= e.event_time THEN 'known at attack time'
            ELSE 'recognised later' END                 AS knowledge,
       COUNT(*)                                          AS matches,
       COUNT(DISTINCT e.event_id)                        AS attacks,
       ROUND(AVG(CASE WHEN i.recorded_from > e.event_time
                      THEN TIMESTAMPDIFF(HOUR, e.event_time, i.recorded_from) / 24
                 END), 1)                                AS avg_days_late
FROM attack_event e
JOIN event_ioc ei ON ei.event_id      = e.event_id
JOIN ioc i        ON i.ioc_version_id = ei.ioc_version_id
GROUP BY knowledge
ORDER BY knowledge;
