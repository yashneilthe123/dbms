-- the vulnerable procedure is removed once demonstrated
DROP PROCEDURE sp_search_incidents_unsafe;
SHOW PROCEDURE STATUS WHERE Db = 'sentinelx' AND Name LIKE 'sp_search%';
