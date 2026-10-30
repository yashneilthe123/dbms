CREATE TABLE incident_audit (
  audit_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  incident_id      INT NOT NULL,                     -- no FK: the trail must outlive a deleted incident
  action           ENUM('UPDATE','DELETE') NOT NULL,
  changed_by       VARCHAR(288) NOT NULL,            -- USER(): the account that ran the statement
  changed_at       DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  old_status       ENUM('OPEN','INVESTIGATING','CONTAINED','CLOSED'),
  new_status       ENUM('OPEN','INVESTIGATING','CONTAINED','CLOSED'),
  old_priority     ENUM('LOW','MEDIUM','HIGH','CRITICAL'),
  new_priority     ENUM('LOW','MEDIUM','HIGH','CRITICAL'),
  old_assigned_to  INT,
  new_assigned_to  INT,
  INDEX idx_incident (incident_id, changed_at)
);
