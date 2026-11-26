# -*- coding: utf-8 -*-
"""Correct the DO 47 citation in the research dossier.

DepEd Order No. 47, s. 2014, Art. XII creates the Learner Government Coordinating
Council of the presidents of all recognized co-curricular organizations; it does not
say the learner government *supervises* clubs. The "supervision" wording in the draft
came from the school handbook, so the dossier must not attribute it to the Order.

Each target paragraph is rebuilt from its own run properties, so the bold "What it
proves." lead-in and the coloured finding title keep their styling.

Idempotent: re-running finds the corrected text and changes nothing.

Run:  python -X utf8 tools/fix_dossier_citation.py
"""
import copy
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "SSLG Club Classification Research Dossier.docx"

TITLE = "F4  ·  The learner government coordinates clubs; it does not categorize them"
PROOF = (
    "The national instrument that governs clubs fixes recognition and creates a council "
    "of club presidents, the channel through which the learner government coordinates "
    "them. It says nothing about supervision and is silent on categories. Whatever "
    "grouping the school adopts therefore rests on the school's own authority, exercised "
    "through the SSLG."
)
PERMISSIBLE = (
    "A four-cluster scheme is permissible, because nothing national forbids it and "
    "DO 47, s. 2014, Art. XII, gives the SSLG a council of club presidents through which "
    "to coordinate them."
)


def _without_bold(rpr):
    rpr = copy.deepcopy(rpr)
    for tag in ("w:b", "w:bCs"):
        el = rpr.find(qn(tag))
        if el is not None:
            el.set(qn("w:val"), "0")
    return rpr


def rebuild(paragraph, parts):
    """Replace every run with (text, rPr) pairs, keeping each part's own styling."""
    for run in list(paragraph.runs):
        run._r.getparent().remove(run._r)
    for text, rpr in parts:
        run = paragraph.add_run(text)
        if rpr is not None:
            run._r.insert(0, copy.deepcopy(rpr))


def main():
    doc = Document(PATH)
    changed = 0
    for p in doc.paragraphs:
        text = " ".join(p.text.split())
        runs = p.runs
        if not runs:
            continue
        first = runs[0]._r.rPr
        if text.startswith("F4") and "learner government" in text:
            rebuild(p, [(TITLE, first)])
            changed += 1
        elif text.startswith("What it proves.") and "national instrument that governs clubs" in text:
            rebuild(p, [("What it proves. ", first), (PROOF, _without_bold(first))])
            changed += 1
        elif text.startswith("A four-cluster scheme is permissible"):
            rebuild(p, [(PERMISSIBLE, first)])
            changed += 1
    if changed:
        doc.save(PATH)
    print(f"{PATH.name}: {changed} paragraph(s) normalised")
    return 0


if __name__ == "__main__":
    sys.exit(main())
