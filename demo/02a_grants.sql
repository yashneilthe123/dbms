-- Demo step 2a (root): the role matrix, and REVOKE before/after.
SHOW GRANTS FOR 'sx_admin';
SHOW GRANTS FOR 'sx_analyst';
SHOW GRANTS FOR 'sx_viewer';

-- a user's own grants only name the role; USING expands it
SHOW GRANTS FOR 'rahul.mehta'@'localhost';
SHOW GRANTS FOR 'rahul.mehta'@'localhost' USING 'sx_analyst';

-- REVOKE: give the viewer one extra table, then take it away again.
-- Check the "after" from a NEW divya session: open sessions keep some privileges until they reconnect.
GRANT SELECT ON sentinelx.network_log TO 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';
REVOKE SELECT ON sentinelx.network_log FROM 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';

-- how MySQL stores the passwords: salted SHA-256 (caching_sha2_password), never the password itself
SELECT user, host, plugin, account_locked,
       JSON_EXTRACT(user_attributes, '$.Password_locking') AS lockout_rule
FROM mysql.user WHERE user IN ('ananya.rao', 'rahul.mehta', 'divya.iyer');
