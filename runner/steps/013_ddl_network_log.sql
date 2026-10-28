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
