# Task 3 review — Record Notes and Activity Hubs

Reviewer: task reviewer (read-only; only this file was written)
Date: 2026-11-04, ~22:07 local
Deliverables reviewed: `tools/sslg_notes.py`, `tools/tests/test_sslg_notes.py`,
appended test in `tools/tests/test_sslg_content.py`, regenerated `tools/sslg_content.json`,
and the 52 notes generated into the vault.

## Verdict

**SPEC: FAIL** (two binding Activity-Hub spec items undelivered; everything else verified)
**QUALITY: CHANGES REQUESTED**

**Suite is currently RED — see C1.** Final state at 22:12:
`Ran 25 tests ... FAILED (failures=1)`
(`tools/tests/test_sslg_content.py` grew two more tests at 22:12:05, after this package was
cut; the failing one is a manifest data defect, not a renderer defect.)

Critical findings are limited to C1 (blocking, outside the renderer). The Task 3 renderer
itself caused no data loss: no source document was overwritten, no content was invented, and
every mandated record-note/source invariant holds across all 52 real notes.

### Critical

**C1. The delivered test suite does not pass right now, and the failing assertion is real.**
`tools/tests/test_sslg_content.py:77` `test_duplicate_reasons_point_at_a_real_same_hash_file_
without_cycles` fails:
`AssertionError: True is not false : circular pair: OM_SSLG_2026_001 (3).docx <-> OM_SSLG_2026_001 (10).docx`
Both manifest entries declare each other as "byte-identical duplicate of", and both have
`role: duplicate`, so neither names a survivor. Their hash group is exactly
`{(3), (10), (13)}` (`sha e4f8e1db01…`), and `(13)` already points at `(3)`; none of the
three matches the record's primary `OM_SSLG_2026_001.docx`, so these copies are *not*
duplicates of the primary. This text is user-visible: it renders into the Revision history
section of `03 Governance/Memorandum No. 001, s. 2026 - Establishment of LGCC Standing
Committees (25 May 2026).md`.
Attribution: Task 2 manifest data (`tools/sslg_content.json`, mtime 21:56, sha
`5e1ef554d55c`) surfaced by a Task 3-era test addition — the renderer is not implicated.
Fix: in the manifest, keep `(3)` as the cluster head and rewrite `(10)`'s reason to
"byte-identical duplicate of OM_SSLG_2026_001 (3).docx", and rewrite `(3)`'s reason so it
breaks the cycle and stays accurate (e.g. "exact-duplicate cluster head with (10) and (13);
text differs from primary OM_SSLG_2026_001.docx"), then re-run and expect 25 OK.
Gate: do not sign off Task 3 while any test in the combined suite is red.

---

## 1. Claims I independently verified (all TRUE)

Suite re-run: the three modules report **25 tests, 1 FAILURE** at 22:12 (see C1). Earlier in
this review the same command reported 22 OK, and before that 21 OK — the test files were
edited twice *during* the review (see I4). Mutation evidence in §2 was collected against the
11-test note suite (6+5+11 = 22 OK at 22:07).

Structural verification of the real vault (scratch scripts run from
`%LOCALAPPDATA%\Temp`, never inside the vault):

| Check | Result |
| --- | --- |
| All 52 on-disk notes byte-identical to a fresh `render_*` of the manifest | TRUE (0 drift) → deterministic, no hand-edits, no invented prose |
| `## Original document` is the last `## ` section, all 36 record notes | TRUE (36/36) |
| Last non-empty line of every PDF-bearing record note is a `![[...pdf]]` embed | TRUE (10/10; 10 embeds total in vault) |
| DOCX-only notes end with the prominent `Open original DOCX:` link, no fabricated embed | TRUE (26/26) |
| All 13 spec properties + structured `sources:` present in every record note | TRUE (`type, record_type, record_id, date, event_date, school_year, activity, status, source_file, source_path, source_format, related, tags`) |
| `source_file`/`source_path` always point at the `role: primary` entry | TRUE (36/36); `source_keys` roles are only 36 primary + 6 alternative-format |
| `sources:` list matches the manifest entry-for-entry | TRUE |
| TRAIL_STAGES order = proposal → meeting-notice/excuse-letter/request → memorandum → completion-report | TRUE (`sslg_notes.py:5-10`) |
| "Missing stages" names only genuinely absent stages, exact sentence format | TRUE (16/16 hubs, computed independently from linked record types) |
| Windows backslashes leaking into any `current_path`/link | NONE — all forward-slash vault-relative |
| Notes clobbered sources | NONE — 93 root DOCX/PDF present, **0 SHA-256 mismatches** vs the manifest's 104 baseline entries; 0 non-`.md` files created in `02/03/04`; no `Sources/` dir created (no premature Task 6 move); no note path collides with a source path |
| Link integrity | 0 truly broken links. 254 `.md` wikilinks resolve today; the other 131 point at manifest post-migration paths (expected-unresolved, as briefed) |
| Scheduler containment | 0 notes mention `Scheduler_v1-main` |
| Path/filename safety | longest absolute path 225 (< 260); no `<>:"|?*` in note filenames; no `\|` in titles (trail table safe); no newlines in any rendered field |
| Titles with `:` | 2 records (`Onto the Next: Leaders…`) — quoted by `yaml_string` (`sslg_notes.py:14`), valid; filenames use `-` instead |
| Frontmatter parses strictly | TRUE for all 52 — **PyYAML 6.0.3 IS installed** in this environment, contrary to the review instruction's assumption |
| `related:\n  []` empty-list form | valid YAML → parses to `[]` (PyYAML, and for the 6 real empty-`related` notes) |
| `null` for unknown dates | 15 `date: null`, 16 `event_date: null`; no date coerced to a YAML `date` object |

Note: `tools/sslg_content.json` is stored with CRLF (2540 CRLF pairs) while the Python
sources are LF. Harmless for `json.loads`, but it is an inconsistency in the deliverable set.

## 2. Mutation evidence on the three scrutinized tests

Harness: sandbox copy of `tools/` under `%LOCALAPPDATA%\Temp\sslg_mut` (vault untouched).
Each mutant applied to the renderer, suite re-run, renderer restored.

| Mutation | Killed by | Conclusion |
| --- | --- | --- |
| Swap `memorandum` / `completion-report` rows in `TRAIL_STAGES` | `test_activity_trail_orders_proposal_before_letters_then_completion` | real test, not a tautology. `MULTI["records"]` is deliberately scrambled and all dates are `null`, so alphabetical/manifest order would give a different list |
| `_stage_present()` → always `True` | `test_activity_reports_missing_stages_only_for_absent_record_types` + `test_activity_links_record_and_documents_missing_stages` | real test |
| Missing-stage sentence reworded | same two tests | the exact sentence `Not present in the supplied records: <stage>.` IS pinned |
| Collision guard in `generate_notes` neutered | `test_generate_notes_writes_every_note_and_refuses_to_overwrite` + `test_generate_notes_leaves_no_partially_written_note` | real test; the second also proves check-before-write atomicity (nothing else written, pre-existing file preserved) |
| `primary = sources[-1]` | `test_record_has_traceable_metadata_and_original_document_last` + `test_record_lists_every_current_source_representation` | real test |
| **`tags:` block deleted from record frontmatter** (`sslg_notes.py:63`) | **survived — suite green** | see I1 |
| **`activity:` property deleted** (`sslg_notes.py:46`) | **survived — suite green** | see I1 |
| **hub `venue:` property deleted** (`sslg_notes.py:118`) | **survived — suite green** | see I1 |

Caveat on `test_activity_reports_missing_stages_only_for_absent_record_types`
(`test_sslg_notes.py:126`): with only a proposal present it asserts 2 of the 3 expected
missing labels and never checks `"related memoranda"`, so a renderer that silently dropped
the memorandum stage would still pass. No test covers within-stage ordering by date, which
does matter in real data (two activities hold two memoranda each: Project ECOLEAD,
Nationwide Online Survey).

## 3. Findings

### Important

**I1. The brief's mandated required-property set is entirely untested.**
Evidence: the three `tags:`/`activity:`/`venue:` deletion mutants above all leave
`Ran 11 tests ... OK`. The brief (Step 3: "emits all required record properties";
Step 4: `render_activity` "must emit `type: activity`, `title`, `start_date`, `end_date`,
`school_year`, `status`, and `venue`") and spec §Metadata make these load-bearing for
Task 4's Bases views, yet no assertion covers them.
Fix: add to `tools/tests/test_sslg_notes.py` a test that parses the frontmatter block of
one rendered record and one rendered activity and asserts `set(keys) >= REQUIRED` for the
13 record properties and the 7 hub properties, plus `tags[0] == "sslg"`.

**I2. `generate_notes` does not detect duplicate output paths within a single run.**
`tools/sslg_notes.py:196` only probes the filesystem, so two manifest entries resolving to
the same path both pass the check and the second silently overwrites the first.
Demonstrated: with `records[1]["note_path"] = records[0]["note_path"]`, the call returned
52 "written" paths for 36 records while writing 51 files, raising nothing.
Brief conflict: the brief's reference implementation (`task-3-brief.md:179-181`) has
exactly this hole, so the implementer is faithful to the plan. I think the design spec wins
("No move may overwrite an existing destination file"; acceptance criterion 2 "no loss or
overwrite", spec:158, 188). No real data triggers it today — I verified all 52 note paths
are unique, and unique case-insensitively.
Fix: before the disk check, add
`seen, dup = set(), []; for p, _ in outputs: k = str(p).lower(); ...` and include
in-run duplicates in the `FileExistsError`.

**I3. Activity hubs omit two binding spec items: "Related governance" and "organizers".**
spec:80 requires the At-a-glance block to carry organizers; spec:84 item 4 requires a
**Related governance** section linking policies/memoranda that explicitly govern the
activity. Measured over the real vault: `## Related governance` present in **0/16** hubs;
`Organizers` present in **0/16**. (`sslg_notes.py:113-158` simply never emits them.)
Brief conflict: the brief's Step 4 section list omits both, so the implementation matches
the brief. The spec is the higher authority for delivered structure, and the gap is not
blocked on missing data — the evidence already exists in `records[].related`
(e.g. `ACR_SSLG_2026_001` relates to `04 External Memoranda/Division Memorandum
OM-DFSSLG-2026-003…` and `03 Governance/Memorandum No. 001, s. 2026 … (25 May 2026)`),
which the hub never surfaces. Fix: derive `## Related governance` from linked records'
`related` entries whose `note_path` starts with `03 Governance/` or `04 External Memoranda/`
(dedupe, keep only source-evidenced links, otherwise print the spec-sanctioned
"Not stated in source"/"No governing records identified" line) and add
`> **Organizers:** {fmt(...)}`. Otherwise this belongs in the plan as an explicit
deferred item rather than silently dropped.

**I4. Both test files on disk are newer than the review package — the package is not the artifact.**
`task-3-review-package.md:8` presents `test_sslg_notes.py` as **160 lines / 10 tests** and
the report claims "**10 note tests**" / "Ran **21** tests … OK". On disk it is
**172 lines / 11 tests** (sha `528e97b01609…`, mtime 22:04:06). Likewise the package shows
`test_sslg_content.py` at 79 lines / 5 tests; on disk it is 5468 bytes / 8 tests
(sha `be28ba19580e…`, mtime **22:12:05**). Both edits landed *after* the package was written
and *while this review was running* — my first read of each matched the package exactly, and
each was replaced minutes later. The `test_sslg_notes.py` changes are improvements
(`:148-152` now asserts the complete written file set via `rglob`; `:158` adds a real
atomicity test proving check-before-write). The `test_sslg_content.py` additions exposed C1.
`tools/sslg_notes.py` never changed (sha `6637556e6208…`, mtime 21:57) and matches the
package byte-for-byte, so all renderer findings above apply to the reviewed code.
Fix: re-cut the review package, correct the report's counts, and treat 21/22 OK claims as
superseded.

### Minor

**M1. Dates are quoted strings, so Obsidian will type them as Text, not Date.**
`date: "2026-05-27"`, `start_date: null` (`sslg_notes.py:14,44,115-116`). Valid and safe,
and the brief mandates `json.dumps` quoting — brief wins for Task 3. But spec:130 and
acceptance criterion 7 want chronology; Bases date filters/sorts behave better on unquoted
ISO dates or a declared property type. Carry this decision to Task 4 rather than
discovering it there.

**M2. `related:\n  []` (`sslg_notes.py:58-62`).** Valid YAML (verified → `[]`), but the
inline `related: []` is what Obsidian's own frontmatter parser is known to handle. Mandated
verbatim by the brief, so brief wins; flag it for the Task 7 in-app render check, which is
the only place this can actually be settled.

**M3. `activity: ""` for the 5 records with no parent** (`sslg_notes.py:46`). Spec:122 says
the property applies "when applicable"; `null` would be cleaner for Bases "has no activity"
filters than an empty string. Body line "Part of the governance collection." /
"Part of the external collection." (`:67`) is honest and invented-free, just slightly awkward.

**M4. Empty `key_details` renders a bare heading with no fallback** (`sslg_notes.py:77-78`),
and would leave a stray double blank line. Latent only — I confirmed 0 of 36 records have
empty `key_details` (and 0 empty summaries/outcome-less prose gaps). Add the
"Not stated in source" line for symmetry with `fmt`.

**M5. `source_format:` is emitted unquoted from a filename suffix** (`sslg_notes.py:49`),
so a suffix-less file would produce `source_format: ` (empty scalar). Not triggered today
(all 104 files carry `.docx`/`.pdf`). Cheap fix: reuse `yaml_string`.

**M6. Self-referential archive reasons pass through the renderer.**
`04 External Memoranda/Division Memorandum OM-DFSSLG-2026-003-1.pdf` revision-history line
reads: `[[90 Archive/Staging/OM-DFSSLG-2026-003-1.pdf|…]] — staged: pre-existing staging
folder copy, byte-identical to OM-DFSSLG-2026-003-1.pdf` — the "original" named in the
reason is the same basename as the primary, so a reader cannot tell the two files apart.
This is Task 2 manifest wording, not renderer logic (`sslg_notes.py:87`); the renderer is
correct to pass it through. Fix in the manifest by naming the staging path, not the filename.

**M7. `05 General Records/` does not exist because the manifest assigns 0 records there.**
Collections present: activities 27, external 5, governance 4. Spec:63 includes the folder in
the architecture, and the review request asked me to spot-check a note there — **impossible**.
Not a Task 3 defect (`generate_notes` renders exactly what the manifest declares), but the
delivered tree deviates from spec §Vault Architecture, and two candidates that arguably
belong there (the Multi-Purpose Hall request, the Cluster IV notices of meeting) were
attached to activities instead. Ownership: coverage sign-off, not the renderer.

**M8. Redundant review text.** Project ECOLEAD and World Teachers Day hubs print both
"Not present in the supplied records: completion report." and a review reason "No completion
report is present in this collection." Harmless duplication of manifest content
(`sslg_notes.py:145-149` vs `:159-161`); the report already acknowledges it.

## 4. Things I could not verify, and why

1. **Actual Obsidian rendering** — no Obsidian app in this environment. Frontmatter typing
   (M1, M2), callout display, PDF embed preview and Bases compatibility are established only
   by generated text + PyYAML parsing. spec:195 (criterion 9) requires the in-app check and
   requires reporting any check that cannot be done — this is that report.
2. **Whether summaries faithfully describe the DOCX/PDF contents** — requires reading the
   source documents; that is Task 2 scope. I verified the renderer adds nothing beyond the
   manifest (byte-identical re-render), which bounds invention to the manifest layer.
3. **Provenance of the 22:04 test-file edit** — the workspace is not a git repo, so I cannot
   attribute the mid-review change; I reviewed the current disk state and flag the package
   drift in I4.
4. **`test_sslg_content.py` portability** — its first test
   (`test_every_baseline_file_is_accounted_for_exactly_once`) fails in an isolated copy of
   `tools/` because it calls `collect_baseline(ROOT)` against the real vault root. The
   Task-3-appended test (`test_record_sources_order_primary_first_and_pdf_last`) is pure
   data-comparison and environment-safe, which is the right shape for the invariant the
   renderer depends on.
5. **Post-Task-6 link resolution** — by design unresolved now; I confirmed instead that
   every non-`.md` link target exists verbatim in the manifest's `current_path` set, so
   nothing is broken *beyond* the pending move.

## 5. Recommended gate before Task 3 is signed off

1. **Fix C1** — break the circular duplicate reason in `tools/sslg_content.json` (Task 2 data)
   and get the combined suite green. Nothing else should be evaluated while it is red.
2. Fix I3 (or record it as an explicit deferred plan item with owner).
3. Fix I2 (two-line in-run dedupe guard) and add the I1 required-property test.
4. Correct the report's "10 note tests / Ran 21 tests" and re-cut the review package so it
   matches the current test files (I4).
5. Re-run and record the true totals: with C1 fixed, expect **25 OK**.
