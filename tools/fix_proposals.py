# -*- coding: utf-8 -*-
"""Apply the proposal-set fixes to the three activity proposals.

One pass, idempotent: routing blocks are rebuilt from scratch each run, so a second
run changes nothing. Fixes applied here:

  * routing block (TO / THRU / FROM / SUBJECT / DATE) on the house tab stop,
    with the rule under DATE that the accepted memoranda carry
  * page numbers in the letterhead header
  * table header rows repeat, and no row is split across a page break
  * fonts and prose size normalised to the house baseline (Bookman Old Style, 12 pt)
  * AP 007: stray "messa" paragraph removed, missing routing block added,
    paragraph explaining the December dates added
  * AP 009: routed through the SSLG Adviser instead of the SPTA President,
    "A. Donation Drive" label restored, budget header made consistent
  * AP 010: budget column resolved to TBD with an explanation, adoption year fixed,
    signature table aligned

Run:  python -X utf8 tools/fix_proposals.py
"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Pt

ROOT = Path(__file__).resolve().parents[1]
FONT = "Bookman Old Style"
TAB_TWIPS = 1440          # house value column
VALUE_INDENT_PT = 72      # continuation lines sit under the value

PPR_ORDER = [
    "w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
    "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd",
    "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
    "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
]
TRPR_ORDER = [
    "w:cnfStyle", "w:divId", "w:gridBefore", "w:gridAfter", "w:wBefore",
    "w:wAfter", "w:cantSplit", "w:trHeight", "w:tblHeader", "w:tblCellSpacing",
    "w:jc", "w:hidden", "w:ins", "w:del", "w:trPrChange",
]


def insert_ordered(parent, child, order):
    tag = child.tag
    names = [qn(n) for n in order]
    idx = names.index(tag)
    for existing in parent:
        if existing.tag in names and names.index(existing.tag) > idx:
            existing.addprevious(child)
            return child
    parent.append(child)
    return child


def add_tab(p, pos_twips=TAB_TWIPS):
    pPr = p._p.get_or_add_pPr()
    tabs = pPr.find(qn("w:tabs"))
    if tabs is None:
        tabs = OxmlElement("w:tabs")
        insert_ordered(pPr, tabs, PPR_ORDER)
    for old in tabs.findall(qn("w:tab")):
        if old.get(qn("w:pos")) == str(pos_twips):
            tabs.remove(old)
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "left")
    tab.set(qn("w:pos"), str(pos_twips))
    tabs.append(tab)


def add_bottom_rule(p):
    pPr = p._p.get_or_add_pPr()
    old = pPr.find(qn("w:pBdr"))
    if old is not None:
        pPr.remove(old)
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "000000")
    pBdr.append(bottom)
    insert_ordered(pPr, pBdr, PPR_ORDER)


def style_run(run, bold=False, size=12):
    run.bold = bold
    run.font.size = Pt(size)
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), FONT)


def routed_line(doc, label, value, bold_value=True, rule=False, value_only=False):
    p = doc.add_paragraph()
    p.style = doc.styles["No Spacing"]
    pf = p.paragraph_format
    pf.left_indent = Pt(0)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    add_tab(p)
    if rule:
        add_bottom_rule(p)
    if label:
        style_run(p.add_run(label + "\t"), bold=True)
        style_run(p.add_run(value), bold=bold_value)
    else:
        style_run(p.add_run("\t"), bold=False)
        style_run(p.add_run(value), bold=bold_value)
    return p


def continuation(doc, text, bold=False):
    p = doc.add_paragraph()
    p.style = doc.styles["No Spacing"]
    pf = p.paragraph_format
    pf.left_indent = Pt(VALUE_INDENT_PT)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    style_run(p.add_run(text), bold=bold)
    return p


def blank(doc, after=0):
    p = doc.add_paragraph()
    p.style = doc.styles["No Spacing"]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(after)
    style_run(p.add_run(""))
    return p


def rebuild_routing(doc, anchor_text, lines, date_text, subject_text):
    """Replace the paragraph run before anchor_text with a house-format block."""
    anchor = next(p for p in doc.paragraphs
                  if p.text.strip().upper().startswith(anchor_text.upper()))
    # Walk back over the existing routing block (everything since ACTIVITY PROPOSAL).
    stop = next(p for p in doc.paragraphs
                if p.text.strip().upper().startswith("ACTIVITY PROPOSAL"))
    el = stop._p.getnext()
    while el is not None and el is not anchor._p:
        nxt = el.getnext()
        el.getparent().remove(el)
        el = nxt

    built = []
    for item in lines:
        kind = item[0]
        if kind == "field":
            built.append(routed_line(doc, item[1], item[2], bold_value=item[3]))
        elif kind == "cont":
            built.append(continuation(doc, item[1], bold=item[2] if len(item) > 2 else False))
        elif kind == "blank":
            built.append(blank(doc))
    built.append(routed_line(doc, "SUBJECT:", subject_text, bold_value=False))
    built.append(routed_line(doc, "DATE:", date_text, bold_value=False, rule=True))
    built.append(blank(doc))

    for p in built:
        anchor._p.addprevious(p._p)
    return anchor


def fix_tables(doc):
    for t in doc.tables:
        if len(t.rows) >= 3:
            trPr = t.rows[0]._tr.get_or_add_trPr()
            if trPr.find(qn("w:tblHeader")) is None:
                insert_ordered(trPr, OxmlElement("w:tblHeader"), TRPR_ORDER)
            for cell in t.rows[0].cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True
        for row in t.rows:
            trPr = row._tr.get_or_add_trPr()
            if trPr.find(qn("w:cantSplit")) is None:
                insert_ordered(trPr, OxmlElement("w:cantSplit"), TRPR_ORDER)


def normalise_type(doc):
    for p in doc.paragraphs:
        for r in p.runs:
            r.font.size = Pt(12)
    for rf in doc.element.body.iter(qn("w:rFonts")):
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(attr), FONT)
    # Prose sizes only, including the paragraph-mark run properties: table cells keep
    # their condensed size.
    _set_sz_outside_tables(doc.element.body, "24")


def _set_sz_outside_tables(el, val):
    for child in el:
        if child.tag == qn("w:tbl"):
            continue
        if child.tag in (qn("w:sz"), qn("w:szCs")):
            child.set(qn("w:val"), val)
        _set_sz_outside_tables(child, val)


def keep_intro_with_table(doc):
    from docx.text.paragraph import Paragraph
    for t in doc.tables:
        prev = t._tbl.getprevious()
        if prev is not None and prev.tag == qn("w:p"):
            Paragraph(prev, doc._body).paragraph_format.keep_with_next = True


def add_page_numbers(doc):
    for section in doc.sections:
        header = section.header
        if not header.paragraphs:
            continue
        p = header.paragraphs[-1]
        if "PAGE" in "".join(
                t.text or "" for t in p._p.iter(qn("w:instrText"))):
            continue
        width_twips = Emu(section.page_width - section.left_margin
                          - section.right_margin).twips
        pPr = p._p.get_or_add_pPr()
        tabs = pPr.find(qn("w:tabs"))
        if tabs is None:
            tabs = OxmlElement("w:tabs")
            insert_ordered(pPr, tabs, PPR_ORDER)
        for old in tabs.findall(qn("w:tab")):
            if old.get(qn("w:val")) == "right":
                tabs.remove(old)
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right")
        tab.set(qn("w:pos"), str(width_twips))
        tabs.append(tab)

        style_run(p.add_run("\tPage "), bold=False, size=9)
        _field(p, "PAGE")
        style_run(p.add_run(" of "), bold=False, size=9)
        _field(p, "NUMPAGES")


def _field(p, instruction):
    run = p.add_run()
    style_run(run, bold=False, size=9)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, text, end):
        run._r.append(el)


def replace_para_text(p, text):
    runs = p.runs
    if not runs:
        style_run(p.add_run(text))
        return
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    runs[0].text = text


def find(doc, prefix, skip=0):
    hits = [p for p in doc.paragraphs if p.text.strip().upper().startswith(prefix.upper())]
    return hits[skip]


def remove_para(p):
    p._p.getparent().remove(p._p)


def restart_list_at_one(doc, paragraph):
    """Give a paragraph its own numbering instance so its section opens at A.

    The budget is a section of its own; without this it continues the previous
    section's letters and prints "B. Budget Allocation" with no A above it.
    """
    numPr = paragraph._p.pPr.numPr
    num_id = numPr.numId.val
    numbering = doc.part.numbering_part.element
    current = next(n for n in numbering.findall(qn("w:num"))
                   if n.get(qn("w:numId")) == str(num_id))
    if current.find(qn("w:lvlOverride")) is not None:
        return
    abstract = current.find(qn("w:abstractNumId")).get(qn("w:val"))
    next_id = max(int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num"))) + 1
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(next_id))
    ref = OxmlElement("w:abstractNumId")
    ref.set(qn("w:val"), abstract)
    num.append(ref)
    override = OxmlElement("w:lvlOverride")
    override.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:startOverride")
    start.set(qn("w:val"), "1")
    override.append(start)
    num.append(override)
    numbering.append(num)
    numPr.numId.val = next_id


# --------------------------------------------------------------------- AP 009
def fix_ap009():
    path = ROOT / "Activity Proposal - Disyembregalo (AP_SSLG_2026_009).docx"
    doc = Document(path)

    rebuild_routing(
        doc, "ACTIVITY TITLE:",
        [("field", "TO:", "DR. AMPARO M. MUÑOZ", True),
         ("cont", "Principal IV"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",),
         ("field", "THRU:", "AARON KHRISTIAN T. BANAG", True),
         ("cont", "SSLG Adviser"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",),
         ("field", "FROM:", "RHIAN JADE L. CASTRO", True),
         ("cont", "SSLG President"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",)],
        date_text="14 November 2026",
        subject_text="Activity Proposal — DISYEMBREgalo: A Season of Giving",
    )

    # The donation drive already sits in a lettered list ("A. Grade Level Donation
    # Drive", "B. Budget Allocation"); an extra heading would duplicate the letter.
    for p in [p for p in doc.paragraphs if p.text.strip() == "A. Donation Drive"]:
        remove_para(p)

    budget_label = next((p for p in doc.paragraphs
                         if p.text.strip() in ("Budget Allocation", "B. Budget Allocation")),
                        None)
    if budget_label is not None:
        # The letter comes from the list numbering, not from the text, and it restarts
        # with the budget so the section opens at A.
        replace_para_text(budget_label, "Budget Allocation")
        restart_list_at_one(doc, budget_label)

    for t in doc.tables:
        if t.rows[0].cells[0].text.strip().upper() == "MATERIALS NEEDED":
            replace_para_text(t.rows[0].cells[1].paragraphs[0], "BUDGET SOURCE")
        for row in t.rows:
            if row.cells[1].text.strip() == "Special Performance":
                replace_para_text(row.cells[2].paragraphs[0],
                                  "Aquinian's Pride Performing Artist (APPA)")

    fix_tables(doc)
    keep_intro_with_table(doc)
    normalise_type(doc)
    add_page_numbers(doc)
    doc.save(path)
    return path


# --------------------------------------------------------------------- AP 007
def fix_ap007():
    path = ROOT / "Activity Proposal - National Students Day 2026 (AP_SSLG_2026_007).docx"
    doc = Document(path)

    stray = [p for p in doc.paragraphs if p.text.strip().lower() == "messa"]
    for p in stray:
        remove_para(p)

    rebuild_routing(
        doc, "ACTIVITY TITLE:",
        [("field", "TO:", "DR. AMPARO M. MUÑOZ", True),
         ("cont", "Principal IV"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",),
         ("field", "THRU:", "AARON KHRISTIAN T. BANAG", True),
         ("cont", "SSLG Adviser"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",),
         ("field", "FROM:", "RHIAN JADE L. CASTRO", True),
         ("cont", "SSLG President"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",)],
        date_text="14 November 2026",
        subject_text="Activity Proposal — 2026 National Students' Day Celebration",
    )

    # Explain why a 17 November observance is held on 7-9 December.
    if not any(p.text.strip().startswith("Section 3 fixes 17 November")
               for p in doc.paragraphs):
        first = find(doc, "The celebration of National Students")
        p = doc.add_paragraph()
        p.style = doc.styles["No Spacing"]
        pf = p.paragraph_format
        pf.first_line_indent = Pt(36)
        pf.space_before = Pt(0)
        pf.space_after = Pt(6)
        pf.line_spacing = 1.0
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        style_run(p.add_run(
            "Section 3 fixes 17 November as the date of observance. For School Year "
            "2026–2027 the school holds the celebration on 7–9 December 2026, the "
            "three-day block set for it in the school calendar, so that the opening "
            "program, the contests and the club booths can run without cutting into "
            "class time. The celebration remains the National Students' Day observance "
            "under Republic Act No. 11369; only the date of the school-level program "
            "moves. Section 4 of the Act directs the Department of Education to support "
            "the National Youth Commission in facilitating and promoting related "
            "activities in all public and private schools."
        ))
        first._p.addnext(p._p)

    # Space between the letterhead rule and the title.
    title = find(doc, "ACTIVITY PROPOSAL")
    if not title.paragraph_format.space_before:
        title.paragraph_format.space_before = Pt(12)

    fix_tables(doc)
    keep_intro_with_table(doc)
    normalise_type(doc)
    add_page_numbers(doc)
    doc.save(path)
    return path


# --------------------------------------------------------------------- AP 010
def fix_ap010():
    path = ROOT / "Activity Proposal - Model United Nations Club (AP_SSLG_2026_010).docx"
    doc = Document(path)

    rebuild_routing(
        doc, "ACTIVITY TITLE:",
        [("field", "TO:", "DR. AMPARO M. MUÑOZ", True),
         ("cont", "Principal IV"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",),
         ("field", "THRU:", "_________________________", False),
         ("cont", "Club Adviser"),
         ("cont", "Benigno S. Aquino National High School"),
         ("blank",),
         ("field", "FROM:", "AARON Y. HERNANDEZ", True),
         ("cont", "ELLAINE T. JACOB", True),
         ("cont", "JOLEX ALEXIER S. CRUZ", True),
         ("cont", "Founding Members, Model United Nations Club"),
         ("blank",)],
        date_text="18 November 2026",
        subject_text="Activity Proposal — Establishment of the Model United Nations Club",
    )

    # Budget: no figures exist yet, so say so instead of printing an empty column.
    budget = next(t for t in doc.tables
                  if t.rows[0].cells[0].text.strip().upper() == "ITEM")
    replace_para_text(budget.rows[0].cells[1].paragraphs[0], "BUDGET SOURCE")
    for row in budget.rows[1:]:
        replace_para_text(row.cells[2].paragraphs[0],
                          "TBD" if row.cells[0].text.strip().upper() != "TOTAL"
                          else "TBD — subject to approval")

    if not any(p.text.strip().startswith("No amount is fixed at this stage")
               for p in doc.paragraphs):
        note = doc.add_paragraph()
        note.style = doc.styles["No Spacing"]
        note.paragraph_format.first_line_indent = Pt(36)
        note.paragraph_format.space_before = Pt(4)
        note.paragraph_format.space_after = Pt(6)
        note.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        style_run(note.add_run(
            "No amount is fixed at this stage. The Club holds no funds of its own until "
            "it is recognized; the Treasurer shall submit itemized figures with the first "
            "budget request after the first general assembly, for the approval of the "
            "Principal IV."
        ))
        budget._tbl.addnext(note._p)

    # Adoption year: the Constitution takes effect on approval, in 2026.
    adopted = find(doc, "ADOPTED this")
    replace_para_text(adopted, adopted.text.replace("2027", "2026"))

    # Plan of Action intro: drop the stale sentence that claimed the block stops in
    # December; the table carries a Term 3 block through April 2027.
    intro = find(doc, "This Plan of Action operationalizes")
    stale = (" Within Term 2 the Club's activities begin in November 2026, "
             "so the block below covers only November and December.")
    if stale in intro.text:
        replace_para_text(intro, intro.text.replace(stale, ""))

    # Signature table: one alignment, not centred names over left-aligned roles.
    for t in doc.tables:
        if t.rows[0].cells[0].text.strip().upper() == "AARON Y. HERNANDEZ":
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p.paragraph_format.left_indent = Pt(0)
                        p.paragraph_format.first_line_indent = Pt(0)

    # Space under the letterhead rule before the title.
    title = find(doc, "ACTIVITY PROPOSAL")
    title.paragraph_format.space_before = Pt(12)

    fix_tables(doc)
    keep_intro_with_table(doc)
    normalise_type(doc)
    add_page_numbers(doc)
    doc.save(path)
    return path


def main():
    for fn in (fix_ap009, fix_ap007, fix_ap010):
        print("fixed:", fn().name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
