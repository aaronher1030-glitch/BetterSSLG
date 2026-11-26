"""Final review E3: corrected page counts, text-identity claims, 6-note content truthfulness."""
import json
import re
import subprocess
import sys
import zipfile
import difflib
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
byname = {}
for e in data["files"]:
    byname.setdefault(Path(e["current_path"]).name, e)
    byname.setdefault(Path(e["original_path"]).name, e)

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def pages_obj(p):
    return len(re.findall(rb"/Type\s*/Page[^s]", p.read_bytes()))


def pages_raw(p):
    return subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace").count("\f")


def pages_count(p):
    """object scan, with /Count fallback for object-stream PDFs, cross-checked by pdftotext form feeds"""
    o, f = pages_obj(p), pages_raw(p)
    if o:
        return (o, f, "obj")
    raw = p.read_bytes()
    cnts = [int(x) for x in re.findall(rb"/Count\s+(\d+)", raw)]
    return (max(cnts) if cnts else f, f, "count" if cnts else "formfeed")


print("E3a. page counts (corrected): object-scan / form-feed / method")
for e in sorted(data["files"], key=lambda x: x["current_path"]):
    if e["current_path"].lower().endswith(".pdf"):
        p = ROOT / e["current_path"]
        print(f"   {p.name:62s} {pages_count(p)}")


def dtext(p):
    with zipfile.ZipFile(p) as z:
        tree = ET.fromstring(z.read("word/document.xml"))
    return "\n".join("".join(n.text or "" for n in par.findall(".//w:t", NS)).strip()
                     for par in tree.findall(".//w:p", NS))


def ptext(p):
    return subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")


def txt_of(entry):
    p = ROOT / entry["current_path"]
    return ptext(p) if entry["current_path"].lower().endswith(".pdf") else dtext(p)


print("\nE3b. all 'identical text' style claims, longest-name regex")
claim = re.compile(r"(text identical to|text matches|identical text to|text equals)\s+([\w\-. ()]+?\.(?:docx\.pdf|docx|pdf))", re.I)
viol = []
n = 0
for e in data["files"]:
    for m in claim.finditer(e.get("archive_reason") or ""):
        tname = m.group(2).strip()
        te = byname.get(tname)
        n += 1
        if te is None:
            viol.append(("no-target", e["current_path"], tname)); continue
        a = re.sub(r"\s+", "", txt_of(e)); b = re.sub(r"\s+", "", txt_of(te))
        if a != b:
            viol.append(("TEXT-DIFFERS", e["current_path"], tname, len(a), len(b)))
print("   claims:", n, "violations:", len(viol), viol)

print("\nE3c. the three 9-page PDFs of OM_SSLG_2026_001 (ledger says (14).docx.pdf == .docx.pdf, ' (1).pdf differs)")
names = ["OM_SSLG_2026_001.docx.pdf", "OM_SSLG_2026_001 (14).docx.pdf", "OM_SSLG_2026_001.docx (1).pdf"]
norm = {}
for nm in names:
    t = txt_of(byname[nm])
    nb = [l.strip() for l in t.splitlines() if l.strip()]
    norm[nm] = nb
    print(f"   {nm}: nonblank lines={len(nb)}")
print("   (14).docx.pdf == .docx.pdf :", norm[names[0]] == norm[names[1]])
print("   ' (1).pdf == .docx.pdf    :", norm[names[0]] == norm[names[2]])
sm = difflib.SequenceMatcher(None, norm[names[0]], norm[names[2]])
print("   similarity ratio .docx.pdf vs ' (1).pdf:", round(sm.ratio(), 4))
for tag, i1, i2, j1, j2 in sm.get_opcodes()[:8]:
    if tag != "equal":
        print("     ", tag, norm[names[0]][i1:i2][:3], "||", norm[names[2]][j1:j2][:3])

print("\nE3d. 6-note content truthfulness spot check")
checks = [
    ("om-sslg-2026-001-may25", "OM_SSLG_2026_001.docx",
     [r"25(?:st)?\s+May\s+2026|MAY 25, 2026|May 25, 2026", r"OM SSLG No\. 001", r"Rhian Jade L\. Castro",
      r"LGCC Chairperson", r"SSLG President", r"OM[- ]DFSSLG[- ]2026[- ]002"]),
    ("om-sslg-2026-001-may27", "OM_SSLG_2026_001 (8).docx",
     [r"27(?:th)?\s+May\s+2026|MAY 27, 2026|May 27, 2026", r"OM SSLG No\. 001", r"Chloe Danielle L\. David",
      r"Kean Albert J\. Pineda"]),
    ("ap-sslg-2026-007", "AP_SSLG_2026_007_AnnexD_proofread.docx",
     [r"AP_SSLG_2026_007", r"November 17|17 ?- ?18 ?|November 1[78]", r"National Students.{0,3} Day"]),
    ("acr-sslg-2026-006", "ACR_SSLG_2026_006.docx",
     [r"ACR_SSLG_2026_006", r"July 22|22 ?2026", r"Induction"]),
    ("om-sslg-ia-2026-001", "SSLG_Governance_Memorandum_OM-SSLG-IA-2026-001.docx",
     [r"OM-SSLG-IA-2026-001", r"June 2[0-9], 2026|22 ?June ?2026|JUNE 22, 2026", r"\[School Name\]"]),
    ("om-nfsslg-2026-001", "Memorandum-OM-NFSSLG-2026-001_signed-2.pdf",
     [r"OM-NFSSLG-2026-001", r"August 25|25 August 2026|AUGUST 25, 2026", r"September 4|4 September 2026"]),
]
for key, fname, pats in checks:
    rec = next(r for r in data["records"] if r["key"] == key)
    src = byname[fname]
    t = txt_of(src)
    print(f"   [{key}] source={fname} frontmatter date={rec['date']} event={rec['event_date']} id={rec['record_id']!r} status={rec['status']}")
    for pat in pats:
        m = re.search(pat, t, re.I)
        print(f"      {'FOUND ' if m else 'ABSENT'} /{pat}/ -> {(m.group(0)[:60] if m else '')}")
