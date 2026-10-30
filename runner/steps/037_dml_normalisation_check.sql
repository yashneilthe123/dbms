-- functional dependency mitre_technique -> type_id: no technique maps to two attack types (empty result)
SELECT mitre_technique, COUNT(DISTINCT type_id) AS types
FROM attack_type GROUP BY mitre_technique HAVING COUNT(DISTINCT type_id) > 1;

-- update anomaly: copy attacks and their asset's criticality into one flat table, as before 3NF
CREATE TEMPORARY TABLE flat_attack AS
SELECT e.event_id, a.hostname, a.criticality FROM attack_event e JOIN asset a ON a.asset_id = e.asset_id;
UPDATE flat_attack SET criticality = 1 WHERE event_id = 1;
SELECT hostname, GROUP_CONCAT(DISTINCT criticality ORDER BY criticality) AS criticality_values
FROM flat_attack WHERE hostname = 'web-01' GROUP BY hostname;
DROP TEMPORARY TABLE flat_attack;

-- in the normalised schema the fact is stored once, so it cannot disagree with itself
SELECT hostname, criticality FROM asset WHERE hostname = 'web-01';
