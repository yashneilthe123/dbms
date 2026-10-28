SELECT c.src_country, c.attacks,
       ROUND(100 * c.attacks / SUM(c.attacks) OVER (), 1) AS pct,
       (SELECT t.type_name
          FROM attack_event e2
          JOIN attack_type t ON t.type_id = e2.type_id
         WHERE e2.src_country = c.src_country
         GROUP BY t.type_name
         ORDER BY COUNT(*) DESC, t.type_name
         LIMIT 1) AS top_type
FROM (SELECT src_country, COUNT(*) AS attacks
      FROM attack_event
      GROUP BY src_country) AS c
ORDER BY c.attacks DESC, c.src_country;
