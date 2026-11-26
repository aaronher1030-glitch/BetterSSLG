"""Final review E4: deep text inspection of the 6 spot-check sources."""
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def dtext(name):
    from glob import glob
    hits = [p for p in ROOT.rglob(name)]
    p = hits[0]
    with zipfile.ZipFile(p) as z:
        tree = ET.fromstring(z.read("word/document.xml"))
    return p, "\n".join("".join(n.text or "" for n in par.findall(".//w:t", NS)).strip()
                        for par in tree.findall(".//w:p", NS))


def ptext(name):
    p = [x for x in ROOT.rglob(name)][0]
    return p, subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")


targets = [
    ("OM_SSLG_2026_001.docx", ["001", "Chairperson", "President", "s. 2026", "MEMORANDUM", "MAY", "May"]),
    ("OM_SSLG_2026_001 (8).docx", ["001", "s. 2026", "DATE", "May"]),
    ("AP_SSLG_2026_007_AnnexD_proofread.docx", ["AP", "007", "SSLG", "November", "DATE", "Proposer"]),
    ("ACR_SSLG_2026_006.docx", ["ACR", "006", "July", "DATE", "Report"]),
    ("SSLG_Governance_Memorandum_OM-SSLG-IA-2026-001.docx", ["001", "IA", "s. 2026", "June", "DATE", "School Name"]),
    ("Memorandum-OM-NFSSLG-2026-001_signed-2.pdf", ["NFSSLG", "001", "August", "September", "date", "Date"]),
]

for name, keys in targets:
    p, t = (ptext(name) if name.lower().endswith(".pdf") else dtext(name))
    print("=" * 100)
    print("FILE:", p.relative_to(ROOT).as_posix(), "chars:", len(t))
    lines = [l for l in t.splitlines() if l.strip()]
    print("first 14 lines:")
    for l in lines[:14]:
        print("   |", l[:110])
    print("last 12 lines:")
    for l in lines[-12:]:
        print("   |", l[:110])
    print("key hits:")
    for k in keys:
        got = [l for l in lines if k.lower() in l.lower()]
        print(f"   {k!r}: {len(got)} line(s)")
        for g in got[:6]:
            print("       >", g[:120])
