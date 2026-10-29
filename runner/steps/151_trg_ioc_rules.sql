DELIMITER //
CREATE TRIGGER trg_ioc_no_overlap
BEFORE INSERT ON ioc
FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM ioc
             WHERE ioc_type = NEW.ioc_type
               AND ioc_value = NEW.ioc_value
               AND recorded_to IS NULL               -- versions closed with recorded_to are history
               AND (valid_to IS NULL OR valid_to > NEW.valid_from)
               AND (NEW.valid_to IS NULL OR NEW.valid_to > valid_from)) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'An overlapping version of this indicator already exists';
  END IF;
END //

CREATE TRIGGER trg_ioc_no_delete
BEFORE DELETE ON ioc
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Indicator history is append-only; close it with recorded_to instead';
END //

CREATE TRIGGER trg_ioc_retro_hunt
AFTER INSERT ON ioc
FOR EACH ROW
BEGIN
  DECLARE v_run, v_hits, v_assets INT;
  IF NEW.ioc_type = 'ip' THEN
    INSERT INTO retro_hunt_run (ioc_version_id, started_at)
    VALUES (NEW.ioc_version_id, NEW.recorded_from);
    SET v_run = LAST_INSERT_ID();

    -- every old log line from this IP while it was hostile but not yet known
    INSERT INTO retro_hit (run_id, log_id)
    SELECT v_run, log_id
    FROM network_log
    WHERE src_ip = NEW.ioc_value
      AND log_time >= NEW.valid_from
      AND log_time <  NEW.recorded_from
      AND (NEW.valid_to IS NULL OR log_time < NEW.valid_to);
    SET v_hits = ROW_COUNT();

    IF v_hits > 0 THEN
      SET v_assets = (SELECT COUNT(DISTINCT l.dst_asset_id)
                      FROM retro_hit h JOIN network_log l ON l.log_id = h.log_id
                      WHERE h.run_id = v_run);
      INSERT INTO incident (title, priority, status, opened_at)
      VALUES (CONCAT('Retro-hunt: ', NEW.ioc_value, ' hit ', v_assets,
                     ' assets ', v_hits, ' times'),
              IF(v_assets >= 3, 'CRITICAL', 'HIGH'), 'OPEN', NEW.recorded_from);
      UPDATE retro_hunt_run SET incident_id = LAST_INSERT_ID() WHERE run_id = v_run;
    END IF;
  END IF;
END //
DELIMITER ;

SHOW TRIGGERS;
