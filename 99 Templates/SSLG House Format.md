---
type: guide
title: "SSLG House Format"
school_year: "2026-2027"
tags:
  - sslg
  - template
  - format
---

# SSLG House Format

The reusable format baseline for every document built on the BSANHS SSLG letterhead:
office memoranda (OM), notices of meeting (NOM), activity proposals (AP), activity
completion reports (ACR) and excuse letters (EL). The values are encoded once in
[tools/format_spec.py](../tools/format_spec.py) and enforced by
[tools/check_format.py](../tools/check_format.py); this note is the human-readable copy.
The measurements were read back from the accepted issuances in this vault, chiefly
Memorandum No. 002, s. 2026 (Nationwide Online Survey on Digital Device Use), not invented.

## Workflow for every new document

1. **Build** the DOCX from the letterhead shell in
   [[99 Templates/SSLG Memorandum Template (Number and Date Blank).docx]] or by cloning the
   closest accepted issuance. Keep `word/header*.xml` and `word/footer*.xml` byte-identical
   to the source; never retype the letterhead.
2. **Render** to PDF and page screenshots with Word itself, so pagination is the real one:
   `python -X utf8 tools/render_docx.py <file.docx> --preview <Preview dir>`
   (uses Word COM export; also writes the PDF beside the DOCX and PNGs per page).
3. **Check** both layers before calling the document done:
   `python -X utf8 tools/check_format.py <file.docx> <file.pdf>`
   Exit code 1 means at least one rule failed. `--quiet` prints failures only, `--json`
   emits machine-readable results. Check the memo PDF alone, not a bundle with external
   attachments appended — attachments are other people's documents and fail house rules
   by design.
4. **Look** at the PNGs in `Preview/`. The checker catches geometry; the eye catches
   everything else (stray artwork, wrong weight, a rule in the wrong place).
5. **Bundle** attachments below the memo with pypdf only after the memo alone passes.
6. **Record** the document in the vault: `Sources/` for masters and renders, `Preview/`
   for the screenshots, `Notes/` for the record note, activity hub at the folder root.

## Baseline

| Item | Value |
| --- | --- |
| Body font | Bookman Old Style, 12 pt (`w:sz` 24 half-points), nothing else in the body |
| Page | 12240 x 18720 twips (short bond paper, portrait) |
| Margins | top 1440, left/right 993, bottom 0 twips; header 360, footer 490 |
| Text edges | left 49.65 pt, right 562.35 pt |
| Letterhead | the six lines in `spec.HEADER_LINES`, DepEd seal above, rule under "School Year" |
| Footnote | address, telephone, e-mail and the Kapampangan motto, with the three logos |
| Field order | MEMORANDUM / No. / TO: / FROM: / SUBJECT: / DATE: (per kind in `spec.FIELD_ORDER`) |
| Signature order | Prepared by: / Reviewed and Evaluated by: / Concurred: |

### The header block is two columns

This is the tell most often missed. Labels sit on the text margin (49.6 pt); every value
starts on one tab stop at 1440 twips, i.e. 121.6 pt, including continuation lines:

- `TO:` once, then each addressee on its own line, all on the value column.
- `FROM:` then the authority line; the name and title continue on the value column.
- `SUBJECT:` value wraps inside the value column, never back to the margin.
- `DATE:` value on the value column, and a **horizontal rule under the DATE line** closes
  the block (`w:pBdr/w:bottom`, or the template's VML `o:hr` rect).
- Weights: labels and the `No. ____, s. 2026` line and the title under the name are
  **plain**; the values, the addressees and the name are **bold**. The SUBJECT value is
  bold but left-aligned (see rivers below).

### Body and pagination

- Numbered paragraphs `1.` … `n.` without gaps, justified, first line indented one tab.
- A paragraph holding a URL or e-mail (`spec.UNBREAKABLE_TOKEN`) is **left-aligned**:
  justification cannot break the token, so it stretches the rest of the line into rivers.
- `w:keepLines` on every numbered paragraph: if it does not fit, it moves **whole** to the
  next page instead of being cut mid-sentence.
- `w:keepNext` on each signature label so a label never strands at a page foot away from
  its name. Signature lines are left-aligned and single-spaced (`w:line` 240), with blank
  paragraphs carrying the signing gaps; every blank between a label and its name also
  carries `w:keepNext` so the whole block stays on one page.
- Nothing may print past 562.35 pt + 2 pt tolerance; no body text under 10 pt.

## Obvious tells (what a bad render looks like)

1. **Rivers** — a justified line with one huge inter-word gap. The checker flags any gap
   over `max(12 pt, 3 x the document's own median gap)`; the relative term matters because
   a 9 pt footnote spaces differently from a 12 pt body. The label-to-value tab jump is
   exempt (it is a column, not a river), but gaps *inside* the SUBJECT value are not.
2. **Values hugging the labels** — `FROM: By the Authority…` on one line from the margin,
   or addressees indented by a space instead of sitting on the 121.6 pt column.
3. **No rule under DATE**, or a rule under the wrong field.
4. **A paragraph cut by the page break** — the next page opens with the remainder of a
   sentence: not a new number, not an all-cap field or signature label.
5. **Orphan signature label** — "Concurred:" at a page foot, the name on the next page.
6. **Wrong weights** — bold number line, bold title line, or plain addressees.
7. **Scanned signatures on a draft** — the signed precedent carries anchored signature
   images in empty body paragraphs; a draft strips every inherited `w:drawing` run from
   the body (the letterhead seal and footer logos stay). The signatory's own mark may then
   be re-anchored on his name line when he asks for it, with the precedent's exact anchor
   offsets; never copy another person's signature.
8. **Overflow or shrunken text** — anything past the right text edge, or body under 10 pt.

## What the checker enforces

`docx` layer (markup): package XML well-formed (Word silently exports a truncated page
when a part is malformed, so parse before trusting the render); body font and size;
letterhead and footnote present (Word may split a line over many runs, so footer text is
joined run-to-run before matching); field order per kind; no justified paragraph holding a
URL/e-mail; signature order; every TO/FROM/DATE paragraph carries the 1440-twip tab stop;
rule under DATE; numbered paragraphs run 1..n.

`pdf` layer (rendered page): no stretched justified lines; nothing past the right text
edge; no undersized body text; letterhead on every page; field values share the 121.6 pt
column (±6 pt); no paragraph cut across a page break; signature label kept with its name.

The guards are mutation-proven: a copy of an accepted draft with the SUBJECT re-justified
and the tab stops removed fails exactly the tab-stop, stretched-line and column rules
(exit 1). Regression tests live in [tools/tests/test_check_format.py](../tools/tests/test_check_format.py).

## Known inherited artifacts — do not "fix" these

- The footer and one empty body paragraph of the template carry a 1-pixel dot
  (`media/image5.png`). It is in the accepted issuances too; it is furniture, not content.
- Letterhead fonts (Old English Text MT, Trajan Pro, Poor Richard, Bahnschrift) render
  differently on machines without them: the signed PDFs in this vault show a sans-serif
  substitution where a local Word render shows the blackletter original. Both come from
  the same header part; keep the part byte-identical and judge layout, not typeface.
- The precedent's SUBJECT value is justified and shows rivers. House style improves on
  it: left-align the SUBJECT cell. The checker therefore fails the precedent itself on
  stretched lines — that is expected, not a checker bug.

## Draft conventions

- Number stays `No. ____, s. 2026` until the SSLG assigns one; never guess the next number
  from a different series (AP/ACR numbers are not OM numbers).
- No scanned signatures by default; the signatory's own mark may be placed on his name
  line at his request (see tell 7). Other signatories' marks are never copied. Status
  `draft`, `needs_review: yes` until the number is assigned and all blocks are signed.
- When the Vice President returns a manually corrected DOCX, that file becomes the master:
  keep his spacing, weights and blank-line gaps, and limit later edits to pagination guards
  (`w:keepNext` chains, whole-paragraph moves) required by the house rules.
- Record only what the source states; anything absent is `Not stated in source`.

## Folder layout per activity

```
02 Activities/<Activity title>/
  <Activity title>.md      activity hub
  Notes/                   record notes (one per document version)
  Sources/                 DOCX master, PDF render, attachment bundle, received attachments
  Preview/                 page PNGs from tools/render_docx.py
```

New working documents stay outside `tools/sslg_content.json`: that manifest describes the
delivered collection and its generator refuses files the delivered inventory does not
list. Hand-write the hub and record note from
[[99 Templates/Activity Template.md]] and [[99 Templates/Record Template.md]] instead, and
keep every wikilink resolvable so `tools/validate_sslg_vault.py` stays green.

See also: [[99 Templates/SSLG Memorandum Template Guide.md]].