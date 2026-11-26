"""Final review E6: focused measurements on the flagged claims."""
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
fk = {e["key"]: e for e in data["files"]}
byname = {}
for e in data["files"]:
    byname[Path(e["current_path"]).name] = e
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def entry_for(name):
    return byname[name]


def paras(name):
    e = entry_for(name)
    p = ROOT / e["current_path"]
    if e["current_path"].lower().endswith(".pdf"):
        t = subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")
        return [l.strip() for l in t.splitlines() if l.strip()], p, e
    with zipfile.ZipFile(p) as z:
        parts = [n for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)]
        out = []
        for n in parts:
            tree = ET.fromstring(z.read(n))
            for par in tree.findall(".//w:p", NS):
                t = "".join(x.text or "" for x in par.findall(".//w:t", NS)).strip()
                if t:
                    out.append(t)
    return out, p, e


def media(name):
    e = entry_for(name)
    p = ROOT / e["current_path"]
    if not e["current_path"].lower().endswith(".docx"):
        return []
    with zipfile.ZipFile(p) as z:
        return sorted(n for n in z.namelist() if n.startswith("word/media/"))


print("E6a. OM_SSLG_2026_001.docx (25 May primary) — signature evidence")
ls, p, e = paras("OM_SSLG_2026_001.docx")
print("   path:", e["current_path"], "| paragraphs:", len(ls), "| media files:", media("OM_SSLG_2026_001.docx"))
for i, l in enumerate(ls):
    if re.search(r"approved|signature|castro|prepared|president|chairperson|LGCC", l, re.I):
        print(f"     [{i}] {l[:130]}")
print("   LAST 8 lines:")
for l in ls[-8:]:
    print("     |", l[:130])

print("\nE6b. OM_SSLG_2026_001.pdf (25 May alt-format) — same probes")
ls2, p2, e2 = paras("OM_SSLG_2026_001.pdf")
print("   paragraphs:", len(ls2), "| text chars:", sum(len(x) for x in ls2))
for i, l in enumerate(ls2):
    if re.search(r"approved|signature|castro|prepared|president|chairperson", l, re.I):
        print(f"     [{i}] {l[:130]}")
print("   LAST 8 lines:")
for l in ls2[-8:]:
    print("     |", l[:130])

print("\nE6c. media/signature images in all OM_SSLG_2026_001 DOCX copies")
for name in sorted([x for x in byname if x.startswith("OM_SSLG_2026_001") and x.endswith(".docx")]):
    m = media(name)
    print(f"   {name:34s} media={len(m)} {[Path(x).name for x in m]}")

print("\nE6d. DATE lines of the four records whose date my pattern missed")
for name in ["NOM_SSLG_2026_003.docx", "NOM_SSLG_2026_004.docx", "OM_SSLG_2026_002 (7).docx",
             "NOM_SSLG_2026_004.pdf"]:
    ls, p, e = paras(name)
    print(f"   --- {name} ({e['current_path']})")
    for l in ls[:30]:
        if re.search(r"date|\b20\d\d\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", l, re.I):
            print("       >", l[:130])

print("\nE6e. printed identifiers in sources vs manifest record_id")
IDPAT = re.compile(r"(no\.|number|ref(?:erence)? no\.?|office reference no\.?)\s*[:.]?\s*([A-Z0-9\-]{0,24})?\s*(\d{3})?\s*,?\s*s\.?\s*(20\d\d)?", re.I)
rows = []
for r in data["records"]:
    printed = []
    for k in r["source_keys"]:
        nm = Path(fk[k]["current_path"]).name
        try:
            ls, _, _ = paras(nm)
        except Exception as ex:
            ls = []
        for l in ls:
            if IDPAT.search(l) or re.search(r"\b(No\.|Number)\b", l):
                printed.append(l[:110])
    rows.append((r["key"], r["record_id"], printed[:3]))
for a, b, c in rows:
    print(f"   {a:26s} id={str(b):26s} printed={c}")

print("\nE6f. hub 'Organizers:' line presence (explicit)")
for a in data["activities"]:
    hub = (ROOT / a["hub_path"]).read_text(encoding="utf-8")
    print(f"   {a['key']:34s} explicit-organizers-line={'**Organizers:**' in hub} count={hub.count('**Organizers:**')}")

print("\nE6g. World Teachers Day proposal: 2 vs 5 October claim")
for name in ["AP_SSLG_2026_006_revised.docx", "AP_SSLG_2026_006 (3).docx"]:
    try:
        ls, p, e = paras(name)
    except KeyError:
        print("   missing", name); continue
    d = [l for l in ls if re.search(r"october|date", l, re.I)]
    print(f"   {name}: {d[:6]}")

print("\nE6h. ECOLEAD memo copies: dates + numbers claimed in the review reasons")
for name in ["OM_SSLG_2026_002.docx", "OM_SSLG_2026_002 (1).docx", "OM_SSLG_2026_002 (2).docx",
             "OM_SSLG_2026_002 (7).docx", "OM_SSLG_2026_002 (8).docx"]:
    ls, p, e = paras(name)
    dat = [l for l in ls if re.search(r"^date|july|august|september", l, re.I)][:5]
    num = [l for l in ls if re.search(r"no\.\s*\d{3}", l, re.I)][:2]
    print(f"   {name}: dates={dat} numbers={num}")
