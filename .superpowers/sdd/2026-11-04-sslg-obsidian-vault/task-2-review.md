# Task 2 review — Reviewed Content & File Manifest

Reviewer: task reviewer (read-only; no vault file created/moved/deleted). All source checks
performed against real bytes (DOCX via `zipfile`+`word/document.xml`; PDF via `pdftotext`).
Vault root: `C:\Users\Ma Christine\Downloads\SSLG MEMOS`.

## Scope verified

- `tools/sslg_content.json`: 16 activities, 36 records, 104 files, 87 protected files
  (counts read straight from the file — match the report's headline claims).
- `tools/tests/test_sslg_content.py`: **8 test methods on disk**, NOT the 4 shown in
  `task-2-review-package.md` and NOT the "four coverage tests" the report claims.
- Role distribution confirmed on disk: 36 primary, 33 revision, 18 duplicate,
  6 alternative-format, 3 staged, 8 asset = 104.

## Reproducible verification run

`python -m unittest tools.tests.test_sslg_migration tools.tests.test_sslg_content tools.tests.test_sslg_notes`
=> **`Ran 25 tests ... FAILED (failures=1)`** (re-run 3x, same result).
`... test_sslg_content` alone => `Ran 8 tests ... FAILED (failures=1)`.

> NOTE: the very first combined invocation in this session printed `Ran 21 tests OK`;
> every subsequent run (and the per-module runs) show 25 tests / 1 failure. The current,
> reproducible on-disk state is RED. Review is judged against the file as it exists now.

## Spot-checks against real sources (all read-only; >14 files/classifications)

Read actual text for the ECOLEAD No.002/003 family (7), the survey No.002 family (10),
OM No.001 may25/may27 (incl. 4 PDF renders), NOM No.003/004, EL No.004/005/005-1,
the induction AP-001/ACR-006 pair, ACR-001/002, AP-006 World Teachers' Day (revised vs (3)),
AP-007 base/AnnexD/proofread, the governance memo, REQUEST_FOR_MPH, and the OM-CF/DF/NFSSLG
external memoranda. Independent integrity checks: recomputed SHA-256 for all 104 files
against disk (0 mismatches); verified all 18 `duplicate` claims are byte-identical to the
file they name; verified every `revision ... text identical to X` is byte-distinct AND
text-equal; verified the 3 `staged` claims. Path safety checked independently.

## CRITICAL findings

### C1 — Delivered acceptance test FAILS because the manifest contains a circular `duplicate` pointer with no retained survivor
- Evidence: `tools/tests/test_sslg_content.py:78-92`
  (`test_duplicate_reasons_point_at_a_real_same_hash_file_without_cycles`) →
  `AssertionError: ... circular pair: OM_SSLG_2026_001 (3).docx <-> OM_SSLG_2026_001 (10).docx`.
- Manifest data: three files share hash `e4f8e1db01c4…` and are ALL `role: duplicate`:
  - `files[] key om_sslg_2026_001-(3).docx` → `archive_reason: "byte-identical duplicate of OM_SSLG_2026_001 (10).docx"`
  - `files[] key om_sslg_2026_001-(10).docx` → `archive_reason: "byte-identical duplicate of OM_SSLG_2026_001 (3).docx"` (2-node cycle)
  - `files[] key om_sslg_2026_001-(13).docx` → `archive_reason: "byte-identical duplicate of OM_SSLG_2026_001 (3).docx"`
- Verified root cause: the text of (3)/(10)/(13) is **identical** to the may-25 primary
  `OM_SSLG_2026_001.docx` (0 diff lines) but **byte-distinct** from it (different sha). So this
  is a re-saved variant, which the manifest's own taxonomy calls a `revision`
  (cf. sibling entries: `OM_SSLG_2026_001 (2).docx`, `(4)`, `_VP`, `(14) (1)`, `(15)` are all
  `revision` with reason "re-saved copy with text identical to …"). Here all three identical
  copies were labelled `duplicate` and point at each other, so no survivor represents the
  variant outside `90 Archive/Duplicates` and the `Archive Index` "related primary" is circular.
- This is a (a)-manifest-data bug that (b) the shipped test correctly detects.
- Concrete fix: set `om_sslg_2026_001-(3).docx` → `role: "revision"`, `archive_reason:
  "re-saved copy with text identical to OM_SSLG_2026_001.docx"`, `current_path:
  "90 Archive/Revisions/OM_SSLG_2026_001 (3).docx"`; then point `(10)` and `(13)` at `(3)`
  as byte-identical duplicates. Cycle broken; suite goes green; variant keeps a survivor.

## IMPORTANT findings

### I2/I1 — ECOLEAD `om-sslg-2026-002-ecolead`: an `archive_reason` and a `review_reason` assert the opposite of what the bytes show
- Manifest `records[key=om-sslg-2026-002-ecolead].review_reasons[1]`: "the 28 July DOCX omits
  the area rotation schedule that later copies include."
- Manifest `files[key=om_sslg_2026_002-(1).docx].archive_reason`: "28 July No. 002 draft that
  adds the area rotation schedule absent from the canonically named file."
- Contradicted by source: the canonically named primary `OM_SSLG_2026_002.docx` DOES contain
  "…The official Area Rotation Schedule is attached as Annex A." and the Annex A heading
  "Project EcoLead Area Rotation Schedule". Verified: **every** No.002 copy (002.docx, (1),
  (2), 003.docx, 003(3)) references the Area Rotation Schedule; none "omits" it. The real
  delta is the reverse: the canonical (95 paras) additionally carries the rubric paragraph,
  the "Outstanding EcoLead Organization of the Month" recognition, and the full Annex B
  committee body — the shorter 28 July drafts `(1)` (77p) / `(2)` drop those, not Annex A.
- Authority conflict with the brief? The brief/spec only require that `archive_reason`/
  `review_reason` match the bytes; nothing in the brief says to describe a rotation-schedule
  delta. The bytes win. Fix both strings to state the true difference (rubric / Outstanding-
  Month / Annex-B presence), and re-word the record's second review_reason accordingly.

### I3 — Three survey `om-sslg-2026-002-survey-aug27` `revision` copies are mis-reasoned (claim omits parental-consent, which they include)
- Verified presence of the clause "Respondents who are below 18 years of age are advised to
  accomplish the Parental Consent Form (Annex D …)":
  - `OM_SSLG_2026_002 (5).docx` — PRESENT; yet `archive_reason`: "…without the annex list and
    parental-consent paragraph". FALSE.
  - `OM_SSLG_2026_002. (4).docx` — PRESENT; same false reason.
  - `OM_SSLG_2026_002..docx` — PRESENT; same false reason.
  - Only `OM_SSLG_2026_002 (4).docx` and `OM_SSLG_2026_001 (14) (2).docx` actually lack it
    (and (4)'s reason is correct; (14)(2)'s filename/content-mismatch reason is correct).
- Note also the chosen primary for this record, `OM_SSLG_2026_002 (3).docx`, is the 27-Aug
  copy that OMITS the parental-consent clause, while the record's own `key_details` and the
  activity outcome assert that clause. The clause is present only in copies NOT listed in
  `source_keys`. This is defensible because `(3)` is otherwise the most complete 27-Aug variant
  (full Annex A/B + sign-off block) and the record is `needs-review`, but the reviewer should
  knowingly pick a primary that supports the record's stated key_details, or drop that key_detail
  from `(3)`-sourced framing. Fix per-file reasons first (hard factual errors), then reconsider
  primary choice.

### I4 — `om-dfsslg-2026-010`: extraction claim contradicted by the source; date wrongly `null`
- Manifest: `date: null` and `key_details`: "The text layer of the export does not render the
  issuance date, so it is recorded as not stated."
- Source: `pdftotext OM-DFSSLG-2026-010.pdf` renders "26 August 2026" on its own line immediately
  after the FROM block (`Hon. RHIAN JADE L. CASTRO Acting President …`), before numbered body
  item 1. The issuance date IS in the text layer.
- This violates the spec rule that missing info may read "Not stated in source" but present info
  must not be reported as absent. The sibling division memos were extracted correctly
  (`OM-DFSSLG-2026-003` = 16 May 2026, `OM-DFSSLG-2026-007` = 5 June 2026 both match their PDFs),
  so this is an isolated slip. Fix: `date: "2026-08-26"` and remove/correct the key_detail.

### I5 — Excuse-letter statuses are inconsistent and `signed` likely over-claimed
- `el-sslg-2026-005-drill` = `status: "signed"`, key_details "Approved by Amparo M. Munoz, EDD,
  Principal IV"; but `el-sslg-2026-004` = `final` and `el-sslg-2026-005-elections` = `needs-review`
  — all three are editable DOCX bearing the *same* typed block "Approved by: AMPARO M. MUÑOZ,
  EDD Principal IV" (and EL_004/EL_005-elections additionally "Recommending Approval: … Head
  Teacher VI"). None has a signature artifact or signed PDF export.
- Three structurally-identical unsigned letters get three different statuses; and reserving
  `signed` for the drill copy is an over-claim relative to `final` (spec: filesystem/labels are
  supporting, not sole, proof; a typed name ≠ executed signature). The No.005 collision is also
  symmetric but only the elections record carries the `review_reason`; the "clean" `signed`
  drill record carries none even though its own number is contested.
- Fix: apply one rule (typed-but-unsigned DOCX → `final`; `signed` only where a signature
  artifact/signed export exists), and cross-note the 005 numbering conflict on the drill record
  too (or move both under a shared needs-review relationship).

## Things that check out (evidence, not vibes)

- Coverage: `collect_baseline(ROOT)` = 104; manifest `files[]` = 104; every `original_path`
  appears exactly once; all 104 `sha256` match disk bytes; all 87 `protected_files` paths sit
  under `Scheduler_v1-main` (no SSLG record mixed in).
- Duplicate integrity: all 18 `duplicate` entries are genuinely byte-identical to the file they
  name; all `revision` entries whose reason says "text identical to X" are byte-distinct AND
  text-equal (0 exceptions); the 3 `staged` copies match the spec (never promoted to primary;
  `_DUPLICATES_TO_DELETE/OM_SSLG_2026_002. (1).docx` truly differs from `(6)` only by one
  signature-block line break — verified via diff).
- Numbering traps handled correctly (identity by content, not filename):
  - `OM_SSLG_2026_001 (14) (2).docx` (filename says 001) actually holds the 27-Aug survey memo
    numbered No. 002 → assigned to `om-sslg-2026-002-survey-aug27` with a filename/content-mismatch
    reason. Correct.
  - No. 001 25 May vs 27 May issued as separate records (dates + named-roster differ; `(11)`
    genuinely has the roster removed vs `(8)`). Correct.
  - No. 002 reused for ECOLEAD (28 Jul) vs Survey (27/28 Aug) → split into three records. Correct.
  - No. 003 vs No. 002 on the 3-Aug ECOLEAD copies (`(7)`=No.003, `(8)`=No.002, otherwise
    identical except a stray backtick) → both retained, record `needs-review`. Correct.
  - `OM_SSLG_2026_003.docx`/`(3)` carry No. 002 ECOLEAD text (21/23 Sep) → folded into the
    ECOLEAD No.002 record. Correct.
  - `NOM_SSLG_2026_003` reused for two different notices (29 May kick-off vs 6 Jun post-eval/GPOA)
    → split `nom-sslg-2026-003-may29` / `…-jun06`. Correct.
  - `EL_SSLG_2026_005` used for two different letters (drill vs elections) → split, `needs-review`.
- Alternative-format pairs (task 3) are all the SAME logical document (differences are letterhead,
  annex inclusion, or proofread cleanup — never competing subject/date): AP-007 AnnexD.pdf,
  NOM-004.pdf (extra tokens are only the DepEd letterhead; same July 2 / July 3 subject),
  OM_001.docx.pdf→(8) may27 (matches May 27 despite filename), OM_001.pdf→may25 (May 25),
  OM_002.docx.pdf→aug27 survey (Aug 27), OM_002.pdf→aug28 survey (Aug 28). Report's claim that
  no materially-differing DOCX/PDF pair is presented as alternative-format holds.
- needs-review honesty (task 4): the World Teachers' Day conflict reason is exactly right
  (revised copies = 2 Oct + named LGCC groups HBC/La Tigris/APPA; `(3)` = 5 Oct + generic LGCC);
  EL-005, ECOLEAD, survey-aug27, governance-memo `[School Name]` placeholder reasons are all
  concretely supported by the sources.
- Induction proposal→completion link (`ap-sslg-2026-001`↔`acr-sslg-2026-006`) rests on matching
  July 22 date + Multi-Purpose Hall + induction subject (verified in both files), not the number.
- Summaries/key_details (task 8): OM No.001 addressees/"Pursuant to Division Memorandum
  OM-DFSSLG-2026-002", governance-memo legal basis "SSLG Memorandum No. 1, Series of 2026" and
  22-Jun date, MPH request (Principal IV recipient, "no document number stated", cleanliness
  commitment), ACR-001 (1-5 June), ACR-002 (16-25 June, Miting truncated by the drill), AP-001
  `(1)` "adds ASSH Club", AP-007 "adds a zumba segment 3-5 PM with tickets + SPTA" — all
  corroborated verbatim. No invented facts found in these; unknowns are `null`/"Not stated".

## Path safety for the later move step (task 6) — independent check: CLEAN

- 104/104 `current_path` values are unique (also unique case-insensitively → no Windows
  case-collision). No `current_path` collides with any other, and none exists on disk yet →
  no move can overwrite an existing unrelated file (matches spec "no move may overwrite").
- No Windows-illegal characters (`< > " | ? *`, embedded colon) in any `current_path`/`original_path`.
- No trailing dot/space segments; no over-long (>240) paths; leaf filename preserved exactly in
  every `current_path`.

## MINOR findings

- M1 `om-sslg-2026-002-ecolead.review_reasons[0]`: says "Four copies all numbered No. 002" but
  the record actually spans five No.002 copies across three issuance dates. Wording inaccuracy only.
- M2 `ap-sslg-2026-007`: the `alternative-format` PDF is the **non-proofread** `AnnexD.pdf` while
  the primary DOCX is `AnnexD_proofread.docx`; same logical submission (Jaccard 0.95) so acceptable,
  but the alt is not the proofread render — worth a one-word clarification.
- M3 `om-sslg-2026-001-may25.key_details`: "Signed by Hon. Rhian Jade L. Castro" — the DOCX shows
  only a FROM block, no signature artifact; record status is correctly `final`, so soften the
  wording (issued/signed under) to avoid implying an executed signature.
- M4 Page-count metadata (e.g., "Exported as a 10-page PDF" for may-27; the NFSSLG "17/18/3-page"
  split) was derived from form feeds because `pdfinfo` is unavailable; NFSSLG 17/18/3 counts match,
  but the may-27/25 PDFs measured 8–9 by form feed, so the "10-page" figure is plausible yet not
  exactly confirmable — flag as approximate.
- M5 `world-teachers-day` primary is the "revised"/2-Oct variant while `(3)` states 5 Oct (the
  conventional UNESCO date). The "revised"-label rationale is legitimate per spec and the record is
  `needs-review` (no silent winner claimed), but the `primary` file placement still privileges the
  2-Oct copy; note this is a judgment, not a resolved fact.
- M6 Test-contract drift: the brief's Step-1 prescribed a 4-method file; the shipped file has 8.
  The 4 added tests are, on the whole, *improvements* — `test_current_paths_are_unique_and_match_
  the_role_rules`, `test_no_record_source_is_placed_in_the_archive`, and the duplicate-cycle test
  enforce real, useful invariants the brief's version lacked. The drift itself is only a problem
  because the review package/report describe the *old* 4-test file and claim it is green.

## Test adequacy (task 7) — the tests are STRUCTURAL, not classification, checks

The shipped suite proves the *schema/reference integrity* the brief defines, and nothing more:
- `test_every_baseline_file_is_accounted_for_exactly_once` — proves coverage/uniqueness of
  `original_path` vs `collect_baseline`; does NOT check `current_path`, roles, or whether a
  classification is correct. Would NOT catch a wrong-but-64-hex `sha256`.
- `test_file_entries_have_current_paths_hashes_and_roles` — checks role ∈ set, `sha256` matches
  `^[0-9a-f]{64}$`, `current_path` non-empty, staged≠primary. It validates hash SHAPE only; it
  never recomputes the digest against disk, so a transcribed/incorrect hash would pass (my
  independent recompute is what actually proves hashes).
- `test_record_sources_and_relationships_resolve` — referential integrity + `needs-review`⇒
  non-empty `review_reasons`. It does NOT verify a `review_reason`/`archive_reason` is TRUE, and
  does NOT catch the dangerous "labelled final/signed yet contains an unresolved conflict" case
  (that is exactly what I5 is).
- `test_every_non_asset_file_maps_to_a_logical_record_or_archive_reason` — every non-asset maps to
  a record and has an archive_reason (or is primary/alt). Content of the reason unchecked →
  I1/I2/I3 false reasons sail through.
- (added) `test_record_sources_order_primary_first_and_pdf_last` — ordering invariant; good for
  the note renderer; caught nothing.
- (added) `test_current_paths_are_unique_and_match_the_role_rules` — uniqueness AND the invariant
  (role∈{revision,duplicate,staged}) ⇔ path under `90 Archive/`; genuinely useful.
- (added) `test_no_record_source_is_placed_in_the_archive` — no `record.source_keys` file lives in
  the Archive; useful anti-pattern guard.
- (added) `test_duplicate_reasons_point_at_a_real_same_hash_file_without_cycles` — re-derives the
  duplicate target from `archive_reason`, checks it exists, has equal manifest sha, isn't self,
  and isn't a 2-cycle. THIS test correctly catches C1 — and is what turns the suite RED. (It
  compares manifest shas to each other, not to disk, so it proves the cycle but still trusts the
  recorded digests.)
Net: the suite is stronger than the brief's 4 tests and its additions catch C1, but no test in it
verifies classification correctness, hash-against-disk, reason-truth, or status honesty. Those are
human/source judgments, which is why the independent spot-checks above were required and why I1–I5
slipped through.

## Could NOT verify (and why)

- The three signed NFSSLG exports (`Memorandum-OM-NFSSLG-2026-001_signed*`) are image-only (the
  primary has ~16 text chars). Their internal text/dates can't be read; the manifest's 25-Aug
  date and "signed" status rest on the `_signed` filename plus citations inside the school/division
  memos ("in line with OM-NFSSLG-2026-001 dated 25 August 2026"). Implementer disclosed this; it
  is a reasonable provenance chain but not body-verified.
- Exact PDF page counts (`pdfinfo` unavailable) — derived from form feeds (±1).
- Obsidian rendering / final note layout — Tasks 4/5, out of scope for Task 2.

## Data-wrong vs tests-don't-prove (explicit split)

- Manifest data wrong (fix the JSON): C1 (cycle/no survivor), I1/I2 (ECOLEAD rotation-schedule
  reason false), I3 (three survey copies' parental-consent reason false), I4 (DFSSLG-010 date +
  "not rendered" claim false), I5 (inconsistent/over-claimed excuse-letter statuses), M1–M5 wording.
- Tests don't prove the data (the gaps let C1/I1–I5 exist undetected, except C1 which one added
  test does catch): sha never recomputed against disk; `archive_reason`/`review_reason` truth
  unchecked; `final`/`signed` conflict-honesty unchecked.

## Which authority wins where a finding touches the brief

- Brief Step 5 requires the content tests to PASS; they are RED → the brief's gate is unmet
  regardless of data being "mostly fine". Fix the data (C1) to green the suite; do not delete/
  weaken the failing test to make it pass — it is correct.
- Brief says "no current DOCX/PDF pair with material content differences is treated as
  alternative formats" and "preserve exact filenames"; both are met and were independently
  confirmed — no conflict to resolve.

## VERDICTS

SPEC: FAIL
- Substantive spec rules (non-destructive coverage by path+checksum, archive routing, review-queue
  honesty, no-overwrite, no-invention) are broadly satisfied, BUT the deliverable asserts facts the
  source bytes contradict (I1–I4), leaves a content variant with a circular/dangling archive
  pointer and no survivor (C1, which also breaks "every logical record resolves to a source"), and
  over-claims one status (I5) — all of which breach the spec's "do not invent / archive_reason must
  match the bytes / missing info never inferred, present info never reported absent" contract. These
  are conformance failures, not polish. The fixes are localized; re-review after the JSON changes.

QUALITY: CHANGES REQUESTED
- The delivered test suite is RED (fails its own duplicate-cycle check), and the report/review
  package misdescribe the shipped file (4 green tests vs 8 tests / 1 failure). Multiple
  `archive_reason`/`review_reason`/`key_details` fields state the opposite of the source text.
- Credit: hashing/coverage/duplicate byte-identity/path-safety are all clean, and the hard
  numbering traps (No.001/002/003, EL_005, NOM_003 reuse; the `(14)(2)` filename lie; the
  003.docx-contains-002 cases) were handled correctly from content. Fix C1 first (it greens the
  suite), then correct I1–I5 strings and the two survey-primary considerations.


