-- Run as root if a demo account got locked (3 wrong passwords lock it for a day)
-- or if a concurrency rehearsal left incident 6 changed.
ALTER USER 'ananya.rao'@'localhost', 'rahul.mehta'@'localhost', 'divya.iyer'@'localhost' ACCOUNT UNLOCK;

UPDATE sentinelx.incident SET priority = 'MEDIUM', status = 'OPEN' WHERE incident_id = 6;

SELECT user, account_locked FROM mysql.user
WHERE user IN ('ananya.rao', 'rahul.mehta', 'divya.iyer');
