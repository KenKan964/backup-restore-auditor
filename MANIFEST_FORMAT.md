# Expected manifest v1

Strict fields: manifest_version=1, method="sqlite_backup_api", snapshot_at (ISO8601 with timezone), schema, tables.
schema maps sqlite_schema type:name to exact SQL text (internal sqlite_ objects excluded).
tables maps each table to {key: column-name, count: integer, records: {typed-key-token: SHA256}}.
Every table must be covered. Composite keys/views/virtual-table applications are not supported contracts.
Typed key is compact ASCII JSON [Python-type-name,value]. Row digest is SHA256 of compact ASCII JSON
[[column-name,[type-name,value]], ...] in SELECT * column order; BLOB uses ["blob",hex].
No Unicode normalization or fuzzy equality. Integer and text keys differ. Null/duplicate keys are unverifiable.
No raw representative values are emitted, but hashes are not encryption and can permit dictionary attacks.
All keyed rows are hashed, exceeding a representative-only subset. Schema formatting is compared exactly.
Unknown fields, duplicate JSON keys, incomplete table coverage, incorrect count/hash shape/version are rejected.
Timestamp and method are declarations, not cryptographically verified provenance.
See samples/expected.json for a complete synthetic example.

FIX-01 timezone contract: parse datetime, require tzinfo and non-null utcoffset. Positive/negative/Z supported; naive rejected. No new provenance guarantee.
