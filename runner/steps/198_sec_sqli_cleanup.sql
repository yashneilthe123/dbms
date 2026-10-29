-- the vulnerable procedure is removed once demonstrated
DROP PROCEDURE sp_search_incidents_unsafe;
SELECT routine_name, security_type FROM information_schema.routines
WHERE routine_schema = 'sentinelx' AND routine_name LIKE 'sp_search%';
