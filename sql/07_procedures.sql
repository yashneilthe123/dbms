-- SentinelX Review 2: Stored procedures
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- proc_assign_incident ----
DELIMITER //
CREATE PROCEDURE sp_assign_incident(IN p_incident INT, IN p_analyst INT)
BEGIN
  DECLARE v_status VARCHAR(15);
  DECLARE v_role   VARCHAR(10);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;
  SELECT status INTO v_status FROM incident
   WHERE incident_id = p_incident FOR UPDATE;
  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No such incident';
  ELSEIF v_status = 'CLOSED' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Incident is already closed';
  END IF;

  SELECT role INTO v_role FROM analyst WHERE analyst_id = p_analyst;
  IF v_role IS NULL OR v_role = 'viewer' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only analysts or admins can own incidents';
  END IF;

  UPDATE incident
     SET assigned_to = p_analyst,
         status = IF(status = 'OPEN', 'INVESTIGATING', status)
   WHERE incident_id = p_incident;
  COMMIT;

  SELECT incident_id, status, assigned_to FROM incident WHERE incident_id = p_incident;
END //
DELIMITER ;

CALL sp_assign_incident(5, 6);
CALL sp_assign_incident(1, 4);
CALL sp_assign_incident(6, 5);


-- ---- proc_attack_report ----
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
