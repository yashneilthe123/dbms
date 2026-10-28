-- SentinelX Review 2: Tables and constraints
-- MySQL 8.0 (tested on 8.0.46)

DROP DATABASE IF EXISTS sentinelx;
CREATE DATABASE sentinelx;
USE sentinelx;


-- ---- reset ----
DROP DATABASE IF EXISTS sentinelx;
DROP USER IF EXISTS 'ananya.rao'@'localhost', 'rahul.mehta'@'localhost', 'divya.iyer'@'localhost';
DROP ROLE IF EXISTS 'sx_admin', 'sx_analyst', 'sx_viewer';
CREATE DATABASE sentinelx;


-- ---- version ----
SELECT VERSION() AS mysql_version, @@sql_mode AS sql_mode;


-- ---- ddl_asset ----
CREATE TABLE asset (
  asset_id     INT AUTO_INCREMENT PRIMARY KEY,
  hostname     VARCHAR(63) NOT NULL UNIQUE,          -- 63 = max DNS label
  ip_address   VARCHAR(45) NOT NULL UNIQUE,          -- 45 = longest IPv6 text
  asset_type   ENUM('web','db','mail','dns','workstation','iot','vpn') NOT NULL,
  criticality  TINYINT NOT NULL CHECK (criticality BETWEEN 1 AND 5)
);


-- ---- ddl_vulnerability ----
CREATE TABLE vulnerability (
  cve_id     VARCHAR(16) PRIMARY KEY CHECK (cve_id REGEXP '^CVE-[0-9]{4}-[0-9]{4,7}$'),
  cvss       DECIMAL(3,1) NOT NULL CHECK (cvss BETWEEN 0 AND 10),
  published  DATE NOT NULL
);


-- ---- ddl_asset_vulnerability ----
CREATE TABLE asset_vulnerability (
  asset_id     INT NOT NULL,
  cve_id       VARCHAR(16) NOT NULL,
  detected_at  DATE NOT NULL,
  patched_at   DATE,
  PRIMARY KEY (asset_id, cve_id),
  FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE CASCADE,
  FOREIGN KEY (cve_id) REFERENCES vulnerability(cve_id),
  CHECK (patched_at IS NULL OR patched_at >= detected_at)
);


-- ---- ddl_network_log ----
CREATE TABLE network_log (
  log_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
  log_time      DATETIME NOT NULL,
  src_ip        VARCHAR(45) NOT NULL,
  dst_asset_id  INT NOT NULL,
  dst_port      SMALLINT UNSIGNED NOT NULL,          -- 0 to 65535
  protocol      ENUM('TCP','UDP','ICMP') NOT NULL,
  action        ENUM('allowed','blocked') NOT NULL,
  FOREIGN KEY (dst_asset_id) REFERENCES asset(asset_id),
  INDEX idx_src_time (src_ip, log_time)              -- used by retro-hunt
);


-- ---- ddl_attack_type ----
CREATE TABLE attack_type (
  type_id          INT AUTO_INCREMENT PRIMARY KEY,
  type_name        VARCHAR(40) NOT NULL UNIQUE,
  mitre_technique  VARCHAR(9) NOT NULL UNIQUE CHECK (mitre_technique REGEXP '^T[0-9]{4}([.][0-9]{3})?$'),
  base_severity    TINYINT NOT NULL CHECK (base_severity BETWEEN 1 AND 10)
);


-- ---- ddl_mitigation ----
CREATE TABLE mitigation (
  type_id  INT NOT NULL,
  step_no  TINYINT NOT NULL CHECK (step_no > 0),
  action   VARCHAR(100) NOT NULL,
  PRIMARY KEY (type_id, step_no),                    -- weak entity key
  FOREIGN KEY (type_id) REFERENCES attack_type(type_id) ON DELETE CASCADE
);


-- ---- ddl_threat_actor ----
CREATE TABLE threat_actor (
  actor_id        INT AUTO_INCREMENT PRIMARY KEY,
  actor_name      VARCHAR(50) NOT NULL UNIQUE,
  origin_country  CHAR(2) CHECK (origin_country REGEXP '^[A-Z]{2}$'),
  motive          ENUM('financial','espionage','hacktivism','sabotage','unknown') NOT NULL
);


-- ---- ddl_malware ----
CREATE TABLE malware (
  malware_id    INT AUTO_INCREMENT PRIMARY KEY,
  malware_name  VARCHAR(50) NOT NULL UNIQUE,
  family        VARCHAR(30) NOT NULL,
  sha256        CHAR(64) NOT NULL UNIQUE CHECK (sha256 REGEXP '^[0-9a-f]{64}$'),
  actor_id      INT,
  cluster_id    SMALLINT,                            -- filled by the ML job
  FOREIGN KEY (actor_id) REFERENCES threat_actor(actor_id) ON DELETE SET NULL
);


-- ---- ddl_attack_event ----
CREATE TABLE attack_event (
  event_id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  event_time          DATETIME NOT NULL,
  src_ip              VARCHAR(45) NOT NULL,
  src_country         CHAR(2) NOT NULL CHECK (src_country REGEXP '^[A-Z]{2}$'),
  asset_id            INT NOT NULL,
  type_id             INT NOT NULL,
  actor_id            INT,
  malware_id          INT,
  cve_id              VARCHAR(16),
  severity            TINYINT NOT NULL CHECK (severity BETWEEN 1 AND 10),
  blocked             BOOLEAN NOT NULL,
  predicted_severity  ENUM('LOW','MEDIUM','HIGH','CRITICAL'),   -- filled by the ML job
  FOREIGN KEY (asset_id) REFERENCES asset(asset_id),
  FOREIGN KEY (type_id) REFERENCES attack_type(type_id),
  FOREIGN KEY (actor_id) REFERENCES threat_actor(actor_id),
  FOREIGN KEY (malware_id) REFERENCES malware(malware_id),
  FOREIGN KEY (cve_id) REFERENCES vulnerability(cve_id),
  INDEX idx_time (event_time),
  INDEX idx_src (src_ip)
);


-- ---- ddl_analyst ----
CREATE TABLE analyst (
  analyst_id  INT AUTO_INCREMENT PRIMARY KEY,
  full_name   VARCHAR(50) NOT NULL,
  email       VARCHAR(50) NOT NULL UNIQUE CHECK (email REGEXP '^[^@ ]+@[^@ ]+[.][A-Za-z]{2,}$'),
  role        ENUM('admin','analyst','viewer') NOT NULL
);


-- ---- ddl_incident ----
CREATE TABLE incident (
  incident_id  INT AUTO_INCREMENT PRIMARY KEY,
  title        VARCHAR(100) NOT NULL,
  priority     ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL,
  status       ENUM('OPEN','INVESTIGATING','CONTAINED','CLOSED') NOT NULL DEFAULT 'OPEN',
  assigned_to  INT,
  opened_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  closed_at    DATETIME,
  FOREIGN KEY (assigned_to) REFERENCES analyst(analyst_id),
  CHECK ((status = 'CLOSED') = (closed_at IS NOT NULL)),
  CHECK (closed_at IS NULL OR closed_at >= opened_at)
);


-- ---- ddl_incident_event ----
CREATE TABLE incident_event (
  incident_id  INT NOT NULL,
  event_id     BIGINT NOT NULL,
  PRIMARY KEY (incident_id, event_id),
  FOREIGN KEY (incident_id) REFERENCES incident(incident_id) ON DELETE CASCADE,
  FOREIGN KEY (event_id) REFERENCES attack_event(event_id) ON DELETE CASCADE
);


-- ---- ddl_ioc ----
CREATE TABLE ioc (
  ioc_version_id  BIGINT AUTO_INCREMENT PRIMARY KEY,
  ioc_type        ENUM('ip','domain','hash','url') NOT NULL,
  ioc_value       VARCHAR(255) NOT NULL,             -- 253 = longest domain name
  actor_id        INT,
  malware_id      INT,
  valid_from      DATETIME NOT NULL,                 -- valid_period: when it was hostile
  valid_to        DATETIME,
  recorded_from   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,   -- recorded_period: when we knew
  recorded_to     DATETIME,
  FOREIGN KEY (actor_id) REFERENCES threat_actor(actor_id),
  FOREIGN KEY (malware_id) REFERENCES malware(malware_id),
  CHECK (ioc_type <> 'ip' OR ioc_value REGEXP '^[0-9]{1,3}([.][0-9]{1,3}){3}$'),
  CHECK (valid_to IS NULL OR valid_to > valid_from),
  CHECK (recorded_to IS NULL OR recorded_to > recorded_from),
  INDEX idx_value (ioc_value)
);


-- ---- ddl_event_ioc ----
CREATE TABLE event_ioc (
  event_id        BIGINT NOT NULL,
  ioc_version_id  BIGINT NOT NULL,
  PRIMARY KEY (event_id, ioc_version_id),
  FOREIGN KEY (event_id) REFERENCES attack_event(event_id) ON DELETE CASCADE,
  FOREIGN KEY (ioc_version_id) REFERENCES ioc(ioc_version_id)
);


-- ---- ddl_retro_hunt_run ----
CREATE TABLE retro_hunt_run (
  run_id          INT AUTO_INCREMENT PRIMARY KEY,
  ioc_version_id  BIGINT NOT NULL,
  started_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  incident_id     INT UNIQUE,                        -- at most one incident per run
  FOREIGN KEY (ioc_version_id) REFERENCES ioc(ioc_version_id),
  FOREIGN KEY (incident_id) REFERENCES incident(incident_id)
);


-- ---- ddl_retro_hit ----
CREATE TABLE retro_hit (
  run_id  INT NOT NULL,
  log_id  BIGINT NOT NULL,
  PRIMARY KEY (run_id, log_id),
  FOREIGN KEY (run_id) REFERENCES retro_hunt_run(run_id) ON DELETE CASCADE,
  FOREIGN KEY (log_id) REFERENCES network_log(log_id)
);


-- ---- ddl_show_tables ----
SHOW TABLES;
