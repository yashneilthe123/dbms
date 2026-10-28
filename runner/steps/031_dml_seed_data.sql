INSERT INTO vulnerability (cve_id, cvss, published) VALUES
  ('CVE-2024-3400', 10.0, '2024-04-12'),
  ('CVE-2023-4966', 9.4, '2023-10-10'),
  ('CVE-2021-44228', 10.0, '2021-12-10'),
  ('CVE-2023-34362', 9.8, '2023-06-02'),
  ('CVE-2024-6387', 8.1, '2024-07-01'),
  ('CVE-2023-44487', 7.5, '2023-10-10'),
  ('CVE-2022-22965', 9.8, '2022-04-01'),
  ('CVE-2019-0708', 9.8, '2019-05-16'),
  ('CVE-2023-48795', 5.9, '2023-12-18');

INSERT INTO asset_vulnerability (asset_id, cve_id, detected_at, patched_at) VALUES
  (1, 'CVE-2021-44228', '2026-09-02', '2026-09-10'),
  (1, 'CVE-2023-44487', '2026-09-15', NULL),
  (2, 'CVE-2022-22965', '2026-09-05', NULL),
  (3, 'CVE-2023-34362', '2026-08-20', '2026-09-01'),
  (4, 'CVE-2023-4966', '2026-09-12', NULL),
  (5, 'CVE-2023-48795', '2026-09-20', NULL),
  (6, 'CVE-2019-0708', '2026-08-15', NULL),
  (9, 'CVE-2024-3400', '2026-09-01', NULL),
  (9, 'CVE-2024-6387', '2026-09-03', '2026-09-25');

INSERT INTO attack_type (type_id, type_name, mitre_technique, base_severity) VALUES
  (1, 'Brute Force', 'T1110', 6),
  (2, 'Phishing', 'T1566', 5),
  (3, 'Exploit Public-Facing App', 'T1190', 8),
  (4, 'Port Scan', 'T1046', 3),
  (5, 'Ransomware', 'T1486', 10),
  (6, 'DDoS', 'T1498', 7),
  (7, 'Credential Dumping', 'T1003', 9),
  (8, 'Command and Control', 'T1071', 7);

INSERT INTO mitigation (type_id, step_no, action) VALUES
  (1, 1, 'Block the source IP at the firewall'),
  (1, 2, 'Lock the targeted accounts'),
  (1, 3, 'Enforce MFA on the login page'),
  (2, 1, 'Quarantine the email in all mailboxes'),
  (2, 2, 'Reset the password of the user who clicked'),
  (2, 3, 'Block the sender domain'),
  (3, 1, 'Isolate the host from the network'),
  (3, 2, 'Apply the vendor patch'),
  (3, 3, 'Scan the host for web shells'),
  (4, 1, 'Rate-limit the source IP'),
  (5, 1, 'Disconnect the host from the network'),
  (5, 2, 'Restore data from the offline backup'),
  (5, 3, 'Reset all admin credentials'),
  (6, 1, 'Turn on upstream traffic scrubbing'),
  (6, 2, 'Rate-limit HTTP/2 streams per client'),
  (7, 1, 'Reset domain admin passwords'),
  (7, 2, 'Rotate the krbtgt key twice'),
  (8, 1, 'Sinkhole the C2 domain');

INSERT INTO threat_actor (actor_id, actor_name, origin_country, motive) VALUES
  (1, 'Crimson Lynx', 'RU', 'financial'),
  (2, 'Silent Monsoon', 'CN', 'espionage'),
  (3, 'Byte Bandits', NULL, 'hacktivism'),
  (4, 'Iron Kestrel', 'KP', 'sabotage'),
  (5, 'Ghost Parrot', 'BR', 'financial'),
  (6, 'Quiet Willow', 'IR', 'espionage');

INSERT INTO malware (malware_id, malware_name, family, sha256, actor_id, cluster_id) VALUES
  (1, 'LynxLocker', 'Locker', '31daf39d2783c1d131fac1cc54f9165519dae4f9a22164b12f0bef5621a4e7fa', 1, 1),
  (2, 'LynxLoader', 'Loader', '6f7bffacc2f9d7b143cb753a90f80a48793638a0f4c1d4ad556eb1bd64a8e603', 1, 2),
  (3, 'MonsoonRAT', 'RAT', 'f968c5ac3830e7a862da805cd869db72875cc0ecaa2c4f490a0037c7bad431d2', 2, 3),
  (4, 'MonsoonStealer', 'Stealer', '7061e84eb05a9300d1d5eb82886ef767266645289dc0096eb3d7cebee96256f7', 2, 2),
  (5, 'KestrelWiper', 'Wiper', '185a5b513e09e1d5939f984e6219e7855ce4d30a401e328a259f258644e86ee6', 4, 1),
  (6, 'ParrotBot', 'Botnet', 'd6899f70b14408b620ec88b1bff877f15a6620276f9f19149ae3f028f62ecb12', 5, 4),
  (7, 'OrphanMiner', 'Miner', '5ffb17695d02253028e32068b5d60383b4bc7a55aa24efe1d77629676ae64b74', NULL, 4),
  (8, 'WillowRAT', 'RAT', '80224518b2845efe9cee48e30b16a3a5e5791690310f10c1125a4b0a36bb004f', 6, 3);

INSERT INTO attack_event (event_id, event_time, src_ip, src_country, asset_id, type_id, actor_id, malware_id, cve_id, severity, blocked, predicted_severity) VALUES
  (1, '2026-10-01 02:14:00', '198.51.100.23', 'RU', 1, 1, 1, NULL, NULL, 6, 1, 'MEDIUM'),
  (2, '2026-10-01 02:20:00', '198.51.100.23', 'RU', 1, 1, 1, NULL, NULL, 7, 0, 'HIGH'),
  (3, '2026-10-02 11:05:00', '203.0.113.200', 'US', 1, 4, NULL, NULL, NULL, 3, 1, 'LOW'),
  (4, '2026-10-03 09:30:00', '203.0.113.10', 'CN', 4, 2, 2, 3, NULL, 6, 0, 'MEDIUM'),
  (5, '2026-10-04 22:10:00', '203.0.113.10', 'CN', 4, 3, 2, 3, 'CVE-2023-4966', 9, 0, 'CRITICAL'),
  (6, '2026-10-05 01:00:00', '192.0.2.50', 'KP', 3, 3, 4, NULL, 'CVE-2023-34362', 9, 1, 'CRITICAL'),
  (7, '2026-10-05 01:45:00', '192.0.2.50', 'KP', 3, 7, 4, 5, NULL, 9, 0, 'CRITICAL'),
  (8, '2026-10-06 14:20:00', '198.51.100.88', 'BR', 2, 6, 5, 6, NULL, 7, 1, 'HIGH'),
  (9, '2026-10-06 14:25:00', '198.51.100.88', 'BR', 2, 6, 5, 6, NULL, 7, 1, 'HIGH'),
  (10, '2026-10-07 03:33:00', '198.51.100.45', 'RU', 2, 3, 1, 2, 'CVE-2022-22965', 8, 0, 'HIGH'),
  (11, '2026-10-07 04:10:00', '198.51.100.45', 'RU', 2, 5, 1, 1, NULL, 10, 0, 'CRITICAL'),
  (12, '2026-10-08 10:00:00', '203.0.113.200', 'US', 5, 4, NULL, NULL, NULL, 2, 1, 'LOW'),
  (13, '2026-10-08 10:02:00', '203.0.113.200', 'US', 9, 4, NULL, NULL, NULL, 3, 1, 'LOW'),
  (14, '2026-10-09 16:45:00', '192.0.2.77', 'NL', 1, 6, 3, NULL, 'CVE-2023-44487', 8, 0, 'HIGH'),
  (15, '2026-10-10 08:15:00', '203.0.113.11', 'CN', 9, 3, 2, 4, 'CVE-2024-3400', 10, 0, 'CRITICAL'),
  (16, '2026-10-10 08:40:00', '203.0.113.11', 'CN', 9, 7, 2, 4, NULL, 9, 0, 'CRITICAL'),
  (17, '2026-10-11 12:00:00', '198.51.100.23', 'RU', 6, 2, 1, 2, NULL, 5, 1, 'MEDIUM'),
  (18, '2026-10-12 19:30:00', '203.0.113.99', 'IN', 8, 1, NULL, 7, NULL, 4, 0, 'MEDIUM'),
  (19, '2026-10-13 07:05:00', '198.51.100.88', 'BR', 1, 6, 5, 6, NULL, 6, 1, 'MEDIUM'),
  (20, '2026-10-14 23:50:00', '192.0.2.50', 'KP', 7, 2, 4, NULL, NULL, 6, 1, 'MEDIUM'),
  (21, '2026-10-15 05:20:00', '203.0.113.10', 'CN', 3, 3, 2, 3, 'CVE-2021-44228', 8, 1, 'HIGH'),
  (22, '2026-10-16 13:13:00', '203.0.113.200', 'US', 4, 4, NULL, NULL, NULL, 2, 1, 'LOW'),
  (23, '2026-10-18 02:02:00', '198.51.100.45', 'RU', 1, 1, 1, NULL, NULL, 7, 0, 'HIGH'),
  (24, '2026-10-18 02:05:00', '198.51.100.45', 'RU', 1, 1, 1, NULL, NULL, 8, 0, 'HIGH'),
  (25, '2026-10-20 18:00:00', '192.0.2.77', 'NL', 2, 6, 3, NULL, NULL, 7, 1, NULL),
  (26, '2026-10-21 09:09:00', '203.0.113.99', 'IN', 8, 1, NULL, 7, NULL, 4, 1, NULL),
  (27, '2026-10-22 21:30:00', '198.51.100.88', 'BR', 7, 2, 5, 6, NULL, 5, 1, NULL),
  (28, '2026-10-24 03:15:00', '203.0.113.11', 'CN', 5, 3, 2, 4, 'CVE-2023-48795', 7, 0, NULL),
  (29, '2026-10-25 11:11:00', '198.51.100.23', 'RU', 9, 3, 1, 2, 'CVE-2024-6387', 9, 1, NULL),
  (30, '2026-10-26 15:40:00', '192.0.2.50', 'KP', 3, 5, 4, 5, NULL, 10, 0, NULL);

INSERT INTO analyst (analyst_id, full_name, email, role) VALUES
  (1, 'Ananya Rao', 'ananya.rao@sentinelx.in', 'admin'),
  (2, 'Rahul Mehta', 'rahul.mehta@sentinelx.in', 'analyst'),
  (3, 'Priya Nair', 'priya.nair@sentinelx.in', 'analyst'),
  (4, 'Karan Shah', 'karan.shah@sentinelx.in', 'analyst'),
  (5, 'Divya Iyer', 'divya.iyer@sentinelx.in', 'viewer'),
  (6, 'Arjun Das', 'arjun.das@sentinelx.in', 'analyst');

INSERT INTO incident (incident_id, title, priority, status, assigned_to, opened_at, closed_at) VALUES
  (1, 'Brute force on web-01 from 198.51.100.23', 'HIGH', 'CLOSED', 2, '2026-10-01 02:25:00', '2026-10-01 09:40:00'),
  (2, 'Citrix Bleed exploit on mail-01', 'CRITICAL', 'CLOSED', 3, '2026-10-04 22:20:00', '2026-10-06 18:00:00'),
  (3, 'Iron Kestrel intrusion on db-01', 'HIGH', 'CONTAINED', 2, '2026-10-05 01:10:00', NULL),
  (4, 'Retro-hunt: 198.51.100.45 hit 2 assets 4 times', 'CRITICAL', 'INVESTIGATING', 4, '2026-10-12 08:00:00', NULL),
  (5, 'Retro-hunt: 203.0.113.11 hit 2 assets 4 times', 'CRITICAL', 'OPEN', NULL, '2026-10-20 09:00:00', NULL),
  (6, 'DDoS waves on web servers', 'MEDIUM', 'OPEN', 3, '2026-10-20 18:10:00', NULL),
  (7, 'Brute force on web-01 from 198.51.100.45', 'HIGH', 'INVESTIGATING', 2, '2026-10-18 02:10:00', NULL);

INSERT INTO incident_event (incident_id, event_id) VALUES
  (1, 1),
  (1, 2),
  (2, 4),
  (2, 5),
  (3, 6),
  (3, 7),
  (3, 30),
  (4, 10),
  (4, 11),
  (5, 15),
  (5, 16),
  (6, 8),
  (6, 9),
  (6, 14),
  (6, 19),
  (6, 25),
  (7, 23),
  (7, 24);

INSERT INTO ioc (ioc_version_id, ioc_type, ioc_value, actor_id, malware_id, valid_from, valid_to, recorded_from) VALUES
  (1, 'ip', '198.51.100.23', 1, NULL, '2026-09-25 00:00:00', NULL, '2026-09-28 10:00:00'),
  (2, 'ip', '198.51.100.45', 1, 1, '2026-10-01 00:00:00', NULL, '2026-10-12 08:00:00'),
  (3, 'ip', '203.0.113.10', 2, 3, '2026-09-30 00:00:00', NULL, '2026-10-02 09:00:00'),
  (4, 'ip', '203.0.113.11', 2, 4, '2026-10-05 00:00:00', NULL, '2026-10-20 09:00:00'),
  (5, 'ip', '192.0.2.50', 4, 5, '2026-10-01 00:00:00', NULL, '2026-10-06 12:00:00'),
  (6, 'ip', '198.51.100.88', 5, 6, '2026-10-01 00:00:00', NULL, '2026-10-01 06:00:00'),
  (7, 'domain', 'lynx-update.example', 1, 2, '2026-09-20 00:00:00', NULL, '2026-10-08 15:00:00'),
  (8, 'hash', 'f968c5ac3830e7a862da805cd869db72875cc0ecaa2c4f490a0037c7bad431d2', 2, 3, '2026-09-15 00:00:00', NULL, '2026-09-18 11:00:00'),
  (9, 'url', 'http://parrot-cdn.example/b.bin', 5, 6, '2026-10-01 00:00:00', NULL, '2026-10-15 16:00:00'),
  (10, 'ip', '192.0.2.77', 3, NULL, '2026-10-08 00:00:00', NULL, '2026-10-10 14:00:00'),
  (11, 'ip', '203.0.113.250', NULL, NULL, '2026-10-01 00:00:00', NULL, '2026-10-02 07:00:00'),
  (12, 'domain', 'monsoon-mail.example', 2, 3, '2026-09-28 00:00:00', '2026-10-10 00:00:00', '2026-09-29 13:00:00');

INSERT INTO event_ioc (event_id, ioc_version_id) VALUES
  (1, 1),
  (2, 1),
  (17, 1),
  (29, 1),
  (10, 2),
  (11, 2),
  (23, 2),
  (24, 2),
  (4, 3),
  (5, 3),
  (21, 3),
  (15, 4),
  (16, 4),
  (28, 4),
  (6, 5),
  (7, 5),
  (20, 5),
  (30, 5),
  (8, 6),
  (9, 6),
  (19, 6),
  (27, 6),
  (14, 10),
  (25, 10),
  (10, 7),
  (4, 8),
  (8, 9);

INSERT INTO network_log (log_id, log_time, src_ip, dst_asset_id, dst_port, protocol, action) VALUES
  (1, '2026-09-20 03:10:00', '198.51.100.77', 1, 22, 'TCP', 'allowed'),
  (2, '2026-09-20 03:12:00', '198.51.100.77', 1, 22, 'TCP', 'blocked'),
  (3, '2026-09-24 14:00:00', '198.51.100.77', 3, 3306, 'TCP', 'allowed'),
  (4, '2026-09-28 22:45:00', '198.51.100.77', 9, 443, 'TCP', 'allowed'),
  (5, '2026-10-01 01:30:00', '198.51.100.77', 3, 3306, 'TCP', 'allowed'),
  (6, '2026-10-02 01:31:00', '198.51.100.77', 9, 443, 'TCP', 'blocked'),
  (7, '2026-10-04 05:05:00', '198.51.100.77', 1, 443, 'TCP', 'allowed'),
  (8, '2026-10-05 06:00:00', '198.51.100.77', 3, 3306, 'TCP', 'allowed'),
  (9, '2026-10-03 03:00:00', '198.51.100.45', 2, 8080, 'TCP', 'allowed'),
  (10, '2026-10-05 03:10:00', '198.51.100.45', 2, 8080, 'TCP', 'allowed'),
  (11, '2026-10-06 23:00:00', '198.51.100.45', 1, 443, 'TCP', 'allowed'),
  (12, '2026-10-07 03:30:00', '198.51.100.45', 2, 8080, 'TCP', 'allowed'),
  (13, '2026-10-18 02:01:00', '198.51.100.45', 1, 22, 'TCP', 'allowed'),
  (14, '2026-10-18 02:03:00', '198.51.100.45', 1, 22, 'TCP', 'allowed'),
  (15, '2026-10-08 07:00:00', '203.0.113.11', 9, 443, 'TCP', 'allowed'),
  (16, '2026-10-10 08:10:00', '203.0.113.11', 9, 443, 'TCP', 'allowed'),
  (17, '2026-10-10 08:35:00', '203.0.113.11', 9, 443, 'TCP', 'allowed'),
  (18, '2026-10-12 04:00:00', '203.0.113.11', 5, 53, 'UDP', 'allowed'),
  (19, '2026-10-24 03:10:00', '203.0.113.11', 5, 22, 'TCP', 'allowed'),
  (20, '2026-10-01 02:13:00', '198.51.100.23', 1, 22, 'TCP', 'blocked'),
  (21, '2026-10-11 11:58:00', '198.51.100.23', 6, 445, 'TCP', 'blocked');

INSERT INTO retro_hunt_run (run_id, ioc_version_id, started_at, incident_id) VALUES
  (1, 2, '2026-10-12 08:00:00', 4),
  (2, 4, '2026-10-20 09:00:00', 5);

INSERT INTO retro_hit (run_id, log_id) VALUES
  (1, 9),
  (1, 10),
  (1, 11),
  (1, 12),
  (2, 15),
  (2, 16),
  (2, 17),
  (2, 18);
