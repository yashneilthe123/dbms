# SentinelX: Cyber Attack Intelligence and Threat Hunting Platform

A small Security Operations Centre (SOC) database built for the **Database Systems (BCSE302P) lab project** at VIT Vellore.
Firewall logs, detected attacks, the servers they hit, attacker groups, malware, CVEs, indicators of compromise (IOCs),
incidents and analysts are stored once, linked properly, and searched with plain SQL.

- **16 tables in Third Normal Form (3NF)**, MySQL 8.0
- **Everything here was actually run** on MySQL 8.0.46. The raw client output is in [`mysql-output/`](mysql-output)
- Two features of our own:
  - **Retro-hunt:** when a new bad IP is added, a trigger searches old logs for the time it was already hostile but not yet known, and opens an incident if it finds anything.
  - **Time machine:** every indicator stores *when it was hostile* and *when we learned about it*, so results can be split into "known then" and "learned later".

## ER diagram

![ER diagram](diagrams/er_diagram.png)

Chen notation: 12 entities, 17 relationships (12 one-to-many, one of them identifying; 4 many-to-many; 1 one-to-one).
The relational schema with every foreign key is in [`diagrams/relational_schema.png`](diagrams/relational_schema.png).

## What's in the repo

| Folder | Contents |
| --- | --- |
| [`reports/`](reports) | Review 1 report (ER diagram, tables, normalisation) and Review 2 report (all SQL with real screenshots), as PDF and Word |
| [`sql/`](sql) | The SQL, in run order: `01_ddl.sql` to `12_security.sql`, plus `sentinelx_schema.sql` (schema only) |
| [`runner/`](runner) | One-click Windows runner that executes every step and saves the output |
| [`mysql-output/`](mysql-output) | Real output of every step from MySQL 8.0.46 (`.err.txt` files hold the intended error demos) |
| [`diagrams/`](diagrams) | ER diagram, relational schema, system architecture |
| [`tools/`](tools) | Python that generates the seed data and step files and renders output into screenshots |

## What the SQL covers

| Area | What's there |
| --- | --- |
| DDL | 16 tables with PRIMARY KEY, FOREIGN KEY (CASCADE / SET NULL), UNIQUE, CHECK, ENUM, indexes |
| DML | 10 assets, 30 attacks, 12 IOCs, 7 incidents, 50,021 log lines (50,000 generated with a recursive CTE), UPDATE, DELETE, and 5 statements rejected by constraints |
| Queries | 40 queries: basic, aggregate (WHERE vs HAVING), all join types (FULL OUTER emulated), subqueries (incl. the NOT IN + NULL pitfall), UNION / INTERSECT / EXCEPT, CASE / COALESCE / NULLIF / date / string / numeric, window functions |
| Complex queries | 11 multi-table business queries (CQ-01 to CQ-11) |
| Views | `v_attack_details` (5-table join), `v_asset_risk` (aggregated), `v_my_incidents` (row-level security, WITH CHECK OPTION), `v_vulnerability`, `v_retro_hunt_summary` |
| Routines | `fn_severity_label`, `fn_asset_risk`; `sp_assign_incident` (SELECT ... FOR UPDATE, SIGNAL, ROLLBACK), `sp_attack_report` |
| Triggers | `trg_attack_auto_incident`, `trg_ioc_retro_hunt`, `trg_ioc_no_overlap`, `trg_ioc_no_delete` |
| Cursors | `sp_escalate_incidents`, `sp_asset_risk_report` |
| Transactions | SAVEPOINT / ROLLBACK TO / COMMIT, and a failed batch rolled back as a whole |
| Indexes | EXPLAIN before and after `idx_src_time`: full scan of 50,163 rows down to a range read of 8 |
| Security | Roles `sx_admin`, `sx_analyst`, `sx_viewer`; GRANT / REVOKE; least-privilege errors (1142, 1369) |

## Run it yourself

**Windows (easiest):** install MySQL Server 8.0.31 or later, then double-click `runner/RUN_ME.bat` and type your MySQL root
password. It runs every file in `runner/steps/` and writes the output to `runner/out/`.

**Any OS, with the mysql client:**

```bash
mysql -u root -p < sql/01_ddl.sql
mysql -u root -p sentinelx < sql/02_dml.sql
mysql -u root -p sentinelx --table < sql/03_queries_A_to_G.sql
# ... and so on up to 11_indexes_explain.sql
```

> **Warning:** `01_ddl.sql` starts with `DROP DATABASE IF EXISTS sentinelx`.
>
> The last part of `12_security.sql` has to be run while logged in as the test users it creates (`divya.iyer`, `rahul.mehta`, `ananya.rao`); the runner does this for you. These are local test accounts with made-up passwords.

## About the data

The data is a hand-made test set, so every result can be checked by hand. Attacker IPs come from the address ranges reserved
for documentation (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24), so no real address is marked as bad. Attacker and
malware names are made up. The CVE IDs are real.

## Team

| Name | Registration No. |
| --- | --- |
| Shlok Gupta | 24BCI0061 |
| Shreya Bhushan | 24BCI0086 |
| Yashneil Purkayastha | 24BDS0158 |

Faculty: Dr. Anand Bihari, School of Computer Science and Engineering, VIT Vellore.
