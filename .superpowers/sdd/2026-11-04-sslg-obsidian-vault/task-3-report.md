# Task 3 report — Record Notes and Activity Hubs

## What was built

- `tools/sslg_notes.py` — deterministic note renderer.
  - Public interfaces required by the brief: `wikilink(path, label=None)`,
    `render_record(record, data)`, `render_activity(activity, data)`,
    `generate_notes(root, data)`, plus `yaml_string` and `indexes`.
  - Helpers: `fmt` (renders `Not stated in source`), `_stage_present`,
    `_stage_rank`, `_stage_label`, `_ordered_trail`, and the `TRAIL_STAGES`
    ordering table (proposal → meeting-notice/excuse-letter/request →
    memorandum → completion-report).
- `tools/tests/test_sslg_notes.py` — 10 note tests.
- `tools/tests/__init__.py` — makes `tools.tests` a regular package.

## TDD evidence

RED (Step 2, before implementation):

```
ModuleNotFoundError: No module named 'tools.sslg_notes'
Ran 1 test in 0.000s
FAILED (errors=1)
```

Second RED found while extending coverage — the manifest-ordering invariant test
added to `tools/tests/test_sslg_content.py` failed against the real data:

```
FAIL: test_record_sources_order_primary_first_and_pdf_last
AssertionError: 'alternative-format' != 'primary' : ap-sslg-2026-007
Ran 5 tests ... FAILED (failures=1)
```

Third RED — a real renderer bug observed in the failing assertion output:
`lines.extend()` was called with a bare f-string for the activity
`## Original files` bullets, so the wikilink was exploded one character per
line (`-\n \n[\n[\n0\n2 ...`). Fixed with `append`, and the test now asserts
both the nested source links and the absence of the split form.

GREEN (final):

```
python -m unittest tools.tests.test_sslg_migration tools.tests.test_sslg_content tools.tests.test_sslg_notes
Ran 21 tests in 0.350s
OK
```

## Manifest fix required by the renderer

`ap-sslg-2026-007` listed its alternative-format PDF before its primary DOCX, so
the generated note would have pointed `source_file`/`source_path` at the wrong
copy. Fixed in the scratch builder
(`.superpowers/sdd/2026-11-04-sslg-obsidian-vault/gen_content.py`) by
normalizing every `source_keys` list to primary-first, PDF-last, then
regenerating `tools/sslg_content.json`:

```
wrote 16 activities, 36 records, 104 files, 87 protected
```

## Generation run (Step 5)

```
Generated 52 new activity and record notes
```

Verified after generation, programmatically over all 36 record notes:

- `## Original document` is the last `## ` section in every record note.
- Every record that has a PDF source ends with the `![[...pdf]]` embed
  (`pdf-not-last: []`).
- 26 records are DOCX-only; their final section is a prominent
  `Open original DOCX: <exact filename>` link plus a note that Obsidian cannot
  preview DOCX. No PDF embed was invented for them.
- No note path collisions, no duplicate note paths, longest absolute path 225
  characters, no illegal filename characters.
- 93 root DOCX/PDF sources are still in place (`ls *.docx *.pdf | wc -l` = 93):
  notes were generated before any source move, as the brief requires.

`generate_notes` re-checks collisions and raises `FileExistsError` before
writing, verified by `test_generate_notes_writes_every_note_and_refuses_to_overwrite`.

## Design decisions inside the brief

- YAML scalars use `json.dumps` quoting, so titles containing commas, colons and
  apostrophes stay valid.
- Empty `related` emits `related:\n  []` (the brief's form) rather than a list
  containing an empty list.
- Record `tags` lead with `sslg` and add the `record_type`, per the spec's
  "small controlled set led by `sslg`".
- `activity:` property stores the full-path wikilink to the hub, per the spec's
  "wikilink to the parent activity".
- The activity `## Original files` section links each record note and, nested,
  the exact source filenames — spec requires direct access to both.
- Missing stages use the exact sentence `Not present in the supplied records: <stage>.`
  and only for stages absent among that activity's linked records.
- Unknown dates/statuses render `Not stated in source`; nothing is inferred.

## Concerns

- Notes reference sources at their post-migration `current_path`, which does not
  exist until Task 6 moves the files. Until then, wikilinks and PDF embeds in the
  `## Original files` / `## Original document` sections are unresolved in Obsidian.
- Obsidian rendering itself was not exercised (no app instance in this
  environment): frontmatter parsing, callout display, and Bases compatibility are
  verified only by generated text and tests.
- Two activity hubs carry a review reason that restates a missing stage
  (e.g. Project ECOLEAD "No completion report is present in this collection.");
  harmless duplication of manifest content, left as authored in Task 2.
