-- SentinelX Review 2: Stored procedures
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- proc_assign_incident ----
DELIMITER //
CREATE PROCEDURE sp_assign_incident(IN p_incident INT, IN p_analyst INT)
BEGIN
  DECLARE v_status VARCHAR(15);
  DECLARE v_owner  INT;
  DECLARE v_role   VARCHAR(10);
  DECLARE v_caller_id   INT;
  DECLARE v_caller_role VARCHAR(10);
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  -- this procedure runs as its DEFINER (root), so CURRENT_USER() is root;
  -- USER() is the account that called it. Strip the host, map it to an analyst.
  SELECT analyst_id, role INTO v_caller_id, v_caller_role FROM analyst
   WHERE email = CONCAT(SUBSTRING_INDEX(USER(), '@', 1), '@sentinelx.in');
  IF v_caller_role IS NULL AND SUBSTRING_INDEX(USER(), '@', 1) <> 'root' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Caller is not a registered analyst';
  END IF;

  START TRANSACTION;
  SELECT status, assigned_to INTO v_status, v_owner FROM incident
   WHERE incident_id = p_incident FOR UPDATE;
  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No such incident';
  ELSEIF v_status = 'CLOSED' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Incident is already closed';
  END IF;

  -- analysts may only claim an unassigned incident (or one they own) for themselves
  IF v_caller_role = 'analyst'
     AND (p_analyst <> v_caller_id OR (v_owner IS NOT NULL AND v_owner <> v_caller_id)) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Analysts can only claim unassigned incidents for themselves';
  ELSEIF v_caller_role = 'viewer' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Viewers cannot assign incidents';
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


-- ---- proc_report_ioc ----
-- analysts add indicators through this procedure instead of writing to the ioc table;
-- recorded_from is the real clock (SYSDATE, not NOW: NOW follows a session's SET timestamp,
-- which any user may change), so an analyst cannot backdate when we learned about it
DELIMITER //
CREATE PROCEDURE sp_report_ioc(IN p_type VARCHAR(6), IN p_value VARCHAR(255),
                               IN p_valid_from DATETIME, IN p_actor INT, IN p_malware INT)
BEGIN
  INSERT INTO ioc (ioc_type, ioc_value, actor_id, malware_id, valid_from, recorded_from)
  VALUES (p_type, p_value, p_actor, p_malware, p_valid_from, SYSDATE());
  SELECT ioc_version_id, ioc_type, ioc_value, valid_from, recorded_from
  FROM ioc WHERE ioc_version_id = LAST_INSERT_ID();
END //

-- who am I, and whose rights am I using? Inside a DEFINER routine the two differ.
CREATE PROCEDURE sp_whoami()
BEGIN
  SELECT USER() AS called_by, CURRENT_USER() AS running_with_rights_of;
END //
DELIMITER ;

CALL sp_whoami();
