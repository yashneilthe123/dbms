<!--
Team note, delete before pasting into the report:
- Section 1 is the text for the Review 3 report. Sections 2 and 3 are the edit list and the work-breakdown check.
- The work-breakdown rows must describe what each person really did. Leave a row blank rather than guess.
- The Review 3 changes on branch review3-hardening were made with an AI assistant (Claude). Check whether VIT or Dr. Bihari
  require that to be disclosed, and say so in the report if they do.
-->

# 1. Scope Revision and Design Changes since Review 2

*Revised on 29 October 2026.*

## 1.1 What we removed, and why

The Review 2 report described more than the project contains. Sections 5.2, 6 and 19 and Fig. 1 listed a FastAPI
backend, a React dashboard and machine-learning jobs written with pandas and scikit-learn. These were planned
but never built, and none of them are in the repository. Fig. 1 also showed a Python ingestion pipeline and a dataset
of 600,000 logs and 115,000 events. The only Python in the project generates the test data and the step files, and
the dataset is 50,021 log lines and 30 attacks. We should have marked these parts as planned work, and we are
correcting that here.

For Review 3 we have narrowed the scope to what a DBMS project should be judged on: the database design, the SQL,
and the security of the database itself. The database was always the core of SentinelX. Every rule that matters
already runs inside MySQL as a constraint, trigger, procedure or privilege, so removing the application layer
removes no behaviour. Users work through the `mysql` client and MySQL Workbench, and what each user can do is
decided by their role, not by an application.

| Removed | Where Review 2 claimed it | Review 3 status |
| --- | --- | --- |
| FastAPI backend | 5.2, 6, 19 | Removed. Roles, views and procedures are the access layer (12.7). |
| React SOC dashboard | 5.2, 7, 19, Fig. 1 | Removed. The "dashboard" module is the views `v_attack_details` and `v_asset_risk`. |
| scikit-learn ML jobs | 5.2, 6, 9, 10, A7, C5 | Removed. The two columns they were meant to fill were changed (changes 12 and 13). |
| Python ingestion / ETL | Fig. 1 | Never built. Test data comes from `tools/gen_seed.py` and a recursive CTE. |

## 1.2 Design changes since Review 2

Numbering continues from the Review 2 change log (changes 1 to 11).

| # | Change | Reason |
| --- | --- | --- |
| 12 | `attack_event.predicted_severity` renamed to `triage_priority`: a priority an analyst sets, NULL until triaged | No ML job exists to predict anything. The column now records an analyst's decision, which is not a function of `severity`: events 5 and 6 both have severity 9 but are CRITICAL and HIGH, because event 6 was blocked. So there is no transitive dependency `event_id → severity → triage_priority`, and the table stays in 3NF. |
| 13 | `malware.cluster_id` dropped | Only the ML job would have filled it. Query C5 now self-joins `malware` on `actor_id` (pairs of malware used by the same threat actor). |
| 14 | `01_ddl.sql` selects the database again after re-creating it | Run on its own, the script dropped the database it was using and stopped with ERROR 1046 at the first CREATE TABLE. Our runner hid this because it always passed `--database`. |
| 15 | `sp_assign_incident` checks who is calling it | Our own testing found a privilege escalation. The procedure runs with its definer's rights, so an analyst could call it to hand his incident to a colleague, or take a colleague's incident. That is the change `WITH CHECK OPTION` blocks on `v_my_incidents`. The procedure now maps `USER()` (the caller, not `CURRENT_USER()`, which is the definer) to an analyst, and analysts may only claim unassigned incidents for themselves. |
| 16 | Analyst role reads only views and runs only procedures | Review 2 granted analysts SELECT on ten base tables, plus INSERT on `ioc`, so views were not the only access path. Analysts now read indicators through the new view `v_ioc` and report them through the new procedure `sp_report_ioc`, which always sets `recorded_from` to the current time, so nobody can backdate when we learned about an indicator. |
| 17 | Accounts lock after 3 wrong passwords (`FAILED_LOGIN_ATTEMPTS 3 PASSWORD_LOCK_TIME 1`) | Before this, any number of wrong passwords could be tried. |
| 18 | New procedure `sp_load_log_batch` with an exit handler that rolls back | MySQL undoes only the failed statement, not the transaction. The Review 2 demo worked only because the script called ROLLBACK itself. Step 172 shows both behaviours. |
| 19 | Four more EXPLAIN plans (step 183) | They show the leftmost-prefix rule (full index scan, and MySQL 8's skip scan as the alternative), a function on the column that hides the index, the same filter rewritten as a range read, and EXPLAIN ANALYZE with real timings. |
| 20 | `13_tests.sql`: 49 automatic tests | 28 run as root, 11 as the analyst, 5 as the viewer and 5 as the admin. Each prints PASS or FAIL, and all 49 pass on a clean build. |
| 21 | New table `incident_audit` with triggers on `incident` | Every UPDATE or DELETE of an incident is recorded with the account that made it (`USER()`), the time, and the old and new status, priority and owner. This happens whether the change came through a view, a procedure or a direct statement. `CURRENT_USER()` would always record root, the trigger's definer. The table has no foreign key, so the trail survives the incident being deleted. Two more triggers make it append-only. |
| 22 | `sx_admin` lost CREATE, ALTER, DROP and TRIGGER | Review 2 gave the admin role ALL PRIVILEGES, which included dropping the audit triggers or truncating the audit table (TRUNCATE does not fire triggers). Schema changes now stay with root, the DBA. |
| 23 | SQL-injection demonstration (steps 196–198) | A search procedure built with CONCAT lets the analyst read every incident and every analyst's email, although he only holds EXECUTE: the injected SQL runs with the procedure's rights. The parameterised version is safe. The vulnerable procedure is dropped after the demonstration. |
| 24 | `trg_ioc_no_overlap` ignores versions closed with `recorded_to` | Found while building the demo. `trg_ioc_no_delete` tells users to close a version with `recorded_to`, but the overlap check still counted closed versions, so a corrected version could never be added. |
| 25 | Backup and point-in-time recovery runbook (`demo/07_backup_recovery.md`) | Rehearsed with mysqldump and the binary log, stopping at the binlog position of the bad DELETE. |
| 26 | Architecture figure redrawn (`tools/draw_architecture.py`) | The old Fig. 1 showed components that do not exist. |

## 1.3 Limitations (replaces Review 2 section 17)

- There is no application or user interface. The project is the database: users connect with the `mysql` client.
- There is no automatic detection or prediction. Attacks and their severity are recorded as input, as they would come from a firewall or IDS, and analysts set the triage priority.
- The data is a hand-made test set, not real traffic. Attacker IPs come from documentation-only address ranges, and the attacker and malware names are made up. The CVE IDs are real.
- Retro-hunts only work for IP addresses. Domains and file hashes would need DNS and file logs.
- MySQL has no exclusion constraint, so the rule that indicator versions never overlap lives in a trigger.
- Triggers record only changes that succeed. Failed logins and denied privileges need the server's error log or an audit plugin, which MySQL Community does not include.

# 2. Edit list for the final report

| Review 2 section | Edit |
| --- | --- |
| 5.2 Software | Remove FastAPI, pandas, scikit-learn, Node.js, React and Vite. Keep MySQL 8.0.46, Workbench, draw.io, Git, and Python 3 for the generator scripts in `tools/`. |
| 6 Architecture, Fig. 1 | Replace with the new `diagrams/architecture.png`. Delete the sentence about the FastAPI backend and the ML jobs. |
| 7 Modules | Rename "Dashboard and search" to "Search and reporting". Add "Audit trail" (`incident_audit`, its triggers). |
| 8 ER diagram, relational schema | Remove `cluster_id` from MALWARE. Rename `predicted_severity` to `triage_priority` on ATTACK_EVENT. Add INCIDENT_AUDIT: it has no relationship line, because it deliberately has no foreign key. These two PNGs were drawn by hand in draw.io and still need this edit. |
| 9 Tables (p. 13–14) | Update the `malware` and `attack_event` attribute tables and the Fig. 11 / Fig. 12 screenshots. |
| 10 UPDATE demo (p. 20–21) | The analyst triages attacks 25 and 26. New Fig. 22 from `mysql-output/033_dml_update.txt`. |
| 11 A7, C5 (p. 25, 29) | New titles and screenshots from `mysql-output/047_A7.txt` and `065_C5.txt`. |
| 12.7 Security | New grants, the caller check and the lockout. Show the exploit failing (`194_sec_analyst__as_rahul`). |
| 13 Transactions | Add step 172, the handler-based rollback. |
| 14 Indexes | Add step 183. |
| 17 Limitations | Replace with 1.3 above. |
| 19 Work breakdown | Remove "FastAPI backend" and "React dashboard". See section 3. |
| New | Testing chapter built from `mysql-output/200_tests.txt` to `203_tests__as_ananya.txt` (49 tests). |
| New | Concurrency (`demo/06_concurrency.md`), backup and recovery (`demo/07_backup_recovery.md`), audit trail (steps 153 and 195) and SQL injection (steps 196–198). Use the evidence files for screenshots. |

# 3. Work breakdown check

The Review 2 table assigned the FastAPI backend to Shlok and the React dashboard to Yashneil. Remove both. Then fill
in each person's real Review 3 work. Every student will be asked about the parts listed against their name.

| Team member | Review 2 work that stays | Review 3 work (fill in truthfully) |
| --- | --- | --- |
| Shlok Gupta (24BCI0061) | Retro-hunt and IOC triggers, indexes and EXPLAIN, transactions | |
| Shreya Bhushan (24BCI0086) | ER diagram, normalisation, DDL and constraints, views, stored procedures and cursors, SQL security | |
| Yashneil Purkayastha (24BDS0158) | Test data and DML, SQL queries A–G, complex business queries, functions, the report | |
