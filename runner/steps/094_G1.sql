SELECT a.hostname,
       COUNT(e.event_id) AS attacks,
       RANK()       OVER (ORDER BY COUNT(e.event_id) DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY COUNT(e.event_id) DESC) AS dense_rnk,
       ROW_NUMBER() OVER (ORDER BY COUNT(e.event_id) DESC, a.hostname) AS row_no
FROM asset a
LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname
ORDER BY row_no;
