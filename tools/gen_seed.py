"""Seed data for SentinelX Review 2. Single source of truth: writes 030/031 SQL files
and is reused by the SQLite simulation that predicts expected outputs."""
import hashlib

ASSETS = [  # id, hostname, ip, type, criticality
    (1, 'web-01', '10.0.1.10', 'web', 5), (2, 'web-02', '10.0.1.11', 'web', 4),
    (3, 'db-01', '10.0.2.20', 'db', 5), (4, 'mail-01', '10.0.3.30', 'mail', 3),
    (5, 'dns-01', '10.0.4.40', 'dns', 4), (6, 'ws-hr-01', '10.0.5.51', 'workstation', 2),
    (7, 'ws-fin-01', '10.0.5.52', 'workstation', 3), (8, 'cam-01', '10.0.6.60', 'iot', 1),
    (9, 'vpn-01', '10.0.7.70', 'vpn', 4), (10, 'ws-dev-01', '10.0.5.53', 'workstation', 2),
]
VULNS = [  # cve, cvss, published
    ('CVE-2024-3400', 10.0, '2024-04-12'), ('CVE-2023-4966', 9.4, '2023-10-10'),
    ('CVE-2021-44228', 10.0, '2021-12-10'), ('CVE-2023-34362', 9.8, '2023-06-02'),
    ('CVE-2024-6387', 8.1, '2024-07-01'), ('CVE-2023-44487', 7.5, '2023-10-10'),
    ('CVE-2022-22965', 9.8, '2022-04-01'), ('CVE-2019-0708', 9.8, '2019-05-16'),
    ('CVE-2023-48795', 5.9, '2023-12-18'),
]
ASSET_VULN = [  # asset, cve, detected, patched
    (1, 'CVE-2021-44228', '2026-09-02', '2026-09-10'), (1, 'CVE-2023-44487', '2026-09-15', None),
    (2, 'CVE-2022-22965', '2026-09-05', None), (3, 'CVE-2023-34362', '2026-08-20', '2026-09-01'),
    (4, 'CVE-2023-4966', '2026-09-12', None), (5, 'CVE-2023-48795', '2026-09-20', None),
    (6, 'CVE-2019-0708', '2026-08-15', None), (9, 'CVE-2024-3400', '2026-09-01', None),
    (9, 'CVE-2024-6387', '2026-09-03', '2026-09-25'),
]
TYPES = [  # id, name, technique, base severity
    (1, 'Brute Force', 'T1110', 6), (2, 'Phishing', 'T1566', 5),
    (3, 'Exploit Public-Facing App', 'T1190', 8), (4, 'Port Scan', 'T1046', 3),
    (5, 'Ransomware', 'T1486', 10), (6, 'DDoS', 'T1498', 7),
    (7, 'Credential Dumping', 'T1003', 9), (8, 'Command and Control', 'T1071', 7),
]
MITIGATION = [
    (1, 1, 'Block the source IP at the firewall'), (1, 2, 'Lock the targeted accounts'), (1, 3, 'Enforce MFA on the login page'),
    (2, 1, 'Quarantine the email in all mailboxes'), (2, 2, 'Reset the password of the user who clicked'), (2, 3, 'Block the sender domain'),
    (3, 1, 'Isolate the host from the network'), (3, 2, 'Apply the vendor patch'), (3, 3, 'Scan the host for web shells'),
    (4, 1, 'Rate-limit the source IP'),
    (5, 1, 'Disconnect the host from the network'), (5, 2, 'Restore data from the offline backup'), (5, 3, 'Reset all admin credentials'),
    (6, 1, 'Turn on upstream traffic scrubbing'), (6, 2, 'Rate-limit HTTP/2 streams per client'),
    (7, 1, 'Reset domain admin passwords'), (7, 2, 'Rotate the krbtgt key twice'),
    (8, 1, 'Sinkhole the C2 domain'),
]
ACTORS = [  # id, name, origin, motive
    (1, 'Crimson Lynx', 'RU', 'financial'), (2, 'Silent Monsoon', 'CN', 'espionage'),
    (3, 'Byte Bandits', None, 'hacktivism'), (4, 'Iron Kestrel', 'KP', 'sabotage'),
    (5, 'Ghost Parrot', 'BR', 'financial'), (6, 'Quiet Willow', 'IR', 'espionage'),
]
def sha(name):
    return hashlib.sha256(name.encode()).hexdigest()
MALWARE = [  # id, name, family, actor
    (1, 'LynxLocker', 'Locker', 1), (2, 'LynxLoader', 'Loader', 1),
    (3, 'MonsoonRAT', 'RAT', 2), (4, 'MonsoonStealer', 'Stealer', 2),
    (5, 'KestrelWiper', 'Wiper', 4), (6, 'ParrotBot', 'Botnet', 5),
    (7, 'OrphanMiner', 'Miner', None), (8, 'WillowRAT', 'RAT', 6),
]
LEVELS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
def triage(sev, blocked):
    # analyst's call: starts from severity, one level lower if the firewall already blocked it,
    # so triage_priority is not determined by severity alone
    level = 3 if sev >= 9 else 2 if sev >= 7 else 1 if sev >= 4 else 0
    return LEVELS[max(level - blocked, 0)]
# id, time, src_ip, country, asset, type, actor, malware, cve, severity, blocked
EVENTS = [
    (1, '2026-10-01 02:14:00', '198.51.100.23', 'RU', 1, 1, 1, None, None, 6, 1),
    (2, '2026-10-01 02:20:00', '198.51.100.23', 'RU', 1, 1, 1, None, None, 7, 0),
    (3, '2026-10-02 11:05:00', '203.0.113.200', 'US', 1, 4, None, None, None, 3, 1),
    (4, '2026-10-03 09:30:00', '203.0.113.10', 'CN', 4, 2, 2, 3, None, 6, 0),
    (5, '2026-10-04 22:10:00', '203.0.113.10', 'CN', 4, 3, 2, 3, 'CVE-2023-4966', 9, 0),
    (6, '2026-10-05 01:00:00', '192.0.2.50', 'KP', 3, 3, 4, None, 'CVE-2023-34362', 9, 1),
    (7, '2026-10-05 01:45:00', '192.0.2.50', 'KP', 3, 7, 4, 5, None, 9, 0),
    (8, '2026-10-06 14:20:00', '198.51.100.88', 'BR', 2, 6, 5, 6, None, 7, 1),
    (9, '2026-10-06 14:25:00', '198.51.100.88', 'BR', 2, 6, 5, 6, None, 7, 1),
    (10, '2026-10-07 03:33:00', '198.51.100.45', 'RU', 2, 3, 1, 2, 'CVE-2022-22965', 8, 0),
    (11, '2026-10-07 04:10:00', '198.51.100.45', 'RU', 2, 5, 1, 1, None, 10, 0),
    (12, '2026-10-08 10:00:00', '203.0.113.200', 'US', 5, 4, None, None, None, 2, 1),
    (13, '2026-10-08 10:02:00', '203.0.113.200', 'US', 9, 4, None, None, None, 3, 1),
    (14, '2026-10-09 16:45:00', '192.0.2.77', 'NL', 1, 6, 3, None, 'CVE-2023-44487', 8, 0),
    (15, '2026-10-10 08:15:00', '203.0.113.11', 'CN', 9, 3, 2, 4, 'CVE-2024-3400', 10, 0),
    (16, '2026-10-10 08:40:00', '203.0.113.11', 'CN', 9, 7, 2, 4, None, 9, 0),
    (17, '2026-10-11 12:00:00', '198.51.100.23', 'RU', 6, 2, 1, 2, None, 5, 1),
    (18, '2026-10-12 19:30:00', '203.0.113.99', 'IN', 8, 1, None, 7, None, 4, 0),
    (19, '2026-10-13 07:05:00', '198.51.100.88', 'BR', 1, 6, 5, 6, None, 6, 1),
    (20, '2026-10-14 23:50:00', '192.0.2.50', 'KP', 7, 2, 4, None, None, 6, 1),
    (21, '2026-10-15 05:20:00', '203.0.113.10', 'CN', 3, 3, 2, 3, 'CVE-2021-44228', 8, 1),
    (22, '2026-10-16 13:13:00', '203.0.113.200', 'US', 4, 4, None, None, None, 2, 1),
    (23, '2026-10-18 02:02:00', '198.51.100.45', 'RU', 1, 1, 1, None, None, 7, 0),
    (24, '2026-10-18 02:05:00', '198.51.100.45', 'RU', 1, 1, 1, None, None, 8, 0),
    (25, '2026-10-20 18:00:00', '192.0.2.77', 'NL', 2, 6, 3, None, None, 7, 1),
    (26, '2026-10-21 09:09:00', '203.0.113.99', 'IN', 8, 1, None, 7, None, 4, 1),
    (27, '2026-10-22 21:30:00', '198.51.100.88', 'BR', 7, 2, 5, 6, None, 5, 1),
    (28, '2026-10-24 03:15:00', '203.0.113.11', 'CN', 5, 3, 2, 4, 'CVE-2023-48795', 7, 0),
    (29, '2026-10-25 11:11:00', '198.51.100.23', 'RU', 9, 3, 1, 2, 'CVE-2024-6387', 9, 1),
    (30, '2026-10-26 15:40:00', '192.0.2.50', 'KP', 3, 5, 4, 5, None, 10, 0),
]
# events 1-24 already triaged by an analyst; 25-30 not yet (25 and 26 are triaged by the UPDATE demo)
def triaged(e):
    return triage(e[9], e[10]) if e[0] <= 24 else None

ANALYSTS = [
    (1, 'Ananya Rao', 'ananya.rao@sentinelx.in', 'admin'), (2, 'Rahul Mehta', 'rahul.mehta@sentinelx.in', 'analyst'),
    (3, 'Priya Nair', 'priya.nair@sentinelx.in', 'analyst'), (4, 'Karan Shah', 'karan.shah@sentinelx.in', 'analyst'),
    (5, 'Divya Iyer', 'divya.iyer@sentinelx.in', 'viewer'), (6, 'Arjun Das', 'arjun.das@sentinelx.in', 'analyst'),
]
INCIDENTS = [  # id, title, priority, status, assigned, opened, closed
    (1, 'Brute force on web-01 from 198.51.100.23', 'HIGH', 'CLOSED', 2, '2026-10-01 02:25:00', '2026-10-01 09:40:00'),
    (2, 'Citrix Bleed exploit on mail-01', 'CRITICAL', 'CLOSED', 3, '2026-10-04 22:20:00', '2026-10-06 18:00:00'),
    (3, 'Iron Kestrel intrusion on db-01', 'HIGH', 'CONTAINED', 2, '2026-10-05 01:10:00', None),
    (4, 'Retro-hunt: 198.51.100.45 hit 2 assets 4 times', 'CRITICAL', 'INVESTIGATING', 4, '2026-10-12 08:00:00', None),
    (5, 'Retro-hunt: 203.0.113.11 hit 2 assets 4 times', 'CRITICAL', 'OPEN', None, '2026-10-20 09:00:00', None),
    (6, 'DDoS waves on web servers', 'MEDIUM', 'OPEN', 3, '2026-10-20 18:10:00', None),
    (7, 'Brute force on web-01 from 198.51.100.45', 'HIGH', 'INVESTIGATING', 2, '2026-10-18 02:10:00', None),
]
INCIDENT_EVENT = [(1, 1), (1, 2), (2, 4), (2, 5), (3, 6), (3, 7), (3, 30), (4, 10), (4, 11), (5, 15), (5, 16),
                  (6, 8), (6, 9), (6, 14), (6, 19), (6, 25), (7, 23), (7, 24)]
# id, type, value, actor, malware, valid_from, valid_to, recorded_from
IOCS = [
    (1, 'ip', '198.51.100.23', 1, None, '2026-09-25 00:00:00', None, '2026-09-28 10:00:00'),
    (2, 'ip', '198.51.100.45', 1, 1, '2026-10-01 00:00:00', None, '2026-10-12 08:00:00'),
    (3, 'ip', '203.0.113.10', 2, 3, '2026-09-30 00:00:00', None, '2026-10-02 09:00:00'),
    (4, 'ip', '203.0.113.11', 2, 4, '2026-10-05 00:00:00', None, '2026-10-20 09:00:00'),
    (5, 'ip', '192.0.2.50', 4, 5, '2026-10-01 00:00:00', None, '2026-10-06 12:00:00'),
    (6, 'ip', '198.51.100.88', 5, 6, '2026-10-01 00:00:00', None, '2026-10-01 06:00:00'),
    (7, 'domain', 'lynx-update.example', 1, 2, '2026-09-20 00:00:00', None, '2026-10-08 15:00:00'),
    (8, 'hash', sha('MonsoonRAT'), 2, 3, '2026-09-15 00:00:00', None, '2026-09-18 11:00:00'),
    (9, 'url', 'http://parrot-cdn.example/b.bin', 5, 6, '2026-10-01 00:00:00', None, '2026-10-15 16:00:00'),
    (10, 'ip', '192.0.2.77', 3, None, '2026-10-08 00:00:00', None, '2026-10-10 14:00:00'),
    (11, 'ip', '203.0.113.250', None, None, '2026-10-01 00:00:00', None, '2026-10-02 07:00:00'),
    (12, 'domain', 'monsoon-mail.example', 2, 3, '2026-09-28 00:00:00', '2026-10-10 00:00:00', '2026-09-29 13:00:00'),
]
EVENT_IOC = [(1, 1), (2, 1), (17, 1), (29, 1), (10, 2), (11, 2), (23, 2), (24, 2), (4, 3), (5, 3), (21, 3),
             (15, 4), (16, 4), (28, 4), (6, 5), (7, 5), (20, 5), (30, 5), (8, 6), (9, 6), (19, 6), (27, 6),
             (14, 10), (25, 10), (10, 7), (4, 8), (8, 9)]
# hand-written log lines: id, time, src_ip, dst_asset, port, protocol, action
LOGS = [
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
    (21, '2026-10-11 11:58:00', '198.51.100.23', 6, 445, 'TCP', 'blocked'),
]
RETRO_RUNS = [(1, 2, '2026-10-12 08:00:00', 4), (2, 4, '2026-10-20 09:00:00', 5)]
RETRO_HITS = [(1, 9), (1, 10), (1, 11), (1, 12), (2, 15), (2, 16), (2, 17), (2, 18)]
NOISE_ROWS = 50000


def q(v):
    if v is None:
        return 'NULL'
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def values(rows):
    return ',\n'.join('  (' + ', '.join(q(v) for v in r) + ')' for r in rows)


def asset_insert():
    return ("INSERT INTO asset (asset_id, hostname, ip_address, asset_type, criticality) VALUES\n"
            + values(ASSETS) + ";\n")


def seed_rest():
    s = []
    s.append("INSERT INTO vulnerability (cve_id, cvss, published) VALUES\n" + values(VULNS) + ";")
    s.append("INSERT INTO asset_vulnerability (asset_id, cve_id, detected_at, patched_at) VALUES\n" + values(ASSET_VULN) + ";")
    s.append("INSERT INTO attack_type (type_id, type_name, mitre_technique, base_severity) VALUES\n" + values(TYPES) + ";")
    s.append("INSERT INTO mitigation (type_id, step_no, action) VALUES\n" + values(MITIGATION) + ";")
    s.append("INSERT INTO threat_actor (actor_id, actor_name, origin_country, motive) VALUES\n" + values(ACTORS) + ";")
    s.append("INSERT INTO malware (malware_id, malware_name, family, sha256, actor_id) VALUES\n"
             + values([(m[0], m[1], m[2], sha(m[1]), m[3]) for m in MALWARE]) + ";")
    s.append("INSERT INTO attack_event (event_id, event_time, src_ip, src_country, asset_id, type_id, actor_id, malware_id, cve_id, severity, blocked, triage_priority) VALUES\n"
             + values([e + (triaged(e),) for e in EVENTS]) + ";")
    s.append("INSERT INTO analyst (analyst_id, full_name, email, role) VALUES\n" + values(ANALYSTS) + ";")
    s.append("INSERT INTO incident (incident_id, title, priority, status, assigned_to, opened_at, closed_at) VALUES\n" + values(INCIDENTS) + ";")
    s.append("INSERT INTO incident_event (incident_id, event_id) VALUES\n" + values(INCIDENT_EVENT) + ";")
    s.append("INSERT INTO ioc (ioc_version_id, ioc_type, ioc_value, actor_id, malware_id, valid_from, valid_to, recorded_from) VALUES\n" + values(IOCS) + ";")
    s.append("INSERT INTO event_ioc (event_id, ioc_version_id) VALUES\n" + values(EVENT_IOC) + ";")
    s.append("INSERT INTO network_log (log_id, log_time, src_ip, dst_asset_id, dst_port, protocol, action) VALUES\n" + values(LOGS) + ";")
    s.append("INSERT INTO retro_hunt_run (run_id, ioc_version_id, started_at, incident_id) VALUES\n" + values(RETRO_RUNS) + ";")
    s.append("INSERT INTO retro_hit (run_id, log_id) VALUES\n" + values(RETRO_HITS) + ";")
    return '\n\n'.join(s) + '\n'


NOISE_SQL = """SET SESSION cte_max_recursion_depth = 60000;
INSERT INTO network_log (log_time, src_ip, dst_asset_id, dst_port, protocol, action)
WITH RECURSIVE seq (n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 50000)
SELECT TIMESTAMP('2026-09-01') + INTERVAL n * 100 SECOND,
       CONCAT('172.16.', n MOD 40, '.', 1 + n MOD 250),
       1 + n MOD 9,
       ELT(1 + n MOD 5, 443, 80, 53, 25, 22),
       IF(n MOD 5 = 2, 'UDP', 'TCP'),
       IF(n MOD 47 = 0, 'blocked', 'allowed')
FROM seq;
"""
