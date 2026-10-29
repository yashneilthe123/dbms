-- Short queries to back up viva answers on our own data (root session).
-- Each block is numbered like docs/viva_map.md.
USE sentinelx;

-- Q2  FD mitre_technique -> type_id holds: no technique maps to two attack types (empty result)
SELECT mitre_technique, COUNT(DISTINCT type_id) AS types
FROM attack_type GROUP BY mitre_technique HAVING COUNT(DISTINCT type_id) > 1;

-- Q3  update anomaly if attack_event and asset were one table
CREATE TEMPORARY TABLE flat_attack AS
SELECT e.event_id, a.hostname, a.criticality, e.severity
FROM attack_event e JOIN asset a ON a.asset_id = e.asset_id;
UPDATE flat_attack SET criticality = 1 WHERE event_id = 1;     -- someone fixes "one row"
SELECT hostname, GROUP_CONCAT(DISTINCT criticality) AS criticality_values
FROM flat_attack WHERE hostname = 'web-01' GROUP BY hostname;  -- web-01 now has two criticalities
DROP TEMPORARY TABLE flat_attack;

-- Q9  CHECK lets NULL through: CHECK gives UNKNOWN for NULL, and UNKNOWN passes
SELECT actor_name, origin_country FROM threat_actor WHERE origin_country IS NULL;

-- Q10 TRUNCATE is refused on a table other tables point to
TRUNCATE TABLE asset;                                           -- ERROR 1701

-- Q11 the row an INNER JOIN would lose
SELECT a.hostname, COUNT(e.event_id) AS attacks
FROM asset a LEFT JOIN attack_event e ON e.asset_id = a.asset_id
GROUP BY a.hostname HAVING attacks = 0;                         -- ws-dev-01

-- Q17 COUNT(*) vs COUNT(col) vs COUNT(DISTINCT col) on the 30 seed attacks: 30, 18, 7
SELECT COUNT(*) AS all_rows, COUNT(malware_id) AS with_malware, COUNT(DISTINCT malware_id) AS distinct_malware
FROM attack_event WHERE event_id <= 30;

-- Q25/Q26 isolation level and durability settings
SELECT @@transaction_isolation, @@innodb_flush_log_at_trx_commit, @@sync_binlog, @@innodb_doublewrite;

-- Q30 sp_escalate_incidents (a cursor) as ONE set-based UPDATE with the same rule; rolled back
START TRANSACTION;
UPDATE incident i
JOIN (SELECT ie.incident_id, MAX(e.severity) AS worst
      FROM incident_event ie JOIN attack_event e ON e.event_id = ie.event_id
      GROUP BY ie.incident_id) w ON w.incident_id = i.incident_id
SET i.priority = CASE WHEN w.worst >= 10 THEN 'CRITICAL'
                      WHEN w.worst >= 8 AND i.priority IN ('LOW', 'MEDIUM') THEN 'HIGH'
                      ELSE i.priority END
WHERE i.status <> 'CLOSED';
ROLLBACK;

-- Q33 how account passwords are stored
SELECT user, plugin, LEFT(authentication_string, 7) AS hash_prefix
FROM mysql.user WHERE user IN ('ananya.rao', 'rahul.mehta', 'divya.iyer');
-- $A$005$ = caching_sha2_password: SHA-256, salted, 5,000 rounds
