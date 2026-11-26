# Task 2 report - Reviewed content and file manifest

## What was built

- `tools/tests/test_sslg_content.py` - four coverage tests over the real inventory.
- `tools/sslg_content.json` - 16 activities, 36 logical records, 104 baseline files, 87 protected Scheduler files.

## TDD evidence

RED: `python -m unittest tools.tests.test_sslg_content -v` before the manifest existed.

```
FileNotFoundError: [Errno 2] No such file or directory:
  '...\\tools\\sslg_content.json'
Ran 0 tests in 0.043s
FAILED (errors=1)
```

Expected: the coverage tests read the manifest at import of `setUpClass`, so a missing manifest cannot pass.

GREEN: after authoring the manifest.

```
python -m unittest tools.tests.test_sslg_migration tools.tests.test_sslg_content
Ran 10 tests in 0.313s
OK
```

`tools.tests.test_sslg_content` alone: `Ran 4 tests ... OK`, output pristine.

## How the manifest was produced

Content evidence was read from source only, never from filenames alone:

- Every DOCX was parsed read-only through `zipfile.ZipFile` + `word/document.xml`.
- Every PDF was read with `pdftotext`; three signed NFSSLG exports have no text layer and are recorded as image-only sources rather than summarised from guesswork.
- All 104 baseline files were hashed with `sha256()` from Task 1. The manifest was emitted by a scratch builder (`.superpowers/sdd/2026-11-04-sslg-obsidian-vault/gen_content.py` plus `sdd_act_*.py`, `sdd_rec_*.py`, `sdd_file_*.py` data modules) that refuses to write unless the file rows exactly cover `collect_baseline(ROOT)` and every record has at least one source. Hashes are computed from disk, never transcribed.

Role distribution: 36 primary, 33 revision, 18 duplicate, 6 alternative-format, 3 staged, 8 asset.

## Classification decisions

- Logical records were grouped by title, subject, stated date and stated number, then cross-checked with text diffs. Filesystem numbering was treated as a claim, not evidence: `OM_SSLG_2026_003.docx` and `OM_SSLG_2026_003 (3).docx` contain No. 002 ECOLEAD text, `OM_SSLG_2026_001 (14) (2).docx` contains the No. 002 survey text, and `OM_SSLG_2026_002 (7).docx` contains No. 003.
- Text-identical but byte-distinct copies are `revision` with the reason naming the difference; byte-identical copies are `duplicate`. Only true current representations of one record share a note as `primary` plus `alternative-format`.
- `AP_SSLG_2026_007_AnnexD_proofread.docx` is primary for the National Students' Day proposal because the source carries an explicit `proofread` label and the Annex D PDF is kept as its alternative format; the un-proofread Annex D and the three identical base proposals are revisions/duplicates.
- Pre-existing `_DUPLICATES_TO_DELETE` material is `staged`, never deleted, and is not silently promoted to `duplicate`.
- Unknown dates are `null`. Records that could not be resolved responsibly are `needs-review` with a concrete reason: `ap-sslg-2026-005`, `ap-sslg-2026-006` (2 October against 5 October), `el-sslg-2026-005-elections` (two different letters both numbered EL_SSLG_2026_005 on 23 June 2026), `om-sslg-2026-002-ecolead`, `om-sslg-2026-002-survey-aug27`, `om-sslg-2026-003-ecolead`. `om-sslg-2026-001-draft-vp` is `draft` because number and date are blank placeholders.
- The induction proposal-to-completion link (`ap-sslg-2026-001` to `acr-sslg-2026-006`) rests on matching activity title, 22 July 2026 date and Multi-Purpose Hall venue, not on the shared number alone.

## Checkpoint 2 audit of ambiguous records

Manually compared every flagged entry against its source:

- World Teachers' Day: `revised` copies state 2 October 2026 and drop two programme lines that name LGCC collaborative performance groups; `AP_SSLG_2026_006 (3).docx` states 5 October 2026. Neither is signed and no later document resolves it, so no silent winner was chosen.
- ECOLEAD: four copies numbered No. 002 carry issuance dates 28 July, 21 September and 23 September 2026 with start dates 31 July, 22 September and 30 September; two copies dated 3 August disagree with each other on No. 002 versus No. 003. All retained, record flagged.
- Survey: No. 002 is used for both ECOLEAD (28 July) and the survey (27 and 28 August), and DOCX copies differ on whether annex and parental-consent paragraphs are present. Split into a 27 August and a 28 August logical record because the 28 August set is adviser-reviewed and has signed PDF exports.
- No DOCX/PDF pair with material content differences is presented as alternative formats: alternative-format is used only for AP_SSLG_2026_007 Annex D, NOM_SSLG_2026_004, and the survey/standing-committee exports whose text matches the chosen primary.

## Files changed

- Added `tools/sslg_content.json`
- Added `tools/tests/test_sslg_content.py`
- No source document was modified; no file was moved in this task.

## Concerns

- `om-sslg-2026-002-ecolead` keeps `OM_SSLG_2026_002.docx` as primary on canonical-filename grounds even though the September copies are later; the record is `needs-review`, so the vault does not claim a resolved winner.
- The three signed NFSSLG PDFs have no extractable text, so their summaries rest on file provenance and the citations inside the school-level memoranda rather than on their own body text.
- Scratch builder modules live under `.superpowers/` and are not vault artifacts; the JSON is the reviewed deliverable.
