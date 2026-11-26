"""Build the Project Calm and Disyembregalo/Students Week notices of meeting.

Both clone NOM_SSLG_2026_003 (1).docx so the letterhead parts stay byte-identical, replace
the date, TO / SUBJECT / AGENDA blocks and the numbered body, and strip the inherited
signature scans (a draft carries no borrowed signatures).
"""
import copy
import shutil
import zipfile
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "02 Activities/Brigada Eskwela 2026/Sources/NOM_SSLG_2026_003 (1).docx"
DATE = "November 10, 2026"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

CONTACT = [
    ("For inquiries, concerns, and clarifications, please contact ", False),
    ("Hon. MICAELLA SABELLE R. MONLOY \u2013 Chairperson, Secretariat Committee ", True),
    ("at micaellasabelle30@gmail.com or www.facebook.com/ellalalalalaco2s.", False),
]
MANDATORY = [("Attendance in these meetings is strictly mandatory for all concerned members.", False)]
MANDATORY_ONE = [("Attendance in this meeting is strictly mandatory for all concerned members.", False)]
COMPLIANCE = [("For information and compliance.", False)]

PROJECT_CALM = {
    "out": ROOT / "Notice of Meeting - Project Calm.docx",
    "to": (
        "CLASS PRESIDENTS, GRADES 7 TO 12",
        "All Others Concerned",
    ),
    "subject": "PROJECT CALM ORIENTATION MEETINGS FOR CLASS PRESIDENTS",
    "agenda": (
        "a. Project Calm: Overview and Mechanics",
        "b. Role of Class Presidents",
        "c. Schedule of Face-to-Face Sessions",
        "d. Other Concerns",
    ),
    "body1": [
        (
            "In exigency of service, this Office hereby notifies the class presidents of "
            "Grades 7 to 12 that the Project Calm orientation meetings shall be held face "
            "to face on ",
            False,
        ),
        ("November 11, 2026, 10:00 A.M. to 11:00 A.M.", True),
        (", for Grades 7 and 8, and ", False),
        ("1:00 P.M. to 2:00 P.M.", True),
        (", for Grades 9 and 10; and on ", False),
        ("November 12, 2026, 10:00 A.M. to 11:00 A.M.", True),
        (
            ", for Grades 11 and 12. These sessions shall discuss the Project Calm "
            "scheme and the role of class presidents in its implementation.",
            False,
        ),
    ],
    "mandatory": MANDATORY,
}

DISYEMBREGALO = {
    "out": ROOT / "Notice of Meeting - Disyembregalo and Students Week.docx",
    "to": (
        "PRESIDENTS OF REGISTERED CLUBS AND ORGANIZATIONS",
        "All Others Concerned",
    ),
    "subject": "DISYEMBREGALO AND STUDENTS WEEK MEETING FOR CLUB AND ORGANIZATION PRESIDENTS",
    "agenda": (
        "a. Disyembregalo: Concept and Mechanics",
        "b. Students Week: Activities and Participation",
        "c. Role of Club and Organization Presidents",
        "d. Other Concerns",
    ),
    "body1": [
        (
            "In exigency of service, this Office hereby notifies the presidents of all "
            "registered clubs and organizations that a face-to-face meeting has been "
            "scheduled on ",
            False,
        ),
        ("November 12, 2026, 1:00 P.M. to 2:00 P.M.", True),
        (". This meeting shall convene to discuss ", False),
        ("Disyembregalo", True),
        (" and ", False),
        ("Students Week", True),
        (
            ", including their activities and the participation of the different clubs "
            "and organizations.",
            False,
        ),
    ],
    "mandatory": MANDATORY_ONE,
}


def clear_content(paragraph):
    for child in list(paragraph._p):
        if child.tag in (W + "r", W + "hyperlink"):
            paragraph._p.remove(child)


def add_runs(paragraph, parts, size=12):
    for text, bold in parts:
        run = paragraph.add_run(text)
        run.font.name = "Bookman Old Style"
        run.font.size = Pt(size)
        run.font.bold = bold


def strip_drawings(paragraph):
    for run in list(paragraph.runs):
        if run._r.findall(".//" + W + "drawing"):
            run._r.getparent().remove(run._r)


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
    tmp.replace(docx_path)


def build(cfg):
    out = cfg["out"]
    shutil.copy2(SRC, out)
    d = docx.Document(out)
    paras = d.paragraphs

    paras[0].runs[0].text = DATE

    # TO cell
    to_cell = d.tables[0].rows[0].cells[1]
    p = to_cell.paragraphs[0]
    clear_content(p)
    add_runs(p, [(line if i == 0 else "\n" + line, True) for i, line in enumerate(cfg["to"])])

    # FROM: drop the borrowed signature scans, keep the block
    strip_drawings(paras[3])
    strip_drawings(paras[5])

    # SUBJECT cell
    subj_cell = d.tables[1].rows[0].cells[1]
    p = subj_cell.paragraphs[0]
    clear_content(p)
    add_runs(p, [(cfg["subject"], True)])

    # AGENDA cell: first paragraph plus clones for the remaining items
    agenda_cell = d.tables[2].rows[0].cells[1]
    first = agenda_cell.paragraphs[0]
    for extra in agenda_cell.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    clear_content(first)
    add_runs(first, [(cfg["agenda"][0], True)])
    cursor = first
    for item in cfg["agenda"][1:]:
        new_p = copy.deepcopy(first._p)
        cursor._p.addnext(new_p)
        cursor = Paragraph(new_p, first._parent)
        clear_content(cursor)
        add_runs(cursor, [(item, True)])
    for p in agenda_cell.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Numbered body
    for idx, parts in ((6, cfg["body1"]), (7, cfg["mandatory"]), (8, CONTACT), (9, COMPLIANCE)):
        p = paras[idx]
        clear_content(p)
        add_runs(p, parts)
    paras[8].alignment = WD_ALIGN_PARAGRAPH.LEFT

    # The master ends with an empty spacer paragraph; drop it so nothing lands on page 2.
    if not paras[10].text.strip():
        paras[10]._p.getparent().remove(paras[10]._p)

    d.save(out)
    restore_letterhead_parts(out, SRC)
    print("wrote", out)


def main():
    build(PROJECT_CALM)
    build(DISYEMBREGALO)


if __name__ == "__main__":
    main()
