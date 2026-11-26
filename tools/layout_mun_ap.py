# -*- coding: utf-8 -*-
"""Paginate, measure, and export the MUN proposal through Word."""
import hashlib
import zipfile
from pathlib import Path

import win32com.client as win32

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "Activity Proposal - Model United Nations Club (AP_SSLG_2026_010).docx"
PDF = DOCX.with_suffix(".pdf")
SRC = ROOT / "Activity Proposal - Disyembregalo (AP_SSLG_2026_009).docx"

word = win32.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(str(DOCX), ReadOnly=False)
try:
    sec = doc.Sections(1)
    sec.PageSetup.BottomMargin = 75.6
    doc.Repaginate()
    pages = doc.ComputeStatistics(2)
    print("pages", pages)
    print("page size", round(sec.PageSetup.PageWidth, 1), round(sec.PageSetup.PageHeight, 1))
    print("margins", round(sec.PageSetup.LeftMargin, 1), round(sec.PageSetup.RightMargin, 1),
          round(sec.PageSetup.TopMargin, 1), round(sec.PageSetup.BottomMargin, 1))
    print("tables", doc.Tables.Count)
    for i in range(1, doc.Tables.Count + 1):
        t = doc.Tables(i)
        start = t.Range.Information(3)
        end = t.Range.Characters.Last.Information(3)
        print(f"table {i}: rows={t.Rows.Count} cols={t.Columns.Count} pages={start}-{end} "
              f"width={round(t.PreferredWidth, 1)}")
        widths = []
        for c in range(1, t.Columns.Count + 1):
            try:
                widths.append(round(t.Columns(c).Width, 1))
            except Exception:
                widths.append(None)
        print("   widths", widths, "sum", round(sum(w for w in widths if w), 1))
    # Locate key headings
    for needle in ["ACTIVITY PROPOSAL", "RATIONALE:", "BUDGET:", "ANNEX A", "ANNEX B", "ANNEX C",
                   "ARTICLE XIV", "ADOPTED this", "PLAN OF ACTION", "FOUNDING MEMBERS AND INTERIM"]:
        rng = doc.Content
        rng.Find.ClearFormatting()
        rng.Find.Text = needle
        if rng.Find.Execute():
            print(f"heading '{needle}' on page {rng.Information(3)}")
    doc.Save()
    doc.ExportAsFixedFormat(str(PDF), 17)
finally:
    doc.Close(False)
    try:
        word.Quit()
    except Exception:
        pass

with zipfile.ZipFile(SRC) as a, zipfile.ZipFile(DOCX) as b:
    for name in a.namelist():
        if name.startswith(("word/header", "word/footer")):
            ha = hashlib.sha256(a.read(name)).hexdigest()
            hb = hashlib.sha256(b.read(name)).hexdigest() if name in b.namelist() else "MISSING"
            print("part", name, "MATCH" if ha == hb else "DIFF")
print("PDF", PDF, PDF.stat().st_size)
