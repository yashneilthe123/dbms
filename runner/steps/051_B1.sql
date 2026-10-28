SELECT t.type_name, COUNT(*) AS attacks
FROM attack_event e
JOIN attack_type t ON t.type_id = e.type_id
GROUP BY t.type_name
ORDER BY attacks DESC, t.type_name;
