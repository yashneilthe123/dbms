GRANT SELECT ON sentinelx.network_log TO 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';

REVOKE SELECT ON sentinelx.network_log FROM 'sx_viewer';
SHOW GRANTS FOR 'sx_viewer';
