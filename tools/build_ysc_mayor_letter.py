"""Build the YSC letter to Mayor Villanueva in the house request-letter format.

Clones Request Letter - Multi-Purpose Hall.docx for the letterhead and paragraph
geometry, rewrites the body, and lays out the signature area the way the DepEd
papers here do it: "Respectfully yours." over the preparer, one "Noted by:" row
with two co-notaries side by side, then "Approved by:" left open for signature.
The SSLG-only LGCC line is removed from the header.
"""
import time
from copy import deepcopy
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

from build_calm_letter import add_runs, clear_runs, restore_letterhead_parts
from build_ysc_letters import LGCC_LINE, drop_header_line, set_label, set_name

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Request Letter - Multi-Purpose Hall.docx"
OUT = ROOT / "Letter - YSC Meeting and Fund Request (Mayor Villanueva).docx"

DATE = "November 13, 2026"
MEMBERS = (
    "Aaron Y. Hernandez (11-Onyx), Ellaine T. Jacob (11-Ilmenite), "
    "and Jolex Alexier S. Cruz (11-Jacinth)"
)

GREETING = "\tGreetings in the spirit of shared service and institutional excellence!"
PARAGRAPHS = [
    [
        ("\tWe respectfully request a meeting with your Office at your earliest "
         "convenience to discuss the projects of the ", False),
        ("Concepcion Local Government Unit", True),
        (", particularly on environmental protection and waterway management, "
         "and to present the school\u2019s ", False),
        ("Olympiad Club", True),
        (" entry to the ", False),
        ("Youth Science Convention (YSC) Case Study Competition", True),
        (" of ", False),
        ("Research Fair 2027", True),
        (". The team comprises ", False),
        (MEMBERS, True),
        (".", False),
    ],
    [
        ("\tThe competition requires each team to propose a twelve-month pilot "
         "project for a one-kilometer stretch of a local waterway and a blueprint "
         "for its expansion to the country\u2019s major river systems. We believe "
         "that the team\u2019s proposal can be aligned with the projects of the "
         "LGU, and that the meeting will open areas of cooperation. The Phase 1 "
         "project deadline is on ", False),
        ("5 December 2026", True),
        (".", False),
    ],
    [
        ("\tWe likewise respectfully request financial assistance for the "
         "team\u2019s registration, materials, and transportation to the ", False),
        ("University of the Philippines Diliman", True),
        (" on ", False),
        ("January\u00a09, 2027", True),
        (". Any support from your Office will greatly help the team meet the "
         "requirements of the competition.", False),
    ],
    [
        ("\tWe look forward to your favorable response to this request. "
         "May the Almighty continue to bless us.", False),
    ],
]

PREPARER = ("SIR ELDRIN L. PATIO", "Research Adviser")
NOTERS = [
    ("AMPARO M. MUÑOZ, EDD", ["Principal IV"]),
    (
        "DR. NICOLASA S. CAMAYA",
        [
            "Public School District Supervisor",
            "Concepcion West District",
            "LSB Co-Chairperson",
        ],
    ),
]


def set_spacing(paragraph, before=None, after=None):
    if before is not None:
        paragraph.paragraph_format.space_before = Pt(before)
    if after is not None:
        paragraph.paragraph_format.space_after = Pt(after)


def unitalic(paragraph):
    for run in paragraph._p.findall(qn("w:r")):
        rpr = run.find(qn("w:rPr"))
        if rpr is None:
            continue
        for tag in ("w:i", "w:iCs"):
            for el in rpr.findall(qn(tag)):
                rpr.remove(el)


def no_borders(table):
    tbl_pr = table._tbl.tblPr
    for el in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(el)
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tbl_pr.append(borders)

    for el in tbl_pr.findall(qn("w:tblCellMar")):
        tbl_pr.remove(el)
    mar = OxmlElement("w:tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), "0")
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tbl_pr.append(mar)

    for el in tbl_pr.findall(qn("w:tblW")):
        tbl_pr.remove(el)
    width = OxmlElement("w:tblW")
    width.set(qn("w:w"), str(5120 * 2))
    width.set(qn("w:type"), "dxa")
    tbl_pr.append(width)

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)


def set_name_lines(el, name, lines):
    """Name over one or more role lines, using the template's own break runs."""
    runs = el.findall(qn("w:r"))
    runs[1].find(qn("w:t")).text = name
    runs[3].find(qn("w:t")).text = lines[0]
    anchor = runs[3]
    for line in lines[1:]:
        br = deepcopy(runs[2])
        anchor.addnext(br)
        extra = deepcopy(runs[3])
        extra.find(qn("w:t")).text = line
        br.addnext(extra)
        anchor = extra


def fill_cell(cell, name, lines, name_tpl):
    paragraph = deepcopy(name_tpl)
    set_name_lines(paragraph, name, lines)
    old = cell.paragraphs[0]._p
    old.addnext(paragraph)
    old.getparent().remove(old)


def build():
    OUT.write_bytes(SRC.read_bytes())
    d = docx.Document(OUT)
    paras = d.paragraphs

    paras[0].runs[0].text = DATE + "        "
    date_rpr = paras[0].runs[0]._r.get_or_add_rPr()
    for tag in ("w:sz", "w:szCs"):
        el = date_rpr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            date_rpr.append(el)
        el.set(qn("w:val"), "24")

    clear_runs(paras[1])
    add_runs(paras[1], [
        ("TO:", False),
        ("\tHON. NOEL L. VILLANUEVA", True),
        ("\n\tMunicipal Mayor", True),
    ])

    clear_runs(paras[2])
    add_runs(paras[2], [(GREETING, False)])

    # Master carries three body paragraphs; this letter needs four.
    clear_runs(paras[3])
    add_runs(paras[3], PARAGRAPHS[0])
    clear_runs(paras[4])
    add_runs(paras[4], PARAGRAPHS[1])
    extra = deepcopy(paras[4]._p)
    paras[4]._p.addnext(extra)
    extra_para = docx.text.paragraph.Paragraph(extra, paras[4]._parent)
    clear_runs(extra_para)
    add_runs(extra_para, PARAGRAPHS[2])
    clear_runs(paras[5])
    add_runs(paras[5], PARAGRAPHS[3])

    label_tpl = deepcopy(paras[8]._p)
    name_tpl = deepcopy(paras[9]._p)
    spacer_tpl = deepcopy(paras[6]._p)

    body_el = d.element.body
    for p in list(paras[6:]):
        body_el.remove(p._p)

    anchor = paras[5]._p

    spacer = deepcopy(spacer_tpl)
    anchor.addnext(spacer)
    anchor = spacer

    respects = deepcopy(label_tpl)
    unitalic(docx.text.paragraph.Paragraph(respects, paras[5]._parent))
    set_label(respects, "Respectfully yours.")
    anchor.addnext(respects)
    anchor = respects

    preparer = deepcopy(name_tpl)
    set_name(preparer, *PREPARER)
    set_spacing(docx.text.paragraph.Paragraph(preparer, paras[5]._parent), before=18)
    anchor.addnext(preparer)
    anchor = preparer

    noted = deepcopy(label_tpl)
    set_label(noted, "Noted by:")
    set_spacing(docx.text.paragraph.Paragraph(noted, paras[5]._parent), before=18)
    anchor.addnext(noted)
    anchor = noted

    table = d.add_table(rows=1, cols=2)
    no_borders(table)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    for col in table.columns:
        col.width = Pt(256)
    for cell, (name, role) in zip(table.rows[0].cells, NOTERS):
        cell.width = Pt(256)
        fill_cell(cell, name, role, name_tpl)
    anchor.addnext(table._tbl)
    anchor = table._tbl

    approved = deepcopy(label_tpl)
    set_label(approved, "Approved by:")
    set_spacing(docx.text.paragraph.Paragraph(approved, paras[5]._parent), before=18)
    anchor.addnext(approved)
    anchor = approved

    tail = deepcopy(spacer_tpl)
    anchor.addnext(tail)

    d.save(OUT)
    restore_letterhead_parts(OUT, SRC)
    drop_header_line(OUT, LGCC_LINE)
    print("wrote", OUT)


def main():
    for attempt in range(1, 21):
        try:
            build()
            return
        except PermissionError:
            if attempt == 20:
                raise
            time.sleep(2)


if __name__ == "__main__":
    main()
