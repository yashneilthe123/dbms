SET @tests_pass = 0, @tests_fail = 0;
CALL sp_expect_error('V01', 'viewer can read the risk view',
  "DO (SELECT COUNT(*) FROM v_asset_risk)", 0);
CALL sp_expect_error('V02', 'viewer cannot read a base table',
  "DO (SELECT COUNT(*) FROM attack_event)", 1142);
CALL sp_expect_error('V03', 'viewer cannot delete',
  "DELETE FROM attack_event WHERE event_id = 1", 1142);
CALL sp_expect_error('V04', 'viewer cannot run the assign procedure',
  "CALL sp_assign_incident(9, 5)", 1370);
CALL sp_expect_error('V05', 'viewer cannot update the risk view',
  "UPDATE v_asset_risk SET criticality = 1 WHERE asset_id = 1", 1142);
SELECT @tests_pass AS passed, @tests_fail AS failed;
