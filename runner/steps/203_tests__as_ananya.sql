SET @tests_pass = 0, @tests_fail = 0;
CALL sp_expect_error('A01', 'admin can change incident data',
  "UPDATE incident SET priority = 'HIGH' WHERE incident_id = 9", 0);
CALL sp_check('A02', '... and the audit trail names the admin', 'ananya.rao',
  (SELECT SUBSTRING_INDEX(changed_by, '@', 1) FROM incident_audit ORDER BY audit_id DESC LIMIT 1));
CALL sp_expect_error('A03', 'admin cannot delete audit rows',
  "DELETE FROM incident_audit WHERE audit_id = 1", 1644);
CALL sp_expect_error('A04', 'admin cannot TRUNCATE the audit trail',
  "TRUNCATE TABLE incident_audit", 1142);
CALL sp_expect_error('A05', 'admin cannot change the schema',
  "ALTER TABLE incident ADD COLUMN note VARCHAR(10)", 1142);
SELECT @tests_pass AS passed, @tests_fail AS failed;
