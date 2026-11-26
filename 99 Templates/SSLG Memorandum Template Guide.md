---
type: template
title: "SSLG Memorandum Template (Number and Date Blank)"
school_year: "2026-2027"
tags:
  - sslg
  - template
---

# SSLG Memorandum Template (Number and Date Blank)

Editable shell for a Benigno S. Aquino National High School SSLG/LGCC memorandum. It keeps the received letterhead, fonts, logos, table borders and signature blocks, and replaces all content with bracketed placeholders. Build from a copy; never edit the originals in `02 Activities/**/Sources` or `03 Governance/Sources`.

- DOCX: [[99 Templates/SSLG Memorandum Template (Number and Date Blank).docx|Open template DOCX]]
- PDF preview: ![[99 Templates/SSLG Memorandum Template (Number and Date Blank).pdf]]
- Worked example of every field filled: [[02 Activities/Project ECOLEAD/Notes/Draft Memorandum - Reiteration of the Project ECOLEAD Clean-Up Schedule, Standard of Cleanliness, Compliance Matrix and Presidents' Concurrence (Number and Date Blank).md|Project ECOLEAD reiteration draft]]

## Field map

| Element | Placeholder | Notes |
| --- | --- | --- |
| Memo number | `No. ____, s. ____` | Fill last, after the Secretariat assigns the number |
| `FOR:` | one addressee group per line | Keep the tab after `FOR:`; the label row uses tab stops, not spaces |
| `FROM:` | `Hon. [FULL NAME OF ISSUING OFFICER]` | Second line is the position held |
| SUBJECT table | `[SUBJECT OF THE MEMORANDUM]` | A 1x2 bordered table; the label cell stays `SUBJECT:` |
| `DATE:` | `____________________, ____` | Leave blank until the number is assigned |
| Clauses | `[Clause 1 - …]` through `[Clause 5 - …]`, then labelled clauses | The body is an auto-numbered list; do not type numbers by hand |
| Annex label | `ANNEX A:` / `OM-SSLG-2026-____ – [ANNEX TITLE]` | Each label is its own 1x2 table; keep letter and title cells in order |
| Signature page | Prepared by / Reviewed and Evaluated by / Concurred | Concurrence block lists the organizations that sign the acknowledgment annex |

## Standard annex set

Kept in the order the received memoranda used, so a reader who knows No. 002 and No. 003 is not relearning the layout.

| Annex | Purpose | In the template |
| --- | --- | --- |
| A | Area or assignment rotation | 1 header + 5 blank organization rows |
| B | Monitoring officer assignment matrix | 1 header + 5 blank rows |
| C | Scheduled dates | 1 header + 3 blank month rows |
| D | Verification sheet | Header + 5 `[Aspect to be verified]` rows, then the signature lines for verifier and noted-by |
| E | Acknowledgment and concurrence | `Club or Organization` / `Printed Name of President` / `Signature of President` / `Date Signed`, 5 blank rows |
| F | Compliance and sanction matrix | Left filled as a worked example: first lapse, second, third and subsequent, excused lapse, false certification, each with the action and the effect on recognition |

## Conventions worth keeping

- Number and date stay blank until the Secretariat confirms the series number. This vault already holds five differently dated copies of one No. 002 and a No. 003 whose filename contradicts the number printed inside it, so a guessed number becomes a permanent ambiguity.
- Verification, not attendance, is the unit of compliance. A signed presence list over an unverified area is recorded as non-compliance.
- The student government records compliance and recommends action; it does not impose disciplinary penalties. Keep the `Limits of this Office` clause — it is the reason the sanction annex survives review.
- No person's name is ever invented into a template. Where a roster is missing, leave the cell blank and record that it must come from the registered list.
- Sanctions are staged, with the consequence and the notifier in the same row, so nobody argues about which step they are on.

## Reformatting notes learned the hard way

- Body clauses are auto-numbered by the template's list style. Text extracted with python-docx shows no numbers; the rendered PDF shows `1.` through `11.`. Never add numbers into the text.
- Annex label tables and content tables are separate elements, and the annex tables in the received files are split across pages, so a row-count change moves whole blocks around.
- Usable width is 512.8 pt at the received margins (letter, 49.7/49.5 pt). Fix widths explicitly for any table with tick-boxes or signature cells; autofit squeezes them to unreadable columns. Keep indent plus total width under 512.8.
- The SUBJECT row sits 4.8 pt outside the left margin by design in the received template. That is inherited, not a defect.
- Obsidian does not preview DOCX. Link the DOCX with an open link and embed the PDF.

## Tooling used to build and check these

```bash
# structure and text
python -X utf8 -c "from docx import Document; d=Document(r'<file>.docx'); [print(t.rows[0].cells[0].text, len(t.rows), len(t.columns)) for t in d.tables]"
```

```bash
# layout, pagination and PDF, through the installed Word
python -X utf8 -   # open with win32com Word.Application, Columns(i).SetWidth, Repaginate,
                   # ComputeStatistics(2) for pages, ExportAsFixedFormat(path, 17) for PDF
```

```bash
# read back what actually rendered
pdftotext -layout "<file>.pdf" - | grep -n "ANNEX\|No. ____"
# vault integrity after any note or link change
python -X utf8 tools/validate_sslg_vault.py
```

Word's `Quit()` throws an `AttributeError` or RPC error through pywin32 on this machine; the document is already closed and saved at that point, and no Word process survives.
