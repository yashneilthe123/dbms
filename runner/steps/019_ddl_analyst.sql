CREATE TABLE analyst (
  analyst_id  INT AUTO_INCREMENT PRIMARY KEY,
  full_name   VARCHAR(50) NOT NULL,
  email       VARCHAR(50) NOT NULL UNIQUE CHECK (email REGEXP '^[^@ ]+@[^@ ]+[.][A-Za-z]{2,}$'),
  role        ENUM('admin','analyst','viewer') NOT NULL
);
