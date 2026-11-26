"""Build the Program Management Team / Technical Working Group issuances for
DISYEMBREgalo and the Students Week opening program.

Each document clones NOM_SSLG_2026_003 (1).docx so the letterhead parts stay
byte-identical, reuses its TO / SUBJECT blocks, and replaces the agenda table
with the committee assignment table modelled on the World Teachers' Day AP
(AP 006).
"""
import copy
import shutil
import time
import zipfile
from pathlib import Path

import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "02 Activities/Brigada Eskwela 2026/Sources/NOM_SSLG_2026_003 (1).docx"
DATE = "November 15, 2026"
FONT = "Bookman Old Style"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

COLUMNS = [
    ("DESIGNATION", 101),
    ("SCOPE OF WORK", 195),
    ("CLUB / ORGANIZATION", 128),
    ("NAME OF PERSONNEL", 88.8),
]

SIGNATORIES = [
    ("Prepared by:", "SAMANTHA JOY C. DE VENECIA", "SSLG Treasurer"),
    ("Noted by:", "AARON KHRISTIAN T. BANAG", "SSLG Adviser"),
    ("Approved by:", "AMPARO M. MUÑOZ, EdD", "Principal IV"),
]

CONFIGS = [
    {
        "out": ROOT / "Technical Working Group - Disyembregalo.docx",
        "subtitle": "DISYEMBREgalo: A Season of Giving \u2014 December 10, 2026",
        "subject": "DESIGNATION OF THE TECHNICAL WORKING GROUP FOR DISYEMBREgalo",
        "intro": (
            "In preparation for DISYEMBREgalo: A Season of Giving on December 10, "
            "2026, the following committees are hereby constituted. Each committee "
            "shall perform the tasks below and shall work under the supervision of the "
            "SSLG Advisers."
        ),
        "rows": [
            ("Attendance and Registration",
             "Registration of beneficiaries; attendance",
             "B&E Club and ValEd Club"),
            ("Program and Tarpaulin",
             "Program, tarpaulins, and printed materials",
             "AP Club and RCYC"),
            ("Stage Decoration",
             "Stage design, set-up, and dismantling",
             "ASSH Club and STEM Club"),
            ("Venue and Physical Arrangements",
             "Chairs, tables, and gift area; set-up",
             "BERT Club and ICONS Club"),
            ("Sound System",
             "Audio set-up, operation, and pack-up",
             "Technical Professional Club"),
            ("Documentation",
             "Photo and video coverage; report",
             "BKB Club"),
        ],
        "note": (
            "All other clubs and organizations shall assist in the sorting and packing "
            "of donations upon the request of the SSLG Advisers."
        ),
    },
    {
        "out": ROOT / "Technical Working Group - Students Week Opening Program.docx",
        "subtitle": "Students Week Opening Program \u2014 December 7, 2026",
        "subject": (
            "DESIGNATION OF THE TECHNICAL WORKING GROUP FOR THE STUDENTS WEEK "
            "OPENING PROGRAM"
        ),
        "intro": (
            "In preparation for the opening program of the 2026 National Students' Day "
            "Celebration on December 7, 2026, the following committees are hereby "
            "constituted. Each committee shall perform the tasks below and shall work "
            "under the supervision of the SSLG Advisers."
        ),
        "rows": [
            ("Program and Tarpaulin",
             "Program, tarpaulins, and printed materials",
             "ARS Club and TVE Club"),
            ("Stage Decoration",
             "Stage design, set-up, and dismantling",
             "MAPEH Club, PFG, and YES-O"),
            ("Venue and Physical Arrangements",
             "Chairs, tables, and venue set-up",
             "Samahan ng Bagong Sibol"),
            ("Sound System",
             "Audio set-up, operation, and pack-up",
             "APPA Club Officers"),
            ("Documentation",
             "Photo and video coverage; report",
             "English Club"),
        ],
        "note": (
            "All clubs and organizations shall join the presentation of banners and "
            "shall prepare their booths from 12:00 NN to 3:00 P.M."
        ),
    },
]


def clear_content(paragraph):
    for child in list(paragraph._p):
        if child.tag in (W + "r", W + "hyperlink", W + "bookmarkStart", W + "bookmarkEnd"):
            paragraph._p.remove(child)


def add_runs(paragraph, parts, size=12):
    for text, bold in parts:
        run = paragraph.add_run(text)
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = bold


def strip_drawings(paragraph):
    for run in list(paragraph.runs):
        if run._r.findall(".//" + W + "drawing"):
            run._r.getparent().remove(run._r)


def new_paragraph_like(model, parent, text, bold=False, size=12, align=None,
                       space_before=0, space_after=0):
    new_p = copy.deepcopy(model._p)
    for child in list(new_p):
        if child.tag != W + "pPr":
            new_p.remove(child)
    p_pr = new_p.find(W + "pPr")
    if p_pr is not None:
        for tag in ("numPr", "ind"):
            el = p_pr.find(W + tag)
            if el is not None:
                p_pr.remove(el)
    parent.addnext(new_p)
    para = Paragraph(new_p, parent.getparent())
    add_runs(para, [(text, bold)], size=size)
    if align is not None:
        para.alignment = align
    fmt = para.paragraph_format
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    return para


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    for tag in ("tblBorders", "tblLayout", "tblW"):
        el = tbl_pr.find(qn(f"w:{tag}"))
        if el is not None:
            tbl_pr.remove(el)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tbl_pr.append(borders)


def fix_table_layout(table, widths):
    tbl_pr = table._tbl.tblPr
    for tag in ("tblLayout", "tblW"):
        el = tbl_pr.find(qn(f"w:{tag}"))
        if el is not None:
            tbl_pr.remove(el)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), str(sum(widths) * 20))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_pr.append(tbl_w)
    grid = table._tbl.find(qn("w:tblGrid"))
    for col, width in zip(grid.findall(qn("w:gridCol")), widths):
        col.set(qn("w:w"), str(int(width * 20)))
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        tr_pr.append(cant)
        for cell, width in zip(row.cells, widths):
            cell.width = Pt(width)


def cell_text(cell, text, bold=False, size=9.5):
    para = cell.paragraphs[0]
    clear_content(para)
    add_runs(para, [(text, bold)], size=size)
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fmt = para.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing = Pt(11)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP


def build(cfg):
    out = cfg["out"]
    shutil.copy2(SRC, out)
    d = docx.Document(out)
    paras = d.paragraphs

    p_date, p_title, p_from = paras[0], paras[1], paras[3]
    model_body = paras[6]

    clear_content(p_date)
    add_runs(p_date, [(DATE, False)])
    p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    clear_content(p_title)
    add_runs(p_title, [("TECHNICAL WORKING GROUP", True)], size=14)

    new_paragraph_like(
        p_title, p_title._p, cfg["subtitle"],
        bold=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=0, space_after=6,
    )

    for blank in (paras[2], paras[4]):
        if blank._p.getparent() is not None:
            blank._p.getparent().remove(blank._p)

    p_from.paragraph_format.space_before = Pt(10)
    strip_drawings(p_from)
    clear_content(p_from)
    add_runs(p_from, [
        ("FROM:\t", False),
        ("Hon. RHIAN JADE L. CASTRO", True),
        ("\n\tChairperson, Learner Government Coordinating Council (LGCC)", False),
        ("\n\tPresident, Supreme Secondary Learner Government (SSLG)", False),
    ], size=12)

    to_cell = d.tables[0].rows[0].cells[1]
    clear_content(to_cell.paragraphs[0])
    add_runs(to_cell.paragraphs[0], [
        ("PRESIDENTS AND OFFICERS OF REGISTERED CLUBS AND ORGANIZATIONS", True),
        ("\nAll Others Concerned", True),
    ], size=12)

    subj_cell = d.tables[1].rows[0].cells[1]
    clear_content(subj_cell.paragraphs[0])
    subj_cell.paragraphs[0].paragraph_format.space_before = Pt(6)
    subj_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_runs(subj_cell.paragraphs[0], [(cfg["subject"], True)], size=12)

    agenda = d.tables[2]
    intro = new_paragraph_like(
        model_body, agenda._tbl.getprevious(), cfg["intro"],
        size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=6,
    )
    agenda._tbl.getparent().remove(agenda._tbl)
    spacer = paras[5]
    if spacer._p.getparent() is not None:
        spacer._p.getparent().remove(spacer._p)

    table = d.add_table(rows=1 + len(cfg["rows"]), cols=len(COLUMNS))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    widths = [w for _, w in COLUMNS]
    fix_table_layout(table, widths)

    header = table.rows[0]
    header._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for cell, (label, _) in zip(header.cells, COLUMNS):
        cell_text(cell, label, bold=True)
        set_cell_shading(cell, "D9D9D9")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    for row, (designation, scope, club) in zip(table.rows[1:], cfg["rows"]):
        cell_text(row.cells[0], designation, bold=True)
        cell_text(row.cells[1], scope)
        cell_text(row.cells[2], club)
        cell_text(row.cells[3], "")

    intro._p.addnext(table._tbl)

    note = new_paragraph_like(
        model_body, table._tbl, cfg["note"], size=9.5,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=6, space_after=0,
    )
    closing = new_paragraph_like(
        model_body, note._p, "For information, guidance, and compliance.",
        size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=4, space_after=8,
    )

    sig_table = d.add_table(rows=1, cols=3)
    sig_widths = [175, 168, 169]
    fix_table_layout(sig_table, sig_widths)
    for cell, width in zip(sig_table.rows[0].cells, sig_widths):
        cell.width = Pt(width)
    for cell, (label, name, position) in zip(sig_table.rows[0].cells, SIGNATORIES):
        p1 = cell.paragraphs[0]
        add_runs(p1, [(label, False)], size=10)
        p2 = cell.add_paragraph()
        add_runs(p2, [(name, True)], size=9.5)
        p3 = cell.add_paragraph()
        add_runs(p3, [(position, False)], size=9.5)
        for pp in (p1, p2, p3):
            pp.paragraph_format.space_before = Pt(0)
            pp.paragraph_format.space_after = Pt(0)
            pp.paragraph_format.line_spacing = 1
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    closing._p.addnext(sig_table._tbl)

    d.add_paragraph()

    for stale in paras[6:]:
        if stale._p.getparent() is not None:
            stale._p.getparent().remove(stale._p)

    props = d.core_properties
    props.title = out.stem
    props.subject = cfg["subject"]
    props.author = "Supreme Secondary Learner Government"

    d.save(out)
    restore_letterhead_parts(out, SRC)
    print("wrote", out)


def restore_letterhead_parts(docx_path, source_path):
    with zipfile.ZipFile(source_path) as src_zip:
        originals = {
            name: src_zip.read(name)
            for name in src_zip.namelist()
            if name.startswith(("word/header", "word/footer")) and name.endswith(".xml")
        }
    tmp = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx_path) as new_zip, zipfile.ZipFile(
        tmp, "w", zipfile.ZIP_DEFLATED
    ) as out_zip:
        for item in new_zip.infolist():
            out_zip.writestr(item, originals.get(item.filename, new_zip.read(item.filename)))
    for attempt in range(10):
        try:
            tmp.replace(docx_path)
            break
        except PermissionError:
            time.sleep(1.0)
    else:
        raise


def main():
    for cfg in CONFIGS:
        build(cfg)


if __name__ == "__main__":
    main()
