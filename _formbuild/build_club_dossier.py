"""Build the SSLG club-classification research dossier (DOCX).

    python -X utf8 _formbuild/build_club_dossier.py

Writes docs/SSLG Club Classification Research Dossier.docx. Render to PDF with
tools/render_docx.py.
"""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "SSLG Club Classification Research Dossier.docx"

INK = RGBColor(0x1B, 0x1F, 0x24)
MUTED = RGBColor(0x5A, 0x62, 0x6D)
ACCENT = RGBColor(0x1F, 0x3A, 0x5F)
RULE = "8A94A6"
SHADE = "F2F4F7"
SHADE_WARN = "FDF3E7"


# ---------------------------------------------------------------- xml helpers
def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def cell_borders(cell, color="D5D9DF", sz="6"):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tcPr.append(borders)


def no_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        borders.append(el)
    tblPr.append(borders)


def set_widths(table, widths):
    table.autofit = False
    for i, w in enumerate(widths):
        table.columns[i].width = Cm(w)
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def para_border(p, edge="left", color=RULE, sz="18", space="10"):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), sz)
    el.set(qn("w:space"), space)
    el.set(qn("w:color"), color)
    pBdr.append(el)
    pPr.insert_element_before(
        pBdr,
        "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
        "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
        "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
        "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
        "w:textDirection", "w:textAlignment", "w:textboxTightWrap",
        "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr",
        "w:pPrChange",
    )


def page_footer(section, text):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text + "   |   page ")
    run.font.size = Pt(8)
    run.font.color.rgb = MUTED
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "16")
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    p._p.append(fld)


# ---------------------------------------------------------------- text helpers
def body(doc, text, size=10.5, space_after=6, italic=False, color=INK, bold=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.italic = italic
    r.font.bold = bold
    r.font.color.rgb = color
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.7)
    r = p.add_run(text)
    r.font.size = Pt(size)
    return p


def h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = ACCENT
    para_border(p, edge="bottom", color="C9D1DB", sz="8", space="4")
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = ACCENT
    return p


def quote(doc, text, cite=None):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.right_indent = Cm(0.2)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.keep_with_next = True
    r = p.add_run("\u201c" + text + "\u201d")
    r.font.size = Pt(9.5)
    r.font.italic = True
    r.font.color.rgb = RGBColor(0x2A, 0x30, 0x38)
    para_border(p)
    if cite:
        c = doc.add_paragraph()
        c.paragraph_format.left_indent = Cm(0.6)
        c.paragraph_format.space_before = Pt(0)
        c.paragraph_format.space_after = Pt(8)
        cr = c.add_run(cite)
        cr.font.size = Pt(8)
        cr.font.color.rgb = MUTED
        cr.font.bold = True


def finding(doc, tag, title, meta, quotes, proves):
    h2(doc, f"{tag}  \u00b7  {title}")
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    for label, value in meta:
        row = t.add_row()
        cant_split(row)
        c0, c1 = row.cells
        c0.width = Cm(2.9)
        c1.width = Cm(13.4)
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(label)
        r0.font.size = Pt(8.5)
        r0.font.bold = True
        r0.font.color.rgb = MUTED
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(value)
        r1.font.size = Pt(9)
    no_borders(t)
    set_widths(t, [2.9, 13.4])
    for row in t.rows:
        for cell in row.cells:
            cell_borders(cell, color="FFFFFF")
    for row in t.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(2)
    sp.paragraph_format.keep_with_next = True
    for q, cite in quotes:
        quote(doc, q, cite)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("What it proves. ")
    r.font.size = Pt(9.5)
    r.font.bold = True
    r2 = p.add_run(proves)
    r2.font.size = Pt(9.5)


def table(doc, headers, rows, widths, size=9, header_fill="E8ECF2", zebra=True,
          keep_together=False):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    hdr = t.rows[0]
    repeat_header(hdr)
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        c.width = Cm(widths[i])
        shade(c, header_fill)
        cell_borders(c)
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = ACCENT
    for n, row in enumerate(rows):
        cells = t.add_row().cells
        cant_split(t.rows[-1])
        for i, val in enumerate(row):
            c = cells[i]
            c.width = Cm(widths[i])
            cell_borders(c)
            if zebra and n % 2 == 1:
                shade(c, "FAFBFC")
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(str(val))
            r.font.size = Pt(size)
    set_widths(t, widths)
    if keep_together:
        for row in t.rows[:-1]:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True
    return t


def note_box(doc, title, text, fill=SHADE_WARN):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    cell.width = Cm(16.3)
    shade(cell, fill)
    cell_borders(cell, color="E3D9C6")
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(title + " ")
    r.font.size = Pt(9.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x7A, 0x4A, 0x12)
    r2 = p.add_run(text)
    r2.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ---------------------------------------------------------------- document
def build():
    doc = Document()

    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")

    s = doc.sections[0]
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(1.8)
    s.left_margin = Cm(2.3)
    s.right_margin = Cm(2.3)
    page_footer(s, "SSLG Club Classification \u00b7 Research Dossier \u00b7 23 November 2026")

    # ---- title block
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("SUPREME SECONDARY LEARNER GOVERNMENT")
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = MUTED

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("School Club Classification")
    r.font.size = Pt(26)
    r.font.bold = True
    r.font.color.rgb = ACCENT

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("Research dossier: what the national issuances actually say, "
                  "with the exact line for every claim")
    r.font.size = Pt(11.5)
    r.font.color.rgb = MUTED
    r.font.italic = True

    t = doc.add_table(rows=0, cols=2)
    t.autofit = False
    meta = [
        ("Prepared for", "Benigno S. Aquino National High School \u2014 SSLG"),
        ("Date", "23 November 2026"),
        ("Purpose", "Test whether the school's clubs can be grouped into four clusters, "
                    "the way Philippine Science High School does"),
        ("Method", "Web search plus direct download of the cited PDFs; text extracted "
                   "from the PDF text layer where one exists"),
        ("Companion note", "03 Governance/School Club Classification Framework (Proposal).md"),
    ]
    for label, value in meta:
        row = t.add_row()
        c0, c1 = row.cells
        c0.width = Cm(3.4)
        c1.width = Cm(12.9)
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(label.upper())
        r0.font.size = Pt(7.5)
        r0.font.bold = True
        r0.font.color.rgb = MUTED
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(value)
        r1.font.size = Pt(9)
    no_borders(t)
    set_widths(t, [3.4, 12.9])
    for row in t.rows:
        for cell in row.cells:
            cell_borders(cell, color="FFFFFF")

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(6)

    note_box(
        doc,
        "Read this first.",
        "The evidence supports a four-cluster scheme, but not as a national rule. "
        "No DepEd issuance prescribes categories for school clubs. The four-way split "
        "is a school-level policy, and one cluster (sports) collides with a separate "
        "national mandate that allows only one sports club per school.",
    )

    # ---- 1
    h1(doc, "1. Purpose and method")
    body(doc, "The question was whether the recognized clubs of BSANHS can be sorted "
              "into four categories the way Pisay sorts its clubs. That needed three "
              "checks: what the national layer requires, what Pisay actually does, and "
              "what the school currently has. Each is reported below as a numbered "
              "finding with its source and the exact line.")
    body(doc, "Quotations are reproduced as they appear in the source. Where a source PDF "
              "is a scan whose text layer was produced by OCR, obvious scanning errors were "
              "corrected silently; no wording was changed. Each finding carries a grade:")
    table(
        doc,
        ["Grade", "Meaning"],
        [
            ["VERBATIM", "Extracted directly from the PDF's own text layer."],
            ["OCR", "Scanned page; read from the OCR layer."],
            ["SECONDARY", "Quoted by another document, not read in the original."],
            ["INFERENCE", "Not stated; follows from what the documents say."],
        ],
        [2.6, 13.7],
        size=8.5,
    )

    # ---- 2
    h1(doc, "2. Findings at a glance")
    table(
        doc,
        ["#", "Finding", "Grade"],
        [
            ["F1", "Only the School Sports Club is called \u201cinstitutionalized\u201d; the term "
                   "covers one organization, not all clubs.", "VERBATIM"],
            ["F2", "A school may have only one School Sports Club, and Arnis is mandatory.", "VERBATIM"],
            ["F3", "DO 22 carries two different effectivity clauses that contradict each other.",
             "VERBATIM"],
            ["F4", "The learner government supervises and recognizes clubs; it does not "
                   "classify them into categories.", "SECONDARY"],
            ["F5", "The national club policy is still a draft being finalized, not an Order.", "OCR"],
            ["F6", "The five-option Category field is a division-localized form, not a "
                   "national template.", "OCR"],
            ["F7", "Pisay publishes exactly four club groupings.", "VERBATIM"],
            ["F8", "BSANHS has at least twenty recognized clubs and organizations; no "
                   "official registry was found in the vault.", "INFERENCE"],
        ],
        [1.2, 12.6, 2.5],
        size=9,
        keep_together=True,
    )

    # ---- 3
    h1(doc, "3. Evidence: the national layer")

    finding(
        doc, "F1", "Only the School Sports Club is \u201cinstitutionalized\u201d",
        [
            ("Source", "DepEd Order No. 022, s. 2025, Policy Guidelines on the "
                       "Institutionalization of the School Sports Club in Public Schools"),
            ("Date", "7 August 2025, signed by Secretary Sonny Angara"),
            ("Locator", "Transmittal page, paragraphs 1 to 3"),
            ("Grade", "VERBATIM \u2014 read from the PDF text layer"),
            ("File", "DO_s2025_022r.pdf, 24 pages"),
        ],
        [
            ("Recognizing the necessity of promoting learners' holistic development by improving "
             "their physical fitness and well-being, the Department of Education (DepEd) issues "
             "the enclosed Policy Guidelines on the Institutionalization of the School Sports "
             "Club (SSC) in Public Schools, which aims to allow for more active and accessible "
             "sports participation among all types of learners.",
             "Paragraph 1"),
            ("This Order guides school sports clubs' establishment, operations, management, "
             "merits and rewards, fund sources, and monitoring.",
             "Paragraph 2"),
            ("The schools with existing school sports clubs shall adopt the guidelines provided "
             "herein, and the schools without SSCs shall establish their school sports clubs "
             "accordingly.",
             "Paragraph 3"),
        ],
        "The word \u201cinstitutionalization\u201d appears in the title and is applied to a single "
        "body, the School Sports Club. No equivalent Order exists for any other club. "
        "Clubs in general are \u201crecognized\u201d or \u201caccredited\u201d; only the SSC is "
        "\u201cinstitutionalized.\u201d",
    )

    finding(
        doc, "F2", "One sports club per school, and Arnis is mandatory",
        [
            ("Source", "DepEd Order No. 022, s. 2025, enclosed policy guidelines"),
            ("Locator", "Printed page 12 of 22, section on club establishment"),
            ("Grade", "VERBATIM \u2014 read from the PDF text layer"),
        ],
        [
            ("Schools shall have only one School Sports Club, with Arnis as a mandatory sport, "
             "and may offer additional sports based on the following: (a) athletics and/or "
             "swimming as basic sports, (b) sports played in Palarong Pambansa, (c) Philippine "
             "Games, (d) learners' preferred sports as per survey results, and (e) sports under "
             "existing sports associations.",
             "Page 12 of 22"),
            ("Each learner shall be admitted to only one (1) sport in the SSC per academic year "
             "to promote continuous sports skills development.",
             "Page 12 of 22"),
        ],
        "A school cannot operate several competing sports clubs. Any four-cluster scheme has "
        "to place the registered SSC inside the sports cluster rather than invent a second "
        "sports body beside it.",
    )

    finding(
        doc, "F3", "DO 22 contradicts itself on when it took effect",
        [
            ("Source", "DepEd Order No. 022, s. 2025"),
            ("Locator", "Transmittal page paragraph 5 versus printed page 22, section IX"),
            ("Grade", "VERBATIM \u2014 read from the PDF text layer"),
        ],
        [
            ("This Order shall take effect upon its approval, issuance, and 15 days after its "
             "publication in the Official Gazette or a newspaper of general circulation.",
             "Transmittal page, paragraph 5"),
            ("This Order shall take effect immediately upon its approval, issuance, and "
             "publication on the DepEd website.",
             "Page 22 of 22, Effectivity and Transitory Provisions"),
        ],
        "Two effectivity clauses with different triggers sit in the same Order. This does not "
        "affect the school's obligation to comply, but it is worth knowing before anyone "
        "cites a start date for the SSC in a memorandum.",
    )

    finding(
        doc, "F4", "The learner government supervises clubs; it does not categorize them",
        [
            ("Source", "DepEd Order No. 47, s. 2014, Constitution and By-Laws of the Supreme "
                       "Pupil Government and Supreme Student Government"),
            ("Locator", "Article XII, Section 1, as quoted in SDO Valenzuela DM No. 047, s. 2026"),
            ("Grade", "SECONDARY \u2014 the line is quoted by the division memorandum; the "
                      "2014 Order itself was not downloaded"),
        ],
        [
            ("the Coordinating Council shall be composed of the different Presidents of all "
             "recognized legitimate campus co-curricular organizations",
             "Quoted in SDO Valenzuela DM No. 047, s. 2026, paragraph 1"),
        ],
        "The national instrument that governs clubs establishes recognition and supervision, "
        "and creates a council of club presidents. It is silent on categories. Whatever "
        "grouping the school adopts therefore rests on the school's own authority, exercised "
        "through the SSLG.",
    )

    finding(
        doc, "F5", "The national club policy is still a draft",
        [
            ("Source", "Four issuances across three years, listed below"),
            ("Grade", "OCR \u2014 the regional memoranda are scans; wording read from the "
                      "OCR layer"),
            ("Caveat", "This shows the policy was still being finalized in October 2026. It "
                       "does not prove no final Order has been signed since."),
        ],
        [
            ("The Operations Strand, through the Bureau of Learner Support Services \u2014 Youth "
             "Formation Division (BLSS-YFD), will conduct a Validation of the Policy Guidelines "
             "on the Operationalization of School Clubs and Organizations in Basic Education on "
             "October 14-18, 2024, in La Union (exact venue will be announced through an advisory).",
             "Region VIII RM No. 242, s. 2024, quoting DM-OUOPS-2024-11-07925"),
            ("The Office of the Undersecretary for Operations (OUOPS) through the Bureau of "
             "Learner Support Services-Youth Formation Division (BLSS-YFD) is set to conduct a "
             "second phase of Validation of the Policy Guidelines on the Establishment and "
             "Operationalization of School Clubs and Organizations in the Basic Education from "
             "May 6-9, 2025, at DepEd Ecotech Center, Lahug, Cebu City.",
             "NCR RM No. 403, s. 2025, quoting DM-OUOPS-2025-11-02604"),
            ("To review and refine the draft guidelines particularly the provisions on "
             "accreditation and other implementation requirements; and identify areas for "
             "strengthening to ensure that the guidelines are practical, responsive, and "
             "applicable to the current school contexts, including the three-term school calendar",
             "DM-OUGOPS-2026-15-094040, objective (a), as reproduced in Region VIII RM No. 1308, s. 2026"),
            ("To consolidate the inputs and recommendations for further refinement and "
             "finalization of the guidelines.",
             "DM-OUGOPS-2026-15-094040, objective (c)"),
        ],
        "The document has been validated twice, piloted from January 2026, and was still "
        "described as a draft needing \u201cfinalization\u201d at a feedback session on 13 to 15 "
        "October 2026 in Baguio. It cannot yet be cited as authority for a cluster scheme.",
    )

    finding(
        doc, "F6", "The five-option Category field is division-level, not national",
        [
            ("Source", "SDO Valenzuela City, Division Memorandum No. 047, s. 2026, School Club "
                       "and Organization \u2014 Localized Guidelines on Accreditation"),
            ("Date", "5 January 2026"),
            ("Locator", "Enclosure 1, Application Form, I. Profile / General Information; "
                        "repeated in the attached Constitution and By-Laws template"),
            ("Grade", "OCR \u2014 read from the OCR layer of the PDF"),
            ("Caveat", "The file could not be re-downloaded for a clean read: the host returns "
                       "HTTP 429 (too many requests) to automated requests. Open it in a browser."),
        ],
        [
            ("Category \u2014 Academic or Subject-Related / Advocacy and Awareness / Leadership & "
             "Governance / Faith and Belief / Interest and Talent",
             "Enclosure 1, Application Form, item I"),
            ("This organization shall be: Academic or Subject Area-Related / Faith and Belief / "
             "Advocacy and Awareness / Interest and Talent / Leadership and Governance",
             "Constitution and By-Laws template, Article I"),
        ],
        "A five-option category set exists and is in active use, but the document that carries "
        "it is a division-localized template adopted under DO 47, s. 2014. No national issuance "
        "printing these five options was found. The correct description is \u201ccurrent division "
        "practice,\u201d not \u201cnational standard.\u201d",
    )

    # ---- 4
    h1(doc, "4. Evidence: Pisay")

    finding(
        doc, "F7", "Pisay publishes exactly four club groupings",
        [
            ("Source", "Philippine Science High School Main Campus, clubs site"),
            ("Locator", "Site navigation and index heading \u201cClubs 2018-2019\u201d"),
            ("Grade", "VERBATIM \u2014 read from the page"),
            ("Caveat", "The index is labelled 2018-2019. It shows the school's grouping "
                       "practice, not a current official list."),
        ],
        [
            ("Arts Clubs  \u00b7  Socio-Spiritual Clubs  \u00b7  Sports Clubs  \u00b7  STEM Clubs",
             "Site navigation, four top-level club sections"),
        ],
        "The four-way split is real and is the model the proposal borrows. It is a school "
        "convention, published on a club site, not a DepEd rule \u2014 which is exactly why "
        "BSANHS can adopt the shape without needing permission.",
    )

    # ---- 5
    h1(doc, "5. Evidence: the school's own clubs")

    finding(
        doc, "F8", "At least twenty recognized clubs and organizations",
        [
            ("Source", "Vault records: AP_SSLG_2026_001 (Onto the Next: Leaders 2026-2027 "
                       "Induction Ceremony) and AP_SSLG_2026_006 (World Teachers' Day 2026)"),
            ("Locator", "Program Management Team tables, which name each club and its officers"),
            ("Grade", "INFERENCE \u2014 the count is a consolidation across documents, not a "
                      "line in any one document"),
            ("Caveat", "No Registry of Accredited School Clubs and Organizations for BSANHS "
                       "was found in the vault."),
        ],
        [
            ("STEM Club Officers / MAPEH Club Officers / B&E Club Officers / BKB Club Officers / "
             "TVE Club Officers / A.R.S. Club Officers / ASSH Club Officers",
             "AP_SSLG_2026_001, Program Management Team"),
            ("BERT Club Officers / ValEd Club Officers / AP Club Officers / RCYC Officers / "
             "BSP Outfit 169 / Senior Scouts Outfit 282 / Aquinian's Pride Performing Artist "
             "(APPA) Club Officers",
             "AP_SSLG_2026_006, Program Management Team"),
        ],
        "The school has a working set of clubs spanning subject departments, tracks, "
        "performance groups, uniformed organizations and advocacy bodies. The list is stable "
        "enough to classify, but it should be checked against the school's own accreditation "
        "registry before any memorandum names it.",
    )

    # ---- 6
    h1(doc, "6. What the evidence supports")
    for txt in [
        "A four-cluster scheme is permissible, because nothing national forbids it and the "
        "SSLG already holds supervision over clubs under DO 47, s. 2014.",
        "It cannot be presented as a DepEd requirement. It is a school policy, and should be "
        "written as one.",
        "It must not replace the category declared on the accreditation form. The form keeps "
        "its field; the cluster is an additional operational layer.",
        "The sports cluster is constrained: one registered SSC, Arnis mandatory, registered "
        "through the SSC forms with the Schools Division Office.",
    ]:
        bullet(doc, txt)

    # ---- 7
    h1(doc, "7. Recommendation")
    body(doc, "The following is a proposal, not a finding. It follows the Pisay shape and "
              "keeps the four clusters close to equal in size.")

    table(
        doc,
        ["Cluster", "Name", "Covers", "Clubs"],
        [
            ["A", "AGHAM \u2014 Academic & STEM",
             "Subject, track and competition clubs", "8"],
            ["B", "SINING \u2014 Arts, Culture & Media",
             "Performance, visual arts, music, dance, media", "4"],
            ["C", "LAKAS \u2014 Sports, Health & Wellness",
             "Sports, PE, health and wellness", "2 or 3"],
            ["D", "BAYANIHAN \u2014 Socio-Civic, Service & Spiritual",
             "Environment, anti-vice, resilience, red cross, scouting", "6"],
        ],
        [1.7, 5.0, 6.6, 1.9],
        size=9,
    )
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    rows = [
        ["1", "Mathematics Club", "A", ""],
        ["2", "Science, Technology, Engineering and Mathematics (STEM) Club", "A", ""],
        ["3", "English Club", "A", ""],
        ["4", "Araling Panlipunan (AP) Club", "A", ""],
        ["5", "Values Education (ValEd) Club", "A", "Faith content may co-plan with D"],
        ["6", "Business and Entrepreneurship (B&E) Club", "A", ""],
        ["7", "Technical-Vocational Education (TVE) / Technical Professional Club", "A",
         "To confirm: one club or two"],
        ["8", "Arts, Social Sciences and Humanities (ASSH) Club", "A",
         "Humanities content may co-plan with B"],
        ["9", "Aquinian's Pride Performing Artist (APPA)", "B", ""],
        ["10", "La Tigris Dance Troupe", "B", ""],
        ["11", "Harmonic Blend Chorale (HBC)", "B", ""],
        ["12", "Aquinian Radiance Syndicate (ARS)", "B",
         "To confirm: media or visual arts"],
        ["13", "Sports, Health and Wellness Club", "C", ""],
        ["14", "MAPEH Club", "C", "PE/Health home; Music and Arts co-plan with B"],
        ["15", "Youth for Environment in Schools Organization (YES-O)", "D", "Mandated"],
        ["16", "Barkada Kontra Bisyo (BKB)", "D", "Mandated advocacy"],
        ["17", "Batang Empowered and Resilient Team (BERT)", "D", "Disaster resilience"],
        ["18", "Red Cross Youth (RCYC)", "D", ""],
        ["19", "Boy Scouts of the Philippines \u2014 Outfit 169", "D", ""],
        ["20", "Senior Scouts \u2014 Outfit 282", "D", ""],
    ]
    roster = table(doc, ["#", "Club or organization", "Cluster", "Note"], rows,
                   [1.0, 8.3, 1.7, 5.0], size=8)
    for row in roster.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(0.5)
                p.paragraph_format.space_after = Pt(0.5)
    body(doc, "Not clustered: the SSLG, which chairs the Learner Government Coordinating "
              "Council and sits above the clusters. Rule for the whole scheme: one club, one "
              "home, assigned at accreditation by primary purpose.", size=9, italic=True)

    h2(doc, "Where the cluster would be used")
    for txt in [
        "GPOA and CAPA \u2014 PPAs filed and consolidated by cluster before the LGCC merge.",
        "Club Fair \u2014 four booth zones.",
        "Election of club officers \u2014 schedule released by cluster.",
        "Induction ceremony \u2014 program order and seating.",
        "Project EcoLead \u2014 area rotation and monthly award computed per cluster.",
        "Project TINIG \u2014 public directory grouped by cluster.",
        "Budget and tokens \u2014 one line per cluster.",
        "Monitoring \u2014 one summary page per cluster in each completion report.",
    ]:
        bullet(doc, txt, size=10)

    # ---- 8
    h1(doc, "8. What could not be verified")
    table(
        doc,
        ["Item", "Why"],
        [
            ["No final numbered Order for the club policy",
             "Absence from everything searched. A final Order may exist; check the DepEd "
             "issuances page before citing."],
            ["A national form printing the five categories",
             "Only the SDO Valenzuela localized template was found."],
            ["The text of DO 47, s. 2014 itself",
             "Quoted second-hand from the Valenzuela memorandum; the 2014 PDF was not "
             "downloaded."],
            ["BSANHS Registry of Accredited Clubs",
             "Not present in the vault. The twenty-club list is reconstructed."],
            ["Nature of the ARS and whether TVE and Technical Professional are one club",
             "Not stated in any vault record."],
            ["Whether the school has a registered SSC",
             "No SSC.1 or SSC.2 registration was found in the vault."],
            ["Division guidance on club categories for SDO Tarlac Province",
             "Not searched. Worth checking before issuing a local policy."],
        ],
        [6.2, 10.1],
        size=9,
    )

    # ---- 9
    h1(doc, "9. Source register")
    body(doc, "All links accessed 23 November 2026. Retrieval status records what happened "
              "when the file was fetched for this dossier.", size=9, italic=True)

    table(
        doc,
        ["Document", "Link", "Retrieved"],
        [
            ["DO 22, s. 2025",
             "deped.gov.ph/wp-content/uploads/DO_s2025_022r.pdf", "Downloaded; text layer read"],
            ["DO 22 landing page",
             "deped.gov.ph/2025/08/07/august-7-2025-do-022-s-2025-policy-guidelines-on-the-"
             "institutionalization-of-the-school-sports-club-in-public-schools", "Read"],
            ["Region VIII RM 1079, s. 2025",
             "region8.deped.gov.ph/wp-content/uploads/2025/09/RM-No.-1079s.-2025-ESSD-SPPS-"
             "MJDR-922025.pdf", "Downloaded; scan, no text layer"],
            ["Region VIII RM 1308, s. 2026",
             "region8.deped.gov.ph/wp-content/uploads/2026/10/RM-No.-1308-s.-2026-ESSD-SPPS-"
             "EAD-100826.pdf", "Downloaded; scan, no text layer"],
            ["Region VIII RM 242, s. 2024",
             "depedro8.azurewebsites.net/wp-content/uploads/2024/10/RM-s2024-1242.pdf",
             "Downloaded; scan, no text layer"],
            ["NCR RM 403, s. 2025",
             "depedncr.com.ph/wp-content/uploads/2025/05/RM-No.-403-s.-2025-Request-for-"
             "Representatives-for-the-Validation-of-the-Policy-Guidelines-on-the-Establishment-"
             "and-Operationalization-of-School-Clubs-and-Organizations-in-the-Basic-Education.pdf",
             "Indexed text read; not downloaded"],
            ["SDO Valenzuela DM 047, s. 2026",
             "depedvalenzuela.com/Documents/Download?id=145&type=issuance",
             "HTTP 429 on download; text read from search index"],
            ["Pisay Main Campus clubs",
             "sites.google.com/pshs.edu.ph/clubs", "Read"],
        ],
        [4.4, 8.9, 3.0],
        size=8,
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run("Prepared 23 November 2026. Every finding above is traceable to the "
                  "document named in its Source line. Findings F1 to F7 are evidence; "
                  "section 7 is recommendation.")
    r.font.size = Pt(8.5)
    r.font.italic = True
    r.font.color.rgb = MUTED

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print("WROTE", OUT)


if __name__ == "__main__":
    build()
