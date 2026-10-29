-- the indicator versions we currently believe (not yet superseded); analysts read IOCs only through this
CREATE VIEW v_ioc AS
SELECT ioc_version_id, ioc_type, ioc_value, actor_id, malware_id,
       valid_from, valid_to, recorded_from
FROM ioc
WHERE recorded_to IS NULL;

SELECT ioc_type, COUNT(*) AS indicators FROM v_ioc GROUP BY ioc_type ORDER BY ioc_type;
