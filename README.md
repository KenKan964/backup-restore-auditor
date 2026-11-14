# Backup Restore Auditor

**Restore a SQLite backup to a separate database and check its contents against a declared snapshot manifest — without altering the backup.**

**v0.1.0 · Experimental · Python 3.11+ · Standard library only · MIT License**

**English** | [日本語](README_ja.md)

## What does it do?

A backup file is not automatically evidence of a usable or complete restore. Even if SQLite can open it, business records may be missing or changed, the schema may differ, or foreign-key constraints may be broken.

**Backup Restore Auditor (BRA)** is a free, local command-line test tool that:

1. Opens a trusted SQLite backup **read-only**.
2. Uses SQLite's **Backup API** to restore a separate, new test database.
3. Compares the restored schema, record counts and **every declared keyed row hash** with an expected manifest.
4. Runs SQLite integrity and foreign-key checks, and writes a JSON diagnostic report.

It also has a `capture` command to create a backup and manifest together from a source DB. **Capturing a manifest does not independently authenticate it:** the person running the audit must establish the manifest's provenance and custody.

> **Scope:** Controlled, local SQLite snapshot inspection — **not** a production disaster-recovery service, backup scheduling system, or proof of latest business state, RPO, RTO or application continuity.

## What it checks

| Check | Evidence compared |
| --- | --- |
| Database integrity | SQLite `PRAGMA integrity_check` |
| Foreign-key relationships | SQLite `PRAGMA foreign_key_check` |
| Schema | Exact SQL text for the declared database schema |
| Table coverage and counts | All SQLite tables, including empty tables, must be represented in the manifest |
| Business records | Unique, non-null text/integer keys and a SHA-256 digest for **every** keyed row |
| Changed or missing records | Row-hash and key differences, not just row counts |
| Evidence availability | Invalid manifests, missing tables and unsupported snapshot evidence are not silently accepted |

The test can detect a record change that leaves the total row count unchanged. It does **not** prove that a supplied manifest reflects the actual state at a particular real-world time.

## Quick start

**Requirements:** Python 3.11 or newer, with no additional packages. Run these commands from the repository root and use a **new output directory** every time.

```sh
python bra.py demo --out bra-demo-001
```

This creates synthetic source data, captures a backup and expected manifest, restores a copy, and checks the restored result. Its main output files are:

```text
bra-demo-001/
  source.sqlite
  capture/
    backup.sqlite
    expected.json
  restore/
    restored.sqlite
    report.json
```

You can also inspect the committed synthetic fixture:

```sh
python bra.py run --backup samples/backup.sqlite --manifest samples/expected.json --out bra-restore-001
```

On Windows, `py -3` can be used instead of `python`. The output's parent directory must exist; existing destinations and symlink path components are rejected. The restored database and report are **retained for manual inspection**, not automatically removed.

### Capture your own controlled snapshot

The `capture` command creates a snapshot backup and its manifest in a new directory, with a single business key column for each table:

```sh
python bra.py capture --db samples/backup.sqlite --keys '{"people":"id","orders":"id"}' --out bra-capture-001
```

The example above uses POSIX shell quoting. On Windows PowerShell, quote and escape the JSON argument according to the shell. Capturing returns `CAPTURED_NOT_AUDITED`, **not** a passing independent restore audit. Review and retain the manifest separately under a trustworthy custody process before treating it as expected evidence.

## Read a result

A successful synthetic audit produces a JSON report like this **excerpt from the recorded demo**:

```json
{
  "schema_version": "bra-report-v1",
  "status": "MATCH",
  "exit_code": 0,
  "findings": [],
  "manifest_trust": "CALLER_SUPPLIED_NOT_EXTERNALLY_AUTHENTICATED",
  "integrity_check": ["ok"],
  "foreign_key_check": []
}
```

See the [recorded demo JSON](evidence/demo.stdout.json) for the complete historical example. A deliberately changed saved value is expected to produce `VIOLATION` rather than `MATCH`; the [recorded CLI checks](evidence/cli_checks.json) include a normal, tampered and unverifiable example.

| Exit | Status | Meaning |
| ---: | --- | --- |
| `0` | `MATCH` | Restored data matches **the supplied manifest** and declared checks |
| `1` | `VIOLATION` | A verifiable difference or integrity violation was detected |
| `2` | `UNVERIFIABLE` | The available evidence, input or environment is insufficient for a reliable result |

A negative-control test that correctly detects a defective backup **passes the test**; the defective backup still has a CLI failure status. Never interpret `MATCH` as independently verified manifest authenticity.

## Expected manifest: what to trust

See [samples/expected.json](samples/expected.json) and [MANIFEST_FORMAT.md](MANIFEST_FORMAT.md).

The v1 manifest declares `method: sqlite_backup_api`, a timezone-aware ISO 8601 `snapshot_at`, exact schema SQL, and `{key, count, records}` for every table. All keyed rows are hashed with type-tagged values (including BLOBs). Keys must be unique, non-null integers or strings; composite keys and fuzzy matching are not supported.

`Z`, `+09:00` and `-07:00` time-zone offsets are accepted. A timezone-less or invalid timestamp is rejected. **A well-formed timestamp is not proof of when the snapshot was actually taken.** The method and timestamp fields are caller declarations, not authenticated attestations. Hashes are not signatures and may expose information about predictable content.

## Testing and reproducibility

The FIX-01 candidate has **37 automated acceptance/regression tests** (28 original tests and 9 added checks). In an independent Linux/Python 3.13.5 review, all 37 passed with **zero unclosed SQLite connection `ResourceWarning` notices** after forced garbage collection. The comparison experiment uses four synthetic inputs across BRA and a limited SQLite/Python baseline (eight executions). This does not prove speed, ROI, or universal detection superiority.

GitHub Actions targets **Ubuntu and Windows × Python 3.11, 3.12 and 3.13**. Check the [live Actions page](https://github.com/KenKan964/backup-restore-auditor/actions) for the current branch's actual results. [evidence/ci_status.json](evidence/ci_status.json) is a **pre-repository historical snapshot**, not a live CI result.

```sh
python -m unittest discover -s tests -v
python -X tracemalloc=5 tools/verify_resources.py
python compare.py > comparison-local.json
```

The resource verification runner performs the tests, three additional fixture generations, the comparison and forced GC. Set `BRA_EVIDENCE` to a **fresh output directory** to store its per-case evidence. Existing files and symlink destinations cause the suite to fail instead of overwriting data.

## Limitations and security

- **Trusted local SQLite only.** Do not use untrusted or adversarial database files; this is not a malicious-database sandbox.
- The backup and capture inputs are opened in read-only mode. The restore writes only to a **separate new output directory**; no SQL migration or arbitrary command interface exists.
- A copy of a main `.sqlite` file alone may omit committed **WAL** contents. The tool uses SQLite's Backup API for snapshots, but it **cannot always infer** an undisclosed missing WAL or prove the presence of external business effects.
- A matching restored database does not prove the snapshot is the **latest** production state, guarantee application recovery, or establish an RPO/RTO target.
- A byte hash for the main backup file does not attest to the unchanged state of WAL/SHM sidecars under concurrent writes.
- Reports may contain table names, typed business-key tokens, schema differences and hashes. Treat the restored DB, manifests and reports as potentially sensitive.
- Resource limits are cooperative; the tool provides no complete isolation against malicious file-system races, resource exhaustion, or concurrent writers.

## Documentation

[日本語 README](README_ja.md) · [Manifest v1 format](MANIFEST_FORMAT.md) · [Technical specification](TECHNICAL_SPEC.md) · [Security](SECURITY.md) · [Comparison and limits](OSS_COMPARISON.md) · [FIX-01 changes](FIX01_CHANGES.md) · [Verification report (Japanese)](REPORT_ja.md) · [Change history](CHANGELOG.md) · [MIT License](LICENSE)

**License:** MIT · Copyright (c) 2026 KenKan964. See [LICENSE](LICENSE).
