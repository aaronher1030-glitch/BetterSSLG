# Final Review — Integrity & Reachability (SSLG Obsidian Vault)

Independent reviewer (did not build). Scope: the five assigned checks, nothing else.
Vault root: `C:\Users\Ma Christine\Downloads\SSLG MEMOS`. Read-only except this file and `sdd_int_*.py`.

Method notes:
- All Python run as `python -X utf8` (cp1252 console quirk).
- Link resolution is case-insensitive with basename fallback, matching Obsidian behaviour.
- Scratch scripts (all re-runnable): `sdd_int_ab.py` (checks 1–2), `sdd_int_c.py` / `sdd_int_f.py`
  (check 3), `sdd_int_d.py` / `sdd_int_e.py` (checks 4–5). Check 4 is by direct read of
  `tools\validate_sslg_vault.py` against the spec.
- Nothing taken from the aborted reviewer's `sdd_final_*.py` scripts; all numbers below are my own measurements.

## Verdicts

1. **Byte preservation — PASS.** 104/104 `current_path` exist with matching SHA-256; 104/104 pre-move baseline
   hashes still present on disk; nothing deleted or altered.
2. **Untouched zones — FINDINGS.** `Scheduler_v1-main\` is exact (87/87, zero drift); `docs\` has no baseline in
   the manifest at all, so its "untouched" claim is undetectable — see I-1.
3. **Stale prose and unreachable files — FINDINGS.** Zero stale pre-migration references and zero broken links
   across 563 wikilinks, but 3 delivered artifacts are unreachable — see I-2.
4. **Validator independence — FINDINGS.** 5 of the 10 acceptance criteria have no corresponding check, and 6
   checks are substring tests that could pass on unrelated text — see I-4, M-2, M-3, M-4.
5. **Navigation counts and the base file — FINDINGS.** Every printed count matches the manifest and the `.base`
   file is structurally correct, but the base "Needs review" view under-covers the Review Queue — see I-3.

Findings count: **Critical 0 / Important 4 / Minor 7.**

## Findings

### Critical

None. No source byte changed, no file went missing, no link broke, and no printed count was wrong.

### Important

**I-1 — `docs\` is entirely outside the protection model, so "docs untouched" cannot be verified by the project's own instrument.**
Measurement: `python -X utf8 .superpowers/sdd/2026-11-04-sslg-obsidian-vault/sdd_int_ab.py` printed
`[2] zone coverage of protected: Counter({'Scheduler_v1-main': 87})` — all 87 `protected_files` entries live under
`Scheduler_v1-main/`, none under `docs/`. Then
`[2] zone docs: protected=0 on-disk=2 extra_vs_protected=2 missing=0`
(`docs/superpowers/plans/2026-11-04-sslg-obsidian-vault.md`, `docs/superpowers/specs/2026-11-04-sslg-obsidian-vault-design.md`).
No pre-migration hash exists for any `docs\` file (nor for `tools\`: `protected=0 on-disk=11`), so edits there
would be invisible to every check in the toolchain. Not evidence of tampering — evidence that the criterion is uninstrumented.

**I-2 — Three delivered artifacts are unreachable from every note, hub, dashboard, Archive Index row, and template.**
Unreachable: `90 Archive\Archive Index.md`, `90 Archive\File Manifest.json`, `99 Templates\Activity Template.md`.
Measurement: `sdd_int_f.py` printed `R1 unreachable (self-reference removed): 4` — the three above plus
`START HERE.md` — with `R2 referencers …` showing `90 Archive/Archive Index.md <- [] (0)`,
`90 Archive/File Manifest.json <- [] (0)`, `99 Templates/Activity Template.md <- [] (0)`, while e.g.
`01 Dashboards/Review Queue.md <- ['START HERE.md', '01 Dashboards/Activity Dashboard.md'] (2)` proves the method
does find real referencers. Cross-checked with `grep -rn "File Manifest" --include=*.md .` and
`grep -rn "Activity Template" --include=*.md --include=*.base .` → zero hits each.
Why it matters: spec line 156 makes `Archive Index.md` the original-path→current-path→checksum map and line 194
makes the templates an acceptance surface; a reader following `START HERE.md` → `Document Library.md` never reaches
any of them. `Document Library.md:34` names `99 Templates/` in prose and links only `Record Template`
(`sdd_int_e.py` G: `'Record Template' referenced in: ['01 Dashboards/Document Library.md']`), never the activity one.
`START HERE.md` is excluded from this finding: spec line 136 defines it as the entry point, so having no inbound
link is by design.
Correction logged: my first pass (`sdd_int_c.py`) reported only 2 unreachable because it let a file satisfy its own
reachability by containing its own title; `sdd_int_f.py` excludes self-reference and is the number used here.

**I-3 — The base "Needs review" view returns 6 records; the Review Queue carries 8 records plus 13 activities, and no base view can show the activities.**
Measurement: `sdd_int_e.py` A3/T4 printed `needs-review status in notes: 6 | manifest records status needs-review: 6`
against `records with review_reasons: 8` / `activities with review_reasons: 13`; `python -X utf8 -c …` T4 printed
`base Needs-review size: 6 | Review Queue records: 8 | flagged activities: 13`. The two records flagged in the queue
but invisible to the view are
`03 Governance/Draft Memorandum - Standing Committee Distribution (Number and Date Blank).md` (`status: draft`) and
`03 Governance/Memorandum OM-SSLG-IA-2026-001 - … Policy.md` (`status: final`) — see X1 output. Every one of the five
views starts with `type == "record"` (`01 Dashboards\SSLG Records.base`, views 0–4), so the 16 hubs
(`type: activity`, measured `A2 hub frontmatter type values: {'activity': 16}`) can never appear in any view.
Spec line 193 requires the needs-review view to "return the intended notes", so 2 records + 13 activities are
intended-but-not-returned. Not a broken count claim: `01 Dashboards\Review Queue.md:14` "Needs review: 8 records,
13 activities" is exactly right against the manifest.

**I-4 — The validator checks a private copy of the inventory, never the delivered manifest, and never reconciles against the baseline (spec criteria 2, 6, 8, 9, 10 uncovered).**
`tools\validate_sslg_vault.py:186` loads `root / "tools" / "sslg_content.json"`. The delivered artifact is
`90 Archive\File Manifest.json`. Measurement: `sdd_int_c.py` A2 shows the two are identical **today**
(`files: identical=True`, `protected_files: identical=True`, `records: identical=True`, `activities: identical=True`,
both 16/36/104/87), but nothing in the toolchain enforces that — editing only `File Manifest.json` leaves
`VALIDATION PASSED` intact while the archive's own inventory silently diverges.
`grep -n "baseline\|Archive Index\|99 Templates\|Templates" tools/validate_sslg_vault.py` → **NO MATCHES**, i.e.
`pre-move-baseline.json`, `Archive Index.md` and the templates are never opened. Criterion-to-check map against
`docs\superpowers\specs\2026-11-04-sslg-obsidian-vault-design.md:187-196`:

| # | Spec criterion | Validator check | Status |
|---|---|---|---|
| 1 | Preservation | `:67-77` files exist + SHA-256; `:79-84` protected | covered |
| 2 | Baseline/final inventories reconcile | none — baseline never read; `:160-163` only lists root `.docx/.pdf` | **not covered** |
| 3 | One summary note per record, note resolves to source | `:109-113` note exists, `:124-127` source in final section | structural only; no duplicate-note check (`X2`/`X3`: 5 `record_id` values shared by 2–3 notes, accepted because uniqueness is never asserted) |
| 4 | Final section is "Original document" | `:119-121` exact heading equality | covered |
| 5 | Link integrity | `:137-144` | partial — see M-4, only `[[…]]` scanned, no folder-relative or `[t](p)` handling |
| 6 | Relationship accuracy | `:129-133` checks only that keys exist in the JSON | **not covered** (evidence requirement is manual) |
| 7 | Dashboard coverage, no Scheduler | `:173-177` | substring-only, see M-2; no check of printed counts or of I-3's under-coverage |
| 8 | Template consistency | none | **not covered** — my own measurement passes it: Record Template carries all 15 `REQUIRED_NOTE_PROPERTIES` (`T2: missing vs …: []`) and ends `## Original document`, matching delivered notes (`T3`) |
| 9 | Obsidian rendering | none | **not covered** (correctly — see Unverified) |
| 10 | AI traceability | `:116-118` property presence | partial — values never resolved; my check confirms `frontmatter source_path that do NOT resolve: 0` |

### Minor

**M-1 — Two empty pre-migration directories still sit at the vault root and the validator cannot see them.**
`ls -a` and `python -X utf8 -c "os.listdir(...)"` both return `['OM_SSLG_2026_001', '_DUPLICATES_TO_DELETE']`, with
`find "_DUPLICATES_TO_DELETE" -type f | wc -l` → `0` and `find "OM_SSLG_2026_001" -type f | wc -l` → `0`.
`validate_sslg_vault.py:160` filters `path.is_file()`, and `:165` tests `any(staging.rglob("*"))`, so an empty
`_DUPLICATES_TO_DELETE` passes. Spec line 155 wanted that material relocated into the archive — it was
(`90 Archive/Staging/` holds 3 files, `role: staged` ×3 per `file roles` counter) — but the emptied folders remain.

**M-2 — Six acceptance checks are plain substring tests satisfiable by unrelated text (latent; current exposure measured as zero).**
`validate_sslg_vault.py:106` `note_path not in text` (hub→record link), `:126` `path not in final` (source
attachment), `:154` `entry["title"] not in queue`, `:157` `reason not in queue` (and neither binds a reason to the
entry it belongs to — any occurrence anywhere in `Review Queue.md` satisfies it), `:174` `f"name: {view}" not in base`,
`:176` `'file.folder != "Scheduler_v1-main"' not in base`. Measured current exposure: `sdd_int_e.py` A reported
`sources mentioned in final section WITHOUT wikilink/embed syntax: 0` and hub trails verified row-by-row
(`B2 hub missing its own record note: 0`), so no check is being satisfied by bare prose today.

**M-3 — Property-presence check accepts empty/null values.** `:117` `rf"(?m)^{prop}:"` passes on `date: null`.
Measured 13 record notes with `date = 'null'` and 2 with `record_id = 'null'`
(e.g. `02 Activities/Cluster IV …/Notes/Notice of Meeting - Cluster IV … (16 May 2026).md`,
`02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Request for Use of the Multi-Purpose Hall ….md`).
These are honest unknowns, not fabrications — but "the property exists" is not "the record is dated", and criterion
10 leans on that regex. (Retracted claim: `related:` appeared empty in my first scan; direct inspection shows it is
normal YAML list style — `related:\n  - "[[…]]"`. Not a finding.)

**M-4 — The link-integrity scan skips the archive and the templates entirely.**
`VAULT_NOTE_PREFIXES` (`:17-18`) is `01 Dashboards/ 02 Activities/ 03 Governance/ 04 External Memoranda/
05 General Records/`; `90 Archive/` and `99 Templates/` are absent and neither is in `declared_notes`, so
`Archive Index.md` and both templates are never link-checked. Current exposure zero: `sdd_int_f.py` G measured
`Record Template.md: 0 unique wikilinks`, `Activity Template.md: 0 unique wikilinks`,
`Archive Index.md: 0 unique wikilinks` — they contain no `[[…]]` to break. Also note `05 General Records/` is a
prefix the validator expects but does not exist on disk (`05 General Records exists on disk: False`);
`Document Library.md` correctly does not claim it.

**M-5 — Duplicate `record_id` values across distinct primary notes.** `collections.Counter` over the manifest gave
`{'EL_SSLG_2026_005': 2, None: 2, 'NOM_SSLG_2026_003': 2, 'OM SSLG No. 001, s. 2026': 2, 'OM SSLG No. 002, s. 2026': 3}`,
and the same distribution read back from the notes' own frontmatter on disk. This is the intended outcome of spec
line 157 (conflicting numbers, no silent winner) and those notes are in the Review Queue — but nothing asserts
note↔record uniqueness, so a genuine accidental duplicate would look identical.

**M-6 — `START HERE.md` links 9 of the 36 record notes.** Measured `E) START HERE links: hub links present: 16 /16,
record-note links present: 9 /36`. Consistent with spec line 136 (entry point links dashboards + governance +
external memoranda + review queue), and every note is reachable through its hub; recorded so the reader knows the
homepage is not an exhaustive index.

**M-7 — No inventory orphans; accounting is closed.** 165 files exist under the eight vault zones
(`01 Dashboards`, `02 Activities`, `03 Governance`, `04 External Memoranda`, `80 Assets`, `90 Archive`,
`99 Templates` plus `START HERE.md`) = 104 manifest files + 60 `.md` + 1 `.base`, and
`ORPHAN files (on disk, not in manifest, not md/base/manifest): 0`, `manifest paths not on disk: []`.
Note the composition: `file roles: {'primary': 36, 'revision': 33, 'duplicate': 18, 'asset': 8,
'alternative-format': 6, 'staged': 3}` and `file suffixes: {'.docx': 76, '.pdf': 20, '.png': 8}` — the 8 PNGs are
the "supporting images" of spec line 187 and each appears exactly once, in `Archive Index.md`, not embedded in the
governance note that produced them (`asset 80 Assets/OM_SSLG_2026_001-1.png referenced by: ['90 Archive/Archive Index.md'] count: 1`).

### Check 3 and check 5 measurements that came back clean

Stale prose / broken links (check 3), `sdd_int_c.py` + link census:
- `md files scanned: 60 wikilinks: 563 markdown links: 0 unique wikilink targets: 153`.
- `C1 '_DUPLICATES_TO_DELETE' references in vault md: 0`; the only mention anywhere is
  `C4 mentions of '_DUPLICATES_TO_DELETE': ['90 Archive/Archive Index.md']` — the `original_path` column, which is
  correct per spec line 156, not stale prose.
- `C2 root-level (prefix-less) source-file wikilinks: 0` — no note links `OM_SSLG_2026_001.docx` bare; every source
  link carries its post-move folder.
- `C3 unresolved link targets: 0`, with the extra guard that markdown links were scanned too (0 exist).

Navigation counts (check 5), `sdd_int_d.py` / `sdd_int_e.py` / `sdd_int_f.py`:
- `START HERE.md:10` "16 activities, 36 logical records" = manifest.
- `01 Dashboards\Activity Dashboard.md:13` same claim; `activity rows parsed: 16 (manifest activities: 16)`;
  trail-count column `rows: 16 mismatches: 0`, column sum 31 = `manifest records with activity set: 31`
  (31 + 5 external = 36, so the trail column and the 36-record claim are both right).
- `Timeline.md` prints no totals (`grep -nE "[0-9]{1,3} +(activities|records|…)" 01 Dashboards\Timeline.md` → no hit),
  but coverage is complete: `activities absent from Timeline: []`, `records absent from Timeline: 0`.
- `Review Queue.md:14` "Needs review: 8 records, 13 activities" = manifest; `flagged entries in manifest: 21
(records: 8 activities: 13)`, `flagged entries whose TITLE is absent from queue: []`,
`total reasons in manifest: 29 | reasons absent from queue: 0`, `queue ### headings: 21`,
`queue headings not matching any declared note: []`, and the independent frontmatter cross-check
`of those, absent from Review Queue: []` for the 6 notes + 2 hubs that self-report `status: needs-review`.
So: every flagged record and activity is listed, with **all** 29 reasons — not just the first.
- `Document Library.md:29-34` claims `02 Activities/`, `03 Governance/`, `04 External Memoranda/`, `80 Assets/`,
  `90 Archive/`, `99 Templates/`; `existing top-level vault folders` returned all six (the trailing-slash strings in
  that output are my comparison artifact, not missing folders). `![[01 Dashboards/SSLG Records.base]]` at line 25
  resolves. It does not claim a `05 General Records/`.
- `01 Dashboards\SSLG Records.base`: `YAML parse: OK; top keys: ['filters', 'views']`, `view count: 5` with names
  `All records / Proposals / Completion reports / Memoranda / Needs review`, and top-level
  `filters.and = ['file.folder != "Scheduler_v1-main"', 'file.folder != "99 Templates"']` — both required exclusions
  present, at global scope so they apply to all five views. Record-type filters match the notes exactly:
  `proposal: frontmatter=7 manifest=7`, `completion-report: 6/6`, `memorandum: 12/12`, `type values: {'record': 36}`.

Check 1 and 2 detail is in the verdict lines and I-1; the raw run is
`python -X utf8 .superpowers/sdd/2026-11-04-sslg-obsidian-vault/sdd_int_ab.py`
(`[1a] … MISSING: 0 … HASH MISMATCH: 0`, `[1b] baseline keys == manifest original_paths: True`,
`[1c] baseline HASHES not found anywhere on disk: 0`, `[2] protected MISSING: 0 … HASH MISMATCH: 0`,
`zone Scheduler_v1-main: protected=87 on-disk=87 extra=0 missing=0`).
Reference commands that still pass and are therefore not findings:
`python -X utf8 -m unittest discover -s tools/tests` (54 tests) and
`python -X utf8 tools/validate_sslg_vault.py` (VALIDATION PASSED: 16 activities, 36 records, 104 files, 87 protected).

## Unverified

1. **Obsidian rendering (spec criterion 9).** No Obsidian app on either machine, so callouts, tables, PDF embeds and
   Bases view rendering are unverified. Reported explicitly per the criterion's own instruction rather than claimed.
   The `.base` file was verified only as YAML (`yaml.safe_load` OK), not as a Bases document Obsidian will accept —
   in particular I cannot confirm that `file.folder != "…"` is the filter grammar Bases expects.
2. **Semantic truth of the 36 summaries.** `tools\sslg_content.json` carries the extracted document text; comparing
   every `summary`/`key_details` claim against the DOCX/PDF bodies is content review, outside this scope.
   Relationship *accuracy* (criterion 6) is likewise unverified beyond key resolvability.
3. **`docs\` and `tools\` were never modified.** Not the same finding as I-1: I report the absence of a baseline,
   not proof of drift. No timestamp comparison was performed.
4. **Whether the 104 originals' *contents* are meaningful** (e.g. that `OM_SSLG_2026_001.docx.pdf` is really a PDF of
   that DOCX). Byte preservation proves they are the same bytes the baseline recorded, nothing more.
5. **PDF embed viability.** I confirmed source paths appear inside `![[…]]` embed/link syntax in the final section of
   every record note, but not that each target opens as an embed (no app), and I did not check PDF page integrity.
