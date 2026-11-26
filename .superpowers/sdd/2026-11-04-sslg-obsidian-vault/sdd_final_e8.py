"""Final review E8: evidence for the nfsslg date/ID, adviser-name claims, and 6 spot notes."""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
fk = {e["key"]: e for e in data["files"]}
byname = {}
for e in data["files"]:
    byname.setdefault(Path(e["current_path"]).name, []).append(e)
rec_by_key = {r["key"]: r for r in data["records"]}


def text_of(p: Path) -> str:
    if p.suffix.lower() == ".docx":
        out = []
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            for n in ["word/document.xml"] + [x for x in names if re.match(r"word/(header|footer)\d*\.xml$", x)]:
                if n in names:
                    r = ET.fromstring(z.read(n))
                    out.append("".join(t.text or "" for t in r.iter("{%s}t" % NS["w"])))
        return "\n".join(out)
    if p.suffix.lower() == ".pdf":
        return subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")
    return ""


print("E8a. every file in the vault whose text contains a 25-August-2026 style date or NFSSLG id")
pat = re.compile(r"25\s*(?:th)?\s+August\s+2026|August\s+25,?\s+2026|2026-08-25|08/25/2026|25/08/2026", re.I)
idpat = re.compile(r"OM[\s\-_.]?NFSSLG[\s\-_.]?2026[\s\-_.]?001", re.I)
hits = []
for e in data["files"]:
    p = ROOT / e["current_path"]
    t = text_of(p)
    d, i = bool(pat.search(t)), bool(idpat.search(t))
    if d or i or t.strip() == "":
        hits.append((e["current_path"], "DATE" if d else "", "ID" if i else "", len(t.strip())))
for h in hits:
    print("   ", h)

print("\nE8b. NFSSLG family: text length per file (image-only check)")
for e in data["files"]:
    if "NFSSLG" in e["current_path"]:
        t = text_of(ROOT / e["current_path"])
        print("   ", e["role"], "|", e["current_path"], "| text chars:", len(t.strip()))

print("\nE8c. named-person claims in the 6 spot notes vs their own sources")
spot = ["om-sslg-2026-001-may25", "om-sslg-2026-001-may27", "ap-sslg-2026-007",
        "acr-sslg-2026-006", "om-sslg-ia-2026-001", "om-nfsslg-2026-001"]
namepat = re.compile(r"(?:Hon\.|Mr\.|Ms\.|Atty\.|Dr\.)\s+[A-Z][A-Za-z .'\u2019-]{3,40}?[A-Z]|AARON KHRISTIAN T\. BANAG|AMPARO M\. MU\u00d1OZ")
for k in spot:
    r = rec_by_key[k]
    note = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    body = note.split("---", 2)[2]
    src = "\n".join(text_of(ROOT / fk[s]["current_path"]) for s in r["source_keys"])
    srcn = re.sub(r"\s+", " ", src).replace("\u2019", "'")
    claims = sorted(set(m.group(0).strip() for m in namepat.finditer(body)))
    print(f"   [{k}] named-person claims in note: {len(claims)}")
    for c in claims:
        cc = re.sub(r"\s+", " ", c).replace("\u2019", "'")
        found = cc in srcn or cc.upper() in srcn.upper()
        if not found:
            # tolerate reordered 'Chairperson, X' style
            core = re.sub(r"^(Hon\.|Mr\.|Ms\.|Atty\.|Dr\.)\s*", "", cc)
            found = core.upper() in srcn.upper()
        print("        ", "OK  " if found else "MISS", repr(c))

print("\nE8d. role/adviser/principal words claimed in the 6 spot notes, verified in source")
for k in spot:
    r = rec_by_key[k]
    body = (ROOT / r["note_path"]).read_text(encoding="utf-8").split("---", 2)[2]
    src = re.sub(r"\s+", " ", "\n".join(text_of(ROOT / fk[s]["current_path"]) for s in r["source_keys"])).upper()
    for kw in ["ADVISER", "PRINCIPAL", "SIGNED", "APPROVED", "CONCURRED", "NOTED"]:
        if kw in body.upper():
            print(f"   [{k}] {kw}: in-note yes | in-source {'yes' if kw in src else 'NO (text layer?)'}")

print("\nE8e. 'cited by the Division, Cluster and school-level issuances' claim")
cited = {}
for e in data["files"]:
    if e["role"] in ("primary", "alternative-format") and Path(e["current_path"]).name.startswith(("OM-DFSSLG", "OM-CFSSLG", "OM_SSLG_2026_002")):
        t = re.sub(r"\s+", " ", text_of(ROOT / e["current_path"]))
        cited[Path(e["current_path"]).name] = bool(re.search(r"NFSSLG", t, re.I))
for k, v in cited.items():
    print("   ", k, "-> mentions NFSSLG:", v)
