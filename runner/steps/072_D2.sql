SELECT full_name, email
FROM analyst
WHERE analyst_id = (SELECT assigned_to
                    FROM incident
                    WHERE assigned_to IS NOT NULL
                    ORDER BY opened_at DESC
                    LIMIT 1);
