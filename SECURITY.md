# Security / 安全条件

Trusted local SQLite and synthetic fixtures only. No external network, subprocess, arbitrary SQL or migration interface.
Inputs are read-only; new output directory required. Protect generated DBs, business keys and hashes as potentially sensitive.
No malicious database sandbox, race isolation, repair or disaster recovery guarantee.
Manifest stored beside its backup is not an independent trust anchor. Authenticity/custody must be managed externally.
Private vulnerability reporting is proposed but is **not confirmed enabled**. Until a private reporting channel is configured, do not place confidential vulnerabilities or logs in public issues.
The repository is public. Experimental pre-release v0.1.0 was published on 2026-11-14. The MIT copyright line is attributed to KenKan964 in the updated main branch; the v0.1.0 tag remains an unchanged historical source snapshot. Private vulnerability reporting activation is still unverified. Check the latest six-environment CI results in GitHub Actions rather than historical snapshots.

FIX-01: evidence artifacts are exclusive-create and reject static symlink paths; warning gate forces GC and displays captured ResourceWarning. No timestamp authenticity or same-user race guarantee. Windows verification requires actual GitHub Actions job results; check the latest completed run before publication.
