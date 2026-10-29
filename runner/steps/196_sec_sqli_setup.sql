-- SQL injection demo. Both procedures let an analyst search HIS incidents by title.
-- The unsafe one pastes the text into the SQL; the safe one passes it as a parameter.
DELIMITER //
CREATE PROCEDURE sp_search_incidents_unsafe(IN p_text VARCHAR(100))
BEGIN
  DECLARE v_me INT;
  SELECT analyst_id INTO v_me FROM analyst
   WHERE email = CONCAT(SUBSTRING_INDEX(USER(), '@', 1), '@sentinelx.in');
  SET @sql = CONCAT('SELECT incident_id, title, priority, status, assigned_to FROM incident ',
                    'WHERE assigned_to = ', COALESCE(v_me, -1),
                    ' AND title LIKE ''%', p_text, '%''');
  PREPARE st FROM @sql;
  EXECUTE st;
  DEALLOCATE PREPARE st;
END //

CREATE PROCEDURE sp_search_incidents(IN p_text VARCHAR(100))
BEGIN
  SELECT analyst_id INTO @me FROM analyst
   WHERE email = CONCAT(SUBSTRING_INDEX(USER(), '@', 1), '@sentinelx.in');
  SET @text = p_text;
  PREPARE st FROM 'SELECT incident_id, title, priority, status, assigned_to FROM incident
                   WHERE assigned_to = ? AND title LIKE CONCAT(''%'', ?, ''%'')';
  EXECUTE st USING @me, @text;
  DEALLOCATE PREPARE st;
END //
DELIMITER ;

GRANT EXECUTE ON PROCEDURE sentinelx.sp_search_incidents_unsafe TO 'sx_analyst';
GRANT EXECUTE ON PROCEDURE sentinelx.sp_search_incidents        TO 'sx_analyst';
