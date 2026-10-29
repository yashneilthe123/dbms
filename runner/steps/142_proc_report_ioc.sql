-- analysts add indicators through this procedure instead of writing to the ioc table;
-- recorded_from is always "now", so nobody can backdate when we learned about it
DELIMITER //
CREATE PROCEDURE sp_report_ioc(IN p_type VARCHAR(6), IN p_value VARCHAR(255),
                               IN p_valid_from DATETIME, IN p_actor INT, IN p_malware INT)
BEGIN
  INSERT INTO ioc (ioc_type, ioc_value, actor_id, malware_id, valid_from, recorded_from)
  VALUES (p_type, p_value, p_actor, p_malware, p_valid_from, NOW());
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
