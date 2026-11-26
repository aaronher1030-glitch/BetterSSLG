import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r'C:\Users\Ma Christine\Downloads\4th PNSO Forms'
SIGS = os.path.join(OUT, 'signatures')
COACH_IMG = r'80 Assets\Signature - Oliver R. Francisco.png'
HEAD_IMG = r'80 Assets\Signature - Amparo M. Munoz.png'
SCHOOL = 'Benigno S. Aquino National High School'
COACH = 'Oliver R. Francisco'
HEAD = 'Amparo M. Muñoz, EdD'
STUDENTS = [
    ('Ian M. Poy Lorenzo', os.path.join(SIGS, 'Student - Ian M. Poy Lorenzo.png'), 0.55, '0909 150 9082',
     os.path.join(SIGS, 'Parent - Rodel L. Poy Lorenzo.png'), 0.50, 'Rodel L. Poy Lorenzo'),
    ('Rhian Amber L. Ocampo', os.path.join(SIGS, 'Student - Rhian Amber L. Ocampo.png'), 0.95, '0969 018 6276',
     os.path.join(SIGS, 'Parent - Ramil R. Ocampo.png'), 0.50, 'Ramil R. Ocampo'),
    ('Juan Dominique T. Zamora', os.path.join(SIGS, 'Student - Juan Dominique T. Zamora.png'), 0.60, '0910 217 9930',
     os.path.join(SIGS, 'Parent - Myrna T. Zamora.png'), 0.50, 'Myrna T. Zamora'),
]


def no_borders(t):
    pr = t._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement(f'w:{edge}')
        e.set(qn('w:val'), 'nil')
        b.append(e)
    pr.append(b)


def zero_margins(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    m = OxmlElement('w:tcMar')
    for side in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement(f'w:{side}')
        e.set(qn('w:w'), '0')
        e.set(qn('w:type'), 'dxa')
        m.append(e)
    tcPr.append(m)


def fixed(t, ws):
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    pr = t._tbl.tblPr
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    pr.append(layout)
    tw = OxmlElement('w:tblW')
    tw.set(qn('w:w'), str(int(round(sum(ws) * 1440))))
    tw.set(qn('w:type'), 'dxa')
    pr.append(tw)
    for i, w in enumerate(ws):
        t.columns[i].width = Inches(w)
        for r in t.rows:
            r.cells[i].width = Inches(w)
    for r in t.rows:
        for c in r.cells:
            zero_margins(c)


def ctext(cell, text='', size=11, bold=False, underline=False,
          align=WD_ALIGN_PARAGRAPH.LEFT, color=None):
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    if text:
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        r.underline = underline
        if color:
            r.font.color.rgb = color
    return p


def spacer(doc, pts):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = Pt(pts)
    p.add_run().font.size = Pt(1)


def bg_picture(paragraph, path, height):
    """Place the signature as a behind-text background anchored to this line."""
    run = paragraph.add_run()
    inline = run.add_picture(path, height=Inches(height))._inline

    anchor = OxmlElement('wp:anchor')
    for k, v in (('distT', '0'), ('distB', '0'), ('distL', '0'), ('distR', '0'),
                 ('simplePos', '0'), ('relativeHeight', '0'), ('behindDoc', '1'),
                 ('locked', '0'), ('layoutInCell', '1'), ('allowOverlap', '1')):
        anchor.set(k, v)

    sp = OxmlElement('wp:simplePos')
    sp.set('x', '0')
    sp.set('y', '0')
    anchor.append(sp)

    ph = OxmlElement('wp:positionH')
    ph.set('relativeFrom', 'column')
    al = OxmlElement('wp:align')
    al.text = 'center'
    ph.append(al)
    anchor.append(ph)

    pv = OxmlElement('wp:positionV')
    pv.set('relativeFrom', 'paragraph')
    off = OxmlElement('wp:posOffset')
    # sit the signature just above the underscore baseline
    off.text = str(-int((height - 0.12) * 914400))
    pv.append(off)
    anchor.append(pv)

    for tag in ('wp:extent', 'wp:effectExtent'):
        el = inline.find(qn(tag))
        if el is not None:
            anchor.append(el)
    anchor.append(OxmlElement('wp:wrapNone'))
    for tag in ('wp:docPr', 'wp:cNvGraphicFramePr'):
        el = inline.find(qn(tag))
        if el is not None:
            anchor.append(el)
    anchor.append(inline.find(qn('a:graphic')))

    inline.getparent().replace(inline, anchor)


def statement(doc, parts, ws, inline=False):
    """One flowing line of the acknowledgement text, with field labels beneath names."""
    t = doc.add_table(rows=2, cols=len(parts))
    no_borders(t)
    fixed(t, ws)
    for i, (text, underline, label) in enumerate(parts):
        al = WD_ALIGN_PARAGRAPH.LEFT if (inline or not underline) else WD_ALIGN_PARAGRAPH.CENTER
        ctext(t.rows[0].cells[i], text, underline=underline, align=al)
        if label:
            ctext(t.rows[1].cells[i], label, size=8, bold=True, align=al)
    spacer(doc, 4)


def build(name, sig, sig_h, contact, parent_img, parent_h, parent_name):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for m in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'):
        setattr(sec, m, Inches(1))

    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.15

    ttl = doc.add_paragraph()
    ttl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ttl.paragraph_format.space_after = Pt(24)
    r = ttl.add_run('SCHOOL ACKNOWLEDGEMENT')
    r.bold = True
    r.font.size = Pt(18)

    statement(doc, [
        ('This is to acknowledge that', False, None),
        (name, True, '(Student\u2019s Name)'),
        ('is applying for the 4th PNSO', False, None),
    ], [1.95, 2.0, 2.1])

    statement(doc, [
        ('representing', False, None),
        (SCHOOL, True, '(School Name)'),
    ], [1.0, 5.5], inline=True)

    statement(doc, [
        ('with the full knowledge and support of coach', False, None),
        (COACH, True, '(Coach\u2019s Name)'),
    ], [3.2, 3.3], inline=True)

    t = doc.add_table(rows=2, cols=2)
    no_borders(t)
    fixed(t, [1.15, 5.35])
    ctext(t.rows[0].cells[0], 'and school head')
    p = ctext(t.rows[0].cells[1], HEAD, underline=True)
    rp = p.add_run('.')
    rp.font.size = Pt(11)
    ctext(t.rows[1].cells[1], '(School Principal/ Head\u2019s Name)', size=8, bold=True)
    spacer(doc, 34)

    # signature block
    t = doc.add_table(rows=1, cols=3)
    no_borders(t)
    fixed(t, [2.17, 2.17, 2.16])
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    row = t.rows[0]
    row.height = Inches(1.05)
    row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    labels = [
        ('Signature of Student', sig, sig_h),
        ('Signature of Coach', COACH_IMG, 0.85),
        ('Signature of School Principal/Head', HEAD_IMG, 0.62),
    ]
    for cell, (label, img, h) in zip(row.cells, labels):
        cell.vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
        p2 = cell.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after = Pt(2)
        p2.paragraph_format.line_spacing = 1.0
        r = p2.add_run('______________________')
        r.font.size = Pt(11)
        if img:
            bg_picture(p2, img, h)
        p3 = cell.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p3.paragraph_format.space_after = Pt(0)
        p3.paragraph_format.line_spacing = 1.0
        r = p3.add_run(label)
        r.font.size = Pt(8)
        r.bold = True
    spacer(doc, 34)

    # consent
    cttl = doc.add_paragraph()
    cttl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cttl.paragraph_format.space_after = Pt(12)
    cttl.paragraph_format.line_spacing = 1.0
    r = cttl.add_run('PARENTAL CONSENT/ WAIVER FOR STUDENT REPRESENTATIVE')
    r.bold = True
    r.font.size = Pt(14)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = 1.15
    p.add_run('This is to certify that I am giving my full consent for my son/daughter, ').font.size = Pt(11)
    r = p.add_run(name)
    r.underline = True
    r.font.size = Pt(11)
    p.add_run(', to travel to the designated testing area for the 4th PNSO. I further acknowledge that the Philippine Nuclear Research Institute nor the Department of Science and Technology will not be liable for any untoward incident that may occur in connection with my son/daughter\u2019s participation in the selection of the said event.').font.size = Pt(11)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(42)
    p.paragraph_format.line_spacing = 1.15
    p.add_run('I hereby certify that, to the best of my knowledge, my son/daughter is medically fit and physically capable of traveling to and participating in the activities related to the 4th PNSO, and has no known medical condition that would prevent such participation.').font.size = Pt(11)

    # parent block
    t = doc.add_table(rows=2, cols=2)
    no_borders(t)
    fixed(t, [3.5, 3.0])
    c0, c1 = t.rows[0].cells

    p = c0.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.add_run('______________________________').font.size = Pt(11)
    bg_picture(p, parent_img, parent_h)
    p = c0.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(parent_name)
    r.bold = True
    r.font.size = Pt(11)
    p = c0.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    p.add_run('(Signature over printed name)').font.size = Pt(11)

    p = c1.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run('November 13, 2026')
    r.underline = True
    r.font.size = Pt(11)
    p = c1.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run('Date signed')
    r.bold = True
    r.font.size = Pt(11)

    m = t.rows[1].cells[0].merge(t.rows[1].cells[1])
    p = m.paragraphs[0]
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run('Required:')
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    p.add_run(' Contact number/details of parent/guardian in case of an emergency').font.size = Pt(11)
    p = m.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(contact)
    r.underline = True
    r.font.size = Pt(11)

    fn = f'4th PNSO School Acknowledgement - {name}.docx'
    doc.save(os.path.join(OUT, fn))
    print('saved', fn)


for name, sig, sig_h, contact, parent_img, parent_h, parent_name in STUDENTS:
    build(name, sig, sig_h, contact, parent_img, parent_h, parent_name)
