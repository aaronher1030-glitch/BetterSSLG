"""Build the YSC excuse letter from the YSC school announcement.

Clones Letter - YSC Competition Announcement (School).docx so the Olympiad Club
letterhead (header/footer parts, already stripped of the SSLG LGCC line) stays
byte-identical, then rewrites the date, body and closing. Signature blocks are
trimmed to Prepared by (Research Adviser) and Approved by (Principal IV).
"""
from pathlib import Path

import docx

from build_calm_letter import add_runs, clear_runs, restore_letterhead_parts

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Letter - YSC Competition Announcement (School).docx"

MEMBERS = (
    "Aaron Y. Hernandez (11-Onyx), Ellaine T. Jacob (11-Ilmenite), "
    "and Jolex Alexier S. Cruz (11-Jacinth)"
)

# (date printed on the letter, output filename)
LETTERS = {
    "2026-11-16": ("November 16, 2026", "Excuse Letter - YSC Preparation.docx"),
    "2026-11-17": ("November 17, 2026", "Excuse Letter - YSC Preparation (Nov 17).docx"),
}


def body_1(date):
    return [
        ("\tIn connection with the upcoming ", False),
        ("Youth Science Convention (YSC) Case Study Competition", True),
        (" of ", False),
        ("Research Fair 2027", True),
        (" at the ", False),
        ("University of the Philippines Diliman", True),
        (", we respectfully request to excuse the following Olympiad Club learners "
         "from their respective classes on ", False),
        (f"{date} from 6:00 A.M. to 11:00 A.M.", True),
        (": ", False),
        (MEMBERS, True),
        (".", False),
    ]

BODY_2 = [
    ("\tThe time will be used to prepare the team\u2019s concept project paper and "
     "digital poster for the competition. Their preparation is essential to the "
     "school\u2019s participation in the said undertaking and to the proper "
     "representation of Benigno S. Aquino National High School.", False),
]

CLOSING = (
    "\tWe look forward to your favorable response to this request. "
    "May the Almighty continue to bless us."
)


def build(date, out_name):
    out = ROOT / out_name
    out.write_bytes(SRC.read_bytes())
    d = docx.Document(out)
    paras = d.paragraphs

    paras[0].runs[0].text = date + "        "

    clear_runs(paras[3])
    add_runs(paras[3], body_1(date))
    clear_runs(paras[4])
    add_runs(paras[4], BODY_2)
    clear_runs(paras[5])
    add_runs(paras[5], [(CLOSING, False)])

    # Old closing paragraph (6) is redundant now; the "Noted by" block (11, 12)
    # is not a signatory for this letter. Remove bottom-up so indices hold.
    for index in (12, 11, 6):
        paras[index]._p.getparent().remove(paras[index]._p)

    d.save(out)
    restore_letterhead_parts(out, SRC)
    print("wrote", out)


if __name__ == "__main__":
    import sys

    key = sys.argv[1] if len(sys.argv) > 1 else "2026-11-17"
    date, out_name = LETTERS[key]
    build(date, out_name)
