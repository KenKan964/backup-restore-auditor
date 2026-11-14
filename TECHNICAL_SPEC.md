# Technical specification

API audit(backup_path, manifest_path, out) -> bra-report-v1 JSON dictionary.
capture(source_path,out,keys) uses Backup API and creates manifest from the destination snapshot.
run never edits source. Report records tool_version, restore_id (output directory name), input/manifest hashes,
snapshot_at, integrity_check, foreign_key_check and diagnostic differences.
Backup API rather than main-file copying is used for WAL-aware committed snapshots.

Checks: integrity and foreign keys separately; exact schema SQL; count and all typed-key row hashes.
Codes: CORRUPT_BACKUP, FOREIGN_KEY_VIOLATION, SCHEMA_MISMATCH, CONTENT_MISMATCH,
UNVERIFIABLE_TABLE, SOURCE_CHANGED, UNVERIFIABLE, OUTPUT_FAILED.
Missing table/readback failure is exit2; readable content/schema violation is exit1. Any inspection exception remains unverifiable.
Empty SQLite database with an empty-table manifest is valid; zero-byte backup input is rejected as ambiguous.
Unreadable/corrupt/non-SQLite files return JSON/2, never PASS. Existing output destinations are refused.
Source connections use mode=ro, trusted_schema=OFF, extension loading disabled. No caller-supplied SQL is executed.
Inputs and outputs reside in operator-controlled directories; no complete malicious-DB or path-race isolation.
Tables over100000 rows and manifests over20MB are rejected; Backup API deadline10s, integrity/FK progress deadline5s.
Record scans are bounded by count but large BLOBs/DBs are not fully resource-isolated. Only small trusted local materials are intended.

Source SHA is main-file only. For WAL-mode live tests a writer connection remains open, committed WAL data is verified in restored DB.
No production data is used. Caller must separately establish manifest custody and backup completeness.
A fabricated method/time declaration cannot be authenticated by this MVP; false provenance requires external controls.
References: https://www.sqlite.org/backup.html and https://www.sqlite.org/pragma.html

## FIX-01 lifecycle and timestamp correction

fixture and test SQLite contexts use closing outside the original transaction context, so commit/rollback precedes close even on return/exception.
Existing audit finally-close and capture/baseline closing are retained. WAL live-test connection already closes in finally.
Snapshot timezone is determined by parsed datetime.tzinfo and utcoffset, supporting negative offsets.
Test evidence uses open('x',encoding='utf-8'); symlink destination/ancestors rejected. Same-user path races remain outside guarantee.
Existing schema/hash/Backup API/FK and exit-code contracts are retained.
