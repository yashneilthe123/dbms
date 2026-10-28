DELIMITER //
CREATE PROCEDURE sp_attack_report(IN p_from DATE, IN p_to DATE)
READS SQL DATA
BEGIN
  SELECT t.type_name,
         COUNT(*)        AS attacks,
         SUM(e.blocked)  AS blocked,
         MAX(e.severity) AS worst
  FROM attack_event e
  JOIN attack_type t ON t.type_id = e.type_id
  WHERE e.event_time >= p_from
    AND e.event_time <  p_to + INTERVAL 1 DAY
  GROUP BY t.type_name
  ORDER BY attacks DESC, t.type_name;
END //
DELIMITER ;

CALL sp_attack_report('2026-10-01', '2026-10-15');
