# Backup and point-in-time recovery

This answers the viva question "the table is emptied at 3:15 PM; recover it to 3:14 PM". Rehearse it once, take screenshots, and show the screenshots. **Do not run it live.**

Every command below was run on MySQL 8.0.46 and worked. The transcript is in `demo/evidence/pitr.txt`.

## The idea in one paragraph

A full backup is a snapshot. It holds the database as it was at one moment. The binary log (binlog) records every change made after that, in order, and each change has a position number.

To recover, restore the snapshot. Then replay the binlog from the snapshot's position up to the position just before the bad statement. Changes made after the backup come back, and the accident does not. Use a position, not a time: `--stop-datetime` only has one-second resolution, and the bad statement may share its second with good ones.

## Before you start

```sql
SELECT @@log_bin, @@binlog_format;   -- 1, ROW   (binlog is on by default in MySQL 8.0)
SHOW BINARY LOGS;
```

Run the commands from `cmd` or PowerShell in a folder you can write to. `mysql`, `mysqldump` and `mysqlbinlog` are in `C:\Program Files\MySQL\MySQL Server 8.0\bin`.

The commands use `--result-file` and `source` instead of `>` and `|`. PowerShell 5.1 re-encodes text that passes through a pipe, and that corrupts the dump.

## 1. Full backup (nightly)

```
mysqldump --login-path=sx_root --single-transaction --source-data=2 --routines --triggers --events --databases sentinelx --result-file=sentinelx_full.sql
```

- `--single-transaction` takes a consistent InnoDB snapshot without locking the tables.
- `--source-data=2` writes the binlog position of that snapshot into the file as a comment:
  `-- CHANGE MASTER TO MASTER_LOG_FILE='binlog.000002', MASTER_LOG_POS=16453827;`
- `--routines --triggers --events` are needed. Without them the procedures are not in the backup.
- Users and grants live in the `mysql` schema and are **not** in this dump. They are re-created by `sql/12_security.sql`.

## 2. Normal work continues (this must survive)

```sql
INSERT INTO attack_event (event_time, src_ip, src_country, asset_id, type_id, severity, blocked)
VALUES ('2026-10-29 15:10:00', '203.0.113.123', 'US', 2, 4, 5, 1);
UPDATE incident SET status = 'INVESTIGATING' WHERE incident_id = 6;
```

## 3. The accident at 3:15 PM

```sql
DELETE FROM asset_vulnerability;      -- every patch record gone (9 rows)
```

## 4. Find the bad transaction in the binlog

```sql
SHOW BINLOG EVENTS IN 'binlog.000002' FROM 16453827;
```

```
| Pos      | Event_type     | Info                                          |
| 16453827 | Anonymous_Gtid | ...                                           |  <- the INSERT (keep)
| 16454338 | Anonymous_Gtid | ...                                           |  <- the UPDATE (keep)
| 16454920 | Anonymous_Gtid | SET @@SESSION.GTID_NEXT= 'ANONYMOUS'          |  <- start of the bad transaction
| 16454999 | Query          | BEGIN                                         |
| 16455079 | Table_map      | table_id: 550 (sentinelx.asset_vulnerability) |
| 16455159 | Delete_rows    | table_id: 550 flags: STMT_END_F               |
```

The stop position is the `Pos` of the bad transaction's first event: **16454920**.

## 5. Restore the backup, then replay up to the stop position

Neither step should be written to the binlog again, so both switch it off for their own session.

```
mysql --login-path=sx_root --init-command="SET sql_log_bin=0" -e "source sentinelx_full.sql"

mysqlbinlog --read-from-remote-server --login-path=sx_root --start-position=16453827 --stop-position=16454920 --disable-log-bin --result-file=replay.sql binlog.000002

mysql --login-path=sx_root -e "source replay.sql"
```

`--read-from-remote-server` reads the binlog through the server, so you do not need the path of the data folder.

## 6. Check

```sql
SELECT COUNT(*) FROM asset_vulnerability;                       -- 9    the accident is undone
SELECT COUNT(*) FROM attack_event WHERE src_ip = '203.0.113.123'; -- 1  work after the backup is back
SELECT status FROM incident WHERE incident_id = 6;              -- INVESTIGATING
```

Triggers do not fire a second time during the replay. With `binlog_format = ROW` the binlog stores the rows each statement changed, including the rows our triggers wrote to `incident_audit`, and replay applies those rows directly.

## Talking points

- **Durability after a power failure** is a different mechanism from this. InnoDB writes every change to its redo log and flushes it to disk at COMMIT (`innodb_flush_log_at_trx_commit = 1`). After a crash, InnoDB replays the redo log. The doublewrite buffer protects against half-written pages.
- **Backups protect against people.** A committed `DELETE` is durable too. Only a backup plus the binlog can undo it.
- Keep the backup file on another disk or machine. A backup on the same disk dies with the disk.
