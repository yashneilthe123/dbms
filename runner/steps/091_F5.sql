SELECT LPAD(analyst_id, 4, '0')                    AS staff_no,
       UPPER(full_name)                             AS name_upper,
       CONCAT(LEFT(full_name, 1), '. ',
              SUBSTRING_INDEX(full_name, ' ', -1))  AS short_name,
       SUBSTRING_INDEX(email, '@', 1)               AS username,
       LENGTH(email)                                AS email_length
FROM analyst
ORDER BY analyst_id;
