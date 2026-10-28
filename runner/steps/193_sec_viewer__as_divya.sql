SELECT CURRENT_USER() AS logged_in_as, CURRENT_ROLE() AS active_role;

SELECT hostname, criticality, attacks, not_blocked, open_vulns
FROM v_asset_risk
ORDER BY not_blocked DESC
LIMIT 3;

CALL sp_attack_report('2026-10-20', '2026-10-28');

SELECT * FROM attack_event LIMIT 1;
DELETE FROM attack_event WHERE event_id = 1;
UPDATE v_asset_risk SET criticality = 1 WHERE asset_id = 1;
