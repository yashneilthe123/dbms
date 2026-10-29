# Demo step 6: concurrency, in two terminals

Open two terminals side by side, with different prompts so the examiner can tell them apart:

```
mysql --login-path=sx_root  --prompt="A (root)> "   sentinelx
mysql --login-path=sx_admin --prompt="B (ananya)> " sentinelx
```

Run this in both terminals first, so nothing hangs for 50 seconds:

```sql
SET SESSION innodb_lock_wait_timeout = 5;
```

Reset before each scenario, in A: `UPDATE incident SET priority = 'MEDIUM', status = 'OPEN' WHERE incident_id = 6;`

Paste one numbered step at a time, in the order shown. Say what will happen before you press Enter.

## 6.1 Lost update: two analysts escalate incident 6 "one level up"

| # | Terminal A (root) | Terminal B (ananya) |
|---|---|---|
| 1 | `START TRANSACTION;`<br>`SELECT priority FROM incident WHERE incident_id = 6;` → MEDIUM | |
| 2 | | `START TRANSACTION;`<br>`SELECT priority FROM incident WHERE incident_id = 6;` → MEDIUM |
| 3 | `UPDATE incident SET priority = 'HIGH' WHERE incident_id = 6;`<br>`COMMIT;` | |
| 4 | | `UPDATE incident SET priority = 'HIGH' WHERE incident_id = 6;`<br>`COMMIT;` |
| 5 | `SELECT priority FROM incident WHERE incident_id = 6;` → **HIGH** | |

Two people raised it one level each. It should be CRITICAL, but B's update overwrote A's.

The audit trail proves it. B's row says `old_priority = HIGH`, `new_priority = HIGH`:

```sql
SELECT changed_by, old_priority, new_priority FROM incident_audit
WHERE incident_id = 6 ORDER BY audit_id DESC LIMIT 2;
```

## 6.2 The fix: lock the row when you read it (`SELECT ... FOR UPDATE`)

Reset first. Then:

| # | Terminal A (root) | Terminal B (ananya) |
|---|---|---|
| 1 | `START TRANSACTION;`<br>`SELECT priority FROM incident WHERE incident_id = 6 FOR UPDATE;` → MEDIUM | |
| 2 | | `START TRANSACTION;`<br>`SELECT priority FROM incident WHERE incident_id = 6 FOR UPDATE;`<br>**B freezes. Say so before you press Enter.** |
| 3 | `UPDATE incident SET priority = 'HIGH' WHERE incident_id = 6;`<br>`COMMIT;` | B wakes up and reads **HIGH**. |
| 4 | | `UPDATE incident SET priority = 'CRITICAL' WHERE incident_id = 6;`<br>`COMMIT;` |
| 5 | `SELECT priority FROM incident WHERE incident_id = 6;` → **CRITICAL** | |

If B waits more than 5 seconds it gets `ERROR 1205 Lock wait timeout`. That error rolls back only B's statement, not its transaction: run `ROLLBACK;` in B and start again.

## 6.3 Deadlock (keep as a screenshot unless asked)

| # | Terminal A | Terminal B |
|---|---|---|
| 1 | `START TRANSACTION;`<br>`UPDATE incident SET priority='HIGH' WHERE incident_id = 3;` | |
| 2 | | `START TRANSACTION;`<br>`UPDATE incident SET priority='HIGH' WHERE incident_id = 6;` |
| 3 | `UPDATE incident SET priority='HIGH' WHERE incident_id = 6;` → A waits | |
| 4 | | `UPDATE incident SET priority='HIGH' WHERE incident_id = 3;` → **ERROR 1213 Deadlock**: B is rolled back |
| 5 | A continues. `COMMIT;` | |

Then, in A: `SHOW ENGINE INNODB STATUS\G` shows the LATEST DETECTED DEADLOCK section.

Prevention: always lock rows in the same order, for example lowest `incident_id` first, and retry on 1213.

## 6.4 Isolation level: non-repeatable read (whiteboard backup)

| # | Terminal A | Terminal B |
|---|---|---|
| 1 | `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;`<br>`START TRANSACTION;`<br>`SELECT status FROM incident WHERE incident_id = 6;` → OPEN | |
| 2 | | `UPDATE incident SET status = 'INVESTIGATING' WHERE incident_id = 6;` (autocommit) |
| 3 | `SELECT status FROM incident WHERE incident_id = 6;` → **INVESTIGATING**, a different answer inside one transaction<br>`COMMIT;` | |

Repeat with `REPEATABLE READ`, MySQL's default. Step 3 then still says **OPEN**, because the transaction reads from its own snapshot.

## 6.5 Our own triggers serialise too (talking point)

When two sessions insert the same bad IP at the same moment, the second one waits about 3 seconds and is then rejected. The SELECT inside `trg_ioc_no_overlap` runs as part of an INSERT, so InnoDB makes it a locking read. The waiting session therefore sees the first row once it commits.

Each scenario above was rehearsed on MySQL 8.0.46. The output is in `demo/evidence/concurrency.txt`.
