"""Final review E10: close out the two remaining truthfulness questions."""
import json
import re
import subprocess
import sys
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
fk = {e["key"]: e for e in data["files"]}


def text_of(p: Path) -> str:
    if p.suffix.lower() == ".docx":
        out = []
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            for n in ["word/document.xml"] + [x for x in names if re.match(r"word/(header|footer)\d*\.xml$", x)]:
                if n in names:
                    r = ET.fromstring(z.read(n))
                    out.append("".join(t.text or "" for t in r.iter(NS + "t")))
        return " ".join(out)
    return subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")


def find(name):
    return [e for e in data["files"] if Path(e["current_path"]).name == name]


print("E10a. resolve 'identical text to OM_SSLG_2026_001.docx.pdf' with the FULL filename")
a = find("OM_SSLG_2026_001 (14).docx.pdf")[0]
b = find("OM_SSLG_2026_001.docx.pdf")[0]
ta, tb = text_of(ROOT / a["current_path"]), text_of(ROOT / b["current_path"])
na, nb = re.sub(r"\s+", " ", ta).strip(), re.sub(r"\s+", " ", tb).strip()
print("   chars:", len(na), len(nb), "| exact equal:", na == nb, "| similarity:", round(SequenceMatcher(None, na, nb).ratio(), 4))
print("   reason:", a["archive_reason"])

print("\nE10b. was E2e's violation a matching artifact? compare the DOCX the short name selected")
c = find("OM_SSLG_2026_001.docx")[0]
tc = re.sub(r"\s+", " ", text_of(ROOT / c["current_path"])).strip()
print("   DOCX (25 May) chars:", len(tc), "| similarity PDF(reason target vs DOCX):", round(SequenceMatcher(None, na, tc).ratio(), 4))
print("   -> E2e matched 'OM_SSLG_2026_001.docx' inside 'OM_SSLG_2026_001.docx.pdf':",
      "OM_SSLG_2026_001.docx" in a["archive_reason"] and "OM_SSLG_2026_001.docx.pdf" in a["archive_reason"])

print("\nE10c. the 3 staged entries: role, reason, and whether any claims verified-duplicate status")
for e in data["files"]:
    if e["role"] == "staged":
        print("   ", e["current_path"])
        print("        reason:", e.get("archive_reason"))
print("   'verified duplicate' wording in staged reasons:",
      sum(1 for e in data["files"] if e["role"] == "staged" and re.search(r"verif", (e.get("archive_reason") or ""), re.I)))

print("\nE10d. basenames living at two current paths (Sources + Archive): roles and reasons")
from collections import defaultdict
by = defaultdict(list)
for e in data["files"]:
    by[Path(e["current_path"]).name].append(e)
for n, lst in by.items():
    if len({x["current_path"] for x in lst}) > 1:
        for x in lst:
            print("   ", n, "|", x["role"], "|", x["current_path"], "|", (x.get("archive_reason") or "")[:80])

print("\nE10e. does the record note for om-dfsslg-2026-003 disclose the staged copy?")
recs = {r["key"]: r for r in data["records"]}
t = (ROOT / recs["om-dfsslg-2026-003"]["note_path"]).read_text(encoding="utf-8")
for i, l in enumerate(t.splitlines(), 1):
    if "Staging" in l or "staged" in l.lower():
        print("   :", i, l.strip()[:170])
print("   staged path mentioned in note:", "90 Archive/Staging/OM-DFSSLG-2026-003-1.pdf" in t)
print("   staged path mentioned in Archive Index:", "90 Archive/Staging/OM-DFSSLG-2026-003-1.pdf" in
      (ROOT / "90 Archive/Archive Index.md").read_text(encoding="utf-8"))
