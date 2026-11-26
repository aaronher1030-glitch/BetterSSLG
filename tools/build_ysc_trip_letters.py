"""Build the week-long YSC excuse and the Bamban/Concepcion trip letters.

Clones Letter - YSC Competition Announcement (School).docx for the Olympiad Club
letterhead and rewrites the date, TO block, body, closing and signature chain.
Meeting-letter wording follows Letter - YSC Meeting and Fund Request (Mayor
Villanueva).docx.

    python -X utf8 tools/build_ysc_trip_letters.py
"""
import time
from copy import deepcopy
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from build_calm_letter import add_runs, clear_runs, restore_letterhead_parts

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Letter - YSC Competition Announcement (School).docx"

DATE = "November 17, 2026"

MEMBERS = (
    "Aaron Y. Hernandez (11-Onyx), Ellaine T. Jacob (11-Ilmenite), "
    "and Jolex Alexier S. Cruz (11-Jacinth)"
)

CLOSING = (
    "\tWe look forward to your favorable response to this request. "
    "May the Almighty continue to bless us."
)

# Signature chain requested for this batch: Eldrin signs, the two subject
# supervisors note, the Principal approves. A None label continues the previous
# block (second noter under the same "Noted by:").
BLOCKS = [
    ("Respectfully yours,", "ELDRIN L. PATIO", "Research Adviser"),
    ("Noted by:", "AMADO T. ALIMURUNG", "Head Teacher, Science Department"),
    (None, "RUFTHEL GUTIERREZ", "Subject Group Head"),
    ("Approved by:", "AMPARO M. MUÑOZ, EDD", "Principal IV"),
]

EXCUSE_BODY = [
    [
        ("\tIn connection with the upcoming ", False),
        ("Youth Science Convention (YSC) Case Study Competition", True),
        (" of ", False),
        ("Research Fair 2027", True),
        (" at the ", False),
        ("University of the Philippines Diliman", True),
        (", we respectfully request to excuse the following Olympiad Club "
         "learners from their respective classes from ", False),
        ("November 16 to 20, 2026, from 6:00 A.M. to 11:00 A.M. daily", True),
        (": ", False),
        (MEMBERS, True),
        (".", False),
    ],
    [
        ("\tThe time will be used to prepare the team\u2019s concept project paper and "
         "digital poster for the competition. Their preparation is essential to the "
         "school\u2019s participation in the said undertaking and to the proper "
         "representation of Benigno S. Aquino National High School.", False),
    ],
]

TRANSPO_BODY = [
    [
        ("\tWe respectfully request the use of a school vehicle for the Olympiad "
         "Club team\u2019s visits to the ", False),
        ("Municipal Environment and Natural Resources Office (MENRO) of Bamban", True),
        (" and the ", False),
        ("Municipal Planning and Development Office (MPDO) of Concepcion", True),
        (", Tarlac. The visits will be scheduled on dates to be confirmed with the "
         "two offices.", False),
    ],
    [
        ("\tThe vehicle will transport the team, composed of ", False),
        (MEMBERS, True),
        (", together with their research adviser, from Benigno S. Aquino National "
         "High School to the two offices and back. The visits will support the "
         "team\u2019s preparation for the ", False),
        ("Youth Science Convention (YSC) Case Study Competition", True),
        (" of Research Fair 2027, where the team will propose a twelve-month pilot "
         "project for a one-kilometer stretch of a local waterway.", False),
    ],
    [
        ("\tWe assure you that the vehicle will be used strictly for this official "
         "purpose and that the team will observe the school\u2019s travel and safety "
         "protocols.", False),
    ],
]

MENRO_BODY = [
    [
        ("\tWe respectfully request a meeting with your Office at your earliest "
         "convenience to discuss the projects of the Municipal Environment and "
         "Natural Resources Office, particularly on environmental protection and "
         "waterway management, and to present the school\u2019s ", False),
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
         "Municipality, and that the meeting will open areas of cooperation. The "
         "Phase 1 project deadline is on ", False),
        ("5 December 2026", True),
        (". We would also be grateful for any data, maps, or records on the "
         "waterways within your jurisdiction that your Office may share, and for "
         "your guidance on the environmental priorities of the Municipality.", False),
    ],
]

MPDO_BODY = [
    [
        ("\tWe respectfully request a meeting with your Office at your earliest "
         "convenience to discuss the plans and programs of the Municipal Planning "
         "and Development Office, particularly on land use and waterway "
         "management, and to present the school\u2019s ", False),
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
         "that the team\u2019s proposal can be aligned with the plans of the "
         "Municipality, and that the meeting will open areas of cooperation. The "
         "Phase 1 project deadline is on ", False),
        ("5 December 2026", True),
        (". We would also be grateful for any data, maps, or records on the "
         "waterways within your jurisdiction, including the Comprehensive Land "
         "Use Plan, that your Office may share, and for your guidance on the "
         "development priorities of the Municipality.", False),
    ],
]

SPECS = [
    dict(
        out="Excuse Letter - YSC Preparation (Nov 16-20).docx",
        addressees=("ALL CONCERNED",),
        body=EXCUSE_BODY,
        closing=CLOSING,
    ),
    dict(
        out="Request Letter - School Vehicle (Bamban and Concepcion).docx",
        addressees=("AMPARO M. MUÑOZ, EDD", "Principal IV"),
        body=TRANSPO_BODY,
        closing=CLOSING,
    ),
    dict(
        out="Letter - Meeting Request (Bamban MENRO).docx",
        addressees=(
            "MR. JONATHAN YANGA",
            "Municipal Environment and Natural Resources Officer",
            "Municipality of Bamban, Tarlac",
        ),
        body=MENRO_BODY,
        closing=CLOSING,
    ),
    dict(
        out="Letter - Meeting Request (Concepcion MPDO).docx",
        addressees=(
            "MS. MA. SOCORRO S. PADLAN",
            "Municipal Planning and Development Coordinator",
            "Municipality of Concepcion, Tarlac",
        ),
        body=MPDO_BODY,
        closing=CLOSING,
    ),
]


def set_label(el, text):
    for run in el.findall(qn("w:r")):
        t = run.find(qn("w:t"))
        if t is not None:
            t.text = text
            return
    raise RuntimeError("label template lost its run")


def set_name_block(el, name, role):
    """Rewrite the name paragraph to '<break>NAME<break>Role' with two runs."""
    for run in el.findall(qn("w:r")):
        el.remove(run)
    line_break = OxmlElement("w:r")
    line_break.append(OxmlElement("w:br"))
    el.append(line_break)
    name_run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rpr.append(OxmlElement("w:b"))
    name_run.append(rpr)
    t = OxmlElement("w:t")
    t.text = name
    t.set(qn("xml:space"), "preserve")
    name_run.append(t)
    el.append(name_run)
    role_break = OxmlElement("w:r")
    role_break.append(OxmlElement("w:br"))
    el.append(role_break)
    role_run = OxmlElement("w:r")
    t2 = OxmlElement("w:t")
    t2.text = role
    t2.set(qn("xml:space"), "preserve")
    role_run.append(t2)
    el.append(role_run)
    # Fonts/sizes come from the paragraph mark's rPr and the run defaults; pin
    # them on each run to be safe.
    for run in el.findall(qn("w:r")):
        rpr = run.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            run.insert(0, rpr)
        if rpr.find(qn("w:rFonts")) is None:
            fonts = OxmlElement("w:rFonts")
            fonts.set(qn("w:ascii"), "Bookman Old Style")
            fonts.set(qn("w:hAnsi"), "Bookman Old Style")
            fonts.set(qn("w:cs"), "Arial")
            rpr.insert(0, fonts)
        if rpr.find(qn("w:sz")) is None:
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), "24")
            rpr.append(sz)
        if rpr.find(qn("w:szCs")) is None:
            szcs = OxmlElement("w:szCs")
            szcs.set(qn("w:val"), "24")
            rpr.append(szcs)


def build(spec):
    out = ROOT / spec["out"]
    out.write_bytes(SRC.read_bytes())
    d = docx.Document(out)
    paras = d.paragraphs

    # Date line: keep the master's trailing spacing run and pin it to 12 pt.
    paras[0].runs[0].text = DATE + "        "
    date_rpr = paras[0].runs[0]._r.get_or_add_rPr()
    for tag in ("w:sz", "w:szCs"):
        el = date_rpr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            date_rpr.append(el)
        el.set(qn("w:val"), "24")

    # TO block: label plain, every addressee line bold on the tab column.
    clear_runs(paras[1])
    add_runs(paras[1], [("TO:", False)] + [
        (("\t" if i == 0 else "\n\t") + line, True)
        for i, line in enumerate(spec["addressees"])
    ])

    body_tpl = deepcopy(paras[3]._p)
    closing_tpl = deepcopy(paras[6]._p)
    spacer = deepcopy(paras[8]._p)
    # One blank line before the signature block is enough; the double break in
    # the master pushes the lower signatories into the letterhead footer band.
    spacer_runs = spacer.findall(qn("w:r"))
    if len(spacer_runs) > 1:
        spacer.remove(spacer_runs[-1])
    gap = [spacer]
    label_tpl = deepcopy(paras[9]._p)
    name_tpl = deepcopy(paras[10]._p)

    body_el = d.element.body
    for p in list(paras[3:]):
        body_el.remove(p._p)

    anchor = paras[2]._p
    for parts in spec["body"]:
        el = deepcopy(body_tpl)
        anchor.addnext(el)
        anchor = el
        para = Paragraph(el, paras[2]._parent)
        clear_runs(para)
        add_runs(para, parts)

    closing_el = deepcopy(closing_tpl)
    anchor.addnext(closing_el)
    anchor = closing_el
    closing_para = Paragraph(closing_el, paras[2]._parent)
    clear_runs(closing_para)
    add_runs(closing_para, [(spec["closing"], False)])

    for spacer in gap:
        anchor.addnext(spacer)
        anchor = spacer

    for label, name, role in BLOCKS:
        if label is not None:
            label_el = deepcopy(label_tpl)
            set_label(label_el, label)
            anchor.addnext(label_el)
            anchor = label_el
        name_el = deepcopy(name_tpl)
        set_name_block(name_el, name, role)
        anchor.addnext(name_el)
        anchor = name_el

    d.save(out)
    restore_letterhead_parts(out, SRC)
    print("wrote", out)


def main():
    for spec in SPECS:
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
