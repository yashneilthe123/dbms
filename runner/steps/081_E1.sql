SELECT src_country AS country FROM attack_event
UNION
SELECT origin_country FROM threat_actor WHERE origin_country IS NOT NULL
ORDER BY country;
