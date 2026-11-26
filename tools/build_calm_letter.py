"""Build the Project Calm excuse letter from the July 2026 excuse-letter master.

Clones the accepted EL_SSLG_2026_010.docx so the letterhead (header/footer parts) stays
byte-identical, then rewrites only the date line, the TO block and the three body
paragraphs. Signature blocks are kept as accepted.
"""
import shutil
import zipfile
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "02 Activities/Municipal Short Film Festival 2026/Sources/EL_SSLG_2026_010.docx"
OUT_CLUBS = ROOT / "Excuse Letter - Project Calm.docx"
OUT_SSLG = ROOT / "Excuse Letter - Project Calm (SSLG Officers).docx"
OUT_STE = ROOT / "Excuse Letter - Project Calm (STE B).docx"
OUT_MPH = ROOT / "Request Letter - Multi-Purpose Hall.docx"

DATE = "November 10, 2026"
ADDREESSEES = (
    "SENIOR HIGH SCHOOL TEACHERS",
    "JUNIOR HIGH SCHOOL TEACHERS",
    "All Concerned",
)

CLUB_BODY = [
    ("\tIn accordance with ", False),
    ("PROJECT CALM", True),
    (
        ", we respectfully request to excuse the following "
        "Clubs/Organizations: MAPEH CLUB, ESP CLUB, BATANG EMPOWERED AND RESILIENT "
        "TEAM (BERT), BOY SCOUT OUTFIT 169 & 282, and PFG from their respective classes on ",
        False,
    ),
    ("November 10, 2026 from 11:00 A.M. to 4:00 P.M.", True),
    (
        " Their involvement will be instrumental to the preparations for the "
        "event\u2019s overall success. The complete list of participants per club and "
        "organization is attached as Annex A.",
        False,
    ),
]

SSLG_BODY = [
    ("\tIn accordance with ", False),
    ("PROJECT CALM", True),
    (", we respectfully request to excuse the ", False),
    ("Supreme Secondary Learner Government (SSLG) Officers", True),
    (" from their respective classes on ", False),
    ("November 10, 2026 from 11:00 A.M. to 4:00 P.M.", True),
    (
        " Their involvement will be instrumental to the preparations for the "
        "event\u2019s overall success.",
        False,
    ),
]

BODY_2 = [
    (
        "\tThe time used for this activity will enable the students to carry out "
        "the activities of Project Calm, ensuring that the event fulfills its mandate "
        "of fostering the holistic development of the school community. This is "
        "likewise pivotal in allowing the officers to fulfill their responsibilities "
        "to the student body.",
        False,
    ),
]

STE_BODY = [
    ("\tIn accordance with ", False),
    ("PROJECT CALM", True),
    (", we respectfully request to excuse the ", False),
    # Non-breaking space keeps "STE B" on one line.
    ("STE\u00a0B students", True),
    (" from their classes on ", False),
    ("November 10, 2026 from 11:00 A.M. to 4:00 P.M.", True),
    (
        " Their involvement will be instrumental to the event\u2019s preparations "
        "and overall success. The complete list of participants is attached as Annex A.",
        False,
    ),
]

STE_BODY_2 = [
    (
        "\tThe time used for this activity will enable the students to carry out "
        "the activities of Project Calm, ensuring that the event fulfills its mandate "
        "of fostering the holistic development of the school community.",
        False,
    ),
]

# Request for the Multi-Purpose Hall, addressed to and approved by Sir Pepito.
# Formal name and designation follow the SSLG governance memorandum in this vault
# (OM-SSLG-IA-2026-001): "PEPITO C. DOMINGO JR. / MT 1 - OIC English Dept".
MPH_ADDRESSEES = ("MR. PEPITO C. DOMINGO JR.",)

MPH_BODY = [
    ("\tIn connection with the upcoming ", False),
    ("Students Week and Disyembregalo", True),
    (", we respectfully request the use of the ", False),
    ("Multi-Purpose Hall (MPH)", True),
    (" on ", False),
    # Non-breaking spaces keep each time and its meridiem on one line.
    (
        "November 10, 11, and\u00a012, 2026 from 10:00\u00a0A.M. to 11:00\u00a0A.M. "
        "and 1:00\u00a0P.M. to 2:00\u00a0P.M. each day",
        True,
    ),
    (
        ". The hall will serve as the venue for the meetings of the presidents of all "
        "registered clubs and organizations, where the activities of both events and "
        "the participation of the different clubs and organizations will be discussed.",
        False,
    ),
]

MPH_BODY_2 = [
    (
        "\tThe time requested will allow the club presidents to discuss the details "
        "of Students Week and Disyembregalo, ensuring that both events are carried out "
        "smoothly and that all clubs and organizations are properly guided in their "
        "participation.",
        False,
    ),
]

MPH_APPROVAL = [
    ("\n", False),
    ("PEPITO C. DOMINGO JR.", True),
    ("\n", True),
    ("MT 1 - OIC, English Department", False),
    ("\n", False),
]

# Participant lists exactly as supplied in the SSLG thread; section or role follows the
# name after an em dash where the thread gave one.
ANNEX = [
    ("PFG", [
        "Elizabeth G. Sarmiento",
        "Jenna Nazal Caguiat",
        "Criza Dominique Alimurung",
        "Altheya Razon",
        "Hyacinth Estacio",
        "Xyrene Dizon",
        "Mallumie Dorado",
        "Marjorie M. Dalusong",
        "Jamila Canlas",
        "Akhan Norfrane Yutuc",
        "Allen Sagun",
        "Ainah Palisoc",
        "Jaymhar Villanueva",
        "Wendel Evangelista",
        "Charles John Nuqui",
        "Xian Galaora",
        "Yahsi Tongson",
        "Zabrina Castro",
        "Rhian R. Narciso",
        "Kim Lizhel Tulio",
        "Mildred M. Yumul",
        "Lorenz Pamintuan",
        "Andrei Baluyut",
        "Kate Arzel Canlas",
        "Floribel Chloe Reyes",
        "Gee Ashlee Sebastian",
        "John Louis Perez",
        "Joshua C. Perez",
        "Grenzell Mae Cortez",
        "Ivy Joyce Gaspar",
    ]),
    ("BERT", [
        "Mark Anthony Canono \u2014 8-Papaya",
        "Christopher Garcia \u2014 8-Peach",
        "Mimi P. Gomez \u2014 9-Acacia",
        "Shan Kloe Bulacso \u2014 10-Nebula",
        "Jielan G. Licup \u2014 10-Nebula",
        "Jaybee K. Velasco \u2014 10-Nebula",
        "Mark Daniel P. Ofalla \u2014 10-Nebula",
        "Leyven A. Lozada \u2014 10-Nebula",
        "Yohann Jazz M. Mercado \u2014 10-Nebula",
        "Anthony James B. Estacio \u2014 10-Nebula",
        "Kelvin O. Salunga \u2014 STE 10-B",
        "Janine P. Culala \u2014 STE 10-B",
        "KC Lorraine D. Quiambao \u2014 STE 10-B",
        "John Simon P. Angkil \u2014 STE 10-B",
        "Xavier Manaloto \u2014 STE 10-B",
        "Jhovielyn Aiseah S. Chua \u2014 STE 10-B",
        "Lourrhaine Jhazz M. Aquino \u2014 STE 10-B",
        "Jamila L. Baligod \u2014 10-Taurus",
        "Keith Ann V. Dela Cruz \u2014 10-Virgo",
        "Bambie G. Galang \u2014 9-Lauan",
        "Syd Jeuel Amurao \u2014 9-Dapdap",
        "Cylene Zia Bautista \u2014 9-Oaktree",
        "Micaela Mae C. Lubaton \u2014 9-Oaktree",
        "Jimmuel L. Mallari \u2014 8-Peach",
        "Christian Lloyd Manalo \u2014 7-Hyacinth",
        "Anna Rose D. Antonio",
        "John Patrick S. Sunga",
        "Janelle Robles",
        "Shania Jade B. Porlucas",
        "Ma. Angela B. Baluyut",
    ]),
    ("MAPEH CLUB", [
        "Kristin Daennielle L. Romero \u2014 President",
        "Fervhie Jude M. Poligrates \u2014 Vice President",
        "Rapha Joy C. Licuanan \u2014 Secretary",
        "Francen Luis R. Juanatas \u2014 Treasurer",
        "Jessica D. Reyes \u2014 Auditor",
        "Jhed Nathan B. Lapuz \u2014 P.I.O.",
        "Shaine Chloe E. Esguerra \u2014 P.I.O.",
        "Dawn Kristelle D. Gonzales \u2014 P.O.",
        "Athena Coleen R. Lazaro \u2014 P.O.",
        "Lorraine Tiamzon \u2014 G10 Representative",
        "Maia Reana P. Pangan \u2014 G10 Representative",
        "Homer Timothy V. Gonzales \u2014 G9 Representative",
        "Bryan Llorin L. Magdasoc \u2014 G9 Representative",
        "Chelsy Ann D. Sison \u2014 G8 Representative",
        "Therese Trina P. Tulio \u2014 G8 Representative",
        "Deinielle Andrew C. Ramos \u2014 G7 Representative",
        "John Cedrick A. Lacsina \u2014 G7 Representative",
        "Mar Jun B. Quintia \u2014 G9 Member",
        "Curt Gerich Yhael Nucum \u2014 G9 Member",
        "Rijz Eisha A. Yumul \u2014 G9 Member",
    ]),
    ("BOY SCOUT OUTFIT 169", [
        "Prince Robin Bryan C. Clores \u2014 Grade 10 Capricorn",
        "Ragender Pangilinan \u2014 Grade 9 Dao",
        "Lennur L. Reyes \u2014 Grade 8 Dragonfruit",
        "Plaer Mandy G. Pedalizo \u2014 Grade 7 STE B",
        "Cedrick Mallari \u2014 Grade 10 Capricorn",
        "Daniel Millaris \u2014 Grade 8 Lanzones",
        "Maine Garcia \u2014 Grade 9 Dita",
        "Jean Andrea Briones \u2014 Grade 7 STE B",
        "Alexander S. Dimarucut \u2014 Grade 8 STE C",
        "Sheena Mae Garzo \u2014 Grade 8 Apple",
        "Yuri Evaristo \u2014 Grade 8 Apple",
        "Grenzell Mae Cortez \u2014 Grade 8 Cantaloupe",
        "Clairen Hortillosa \u2014 Grade 8 Peach",
        "Jalilah Radiab \u2014 Grade 7 Adelfa",
        "John Jhay P. Versoza \u2014 Grade 7 Daffodil",
        "Misha Aliah Sese \u2014 Grade 10 Uranus",
        "Princess Adeline D. Garcia \u2014 Grade 7 Daisy",
        "Eufritz Aizen Hipolito \u2014 Grade 7 Daffodil",
        "Roselyn Tapnio \u2014 Grade 8 Mabolo",
        "Keisha Nicole Santos",
    ]),
    ("BOY SCOUT OUTFIT 282", [
        "Canlas, Mary Angeline T. \u2014 12 Collins",
        "Mendoza, Akeisha P. \u2014 11 Luke",
        "Jaramillos, Ryzell Linzae M. \u2014 12 Collins",
        "Cristobal, Thessah \u2014 11 Philippians",
        "Palaganas, Ghillianne A. \u2014 11 Dolomite",
        "Mejia, Alexa Marie M. \u2014 12 Collins",
        "Baltazar, Sophia \u2014 11 Luke",
        "Manuel, Jay Mark A. \u2014 12 Voltage",
        "Marich A. Denosta \u2014 11 Fusion",
        "Cyruz P. Lalu \u2014 11 Matthew",
    ]),
    ("VALED CLUB", [
        "Lance Vibas",
        "Precious Mendoza",
        "Cheska Pare\u00f1a",
        "Gilian Dayrit",
        "Ceshiah Capian",
        "Erica Mae Mangune",
        "Sem Arceo",
        "John Erwin Santos",
        "Naomi Lacson",
        "Calyx Pamintuan",
        "Jadeca Abalos",
        "Lyka Castro",
        "Jhane Manalo",
        "Princess Shammel Hipolito",
        "Decelle Carreon",
        "Jhilian Gonzalez",
        "Jm Pantollana",
        "Hans Hipolito",
        "Paulyn Mandal",
        "Princess Aine Dela Cruz",
        "Rhian Angeles",
        "Sophia Angela Turla",
        "Nadine Hipolito",
        "Gianne De Leon",
        "Cheyanne Maniego",
        "Daniella Lacanlale",
        "Jhasen Tolentino",
        "Shanelle De Leon",
        "Kristian Oderon",
    ]),
    ("PROJECT CALM PARTICIPANTS (SBS)", [
        "Reilee Garcia",
        "Princess Mae Santos",
        "Jin Diaz",
        "Noah Dalusong",
        "Jaycee Arance",
        "Cyrus Gaddi",
        "Janese Murrf",
    ]),
]

# STE B list exactly as supplied in the SSLG thread, capitalization normalized only.
STE_ANNEX = [
    ("STE B", [
        "Athan Jamir Angeles",
        "John Simon Angkil",
        "Xandree Datul",
        "Lance Arman Ebreo",
        "Erdy Jr. Estrada",
        "Sanlee Dave Gonzales",
        "Daniel Matthew Laga",
        "Xavier Manaloto",
        "Jehoshaphat Corby Puerte",
        "Akhio Reyes",
        "Cyrus Salas",
        "Kelvin Salunga",
        "Joaquin Jethro Sumauang",
        "Geoff Liam Tolentino",
        "Miguel Tolentino",
        "Nathan Venus",
        "Kishia Rayne Anunciacion",
        "Reana Atuban",
        "Jhovielyn Aiseah Chua",
        "Elyza Pauleen Cordero",
        "Janine Culala",
        "Dawn Kristelle Gonzales",
        "Diyah Marowe Hipolito",
        "Xhane Ellize Pingol",
        "Kristin Daennielle Romero",
    ]),
]


def clear_runs(paragraph):
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)


def add_runs(paragraph, parts):
    for text, bold in parts:
        run = paragraph.add_run(text)
        run.font.name = "Bookman Old Style"
        run.font.size = Pt(12)
        run.font.bold = bold
        rpr = run._element.get_or_add_rPr()
        fonts = rpr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
        if fonts is not None:
            fonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs", "Arial")


def restore_letterhead_parts(docx_path, source_path):
    """Put the source header/footer parts back byte-for-byte (house rule)."""
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
            data = originals.get(item.filename, new_zip.read(item.filename))
            out_zip.writestr(item, data)
    tmp.replace(docx_path)


def _cell_text(cell, text, bold=False, center=False):
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text)
    run.font.name = "Bookman Old Style"
    run.font.size = Pt(12)
    run.font.bold = bold


def _mark_row(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
    if header:
        trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))


def add_annex(d, groups=None, subtitle_text="PROJECT CALM PARTICIPANTS"):
    """Append Annex A: one bordered table per group, after a section break.

    The annex gets its own bottom margin so the tall letterhead footer never collides
    with table rows; header and footer stay linked to the letter's parts.
    """
    groups = ANNEX if groups is None else groups
    section = d.add_section(WD_SECTION.NEW_PAGE)
    section.bottom_margin = Inches(1.35)

    # add_section leaves an empty paragraph carrying section 1's sectPr. With the
    # letter ending flush against the tall letterhead footer, that empty paragraph
    # spilled onto a blank page 2. Move the sectPr into the letter's last paragraph
    # and drop the empty one, so page 2 starts directly with ANNEX A.
    break_para = d.paragraphs[-1]
    sect_pr = break_para._p.pPr.find(qn("w:sectPr"))
    prev_p = break_para._p.getprevious()
    # The template closes the signature block with a bare line break. Behind a
    # section break that stray line lands on a page of its own, so drop it.
    last_run = prev_p.findall(qn("w:r"))[-1]
    brs = last_run.findall(qn("w:br"))
    if brs and not last_run.findall(qn("w:t")):
        last_run.remove(brs[-1])
        if not last_run.findall(qn("w:br")):
            prev_p.remove(last_run)
    prev_ppr = prev_p.find(qn("w:pPr"))
    if prev_ppr is None:
        prev_ppr = OxmlElement("w:pPr")
        prev_p.insert(0, prev_ppr)
    prev_ppr.append(sect_pr)
    break_para._p.getparent().remove(break_para._p)

    title = d.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(0)
    run = title.add_run("ANNEX A")
    run.font.name = "Bookman Old Style"
    run.font.size = Pt(12)
    run.font.bold = True

    subtitle = d.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(10)
    run = subtitle.add_run(subtitle_text)
    run.font.name = "Bookman Old Style"
    run.font.size = Pt(12)
    run.font.bold = True

    for label, entries in groups:
        if len(groups) > 1:
            heading = d.add_paragraph()
            heading.paragraph_format.space_before = Pt(10)
            heading.paragraph_format.space_after = Pt(3)
            heading.paragraph_format.keep_with_next = True
            run = heading.add_run(f"{label} \u2014 {len(entries)} participants")
            run.font.name = "Bookman Old Style"
            run.font.size = Pt(12)
            run.font.bold = True
        elif len(groups) == 1:
            spacer = d.add_paragraph()
            spacer.paragraph_format.space_before = Pt(0)
            spacer.paragraph_format.space_after = Pt(0)
            spacer.paragraph_format.line_spacing = Pt(4)

        table = d.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        table.autofit = False
        table.alignment = 0
        for col, width in ((0, Inches(0.45)), (1, Inches(6.65))):
            table.columns[col].width = width
        for row in table.rows:
            for col, width in ((0, Inches(0.45)), (1, Inches(6.65))):
                row.cells[col].width = width

        _cell_text(table.rows[0].cells[0], "No.", bold=True, center=True)
        _cell_text(table.rows[0].cells[1], "Name", bold=True)
        _mark_row(table.rows[0], header=True)

        for number, entry in enumerate(entries, start=1):
            row = table.add_row()
            for col, width in ((0, Inches(0.45)), (1, Inches(6.65))):
                row.cells[col].width = width
            _cell_text(row.cells[0], str(number), center=True)
            _cell_text(row.cells[1], entry)
            _mark_row(row)

    d.add_paragraph()


def build(
    out,
    body,
    annex=None,
    body_2=BODY_2,
    addressees=ADDREESSEES,
    approval=None,
):
    shutil.copy2(SRC, out)
    d = docx.Document(out)
    paras = d.paragraphs

    # Date line: keep the right-aligned paragraph and its trailing spacing run.
    paras[0].runs[0].text = DATE

    # TO block
    clear_runs(paras[1])
    add_runs(paras[1], [("TO:", False)] + [
        (f"\t{name}" if i == 0 else f"\n\t{name}", True)
        for i, name in enumerate(addressees)
    ])

    # Body
    clear_runs(paras[3])
    add_runs(paras[3], body)
    clear_runs(paras[4])
    add_runs(paras[4], body_2)

    if annex:
        # Trim the empty spacer so the signature block clears the letterhead footer
        # band; otherwise the last line ("... MUÑOZ, EDD") collides with the band
        # and Word scatters "EDD" across the line.
        paras[6]._p.getparent().remove(paras[6]._p)
        add_annex(d, *annex)

    if approval:
        # The addressee signs off this request himself, so the Head Teacher VI
        # recommending-approval step is dropped and the final block is rewritten.
        for index in (12, 13):
            paras[index]._p.getparent().remove(paras[index]._p)
        clear_runs(paras[15])
        add_runs(paras[15], approval)

    d.save(out)
    restore_letterhead_parts(out, SRC)
    print("wrote", out)


def main():
    # The Project Calm letter now excuses STE B only; the club and SBS annexes are retired.
    build(
        OUT_CLUBS,
        STE_BODY,
        annex=(STE_ANNEX, "STE B PARTICIPANTS"),
        body_2=STE_BODY_2,
    )
    build(OUT_SSLG, SSLG_BODY)
    build(
        OUT_STE,
        STE_BODY,
        annex=(STE_ANNEX, "STE B PARTICIPANTS"),
        body_2=STE_BODY_2,
    )
    build(
        OUT_MPH,
        MPH_BODY,
        body_2=MPH_BODY_2,
        addressees=MPH_ADDRESSEES,
        approval=MPH_APPROVAL,
    )


if __name__ == "__main__":
    main()
