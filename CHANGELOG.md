# Unreleased — documentation and attribution correction (2026-11-14)

- Correct the MIT license copyright attribution to `KenKan964`, at the repository owner's request.
- Align the English/Japanese READMEs and security guidance with the corrected attribution and actual public pre-release state.
- No source code, database fixtures, or tests changed.
- Published `v0.1.0` remains a historical tagged snapshot. A new tag is required to distribute the corrected license in a source archive.

# 0.1.0 / FIX-01 — 2026-11-14

- Exclusive test evidence output, collision/symlink protection.
- Explicit SQLite connection close preserving transaction ordering.
- Parsed timezone validation accepts negative UTC offsets.
- 28 existing +9 regression tests; ResourceWarning0 after repeated fixtures/comparison/GC locally.
- At the original FIX-01 delivery: Windows/six-job CI NOT_RUN, public HOLD (historical snapshot). Subsequent GitHub Actions main-branch run #3 passed all six matrix jobs and experimental pre-release v0.1.0 was published on 2026-11-14.
