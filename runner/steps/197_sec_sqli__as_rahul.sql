-- normal use: rahul's own incidents with 'Brute' in the title
CALL sp_search_incidents_unsafe('Brute');

-- tautology: the WHERE clause becomes (... AND title LIKE '%%') OR 1=1, so every incident comes back,
-- read with root's rights although rahul has no SELECT on incident
CALL sp_search_incidents_unsafe('%'' OR 1=1 -- ');

-- UNION: rows from another table he cannot read
CALL sp_search_incidents_unsafe('%'' UNION SELECT analyst_id, full_name, email, role, NULL FROM analyst -- ');

-- stacked statements are refused: PREPARE takes one statement only
CALL sp_search_incidents_unsafe('x''; DROP TABLE asset; -- ');

-- the safe procedure treats the same text as data: it only matches titles containing it
CALL sp_search_incidents('Brute');
CALL sp_search_incidents('%'' OR 1=1 -- ');
