-- SentinelX Review 2: User-defined functions
-- MySQL 8.0 (tested on 8.0.46)

USE sentinelx;


-- ---- func_severity_label ----
DELIMITER //
CREATE FUNCTION fn_severity_label(p_cvss DECIMAL(3,1))
RETURNS VARCHAR(8)
DETERMINISTIC NO SQL
BEGIN
  RETURN CASE WHEN p_cvss >= 9 THEN 'CRITICAL'
              WHEN p_cvss >= 7 THEN 'HIGH'
              WHEN p_cvss >= 4 THEN 'MEDIUM'
              ELSE 'LOW' END;
END //
DELIMITER ;

SELECT cve_id, cvss, fn_severity_label(cvss) AS label
FROM vulnerability
ORDER BY cvss DESC, cve_id;


-- ---- func_asset_risk ----
DELIMITER //
CREATE FUNCTION fn_asset_risk(p_asset INT)
RETURNS INT
READS SQL DATA
BEGIN
  DECLARE v_crit, v_open, v_hits INT DEFAULT 0;
  SELECT criticality INTO v_crit FROM asset WHERE asset_id = p_asset;
  SELECT COUNT(*) INTO v_open FROM asset_vulnerability
   WHERE asset_id = p_asset AND patched_at IS NULL;
  SELECT COUNT(*) INTO v_hits FROM attack_event
   WHERE asset_id = p_asset AND blocked = 0;
  RETURN v_crit * 10 + v_open * 5 + v_hits * 2;
END //
DELIMITER ;

SELECT hostname, criticality, fn_asset_risk(asset_id) AS risk_score
FROM asset
ORDER BY risk_score DESC, hostname
LIMIT 5;
