INSERT INTO asset (hostname, ip_address, asset_type, criticality) VALUES ('tmp-scan-01', '10.0.9.99', 'workstation', 1);
SELECT asset_id, hostname FROM asset WHERE hostname = 'tmp-scan-01';
DELETE FROM asset WHERE hostname = 'tmp-scan-01';
SELECT COUNT(*) AS assets_left FROM asset;
