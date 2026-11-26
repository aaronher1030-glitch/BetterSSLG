import re, json, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools" / "sslg_content.json").read_text(encoding="utf-8"))
records = {r["note_path"]: r for r in data["records"]}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def docx_text(p):
    parts = []
    with zipfile.ZipFile(p) as z:
        names = [n for n in z.namelist() if n == "word/document.xml"
                 or re.match(r"word/(header|footer)\d*\.xml$", n)]
        for n in names:
            try: root = ET.fromstring(z.read(n))
            except Exception: continue
            for t in root.iter(W + "t"):
                parts.append(t.text or "")
    return "".join(parts)

def pdf_text(p):
    import subprocess
    out = subprocess.run(["pdftotext", "-q", str(p), "-"], capture_output=True)
    return out.stdout.decode("utf-8", "replace")

rows = []
for rel, r in sorted(records.items()):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8", errors="replace")
    fm = yaml.safe_load(t[3:t.index("\n---", 3)])
    rid = fm.get("record_id")
    m = re.search(r">\s*\*\*Document ID:\*\*\s*(.+)", t)
    printed = m.group(1).strip() if m else None
    # gather own source text (primary files for this record)
    src = []
    for f in data["files"]:
        if f.get("record_key") == r["key"] and f.get("role") == "primary":
            fp = ROOT / f["current_path"]
            if fp.suffix.lower() == ".docx" and fp.exists():
                src.append(docx_text(fp))
            elif fp.suffix.lower() == ".pdf" and fp.exists():
                src.append(pdf_text(fp))
    body = "\n".join(src)
    underscore = isinstance(rid, str) and "_" in rid
    token_in_source = bool(rid) and str(rid) in body
    rows.append((rel, rid, printed, underscore, token_in_source))

print("E13 record notes:", len(rows))
und = [x for x in rows if x[3]]
print("E13a underscore-form record_id rendered:", len(und))
print("E13b of those, string absent from own primary DOCX/PDF text (incl headers/footers):",
      sum(1 for x in und if not x[4]))
for x in und:
    if not x[4]:
        print("      ", x[1], "|", x[0].split("/")[-1][:70])
nul = [x for x in rows if x[1] is None]
print("E13c record_id null (rendered 'Not stated in source'):", len(nul))
hyph = [x for x in rows if x[1] and "_" not in str(x[1])]
print("E13d hyphen/other form ids:", len(hyph),
      "| present in own source text:", sum(1 for x in hyph if x[4]))
for x in hyph:
    if not x[4]:
        print("      ABSENT:", x[1], "|", x[0].split("/")[-1][:70])
