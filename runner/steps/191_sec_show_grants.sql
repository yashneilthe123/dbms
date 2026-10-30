SHOW GRANTS FOR 'sx_admin';
SHOW GRANTS FOR 'sx_analyst';
SHOW GRANTS FOR 'sx_viewer';
-- a user's own grants show only the role; USING expands what the role gives
SHOW GRANTS FOR 'rahul.mehta'@'localhost';
SHOW GRANTS FOR 'rahul.mehta'@'localhost' USING 'sx_analyst';
SHOW GRANTS FOR 'divya.iyer'@'localhost' USING 'sx_viewer';
