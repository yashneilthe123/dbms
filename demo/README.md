# Review 3 live demo: run sheet

The faculty template fixes a 10–12 minute demo with six steps in this order: (1) clean build, (2) role-based access, (3) a transaction with a deliberate failure, (4) trigger firing, (5) one optimisation before/after, (6) one concurrency scenario. We follow that order and say each step number out loud. Each student drives two segments.

Every segment has its own file in this folder, and every file has been rehearsed on MySQL 8.0.46. If the examiner interrupts with "show me X", run that segment's file.

## The day before

1. **Store the logins**, so nobody types a password in front of the examiner. Three wrong passwords lock a demo account for a day. Run from `cmd` in the repository folder; each command asks for the password once:
   ```
   mysql_config_editor set --login-path=sx_root  --user=root        --password
   mysql_config_editor set --login-path=sx_admin --user=ananya.rao  --password
   mysql_config_editor set --login-path=sx_rahul --user=rahul.mehta --password
   mysql_config_editor set --login-path=sx_divya --user=divya.iyer  --password
   ```
   The test passwords are in `sql/12_security.sql`.
2. **Rehearse three times with a stopwatch**, on the laptop you will use.
3. **Record one full run** as a backup video.
4. **Copy the repository to a USB stick.**

## 5 minutes before

```
mysql --login-path=sx_root --table -e "source demo/00_preflight.sql"
```

Every line must say OK. If an account is locked: `source demo/00_reset_accounts.sql`.

Open four terminals in the repository folder. Use a big font and a different colour for each, and label every prompt. Open ROOT now. Open the other three straight after step 1: the build drops and re-creates those users, and a session opened before that keeps stale rights.

```
mysql --login-path=sx_root  --prompt="ROOT> "              sentinelx
mysql --login-path=sx_divya --prompt="DIVYA (viewer)> "    sentinelx
mysql --login-path=sx_rahul --prompt="RAHUL (analyst)> "   sentinelx
mysql --login-path=sx_admin --prompt="ANANYA (admin)> "    sentinelx
```

Use the mysql command line, not MySQL Workbench. Workbench's safe-update mode and per-tab autocommit change the results.

## The 11 minutes

| Time | Who | Step | Run | Say / point at |
|---|---|---|---|---|
| 0:00 | S1 | Intro | Show `diagrams/er_diagram.png`, then `diagrams/architecture.png` | "We store a security team's logs, attacks and incidents in MySQL. When a known-bad IP shows up, the database itself opens an incident. Everything we show is SQL; there is no application." |
| 0:30 | S1 | **1. Clean build** | Double-click `runner/RUN_ME.bat` (about 20 s: drops the database, then DDL, DML, every object, users and tests). Then in ROOT: `source demo/01_build_check.sql` | Row counts and object counts. Then `runner/out/200_tests.txt`, last lines: **35 passed, 0 failed**. The analyst, viewer and admin test files show 12, 5 and 7 passed. |
| 1:30 | S2 | **2. Role-based access** | ROOT: `source demo/02a_grants.sql` | The role matrix: admin works with data but cannot change the schema; analyst has only views and procedures; viewer has one view and one report. REVOKE before/after. Passwords are stored as salted SHA-256 (`$A$005$`). |
| 2:30 | S2 | | DIVYA: `source demo/02b_viewer.sql` | The report works; `SELECT` and `DELETE` on a table give **ERROR 1142**. |
| 3:00 | S2 | | RAHUL: `source demo/02c_analyst.sql` | Only his own incidents. 1142 on the table, 1369 from `WITH CHECK OPTION`. `sp_whoami`: he calls it, but it runs with root's rights, so `sp_assign_incident` has to check who called (we found and fixed this bug). |
| 3:45 | S2 | | ANANYA: `source demo/02d_admin_audit.sql` | The audit trail names rahul for his changes. Even the admin cannot DELETE it, TRUNCATE it or drop its trigger. |
| 4:15 | S3 | | ROOT: `source demo/02e_sqli_setup.sql`, RAHUL: `source demo/02f_sqli_attack.sql`, ROOT: `source demo/02g_sqli_cleanup.sql` | **SQL injection.** `' OR 1=1` returns all 9 incidents to rahul, and a UNION leaks every analyst's email, although he only has EXECUTE. The parameterised version returns nothing. The vulnerable procedure is dropped again. |
| 5:30 | S3 | **3. Transaction + failure** | ROOT: `source demo/03_transaction.sql` | First the trap: one failed INSERT, then COMMIT keeps the other row (MySQL does not roll back a transaction on its own). Then `sp_load_log_batch`: its handler rolls back the whole batch (0 rows), and a good batch commits 3. Then a savepoint. |
| 6:30 | S1 | **4. Triggers** | ROOT: `source demo/04_triggers.sql` | A severity-9 attack opens an incident by itself. Reporting `172.16.3.4` makes the database search 50,000 old logs: 24 hits on 9 assets give a CRITICAL incident. Overlapping and deleted IOCs are refused. |
| 7:30 | S3 | **5. Optimisation** | ROOT: `source demo/05_optimisation.sql` | Without the index: `type: ALL`, about 50,000 rows. With `idx_src_time (src_ip, log_time)`: `type: range`, 8 rows. EXPLAIN ANALYZE gives real time. A function on the column hides the index again. |
| 8:30 | S2 + S3 | **6. Concurrency** | ROOT and ANANYA side by side, following `demo/06_concurrency.md` 6.1 and 6.2 | Lost update: both escalate MEDIUM to HIGH, and the audit trail shows ananya overwrote HIGH with HIGH. Then `FOR UPDATE`: **say "B will now freeze"**, A commits, B reads HIGH and sets CRITICAL. |
| 10:15 | S1 | Close | Show `demo/07_backup_recovery.md` and `demo/evidence/pitr.txt` | "If someone deletes data at 3:15, we restore last night's dump and replay the binary log up to the DELETE." Then say what we cut since Review 2 and why (`reports/Review3_scope_revision.md`). |

## When something goes wrong

| Problem | Fix |
|---|---|
| A demo account is locked (ERROR 3955) | ROOT: `source demo/00_reset_accounts.sql` |
| A terminal freezes for more than 5 seconds | It is waiting for a lock: `COMMIT;` or `ROLLBACK;` in the other terminal. Set `SET SESSION innodb_lock_wait_timeout = 5;` at the start. |
| ERROR 1205 Lock wait timeout | Only the statement was rolled back: `ROLLBACK;` and start that scenario again |
| `idx_src_time` is missing after an interrupted step 5 | `CREATE INDEX idx_src_time ON network_log (src_ip, log_time);` |
| `sp_search_incidents_unsafe` left installed | `source demo/02g_sqli_cleanup.sql` |
| Anything else | Run `runner/RUN_ME.bat` again (20 s) and carry on, or play the backup video |

## Evidence to have open in a second window

- `mysql-output/`: the real output of every build step, from the machine it was run on.
- `demo/evidence/concurrency.txt` and `demo/evidence/pitr.txt`: the rehearsed runs of steps 6 and 7.
- `docs/viva_map.md`: all 34 viva questions, each answered on our own tables.
