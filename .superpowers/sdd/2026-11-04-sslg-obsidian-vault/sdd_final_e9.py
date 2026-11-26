"""Final review E9: every named person / role claim in record bodies vs that record's own sources."""
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
fk = {e["key"]: e for e in data["files"]}
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def text_of(p: Path) -> str:
    if p.suffix.lower() == ".docx":
        out = []
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            for n in ["word/document.xml"] + [x for x in names if re.match(r"word/(header|footer)\d*\.xml$", x)]:
                if n in names:
                    r = ET.fromstring(z.read(n))
                    out.append("".join(t.text or "" for t in r.iter(NS + "t")))
        return "\n".join(out)
    if p.suffix.lower() == ".pdf":
        return subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")
    return ""


def norm(s):
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"[^a-z0-9' ]+", " ", s.lower())


NAME = re.compile(r"\b(?:Hon\.|Atty\.|Mr\.|Ms\.|Dr\.)?\s*[A-Z][a-z]{2,}\s+(?:[A-Z][a-z]{1,}\.?\s+){0,3}[A-Z][a-z]{2,}(?:-[A-Z][a-z]+)?\b")
STOP = {"Nationwide Online Survey", "Project", "Brigada Eskwela", "School", "Supreme Secondary",
        "Learner Government", "Department Of", "Western", "Philippines", "National Students",
        "World Teachers", "Foundation Day", "Cluster IV", "Miting De Avance", "Benigno S"}

rows = []
for r in data["records"]:
    t = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    body = t.split("---\n", 2)[2]
    src = norm("\n".join(text_of(ROOT / fk[k]["current_path"]) for k in r["source_keys"]))
    for line in body.splitlines():
        if line.startswith(("#", ">", "|", "-", "[[", "![[", "* ")):
            pass
        for m in NAME.finditer(line):
            tok = re.sub(r"\s+", " ", m.group(0).strip())
            if len(tok) < 6 or tok in rows:
                continue
            n = norm(tok)
            core = re.sub(r"^(hon|atty|mr|ms|dr)\s+", "", n).strip()
            if core in src or n in src:
                rows.append((r["key"], tok, "OK"))
            else:
                # try surname+first token forms
                parts = core.split()
                found = sum(1 for p in parts if len(p) > 3 and p in src)
                rows.append((r["key"], tok, "MISSING" if found == 0 else f"PARTIAL {found}/{len([p for p in parts if len(p)>3])}"))

print("E9a. person-name mentions in record-note bodies vs that record's own sources")
print("   total checks:", len(rows))
from collections import Counter
print("   ", Counter(x[2].split()[0] for x in rows))
for k, tok, verdict in rows:
    if verdict != "OK":
        print("      ", verdict, "|", k, "|", tok)

print("\nE9b. related-link disclosure coverage")
recs = {r["key"]: r for r in data["records"]}
edges = set()
for r in data["records"]:
    for k in r["related"]:
        edges.add((r["key"], k))
cav = re.compile(r"number alone|also used by|same number|different issuance|identifies neither|numbering", re.I)
for a, b in sorted(edges):
    ta = (ROOT / recs[a]["note_path"]).read_text(encoding="utf-8")
    tb = (ROOT / recs[b]["note_path"]).read_text(encoding="utf-8")
    if not (cav.search(ta) or cav.search(tb)):
        print("   edge without any numbering caveat:", a, "<->", b)
print("   edges checked:", len(edges))
