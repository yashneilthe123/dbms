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
