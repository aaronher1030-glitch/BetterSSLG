# Task 1 report — Checksummed Migration Engine

Status: DONE (completed inline after the delegated implementer was cut off by a credit limit)

## What was implemented

`tools/sslg_migration.py` provides the safety layer for all later file moves:

- `sha256(path)` — chunked streaming hash of any file.
- `safe_relative(value)` — rejects absolute paths, `..` traversal, and backslash paths.
- `collect_baseline(root)` — enumerates root DOCX/PDF files plus `_DUPLICATES_TO_DELETE` and `OM_SSLG_2026_001` contents.
- `preflight_moves(root, files)` — returns sorted errors for unsafe paths, duplicate destinations, missing sources, checksum mismatches, and existing destinations; it never mutates.
- `apply_moves(root, files)` — runs preflight first, refuses to move on any error, creates parent directories, verifies the checksum after each rename, and attempts a full rollback of already-moved entries on any failure.
- `write_manifest(root, data)` / `write_archive_index(root, files)` — write `90 Archive/File Manifest.json` and `90 Archive/Archive Index.md`, refusing to overwrite either if it already exists.

`tools/tests/test_sslg_migration.py` covers baseline discovery, byte-preserving moves with recorded hashes, collision refusal, checksum-mismatch detection, path-escape rejection, and duplicate-destination detection. All fixtures use a temp directory; no real vault file is moved by the tests.

## TDD evidence

- RED: the delegated implementer reported creating the test file before the module and running it against the missing `tools.sslg_migration` import. That output was not preserved in a report file because the dispatch was terminated by the account credit limit before the implementer returned.
- GREEN (controller, re-run after takeover):

```text
$ python -m unittest tools.tests.test_sslg_migration -v
test_baseline_includes_only_sslg_source_and_staging_files ... ok
test_move_preserves_bytes_and_records_original_hash ... ok
test_preflight_rejects_existing_destination_and_bad_hash ... ok
test_preflight_rejects_path_escape_and_duplicate_destinations ... ok
----------------------------------------------------------------------
Ran 4 tests in 0.109s
OK
```

## Files changed

- Created: `tools/sslg_migration.py`
- Created: `tools/tests/test_sslg_migration.py`

## Self-review findings

- Implementation matches the plan's public interfaces and error-message keywords verbatim, so later tasks can rely on them.
- No real vault source was moved; the plan's "do not run migration against the real vault yet" checkpoint is respected.
- Minor: the test file imports `json` without using it. Harmless; will be removed in a later cleanup if not needed for Task 2's manifest test.
- Minor: `tools/__pycache__` and `tools/tests/__pycache__` exist as test artifacts. They will be cleaned before the final report.
- No git commit was created because this workspace is not a git repository (ledger ruling).

---

## Fix round 1 — scoped review findings

**Status:** DONE

**Findings addressed:**
- Important #1: `safe_relative` now rejects Windows drive-relative paths, drive-letter paths, and UNC paths before `PurePosixPath` is consulted (`ntpath.splitdrive` guard in `tools/sslg_migration.py:5-21`).
- Important #2: added `test_preflight_rejects_windows_drive_relative_original_path` and `test_audit_writers_create_then_refuse_to_overwrite` to `tools/tests/test_sslg_migration.py:72-97`; the new test uses the previously unused `json` import, so that Minor finding is also resolved.

**Tests run after the fix:**

```text
$ python -m unittest tools.tests.test_sslg_migration -v
test_audit_writers_create_then_refuse_to_overwrite ... ok
test_baseline_includes_only_sslg_source_and_staging_files ... ok
test_move_preserves_bytes_and_records_original_hash ... ok
test_preflight_rejects_existing_destination_and_bad_hash ... ok
test_preflight_rejects_path_escape_and_duplicate_destinations ... ok
test_preflight_rejects_windows_drive_relative_original_path ... ok
----------------------------------------------------------------------
Ran 6 tests in 0.221s
OK
```

**Deferred:** `apply_moves` rollback re-verification after restore; rename-chain preflight over-refusal; `write_archive_index` escaping of `|` in field values (actual source names contain no pipes; the plan's audit path does not exercise that edge case).

## Concerns

- Because the original implementer subagent died mid-task, the task reviewer dispatch is also currently unavailable (same credit limit). This report and the passing test run are the substitute gate for Task 1. If reviewer capacity returns, re-run the task review over `tools/sslg_migration.py` and its tests.
