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
