SET @tests_pass = 0, @tests_fail = 0;
CALL sp_expect_error('S01', 'analyst cannot read a base table',
  "DO (SELECT COUNT(*) FROM attack_event)", 1142);
CALL sp_expect_error('S02', 'analyst can read through the view',
  "DO (SELECT COUNT(*) FROM v_attack_details)", 0);
CALL sp_expect_error('S03', 'analyst cannot run DDL',
  "DROP TABLE asset", 1142);
CALL sp_check('S04', 'v_my_incidents shows only his own rows', '0',
  (SELECT COUNT(*) FROM v_my_incidents WHERE assigned_to <> 2));
CALL sp_expect_error('S05', 'WITH CHECK OPTION blocks handing an incident over',
  "UPDATE v_my_incidents SET assigned_to = 3 WHERE incident_id = 7", 1369);
CALL sp_expect_error('S06', 'procedure blocks giving his incident away',
  "CALL sp_assign_incident(7, 3)", 1644);
CALL sp_expect_error('S07', "procedure blocks taking a colleague's incident",
  "CALL sp_assign_incident(6, 2)", 1644);
CALL sp_expect_error('S08', 'procedure lets him claim an unassigned incident',
  "CALL sp_assign_incident(9, 2)", 0);
CALL sp_expect_error('S09', 'analyst cannot write the ioc table directly',
  "INSERT INTO ioc (ioc_type, ioc_value, valid_from) VALUES ('ip', '192.0.2.200', '2026-10-01')", 1142);
CALL sp_expect_error('S10', 'analyst reports an IOC through the procedure',
  "CALL sp_report_ioc('ip', '192.0.2.200', '2026-10-01', NULL, NULL)", 0);
CALL sp_expect_error('S11', 'analyst cannot read the audit trail',
  "DO (SELECT COUNT(*) FROM incident_audit)", 1142);
-- try to backdate an indicator by moving this session's clock
SET timestamp = UNIX_TIMESTAMP('2026-01-01 00:00:00');
CALL sp_report_ioc('ip', '192.0.2.201', '2026-10-01', NULL, NULL);
SET timestamp = DEFAULT;
CALL sp_check('S12', 'SET timestamp cannot backdate a reported IOC', '0',
  (SELECT COUNT(*) FROM v_ioc WHERE ioc_value = '192.0.2.201' AND recorded_from < '2026-02-01'));
SELECT @tests_pass AS passed, @tests_fail AS failed;
