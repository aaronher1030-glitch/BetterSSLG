"""Build the Science Fair excuse letter (all subject teachers) from the July 2026 master.

Clones the accepted EL_SSLG_2026_010.docx so the letterhead (header/footer parts)
stays byte-identical, then rebuilds the body to match the received November 20, 2026
scan. The principal's name is corrected to AMPARO M. MUÑOZ (the scan misspells it).
"""
import re
import shutil
import zipfile
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "02 Activities/Municipal Short Film Festival 2026/Sources/EL_SSLG_2026_010.docx"
OUT = ROOT / "Excuse Letter - Science Fair (All Subject Teachers).docx"
SEAL = ROOT / "80 Assets/School Seal (from scan).png"

BODY = [
    [
        ("We respectfully inform you that the students participating in the Science "
         "Fair activities on ", False),
        ("November 20, 2026 (Friday), at the school campus", True),
        (" will be excused from attending their regular classes during the conduct "
         "of the said activities.", False),
    ],
    [
        ("Their participation is necessary to ensure the successful implementation "
         "of the Science Fair and to encourage their interest, creativity, teamwork, "
         "and appreciation of science and technology.", False),
    ],
    [
        ("In this regard, we kindly request your consideration and understanding in "
         "allowing the participating students to be excused from all their subjects "
         "during the said activity. We also encourage you to provide them with "
         "opportunities to complete any missed lessons, activities, assignments, or "
         "assessments.", False),
    ],
    [
        ("Thank you very much for your cooperation, understanding, and continued "
         "support in making this school activity a success.", False),
    ],
]


def clear_runs(paragraph):
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)


def style_run(run, bold=False):
    run.font.name = "Bookman Old Style"
    run.font.size = Pt(12)
    run.font.bold = bold
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is not None:
        fonts.set(qn("w:cs"), "Arial")


def new_para(d, parts, align=None, space_before=Pt(0), space_after=Pt(0)):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = space_before
    pf.space_after = space_after
    pf.line_spacing = 1.0
    if align is not None:
        p.alignment = align
    for text, bold in parts:
        style_run(p.add_run(text), bold)
    return p


HDR_NS = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" '
    'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
    'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
    'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
    'mc:Ignorable="w14 w15 wp14"'
)

DRAWING = """<w:r><w:rPr><w:noProof/></w:rPr><w:drawing>
<wp:anchor distT="0" distB="0" distL="114300" distR="114300" simplePos="0" relativeHeight="{rh}" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">
<wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="margin"><wp:align>{align}</wp:align></wp:positionH>
<wp:positionV relativeFrom="paragraph"><wp:posOffset>-152400</wp:posOffset></wp:positionV>
<wp:extent cx="{ext}" cy="{ext}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/>
<wp:docPr id="{pid}" name="Picture {pid}" descr="{descr}"/>
<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>
<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:nvPicPr><pic:cNvPr id="{pid}" name="Picture {pid}" descr="{descr}"/><pic:cNvPicPr><a:picLocks noChangeAspect="1" noChangeArrowheads="1"/></pic:cNvPicPr></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rid}"/><a:srcRect/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{ext}" cy="{ext}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln w="9525"><a:noFill/><a:miter lim="800000"/><a:headEnd/><a:tailEnd/></a:ln></pic:spPr>
</pic:pic></a:graphicData></a:graphic></wp:anchor></w:drawing></w:r>"""

HDR_PARA = """<w:p><w:pPr><w:pStyle w:val="Header"/><w:spacing w:line="240" w:lineRule="auto"/><w:jc w:val="center"/><w:rPr>{rpr}</w:rPr></w:pPr>{runs}</w:p>"""

HDR_RUN = """<w:r><w:rPr>{rpr}</w:rPr>{text}</w:r>"""


def _hdr_rpr(font, sz, color=None):
    color_xml = f'<w:color w:val="{color}"/>' if color else ""
    return (
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="Tahoma"/><w:b/><w:bCs/>'
        f'{color_xml}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    )


def plain_letterhead_header():
    """The plain school letterhead as on the received scan: two seals flanking
    centered lines, no REGION III/LGCC/School Year lines, no rules, no footer."""
    ext = 685800  # 0.75 in seals, as on the scan
    drawings = (
        DRAWING.format(rh="251658752", align="left", ext=ext, pid="46",
                       descr="DepEd official seal", rid="rId1")
        + DRAWING.format(rh="251659000", align="right", ext=ext, pid="47",
                         descr="Benigno S. Aquino National High School seal", rid="rId2")
    )
    paras = [
        HDR_PARA.format(rpr="", runs=drawings),
        HDR_PARA.format(
            rpr='<w:rFonts w:ascii="Old English Text MT" w:hAnsi="Old English Text MT"/>'
                '<w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/>',
            runs=""),
        HDR_PARA.format(
            rpr=_hdr_rpr("Old English Text MT", 24),
            runs=HDR_RUN.format(rpr=_hdr_rpr("Old English Text MT", 24),
                                text="<w:t>Republic of the Philippines</w:t>")),
        HDR_PARA.format(
            rpr=_hdr_rpr("Old English Text MT", 36),
            runs=HDR_RUN.format(rpr=_hdr_rpr("Old English Text MT", 36),
                                text="<w:t>Department of Education</w:t>")),
        HDR_PARA.format(
            rpr=_hdr_rpr("Tahoma", 20),
            runs=HDR_RUN.format(rpr=_hdr_rpr("Tahoma", 20),
                                text="<w:t>Schools Division of Tarlac Province</w:t>")),
        HDR_PARA.format(
            rpr=_hdr_rpr("Poor Richard", 28, "2E74B5"),
            runs=HDR_RUN.format(rpr=_hdr_rpr("Poor Richard", 28, "2E74B5"),
                                text="<w:t>BENIGNO S. AQUINO NATIONAL HIGH SCHOOL</w:t>")),
        HDR_PARA.format(
            rpr=_hdr_rpr("Tahoma", 22),
            runs=HDR_RUN.format(rpr=_hdr_rpr("Tahoma", 22),
                                text="<w:t>Concepcion, Tarlac</w:t>")),
    ]
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {HDR_NS}>{"".join(paras)}</w:hdr>'


def restyle_letterhead(docx_path):
    """Swap the LGCC letterhead for the plain scan letterhead and drop the footer."""
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument'
        '/2006/relationships/image" Target="media/image1.png"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument'
        '/2006/relationships/image" Target="media/schoolseal.png"/>'
        "</Relationships>"
    )
    seal_bytes = SEAL.read_bytes()
    tmp = docx_path.with_suffix(".tmp2.docx")
    with zipfile.ZipFile(docx_path) as zin, zipfile.ZipFile(
        tmp, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/header2.xml":
                data = plain_letterhead_header().encode("utf8")
            elif item.filename == "word/_rels/header2.xml.rels":
                data = rels.encode("utf8")
            elif item.filename == "word/document.xml":
                data = re.sub(rb"<w:footerReference[^>]*/>", b"", data)
            zout.writestr(item, data)
        zout.writestr("word/media/schoolseal.png", seal_bytes)
    tmp.replace(docx_path)


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


def main():
    shutil.copy2(SRC, OUT)
    d = docx.Document(OUT)
    paras = d.paragraphs

    # Keep only the date and TO paragraphs as formatting donors; everything else
    # (greeting, body, signature chain with borrowed signature art) is rebuilt.
    for p in paras[2:]:
        p._p.getparent().remove(p._p)
    for p in d.paragraphs:
        for drawing in p._p.findall(qn("w:r") + "/" + qn("w:drawing")):
            drawing.getparent().remove(drawing)

    date_para = d.paragraphs[0]
    clear_runs(date_para)
    # The master's date paragraph carries a 4.5 in left indent for its right
    # alignment; the scan's date sits at the left margin.
    ind = date_para._p.pPr.find(qn("w:ind"))
    if ind is not None:
        date_para._p.pPr.remove(ind)
    date_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style_run(date_para.add_run("Date: November 20, 2026"), True)

    to_para = d.paragraphs[1]
    clear_runs(to_para)
    style_run(
        to_para.add_run(
            "To: All Subject Teachers\n"
            "Subject: Excuse from Classes Due to Participation in Science Fair Activities"
        ),
        True,
    )

    new_para(d, [("Dear Teachers,", True)], space_before=Pt(6), space_after=Pt(6))
    new_para(d, [("Greetings!", False)], space_after=Pt(6))
    for parts in BODY:
        new_para(d, parts, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=Pt(6))
    new_para(d, [("Respectfully yours,", False)], space_before=Pt(6))

    # Blank lines left for the actual signatures.
    for _ in range(3):
        new_para(d, [("", False)])
    new_para(d, [("AMADO T. ALIMURUNG, PhD", True)])
    new_para(d, [("Head Teacher VI; SCIENCE", False)], space_after=Pt(10))

    new_para(d, [("Noted by:", True)], space_after=Pt(0))
    for _ in range(3):
        new_para(d, [("", False)])
    new_para(d, [("DR. AMPARO M. MUÑOZ", True)])
    new_para(d, [("Principal IV", False)])

    d.save(OUT)
    restore_letterhead_parts(OUT, SRC)
    restyle_letterhead(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
