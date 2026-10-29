# Viva map: every question in the bank, answered on SentinelX

The examiner picks 5–6 of these per student and scores each 0–3. A **3** needs the answer to be correct, justified and tied to *our* project. So every answer below names a SentinelX table, query or file. Where it says **Show**, open that file or run that query.

Suggested leads follow the Review 2 work breakdown:

| Questions | Topic | Lead |
|---|---|---|
| 1–10 | Design and constraints | Shreya |
| 11–17 | Queries | Yashneil |
| 18–27 | Indexes and transactions | Shlok |
| 28–34 | Procedural SQL and security | All |

If the examiner compares a live rebuild with the report: the rules and results are the same, but EXPLAIN row estimates (sampled statistics), timestamps and AUTO_INCREMENT ids after rolled-back changes will differ slightly.

**Everyone must be able to answer all 34**, because the draw is random. Practise with a mock viva: draw 6 at random, and the other two score you 0–3.

---

## Design and normalisation

**1. Why `asset_id` as the primary key? Which other candidate keys exist? Why not a natural key?**
- `hostname` and `ip_address` are both UNIQUE NOT NULL, so both are candidate keys. We rejected them because servers get renamed and re-addressed.
- With a natural key, every change would have to cascade into `network_log` (50,021 rows) and `attack_event`.
- A 4-byte INT also makes joins and indexes smaller than a VARCHAR(63).
- **Show:** `SHOW INDEX FROM asset;` lists three unique indexes.

**2. Give one functional dependency and prove it with attribute closure.**
- In `attack_type(type_id, type_name, mitre_technique, base_severity)`: `mitre_technique → type_id`, because each MITRE technique is one of our attack types (UNIQUE).
- Closure: {mitre_technique}⁺ = {mitre_technique, type_id} → add {type_name, base_severity} through `type_id → …`. That is all four attributes, so `mitre_technique` is a candidate key.
- **Show:** `demo/08_viva_showme.sql` Q2 returns an empty result, so no technique maps to two types.

**3. Show an update anomaly if two of your tables were merged. Which normal form prevents it?**
- Merge `attack_event` and `asset`, so each attack row repeats the host's `criticality`. Then change `web-01`'s criticality on one row only, and web-01 has two criticalities.
- 3NF prevents this: `event_id → asset_id → criticality` is a transitive dependency.
- **Show:** `08_viva_showme.sql` Q3 prints `web-01 | 1,5`.

**4. Is every 3NF relation also in BCNF? Give one where they could differ.**
- Ours are in BCNF: every determinant is a candidate key. In `attack_type`, the determinants `type_id`, `mitre_technique` and `type_name` are all keys.
- It could differ in `mitigation(type_id, step_no, action)` if we added the rule "each action text belongs to exactly one attack type" (`action → type_id`). `action` is not a superkey, but `type_id` is prime, so the table would be 3NF but not BCNF.

**5. When would you denormalise? What risk do you take?**
- For a dashboard that is too slow: store `attack_count` on `asset`, kept up to date by a trigger, instead of computing it in `v_asset_risk`.
- The risk is drift. We actually removed `retro_hunt_run.logs_matched` in Review 2 (change 4) because a stored count can go out of sync with `retro_hit`. The view `v_retro_hunt_summary` computes it instead.

**6. What is the primary key of your M:N junction table, and why?**
- `incident_event(incident_id, event_id)`: one attack is linked to one incident at most once, and the composite key enforces that.
- `asset_vulnerability(asset_id, cve_id)` also carries relationship attributes (`detected_at`, `patched_at`), which belong to the pair rather than to either side.

## Constraints and integrity

**7. Where did you use ON DELETE CASCADE, and where RESTRICT? What goes wrong if you swap them?**
- **CASCADE:** `asset_vulnerability → asset` (patch records mean nothing without the server); `incident_event → incident`; `mitigation → attack_type` (weak entity).
- **RESTRICT** (the default): `attack_event → asset`. You cannot delete a server that has attack history, because that history is evidence.
- **SET NULL:** `malware.actor_id`.
- Swapped: CASCADE on `attack_event → asset` means decommissioning a server silently deletes its attacks and unlinks incidents.
- **Show:** test T06, `DELETE FROM asset WHERE asset_id = 1` → ERROR 1451.

**8. What happens when a referenced parent row is deleted? Demonstrate.**
- An asset that has attacks: refused with 1451 (T06).
- An incident: its `incident_event` rows are removed automatically (T09, run inside a transaction and rolled back).
- Note: cascaded deletes do **not** fire triggers.

**9. Why doesn't CHECK (qty > 0) reject NULL? How do you fix it?**
- CHECK fails only when the condition is FALSE. For NULL it is UNKNOWN, which passes.
- `threat_actor.origin_country` has a REGEXP check, and Byte Bandits still stores NULL (Q9 in the show-me file).
- Fix: add `NOT NULL`, as we did for `criticality`.

**10. DELETE vs TRUNCATE vs DROP: which can be rolled back? Do triggers and FKs matter?**

| | DELETE | TRUNCATE | DROP |
|---|---|---|---|
| Kind | DML, row by row | DDL | DDL |
| Fires DELETE triggers | Yes | No | No (removes the table and its triggers) |
| Can be rolled back | Yes | No, implicit commit | No, implicit commit |
| Allowed on a table other tables point to | Yes, rows checked one by one | No: `TRUNCATE asset` → ERROR 1701 | — |

- TRUNCATE needs the DROP privilege. That is why `sx_admin` cannot truncate `incident_audit` (test A04). It cannot DELETE or INSERT there either: only the triggers write it (A03, A06).

## Queries

**11. Why LEFT JOIN and not INNER JOIN? Show the row that would be lost.**
- C2 counts attacks per asset. An INNER JOIN drops `ws-dev-01`, which has never been attacked (Q11 in the show-me file).

**12. WHERE vs HAVING: rewrite one query wrongly and explain the difference.**
- B5: `WHERE e.severity >= 7` filters rows before grouping; `HAVING COUNT(*) >= 2` filters groups.
- Moving the severity test into HAVING gives ERROR 1054 (unknown column in the HAVING clause): after grouping, single rows' `severity` no longer exists.
- Moving the COUNT into WHERE gives ERROR 1111 (invalid use of a group function): groups don't exist yet when WHERE runs.

**13. NOT IN returns nothing because of a NULL. Why, and what is the fix?**
- D9: `malware.actor_id` is NULL for OrphanMiner, so `actor_id NOT IN (…, NULL)` is never TRUE.
- Fix: `WHERE actor_id IS NOT NULL` inside the subquery, or use NOT EXISTS (D8 style).
- **Show:** test T22.

**14. EXISTS vs IN: when does the optimiser treat them differently? Which did you use and why?**
- D7 uses EXISTS: actors with an unblocked attack. MySQL 8 turns both IN and EXISTS into a semi-join.
- They differ on NULLs with the NOT forms (Q13), and EXISTS can stop at the first match.

**15. Rewrite your correlated subquery as a join. Which is faster on 1M rows, and why?**
- D6 finds the worst attack per asset.
- As a join: compute `SELECT asset_id, MAX(severity) … GROUP BY asset_id` once, then join on (asset_id, severity). Or use `RANK() OVER (PARTITION BY asset_id ORDER BY severity DESC)`, as in G1.
- On 1M rows the join or window version scans once. The correlated form can re-run the subquery per row unless an index on `(asset_id, severity)` makes each run a quick lookup.

**16. UNION vs UNION ALL: cost difference, and when the wrong choice gives a wrong answer.**
- E1 lists countries from attacks and from actors with UNION, so the duplicates are removed (that needs a temporary table and de-duplication).
- UNION ALL is cheaper. Use it when duplicates are meaningful, for example counting events from two sources.
- UNION would silently merge two identical event rows. UNION ALL in E1 would list RU twice.

**17. COUNT(\*), COUNT(col), COUNT(DISTINCT col): predict the three results on your data.**
- On the 30 seed attacks: `COUNT(*) = 30`, `COUNT(malware_id) = 18` (NULLs skipped), `COUNT(DISTINCT malware_id) = 7`.
- **Show:** Q17 in the show-me file.

## Indexes and optimisation

**18. Why index (src_ip, log_time) in that order? Will WHERE log_time = ? use it?**
- Retro-hunt filters `src_ip = ?` (equality) and `log_time` (a range). Equality first means all matching entries sit in one contiguous slice of the index.
- `WHERE log_time …` alone cannot do a normal seek. MySQL 8 can still use **skip scan**, one range per distinct `src_ip` (1,004 of them). Without it, the plan is a full index scan.
- **Show:** step 183, both plans.

**19. An index that exists but is not used.**
- `WHERE SUBSTRING_INDEX(src_ip, '.', 3) = '198.51.100'` gives type `index` and reads about 50,000 rows: the function hides the column.
- `src_ip LIKE '198.51.100.%'` gives type `range`, about 16 rows. `LIKE '%.77'` (leading wildcard) also cannot seek.

**20. Explain your EXPLAIN output row by row.**

| Column | Value | Meaning |
|---|---|---|
| type | `range` (was `ALL`) | Read a slice of the index instead of every row |
| key | `idx_src_time` | The index chosen |
| key_len | 187 | Both columns used: VARCHAR(45) in utf8mb4 = 45×4+2 bytes, plus DATETIME = 5 bytes |
| rows | 8 (was about 50,000) | Estimated rows read: an estimate from table statistics, so it moves a little after every ANALYZE TABLE |
| Extra | `Using index condition` | The `log_time` range is checked inside the index before rows are fetched (`dst_asset_id` is not in the index, so the row is still read) |

- For joins, MySQL 8 uses nested-loop with index lookups (`eq_ref`/`ref`), or a hash join when there is no usable index.
- **Show:** EXPLAIN ANALYZE in step 183 gives real time and rows.

**21. Your table has 200 rows and the index gives no speed-up. Why? How would you prove the benefit?**
- `asset` has 10 rows on a single page, so a full scan is cheaper than an index lookup and the optimiser ignores the index.
- We proved the benefit on 50,021 log lines: about 50,000 estimated rows become 8 (steps 181/182).

**22. What does adding five more indexes cost?**
- Every insert into `network_log` must update every index B+tree: slower loads (our 50,000-row CTE) and slower retro-hunt inserts.
- They also take more disk and buffer pool, and give the optimiser more plans to cost.
- Index what queries actually filter on: we have 2 on `network_log`.

## Transactions and concurrency

**23. Two customers buy the last item at the same time. What happens at READ COMMITTED, and how do you prevent overselling?**
- Our version: two analysts claim the same unassigned incident. Both read "unassigned", both update, and the last writer wins.
- `sp_assign_incident` prevents it with `SELECT … FOR UPDATE`: the second caller waits, then sees the incident is taken and gets the 1644 error.

**24. Explain a lost update with your tables, and two ways to prevent it.**
- **Show:** demo 6.1. Two sessions raise incident 6 "one level" and it ends at HIGH, not CRITICAL. The audit trail shows ananya overwriting HIGH with HIGH.
- Fixes:
  1. Pessimistic locking: `SELECT … FOR UPDATE` (demo 6.2).
  2. Optimistic versioning: add a `version` column and `UPDATE … WHERE version = :read`. 0 rows updated means someone else changed it, so retry.
  3. Make the change atomic: `UPDATE … SET priority = next_level(priority)`.
  4. SERIALIZABLE isolation: turns the conflict into a wait or a deadlock.

**25. Dirty read, non-repeatable read, phantom: which isolation level prevents each?**

| Level | Dirty read | Non-repeatable read | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | Possible | Possible | Possible |
| READ COMMITTED | Prevented | Possible | Possible |
| REPEATABLE READ (our default) | Prevented | Prevented | Prevented for plain reads (snapshot); locking reads use next-key locks |
| SERIALIZABLE | Prevented | Prevented | Prevented |

- **Show:** demo 6.4.

**26. How does your DBMS guarantee durability after a power failure?**
- InnoDB writes the redo log and flushes it to disk at every COMMIT (`innodb_flush_log_at_trx_commit = 1`). The doublewrite buffer guards against torn pages. The binlog is synced too (`sync_binlog = 1`).
- After a crash, the redo log is replayed.
- **Show:** Q25/26 in the show-me file.

**27. How could a deadlock occur in your procedure? How do you avoid it?**
- `sp_assign_incident` locks a single incident row, so on its own it cannot deadlock.
- Two transactions that lock incidents 3 and 6 in opposite orders do deadlock: demo 6.3 gives ERROR 1213, and InnoDB rolls one back.
- Avoid it: lock in a fixed order (lowest id first; `sp_escalate_incidents` walks `ORDER BY incident_id`), keep transactions short, and retry on 1213.

## Procedural SQL and security

**28. Why is your rule in a procedure or trigger and not the application? Give a trigger hazard.**
- Rules that must never be skipped live in the database. "Severity ≥ 8 opens an incident" and "IOC history is append-only" hold whichever tool writes the data.
- Hazards from our own triggers:
  - The retro-hunt trigger scans logs inside the INSERT's transaction, holding locks: a second insert of the same IP waits until the first commits (rehearsed: about 2 s), then is rejected.
  - The auto-incident trigger has a hidden side effect: an INSERT into `attack_event` also writes `incident`.
  - Cascaded deletes do not fire triggers.

**29. Function vs procedure: why is X a function? Can it be used in SELECT? Can it contain a transaction?**
- `fn_asset_risk` returns one value, so it can be used inside SELECT (`SELECT hostname, fn_asset_risk(asset_id) …`).
- Functions cannot COMMIT or ROLLBACK. `sp_assign_incident` must, so it is a procedure.

**30. Why would a set-based UPDATE beat your cursor? When is a cursor still justified?**
- `sp_escalate_incidents` loops row by row. The same rule as one `UPDATE … JOIN` is in Q30 of the show-me file: one statement, one pass, fewer round trips.
- A cursor is justified when each row needs different follow-up work. Ours writes a per-row `escalation_log`.

**31. Craft an SQL injection, give two defences, and say why GRANT alone doesn't protect.**
- **Show:** demo 2e–2g. `sp_search_incidents_unsafe('%'' OR 1=1 -- ')` returns all 9 incidents to rahul, and a UNION returns every analyst's email.
- Defences:
  1. Parameters (`?`) instead of string concatenation: `sp_search_incidents` returns nothing for the same input.
  2. Least privilege for the code itself: an INVOKER procedure or a low-privilege definer.
  3. Validating input.
- GRANT does not help because rahul only had EXECUTE. The injected SQL ran with the **procedure's** rights (root, as DEFINER), so it could even have read the password hashes in `mysql.user`. A definer account limited to this database would contain it.
- The safe procedure also clears its session variable `@me` and refuses a caller it cannot match to an analyst (test T35).
- PREPARE accepts one statement only, so `'; DROP TABLE` fails with 1064.

**32. A staff member should see only their own data. Design it with views, roles and privileges, without changing the application.**
- `v_my_incidents` filters `assigned_to` by `USER()` (the logged-in account, with the host part stripped) and uses `WITH CHECK OPTION`, so updates cannot move rows outside the filter (1369).
- `sx_analyst` has no base-table privileges at all. Tests S01, S04 and S05.

**33. How are passwords stored in your system? What is wrong with MD5(password)?**
- No passwords are in our tables. People log in as MySQL accounts, which use `caching_sha2_password`: a salted SHA-256 hash with 5,000 rounds (`$A$005$…` in `mysql.user`).
- MD5 is fast and usually unsalted, so rainbow tables and GPUs crack it quickly, and it has known collisions.
- (MySQL itself never used MD5. The old `mysql_native_password` was an unsalted double SHA-1.)
- Accounts also lock after 3 wrong passwords.

**34. The table is emptied at 3:15 PM. How do you recover to 3:14 PM?**
- **Show:** `demo/07_backup_recovery.md`. Restore the nightly `mysqldump`, then replay the binlog from the dump's position up to the position just before the DELETE (`--stop-position`, not datetime).
- Rehearsed: 9 rows back, and the work after the backup kept.

---

## Our own bugs (each one is a strong viva story)

1. **ERROR 1046.** `01_ddl.sql` dropped the database it was using and never selected it again. Our runner hid this by passing `--database`. Lesson: test the exact command you document.
2. **Privilege escalation.** `sp_assign_incident` runs as root (DEFINER). An analyst could use it to give away or take any incident, bypassing the `WITH CHECK OPTION` we were proud of. Fixed by checking `USER()` inside the procedure. (`CURRENT_USER()` there is root. `CALL sp_whoami()` shows both.)
3. **"An error rolls back my transaction."** It doesn't. MySQL undoes only the failed statement. Our Review 2 demo only worked because the script called ROLLBACK. Fixed with an exit handler (`sp_load_log_batch`, step 172).
4. **Closed IOCs blocked new versions.** The overlap trigger also counted versions already closed with `recorded_to`. Fixed in Review 3.
5. **The admin could forge audit rows.** With INSERT on the whole schema, `sx_admin` could add an audit row naming rahul. Now writes are granted per data table and `incident_audit` is read-only for every role; only the triggers write it (tests A06, T34).
6. **IOC history could be rewritten.** Only DELETE was blocked; an UPDATE could change an indicator or reopen a closed version. `trg_ioc_only_close` now allows only closing (T32, T33).
7. **Backdating with `SET timestamp`.** Any session may set its own clock, and `NOW()` follows it. `sp_report_ioc`, the audit triggers and the retro-hunt now use `SYSDATE()`, the real clock (S12).
8. **The "safe" search trusted a session variable.** It read the caller into `@me` without clearing it first. Now it clears it and refuses a caller with no analyst row (T35).
