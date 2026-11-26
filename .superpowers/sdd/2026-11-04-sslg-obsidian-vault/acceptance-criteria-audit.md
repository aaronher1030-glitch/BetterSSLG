# Acceptance Criteria Audit — SSLG Obsidian Vault

Spec: `docs/superpowers/specs/2026-11-04-sslg-obsidian-vault-design.md`, section "Verification and Acceptance Criteria" (lines 183-196).
Auditor: read-only session, 2026-11-05. No file was created, moved, modified or deleted by this audit except this report.
Environment: Windows / Git Bash, `python -X utf8`, `pdftotext` available, `pdfinfo` absent, Obsidian application not installed or controllable.

Reproducibility note: every measurement below was run in this session from the vault root
`C:\Users\Ma Christine\Downloads\SSLG MEMOS`. Long inline checks are shown as the exact command used.

---

## Criterion 1 — Preservation: every original DOCX/PDF and supporting image accounted for by path and checksum; source bytes unchanged

**Verdict: PASS**

Command (read-only reconciliation of the pre-move baseline against the delivered manifest and live bytes):

```
python -X utf8 - <<'PY'
# baseline: .superpowers/sdd/2026-11-04-sslg-obsidian-vault/pre-move-baseline.json  {count, files{original_path -> sha256}}
# manifest : 90 Archive/File Manifest.json  files[] = {key, original_path, sha256, role, record_key, archive_reason, current_path}
for op, h in baseline['files'].items():
    e = manifest entry with original_path == op
    sha256(open(e['current_path'],'rb')) == h ?
PY
```

Returned:

- Baseline entries: **104** (`count` field = 104; 104 unique pre-move paths). Baseline `files` maps `original_path` -> SHA-256; the recorded `current_path` for each comes from `90 Archive\File Manifest.json`.
- Baseline path set **==** manifest `original_path` set (exact equality, 104 = 104, no side missing an entry).
- **HASH MATCH: 104 / 104** — recomputed SHA-256 of the live file at each recorded `current_path` equals the baseline hash.
- **HASH MISMATCH: 0**; **BASELINE PATH NOT IN MANIFEST: 0**; **FILE AT current_path MISSING: 0**.
- Manifest `sha256` also equals the baseline `sha256` for all 104 entries (0 disagreements), so the delivered inventory is the same checksum set that was captured before the move.
- Roles of the 104 accounted files: primary 36, revision 33, duplicate 18, asset 8 (PNG images of `OM_SSLG_2026_001`), alternative-format 6, staged 3. All 8 supporting images (`80 Assets/OM_SSLG_2026_001-1.png` … `-8.png`) are individually hash-verified.

Every original DOCX/PDF and supporting image is therefore accounted for by path and checksum, and the bytes at the final location are byte-identical to the pre-move bytes.

---

## Criterion 2 — No loss or overwrite: baseline and final inventories reconcile, including archived material and the pre-existing duplicate-staging folder

**Verdict: PASS**

Commands and measurements:

1. Duplicate-target / overwrite test:

```
python -X utf8 -c "import json,collections; m=json.load(open(r'90 Archive/File Manifest.json',encoding='utf-8')); cp=[e['current_path'] for e in m['files']]; print(len(cp), len(set(cp)))"
```
Returned: `104 104` — 104 distinct `current_path` targets, **0 duplicate destination paths**, i.e. no two originals were moved onto the same file, and no `current_path` collides with another record's.

2. Final-inventory sweep (every source-type file physically present in the vault, excluding `.obsidian`, `.superpowers`, `Scheduler_v1-main`, `docs`, `tools`):

Returned: 104 vault source files, **all 104 present in `manifest.files`**, **0 files in the vault that the manifest does not account for**, **0 manifest `current_path`s not found on disk**. (The only scanned extras were 18 scratch `.txt`/dump files inside `.superpowers\sdd\...`, which are working artifacts of the build, not vault sources.)

3. Archived material breakdown (by first two path segments): `90 Archive/Revisions` 33, `90 Archive/Duplicates` 18, `90 Archive/Staging` 3; live material: 50 (36 primary + 8 asset + 6 alternative-format). `90 Archive/Staging` holds exactly the 3 files of the pre-existing duplicate-staging area: `OM-DFSSLG-2026-003-1.pdf`, `OM_SSLG_2026_002. (1).docx`, `OM_SSLG_2026_002..docx` — each individually hash-matched in step 1 of Criterion 1.

4. Scheduler untouched test:

```
python -X utf8 -c "…verify every manifest['protected_files'] hash and diff disk listing…"
```
Returned: **87 / 87** `protected_files` entries hash-match live; 0 mismatch; 0 missing. Files physically under `Scheduler_v1-main` = **87**, `protected_files` = 87, and the two sets are equal (0 extra on disk, 0 absent). Newest mtime anywhere under `Scheduler_v1-main` = **2026-07-26 18:14:33**, which predates the 2026-11-04/05 migration, so the folder was not written to.

5. Legacy directory emptiness:

```
find OM_SSLG_2026_001 | wc -l        -> 1   (the directory itself only)
find _DUPLICATES_TO_DELETE | wc -l   -> 1   (the directory itself only)
ls -A OM_SSLG_2026_001 | wc -l       -> 0
ls -A _DUPLICATES_TO_DELETE | wc -l  -> 0
```
Returned: both legacy directories **exist and are empty** — they hold no material; their former contents are the 104 hash-verified files above. `validate_sslg_vault.py` independently asserts the same staging-emptiness condition and passed.

Baseline (104) and final (104 + 87 protected) inventories reconcile exactly with zero loss, zero overwrite, and zero unaccounted source file.

---

## Criterion 3 — Coverage: every primary logical record has one summary note and every note resolves to its original source document(s)

**Verdict: PASS**

Commands and returned measurements:

```
python -X utf8 - <<'PY'   # manifest <-> disk coverage matrix
manifest records: 36 entries, 36 unique record keys, 36 unique note_path values
missing note files on disk: 0
physical record notes found (*/Notes/*.md plus 03 Governance and 04 External Memoranda): 36
physical record notes NOT declared in the manifest: 0
manifest activities: 16 (16 unique keys); activity hub files missing on disk: 0; physical hub files: 16; extra hubs: 0
primary-role source files: 36; unique record_key among them: 36  -> 1 primary source : 1 record : 1 note
primary files whose record_key has no manifest record: 0
records with no primary source file: 0
records whose source_keys do not resolve to a manifest file entry: 0
records whose resolved source current_path is missing on disk: 0
PY
```

Summary-section check over all 36 notes:

```
notes without a "## Summary" section: 0
notes with a summary shorter than 5 words: 0
```

Collection split of the 36 records: activities 27, external 5, governance 4. Record types: memorandum 12, proposal 7, completion-report 6, meeting-notice 5, excuse-letter 4, governance-policy 1, request 1.

All 16 activity hubs exist and each links every record belonging to it (`validate_sslg_vault.py` enforces `note_path in hub text` and reported **0** errors). Each of the 36 notes names its source file(s) by exact vault path with format and role in frontmatter (`source_file`, `source_path`, `source_format`, `sources[]`), and 42 record-to-source attachments resolve on disk (see Criterion 4).

---

## Criterion 4 — Source placement: final section of every record note is "Original document", with PDF embeds and DOCX attachment links as applicable

**Verdict: PASS**

Heading-position check (level-two headings parsed with `^## `, per note):

```
record notes WITHOUT a "## Original document" level-two heading: 0 / 36
notes where "Original document" is NOT the last level-two heading: 0 / 36
```

Attachment-form check inside the `## Original document` section of all 36 notes:

```
python -X utf8 - <<'PY'
Counter({('link', '.docx'): 32, ('embed', '.pdf'): 10})
PY
```

- **10 PDF embeds** written as `![[...]]` — one for every PDF associated with a record (total record PDF attachments in the manifest = 10), and `PDF sources NOT embedded in their record note: 0`.
- **32 DOCX open links** written as `[[02 Activities/.../Sources/File.docx|Open original DOCX: File.docx]]` — one for every DOCX attachment (total record DOCX attachments = 42 − 10 PDF = 32). Each is a plain (non-`!`) wikilink, so it opens rather than embeds, and each is preceded by the note "Obsidian does not preview DOCX files; the link opens the original file directly."
- **Exact original filename**: every embed target and every link label carries the untouched original filename (e.g. `ACR_SSLG_2026_001.docx`, `AP_SSLG_2026_007_AnnexD.pdf`, `OM_SSLG_2026_001 (14).docx`), asserted against the record's own `source_keys`: `embed target not a listed source: 0`, `link target not a listed source: 0`, `format/embed mismatches: 0` (no DOCX embedded, no PDF linked-only). All 42 basenames resolve to real files on disk (`embed targets that do not resolve: 0`, `link targets that do not resolve: 0`).
- Independent corroboration: `python -X utf8 tools/validate_sslg_vault.py` re-checks "last `## ` heading must equal `Original document`" plus "every `source_keys` current_path appears in that final section" across all 36 notes and printed `VALIDATION PASSED: 16 activities, 36 records, 104 files, 87 protected`.

Sample verified note (measured, not inferred):
`02 Activities\National Students Day 2026\Notes\Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration.md` ends with a DOCX open link for `AP_SSLG_2026_007_AnnexD_proofread.docx` followed by `![[02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD.pdf]]` as its final content.

---

## Criterion 5 — Link integrity: all internal wikilinks, source links, embeds, and activity-trail links resolve within the vault

**Verdict: PASS**

Independent measurement (this audit, not only the validator) over every vault `.md` (60 notes; `.obsidian`, `.superpowers`, `Scheduler_v1-main`, `docs`, `tools` excluded):

```
python -X utf8 - <<'PY'   # parse every [[target|alias]] / ![[target]] , strip alias+anchor, os.path.exists(root/target or target+'.md')
vault markdown notes scanned: 60
total wikilink/embed references: 569   unique targets: 157
broken (with basename fallback allowed): 0
total references: 569  strict full-path unresolved (no fallback): 0
non-http markdown []()  links: 0   broken: 0
PY
```

Returned **0 unresolved references out of 569**, using the strict test that requires the literal path (or path + `.md`) to exist — no basename rescue was needed. Source links and PDF embeds are a subset of these 569 and were separately confirmed at 42/42 in Criterion 4. Activity-trail links (hub -> notes, note -> hub "Part of", related-records links) are also inside the 569 and resolve.

Corroborating tool runs in this session:

```
python -X utf8 tools/validate_sslg_vault.py
  -> VALIDATION PASSED: 16 activities, 36 records, 104 files, 87 protected   (exit 0)
python -X utf8 -m unittest discover -s tools/tests
  -> Ran 63 tests in 3.553s ... OK
```

---

## Criterion 6 — Relationship accuracy: sampled activity trails match source titles, dates, subjects and explicit references; uncertain cases appear in the Review Queue

**Verdict: PASS**

Method: full-text extraction of the primary source behind every record note — DOCX via `zipfile` read of `word/document.xml` (body + tables), PDF via `pdftotext -layout <file> -` — then string-level comparison against the note/manifest fields. Normalisation for comparison: lowercase, non-alphanumeric stripped (needed because the sources print "May 29, 2026", "June 06, 2026", "DATE: 16 MAY 2026" with irregular spacing).

Measured over the whole record set (not a small sample), and hand-verified source-text against note fields for an 8-record sample (`acr-sslg-2026-001`, `nom-sslg-2026-003-may29`, `om-dfsslg-2026-003`, `om-sslg-2026-002-ecolead`, `ap-sslg-2026-007`, `el-sslg-2026-005-elections`, `om-sslg-2026-001-may25`, `om-nfsslg-2026-001`):

- **Record issuance dates: 21 / 22** notes with a non-null `date` have that date present in their own source text. The single miss (`om-nfsslg-2026-001`, 2026-08-25) is explained below.
- **Event dates: 19 / 20** notes with a non-null `event_date` match their source text. The single miss (`acr-sslg-2026-001`, 2026-06-05) is a *range* endpoint: the source prints "Date: June 1-5, 2026", so 2026-06-05 is correctly derived; verified by reading the extracted text.
- **Identifier provenance: 12 / 12** records marked `id_provenance: printed` have their printed number found in the source body text (e.g. "No. 002, s. 2026" in `OM_SSLG_2026_002.docx`). **22 / 22** records marked `filename` have **no** printed number token in the source text, matching the note wording "derived from the source filename; the document text does not print an identifier". 0 contradictions in either direction.
- Titles/subjects verified by reading: `NOM_SSLG_2026_003 (1).docx` prints "May 29, 2026 / SUBJECT: BRIGADA ESKWELA 2026 and LGCC STANDING COMMITTEES AND COMPOSITION / online meeting … May 31, 2026, 4:00 P.M., via Google Meet" — note has date 2026-05-29, event_date 2026-05-31, activity `brigada-eskwela-2026`, title matching. `EL_SSLG_2026_005 (1).docx` prints "June 23, 2026 … excuse … on June 25, 2026 from 7:00 A.M. to 5:00 P.M." — note has date 2026-06-23, event_date 2026-06-25. `OM-DFSSLG-2026-003-1.pdf` prints "OM-DFSSLG-2026-003 … DATE: 16 MAY 2026 … Brigada Eskwela … June 1-5, 2026" from "Hon. FAITH NAOMI R. MANGANAAN, President, DFSSLG S.Y. 2026-2027" — matches note date, summary, and subject.
- **Explicit references — 16 / 17 reproduced**: scanning every source's extracted text for citation tokens (`...SSLG-20DD-NNN` style codes and `No. NN, s. YYYY` numbers) found **17** distinct in-source citations, of which **16** are reproduced in the corresponding record note. Example that passes: `OM_SSLG_2026_001.docx` prints "Pursuant to Division Memorandum OM-DFSSLG-2026-002" and `03 Governance\Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (25 May 2026).md` states it in `## Summary`. The one miss is the 27 May sibling note (`om-sslg-2026-001-may27`), whose source `OM_SSLG_2026_001 (8).docx` prints the same "OM-DFSSLG-2026-002" preamble but the note never mentions it (`grep -c "DFSSLG"` on that note -> 0). No vault link is fabricated for that citation: OM-DFSSLG-2026-002 was not supplied, so it is correctly named rather than linked. Other external authorities cited inside the sources (e.g. "DepEd Memorandum No. 27, s. 2026" in `OM-DFSSLG-2026-003-1.pdf`) are likewise outside the corpus. Where a record's sources state no relationship at all, the note says so plainly ("No related records established from the supplied sources"), so `related` edges elsewhere are subject/date-derived rather than quotation-derived.
- **Uncertain cases -> Review Queue: 23 / 23** entries carrying `review_reasons` (10 records + 13 activities) appear in `01 Dashboards\Review Queue.md`, and every individual reason string is reproduced (0 omissions, measured by exact substring test).
- The hardest case was checked directly: `om-nfsslg-2026-001`'s primary PDF yields **16 bytes of text via pdftotext — 16 form-feed characters, i.e. an image-only scan with no text layer**. Its unverifiable id/date/status are recorded as filename-derived and carry a `review_reasons` entry ("the image-only primary has no text layer that can confirm them"), which is present verbatim in the Review Queue. The note's own `key_details` states the same limitation.

No sampled relationship contradicted its source. Three residuals were investigated rather than waved away: one event date is a range endpoint ("June 1-5, 2026"), one record is an image-only scan with no text layer (flagged in the Review Queue), and one 27 May note omits the OM-DFSSLG-2026-002 citation its source prints — a completeness slip in a note, not a wrong relationship.

---

## Criterion 7 — Dashboard coverage: activity, record-type, chronological and needs-review views return the intended notes without including the Scheduler application

**Verdict: PASS**

Files inspected: `01 Dashboards\Activity Dashboard.md`, `Document Library.md`, `Review Queue.md`, `Timeline.md`, `SSLG Records.base`.

`01 Dashboards\SSLG Records.base` defines 6 table views plus two vault-wide filters (verbatim top of file):

```
filters:
  and:
    - 'file.folder != "Scheduler_v1-main"'
    - 'file.folder != "99 Templates"'
views: All records (type=="record") | Proposals (record_type=="proposal")
     | Completion reports (record_type=="completion-report") | Memoranda (record_type=="memorandum")
     | Needs review (needs_review=="yes") | Activities needing review (type=="activity" and needs_review=="yes")
```

Measured coverage vs the delivered manifest:

| View | Expected | Returned |
| --- | --- | --- |
| Activity Dashboard (activity view) | 16 activity hubs | 16/16 distinct hub links present (+3 links to sibling dashboards; 19 distinct targets total, 0 foreign) |
| Document Library (record-type view / Bases host) | 6 Bases views embedded via `![[01 Dashboards/SSLG Records.base]]` | all 6 view names declared; record_type counts in manifest: memorandum 12, proposal 7, completion-report 6, meeting-notice 5, excuse-letter 4, governance-policy 1, request 1 |
| Timeline (chronological) | all 36 record notes + 16 hubs | 36/36 record notes and 16/16 hubs linked; 92 record-note links, 0 targets outside the manifest |
| Review Queue (needs-review) | 10 records + 13 activities carrying `review_reasons` | 10/10 and 13/13 present with every reason string reproduced verbatim (0 omissions); header states "Needs review: 10 records, 13 activities." |

Chronological ordering was checked per table, not on the flattened file:

```
section "Activity schedule"          data rows 17, dated 10, ascending: True  (6 remaining rows read "Not stated in source")
section "Activity and meeting dates" data rows 21, dated 20, ascending: True
section "Record issuance dates"      data rows 23, dated 22, ascending: True
```

Scheduler / template exclusion measured directly:

- `grep -rn "Scheduler" "01 Dashboards"` -> 2 hits only, both exclusion statements (`Document Library.md:37` prose, `SSLG Records.base:3` filter). No dashboard wikilink targets Scheduler: **0**.
- `grep -rn "99 Templates" "01 Dashboards"` -> 2 hits: the `!= "99 Templates"` filter and a prose folder description. Dashboard wikilinks targeting `99 Templates`: **0**.
- Vault-wide scan for any wikilink containing `Scheduler` across all 60 notes: **0** — no note or dashboard reaches into the Scheduler folder.

---

## Criterion 8 — Template consistency: new activity and record notes can be created from the templates with the same metadata and source-attachment structure

**Verdict: PASS (structural equivalence measured; the interactive insertion step is manual — see Criterion 9)**

Files inspected: `99 Templates\Record Template.md`, `99 Templates\Activity Template.md`, and `.obsidian\templates.json`.

- Template folder wired to Obsidian's core Templates plugin (measured, read-only): `.obsidian\templates.json` -> `{"folder": "99 Templates"}`; `.obsidian\core-plugins.json` -> `"templates": true`, `"bases": true`, `"properties": true`.
- **Record metadata identity**: frontmatter key set of `Record Template.md` = `{type, title, record_type, record_id, id_provenance, date, event_date, school_year, status, needs_review, activity, source_file, source_path, source_format, sources, related, tags}` plus the nested `sources[]` keys `{file, path, format, role}` (20 keys total). The union of keys across all 36 delivered record notes is **identical** — `template keys missing vs delivered notes: []`, `template keys not used by any note: []`.
- **Activity metadata identity**: `Activity Template.md` keys `{type, title, start_date, end_date, school_year, status, needs_review, venue, tags}` = union of keys across all 16 delivered hubs — 0 missing, 0 extra.
- **Section structure identity**: record template level-two headings `Summary / Key details / Related records / Revision history / Original document` — that exact sequence appears in **36 / 36** record notes (single distinct heading signature, measured with a Counter over all notes). Activity template headings `Summary / Activity trail / Outcomes and follow-up / Related governance / Original files / Missing stages` appear in **16 / 16** hubs.
- **Source-attachment structure identity**: the template prescribes "DOCX files are linked with a prominent open link … PDF files are embedded … Record the exact source filename, its vault-relative path, and its format here" — which is exactly the delivered pattern counted in Criterion 4 (32 DOCX open links, 10 PDF embeds, all with vault-relative path and format in frontmatter).
- Caveat measured rather than assumed: the templates carry `{{title}}` and `{{date:YYYY-MM-DD}}` placeholders (2 and 1 occurrences respectively). Substituting them requires invoking *Insert template* inside Obsidian, which is a write action and was therefore not performed in this read-only audit. All non-interactive structure above is identical to the delivered notes.

---

## Criterion 9 — Obsidian rendering: homepage, callouts, tables, PDF embeds and Bases views checked in Obsidian

**Verdict: CANNOT BE PERFORMED IN THIS ENVIRONMENT**

Reason: Obsidian is not installed and not controllable from this session (Windows / Git Bash; no GUI automation, no `obsidian://` handler, no running Obsidian process). The criterion is explicitly a *visual* check ("checked in Obsidian where app access is available"), and the spec requires that any visual check that cannot be performed be reported rather than claimed. Nothing about rendering was inferred from file structure — the counts below are text-file measurements only and are **not** evidence of correct display.

What was measured here (structure only, `python -X utf8` over the 60 vault notes):

| Construct | Counted in the source files | Rendered in Obsidian |
| --- | --- | --- |
| Callout blocks (`> [!info]`, `> [!warning]`) | 82 blocks — 58 `info`, 24 `warning` | not verified |
| Markdown table blocks | 254 row-bearing table blocks | not verified |
| PDF embeds (`![[...pdf]]`) | 10 | not verified |
| DOCX open links (label "Open original DOCX: ...") | 110 vault-wide, 32 inside record `## Original document` sections | not verified |
| PNG image embeds | 0 — the 8 `80 Assets/OM_SSLG_2026_001-*.png` files are preserved and indexed but embedded in no note | not verified |
| Bases embed of `01 Dashboards/SSLG Records.base` | 1 (Document Library) | not verified |
| Notes with YAML frontmatter (properties pane) | 59 / 60 — the exception is `90 Archive/Archive Index.md`, a pure hash table | not verified |

Manual steps a human must take in Obsidian to close this criterion:

1. Open Obsidian -> "Open folder as vault" -> `C:\Users\Ma Christine\Downloads\SSLG MEMOS`. Confirm Settings -> Core plugins: Bases, Templates, Properties, Page preview are ON (the shipped `.obsidian\core-plugins.json` records true for each; the running app must agree).
2. Homepage: open `START HERE.md` in Reading view. Confirm the five `##` sections render (Reading routes, Collections, Activities, Archive and templates, Not part of this vault) and that every bullet link resolves (solid, not dimmed/unresolved).
3. Callouts: on `START HERE.md`, `01 Dashboards\Review Queue.md` and the activity hubs, confirm the 58 `info` and 24 `warning` callouts render as bordered boxes with icons rather than as plain blockquote text — especially the hub "Review required" warnings and the Review Queue header warning.
4. Tables: open `01 Dashboards\Timeline.md` (3 tables), `01 Dashboards\Activity Dashboard.md` and `90 Archive\Archive Index.md` (104-row hash table); confirm column alignment, no stray pipes, and that long vault-relative paths wrap readably.
5. PDF embeds: in Reading view open `02 Activities\National Students Day 2026\Notes\Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration.md` and the other 9 notes carrying `![[...pdf]]`; confirm the PDF renders inline and is scrollable. Then confirm that `04 External Memoranda\Sources\Memorandum-OM-NFSSLG-2026-001_signed-2.pdf` displays as scanned page images, since it has no text layer to select.
6. DOCX links: click an "Open original DOCX" link (for example `ACR_SSLG_2026_001.docx`) and confirm Obsidian hands the file to the OS/default application instead of showing an error or an empty preview pane.
7. Bases views: open `01 Dashboards\Document Library.md` and confirm the embedded `SSLG Records.base` block renders all 6 table views (All records, Proposals, Completion reports, Memoranda, Needs review, Activities needing review) with populated rows; confirm no Scheduler or `99 Templates` row appears and that the totals look like 36 records / 16 activities.
8. Graph view: with Attachments ON and Unresolved OFF (as shipped in `graph.json`), confirm no node or edge points into `Scheduler_v1-main`.
9. Templates: create a scratch note, run *Insert template* twice (Record Template, then Activity Template) and confirm `{{title}}` / `{{date:YYYY-MM-DD}}` substitute and the properties appear in the Properties pane; delete the scratch notes afterwards. This step writes to the vault, so it must be done by a human, not by this audit.

---

## Criterion 10 — AI traceability: a tool can use note metadata to locate the unchanged source file and distinguish derivative summaries from original material

**Verdict: PASS — with one documented gap (no per-note hash or manifest link)**

1. Locate the unchanged source from note metadata alone:

```
python -X utf8 - <<'PY'   # parse the YAML block, read source_path / source_format, look the path up in 90 Archive/File Manifest.json
records whose frontmatter source_path resolves to a manifest entry carrying a SHA-256: 36 / 36   gaps: []
all sources[] path lines resolving to a manifest entry: 42 / 42
manifest entry exposes sha256 for every file: True
PY
```

Every note states the vault-relative location of its source (`source_path`, plus a `sources[]` block of `file` / `path` / `format` / `role`) and its format (`source_format: docx|pdf`). That path is exactly the `current_path` keyed in `90 Archive\File Manifest.json`, whose `sha256` equals the live bytes (104/104 confirmed in Criterion 1), so the chain note -> source file -> original checksum is closed for all 36 records. The bytes themselves are the untouched originals: the only mutations in the corpus were moves, and `Scheduler_v1-main` was never written (87/87 hashes, mtimes still 2026-07-26).

2. Hash availability — the gap: `grep -rn` for `sha256`, `SHA-256` or any 64-hex token across `02 Activities`, `03 Governance`, `04 External Memoranda`, `99 Templates` returned **0 hits**. No record note prints its own digest and none links the manifest or the Archive Index; the only such links in the vault are two lines in `START HERE.md` ("Archive Index — where every original file came from, where it is now, and its SHA-256" and "File Manifest — the same inventory in machine-readable form"). The digests are reachable in two hops: `90 Archive\Archive Index.md` carries all **104** 64-hex values with role, original path, current path and record key, and `90 Archive\File Manifest.json` carries the same per `key`. Traceability therefore holds for a tool that follows the documented chain, but a note read in isolation does not self-certify its source bytes.

3. Derivative versus original:

```
notes scanned: 36   summary sentences tested (>=5 substantive words): 45
summary sentences reproduced verbatim from the source text: 0
notes containing explicit summary / derivative wording: 36 / 36
```

No summary sentence reproduces source wording verbatim (case- and whitespace-insensitive containment test against the extracted DOCX/PDF text), so `## Summary` and `## Key details` are unambiguously derivative. Original material is kept physically separate and is only ever *embedded or linked* in the final `## Original document` section (10 PDF embeds, 32 DOCX open links, all resolving), never pasted into the note body. Frontmatter adds `id_provenance` (`filename` 22, `printed` 12, `not-stated` 2) and the "At a glance" callout states the distinction in prose — e.g. "Document ID: ACR_SSLG_2026_001 (derived from the source filename; the document text does not print an identifier)" — while every unverifiable field reads `Not stated in source`. `date` (issuance) and `event_date` (event) are separate properties so a tool cannot conflate them, and uncertainty is machine-readable via `needs_review` plus `review_reasons` (23 flagged entries, all reproduced in the Review Queue).

Answer to the question asked: **yes.** An AI can tell the derivative summary from the original text (separate sections, 0/45 verbatim overlap, explicit provenance wording), can locate the unchanged source (36/36 `source_path` values that are byte-hash-identical to the pre-move baseline), and can obtain the digest from the delivered manifest or Archive Index. The one improvement worth making: embed each source's SHA-256 — or a link to `90 Archive/File Manifest.json` — directly in each record note so the integrity proof travels with the note.

---

## Summary of verdicts

| # | Criterion | Verdict | Key measured number |
| --- | --- | --- | --- |
| 1 | Preservation | PASS | 104 / 104 baseline hashes equal the live bytes at the recorded `current_path` |
| 2 | No loss or overwrite | PASS | 0 duplicate destinations; 0 unaccounted vault source files; 87 / 87 Scheduler hashes intact; both legacy directories empty (0 items) |
| 3 | Coverage | PASS | 36 records = 36 primary sources = 36 notes; 0 unresolved `source_keys` |
| 4 | Source placement | PASS | 36 / 36 notes end with `## Original document`; 10 PDF embeds + 32 DOCX links = 42 / 42 exact original filenames |
| 5 | Link integrity | PASS | 0 broken out of 569 wikilink references across 60 notes (strict full-path test) |
| 6 | Relationship accuracy | PASS | dates 21/22 and event dates 19/20 found in source text; explicit citations 16/17 reproduced; id provenance 12/12 printed and 22/22 filename verified; 23/23 uncertain entries in the Review Queue |
| 7 | Dashboard coverage | PASS | 6 Bases views; 16/16 hubs, 36/36 records, 23/23 review entries; 0 links into `Scheduler_v1-main` |
| 8 | Template consistency | PASS (structural) | template key sets identical to delivered notes — 20/20 record keys, 9/9 activity keys; 36/36 and 16/16 heading signatures |
| 9 | Obsidian rendering | CANNOT BE PERFORMED IN THIS ENVIRONMENT | Obsidian absent and not controllable; 82 callouts, 254 table blocks, 10 PDF embeds, 1 Bases file counted as text only |
| 10 | AI traceability | PASS (gap noted) | 36 / 36 `source_path` -> manifest SHA-256; 0 / 45 summary sentences verbatim; 0 per-note hashes |

Corroborating tool runs performed read-only in this session: `python -X utf8 tools/validate_sslg_vault.py` -> `VALIDATION PASSED: 16 activities, 36 records, 104 files, 87 protected` (exit 0); `python -X utf8 -m unittest discover -s tools/tests` -> `Ran 63 tests ... OK`.

Residual items for a human: the nine manual Obsidian steps listed under Criterion 9; adding each source's SHA-256 (or a link to `90 Archive/File Manifest.json`) to the record notes to close the Criterion 10 gap; and restating the OM-DFSSLG-2026-002 citation in the 27 May governance note (Criterion 6).
