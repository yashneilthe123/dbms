-- Demo step 2e (root): install the vulnerable and the safe search procedure.
-- Run from the repository root. demo/02g_sqli_cleanup.sql removes the vulnerable one again.
USE sentinelx;
DROP PROCEDURE IF EXISTS sp_search_incidents_unsafe;
DROP PROCEDURE IF EXISTS sp_search_incidents;
SOURCE runner/steps/196_sec_sqli_setup.sql
