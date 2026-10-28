CREATE TABLE asset (
  asset_id     INT AUTO_INCREMENT PRIMARY KEY,
  hostname     VARCHAR(63) NOT NULL UNIQUE,          -- 63 = max DNS label
  ip_address   VARCHAR(45) NOT NULL UNIQUE,          -- 45 = longest IPv6 text
  asset_type   ENUM('web','db','mail','dns','workstation','iot','vpn') NOT NULL,
  criticality  TINYINT NOT NULL CHECK (criticality BETWEEN 1 AND 5)
);
