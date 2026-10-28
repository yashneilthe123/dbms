CREATE TABLE mitigation (
  type_id  INT NOT NULL,
  step_no  TINYINT NOT NULL CHECK (step_no > 0),
  action   VARCHAR(100) NOT NULL,
  PRIMARY KEY (type_id, step_no),                    -- weak entity key
  FOREIGN KEY (type_id) REFERENCES attack_type(type_id) ON DELETE CASCADE
);
