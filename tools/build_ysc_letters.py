"""Build the three YSC Research Fair 2027 letters for the Olympiad Club.

Clones Request Letter - Multi-Purpose Hall.docx for the school letterhead and
paragraph geometry, rewrites the body and signature blocks, then removes the
SSLG-specific LGCC line from the header. The header is intentionally no longer
byte-identical to the SSLG master: these are external Olympiad Club letters.
"""
import re
import time
import zipfile
from copy import deepcopy
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from build_calm_letter import add_runs, clear_runs, restore_letterhead_parts

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Request Letter - Multi-Purpose Hall.docx"

DATE = "November 13, 2026"
LGCC_LINE = "Learner Government Coordinating Council (LGCC)"

ELDRIN = ("ELDRIN L. PATIO", "Research Adviser")
ANDY = ("SIR ANDY", "Head Teacher, Science Department")
AMPY = ("AMPARO M. MUÑOZ, EDD", "Principal IV")
JEDIDIAH = ("JEDIDIAH ETHAN H. MACALE", "Olympiad Club President")

MEMBERS = (
    "Aaron Y. Hernandez (11-Onyx), Ellaine T. Jacob (11-Ilmenite), "
    "and Jolex Alexier S. Cruz (11-Jacinth)"
)

GREETING = "\tGreetings in the spirit of shared service and institutional excellence!"
CLOSING = (
    "\tWe look forward to your favorable response to this request. "
    "May the Almighty continue to bless us."
)
SCHOOL_CLOSING = (
    "\tWe look forward to your continued support. "
    "May the Almighty continue to bless us."
)

SCHOOL_BODY = [
    [
        ("\tIn connection with the ", False),
        ("Youth Science Convention (YSC) Case Study Competition", True),
        (" of ", False),
        ("Research Fair 2027", True),
        (", organized by UP ALCHEMES at the ", False),
        ("University of the Philippines Diliman", True),
        (", we are pleased to announce that ", False),
        ("Benigno S. Aquino National High School", True),
        (", through the ", False),
        ("Olympiad Club", True),
        (", will be represented by the following learners: ", False),
        (MEMBERS, True),
        (". The Phase I submission of the concept project paper is due on ", False),
        ("5 December 2026", True),
        (".", False),
    ],
    [
        ("\tThe competition requires each team to propose a twelve-month pilot project "
         "for a one-kilometer stretch of a local waterway and a blueprint for its "
         "expansion to the country\u2019s major river systems. The team will prepare "
         "the case study and its digital poster for the said competition.", False),
    ],
    [
        ("\tWe enjoin the faculty and the student body to support the team in this "
         "undertaking, and we shall keep the school informed of its progress.", False),
    ],
]

ANDY_BODY = [
    [
        ("\tIn connection with the ", False),
        ("Youth Science Convention (YSC) Case Study Competition", True),
        (" of ", False),
        ("Research Fair 2027", True),
        (" at the ", False),
        ("University of the Philippines Diliman", True),
        (" on ", False),
        ("5 December 2026", True),
        (", we respectfully request your financial assistance under the ", False),
        ("Financial Education Support", True),
        (" for the participation of the school\u2019s ", False),
        ("Olympiad Club", True),
        (" team.", False),
        (" The team is composed of ", False),
        (MEMBERS, True),
        (".", False),
    ],
    [
        ("\tThe assistance will be used for the team\u2019s registration, the printing "
         "and reproduction of the case study and the digital poster, and the "
         "transportation of the team to the competition venue. Any amount that you may "
         "extend will greatly help the team meet the requirements of the competition "
         "and represent the school in the said undertaking.", False),
    ],
    [
        ("\tWe assure you that all funds received will be properly accounted for and "
         "liquidated in accordance with existing accounting and auditing rules and "
         "regulations.", False),
    ],
]

AMPY_BODY = [
    [
        ("\tIn connection with the ", False),
        ("Youth Science Convention (YSC) Case Study Competition", True),
        (" of ", False),
        ("Research Fair 2027", True),
        (" at the ", False),
        ("University of the Philippines Diliman", True),
        (" on ", False),
        ("5 December 2026", True),
        (", we respectfully request your approval of and financial assistance under "
         "the ", False),
        ("Financial Education Support", True),
        (" for the participation of the school\u2019s ", False),
        ("Olympiad Club", True),
        (" team.", False),
        (" The team is composed of ", False),
        (MEMBERS, True),
        (".", False),
    ],
    [
        ("\tThe assistance will be used for the team\u2019s registration, the printing "
         "and reproduction of the case study and the digital poster, and the "
         "transportation of the team to the competition venue. We respectfully submit "
         "this request for your kind consideration and approval.", False),
    ],
    [
        ("\tWe assure you that all funds received will be properly accounted for and "
         "liquidated in accordance with existing accounting and auditing rules and "
         "regulations.", False),
    ],
]

SCHOOL_SPEC = dict(
    out="Letter - YSC Competition Announcement (School).docx",
    addressees=("ALL CONCERNED",),
    body=SCHOOL_BODY,
    closing=SCHOOL_CLOSING,
    blocks=[("Prepared by:", ELDRIN), ("Noted by:", ANDY), ("Approved by:", AMPY)],
)

ANDY_SPEC = dict(
    out="Letter - YSC Financial Assistance (Sir Andy).docx",
    addressees=("SIR ANDY", "Head Teacher, Science Department"),
    body=ANDY_BODY,
    closing=CLOSING,
    blocks=[("Prepared by:", JEDIDIAH), ("Noted by:", ELDRIN)],
)

AMPY_SPEC = dict(
    out="Letter - YSC Financial Assistance (Maam Ampy).docx",
    addressees=("AMPARO M. MUÑOZ, EDD", "Principal IV"),
    body=AMPY_BODY,
    closing=CLOSING,
    blocks=[("Prepared by:", JEDIDIAH), ("Noted by:", ELDRIN)],
)

def set_label(el, text):
    for run in el.findall(qn("w:r")):
        t = run.find(qn("w:t"))
        if t is not None:
            t.text = text
            return
    raise RuntimeError("label template lost its run")


def set_name(el, name, role):
    runs = el.findall(qn("w:r"))
    if len(runs) != 4:
        raise RuntimeError(f"name template has {len(runs)} runs, expected 4")
    runs[1].find(qn("w:t")).text = name
    runs[3].find(qn("w:t")).text = role


def drop_header_line(path, needle):
    """Remove the paragraph holding `needle` from every header part."""
    with zipfile.ZipFile(path) as z:
        items = [(info, z.read(info.filename)) for info in z.infolist()]
    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in items:
            if info.filename.startswith("word/header") and info.filename.endswith(".xml"):
                xml = data.decode("utf-8")
                if needle in xml:
                    for m in re.finditer(r"<w:p\b[^>]*>.*?</w:p>", xml, re.S):
                        if needle in m.group(0):
                            xml = xml[: m.start()] + xml[m.end():]
                            break
                    else:
                        raise RuntimeError(f"{needle} not in a paragraph of {info.filename}")
                data = xml.encode("utf-8")
            z.writestr(info, data)
    tmp.replace(path)


def build(spec):
    out = ROOT / spec["out"]
    out.write_bytes(SRC.read_bytes())
    d = docx.Document(out)
    paras = d.paragraphs

    # Date line keeps the master's trailing spacing run. The master's run carries no
    # size, so it would inherit 11 pt from pStyle 28; pin it to the 12 pt body size.
    paras[0].runs[0].text = DATE + "        "
    date_rpr = paras[0].runs[0]._r.get_or_add_rPr()
    for tag in ("w:sz", "w:szCs"):
        el = date_rpr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            date_rpr.append(el)
        el.set(qn("w:val"), "24")

    # TO block: label plain, addressees bold on the 121.6 pt column.
    addressees = spec["addressees"]
    clear_runs(paras[1])
    add_runs(paras[1], [("TO:", False)] + [
        (f"\t{name}" if i == 0 else f"\n\t{name}", True)
        for i, name in enumerate(addressees)
    ])

    # Body: rewrite the master's two paragraphs, clone one when a third is needed.
    body = spec["body"]
    clear_runs(paras[3])
    add_runs(paras[3], body[0])
    clear_runs(paras[4])
    add_runs(paras[4], body[1])
    if len(body) > 2:
        extra = deepcopy(paras[4]._p)
        paras[4]._p.addnext(extra)
        clear_runs(docx.text.paragraph.Paragraph(extra, paras[4]._parent))
        add_runs(docx.text.paragraph.Paragraph(extra, paras[4]._parent), body[2])

    # Closing paragraph per letter kind.
    clear_runs(paras[5])
    add_runs(paras[5], [(spec["closing"], False)])

    # Signature templates are cloned before the old blocks are removed. The master
    # keeps two spacer paragraphs between the closing body and the first label;
    # blocks after the first sit directly under each other.
    label_tpl = deepcopy(paras[8]._p)
    name_tpl = deepcopy(paras[9]._p)
    gap = [deepcopy(paras[6]._p), deepcopy(paras[7]._p)]

    body_el = d.element.body
    for p in list(paras[6:]):
        body_el.remove(p._p)

    anchor = paras[5]._p
    for index, (label, (name, role)) in enumerate(spec["blocks"]):
        label_el = deepcopy(label_tpl)
        set_label(label_el, label)
        name_el = deepcopy(name_tpl)
        set_name(name_el, name, role)
        if index == 0:
            for spacer in gap:
                anchor.addnext(spacer)
                anchor = spacer
        anchor.addnext(label_el)
        anchor = label_el
        anchor.addnext(name_el)
        anchor = name_el

    d.save(out)
    restore_letterhead_parts(out, SRC)
    drop_header_line(out, LGCC_LINE)
    print("wrote", out)


def main():
    # WPS/Word keeps a preview handle on documents it has open; retry briefly.
    for spec in (SCHOOL_SPEC, ANDY_SPEC, AMPY_SPEC):
        for attempt in range(1, 21):
            try:
                build(spec)
                break
            except PermissionError:
                if attempt == 20:
                    raise
                time.sleep(2)


if __name__ == "__main__":
    main()
