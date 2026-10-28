-- SentinelX Review 2: Cursors
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- cursor_escalate ----
DELIMITER //
CREATE PROCEDURE sp_escalate_incidents()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_id INT;
  DECLARE v_pri VARCHAR(8);
  DECLARE v_max TINYINT;
  DECLARE cur CURSOR FOR
    SELECT i.incident_id, i.priority, MAX(e.severity)
    FROM incident i
    JOIN incident_event ie ON ie.incident_id = i.incident_id
    JOIN attack_event e    ON e.event_id     = ie.event_id
    WHERE i.status <> 'CLOSED'
    GROUP BY i.incident_id, i.priority
    ORDER BY i.incident_id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  DROP TEMPORARY TABLE IF EXISTS escalation_log;
  CREATE TEMPORARY TABLE escalation_log (
    incident_id INT, old_priority VARCHAR(8), new_priority VARCHAR(8), worst_severity TINYINT);

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO v_id, v_pri, v_max;
    IF done THEN LEAVE read_loop; END IF;
    IF v_max >= 10 AND v_pri <> 'CRITICAL' THEN
      UPDATE incident SET priority = 'CRITICAL' WHERE incident_id = v_id;
      INSERT INTO escalation_log VALUES (v_id, v_pri, 'CRITICAL', v_max);
    ELSEIF v_max >= 8 AND v_pri IN ('LOW', 'MEDIUM') THEN
      UPDATE incident SET priority = 'HIGH' WHERE incident_id = v_id;
      INSERT INTO escalation_log VALUES (v_id, v_pri, 'HIGH', v_max);
    END IF;
  END LOOP;
  CLOSE cur;

  SELECT * FROM escalation_log;
END //
DELIMITER ;

CALL sp_escalate_incidents();


-- ---- cursor_asset_risk ----
DELIMITER //
CREATE PROCEDURE sp_asset_risk_report()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE v_id INT;
  DECLARE v_host VARCHAR(63);
  DECLARE v_score INT;
  DECLARE cur CURSOR FOR SELECT asset_id, hostname FROM asset ORDER BY asset_id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  DROP TEMPORARY TABLE IF EXISTS risk_report;
  CREATE TEMPORARY TABLE risk_report (hostname VARCHAR(63), risk_score INT, band VARCHAR(8));

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO v_id, v_host;
    IF done THEN LEAVE read_loop; END IF;
    SET v_score = fn_asset_risk(v_id);
    INSERT INTO risk_report VALUES (v_host, v_score,
      CASE WHEN v_score >= 60 THEN 'HIGH' WHEN v_score >= 30 THEN 'MEDIUM' ELSE 'LOW' END);
  END LOOP;
  CLOSE cur;

  SELECT * FROM risk_report ORDER BY risk_score DESC, hostname;
END //
DELIMITER ;

CALL sp_asset_risk_report();
