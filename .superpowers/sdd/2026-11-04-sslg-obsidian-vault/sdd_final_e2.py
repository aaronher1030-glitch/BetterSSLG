"""Final review E2: page-count claims vs measured PDF page counts; byte-identical claims."""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_final_lib import h, pdftotext, pdf_page_objects  # noqa: E402

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
byname = {}
for e in data["files"]:
    byname.setdefault(Path(e["current_path"]).name, e)
    byname.setdefault(Path(e["original_path"]).name, e)

PDFS = sorted({e["current_path"] for e in data["files"] if e["current_path"].lower().endswith(".pdf")})
measured = {}
for rel in PDFS:
    p = ROOT / rel
    ff = pdftotext(p).count("\f")
    ff = ff - 1 if ff and pdftotext(p).endswith("\f") else ff
    measured[Path(rel).name] = (pdf_page_objects(p), ff)
print("E2a. measured page counts (object-scan, formfeed) for all", len(PDFS), "PDFs")
for k, v in measured.items():
    print(f"   {k}: {v}")

NUMPAGE = re.compile(r"\b(\d{1,3})[\s-]page\b")
FILETok = re.compile(r"[\w\-. ()]+?\.(?:docx|pdf)|[\w\-. ()]+?\.docx\.pdf")

mdfiles = [p for p in ROOT.rglob("*.md")
           if not p.relative_to(ROOT).as_posix().startswith((".superpowers/", "docs/", "tools/", "Scheduler_v1-main/"))]
print("\nE2b. every 'N-page' claim in the notes, checked against the files named on the same line")
fails, oks = [], 0
for p in mdfiles:
    rel = p.relative_to(ROOT).as_posix()
    for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if "page" not in line.lower():
            continue
        nums = [int(m.group(1)) for m in NUMPAGE.finditer(line)]
        if not nums:
            continue
        toks = set()
        for m in FILETok.finditer(line):
            name = m.group(0).strip()
            # extend greedy match may swallow too much; trim to the last path-less token
            name = name.split("/")[-1].strip()
            if name in byname:
                toks.add(name)
        # also try bare names appearing in wikilinks
        for m in re.finditer(r"\[\[([^\]|]+)", line):
            n = Path(m.group(1)).name
            if n in byname:
                toks.add(n)
        if not toks:
            print(f"   [NOFILE] {rel}:{ln} nums={nums} :: {line[:110]}")
            continue
        for n in sorted(toks):
            for want in nums:
                got = measured.get(n)
                if got is None:
                    print(f"   [NOTPDF] {rel}:{ln} {n} want {want}")
                    continue
                ok = want in got
                if ok:
                    oks += 1
                else:
                    fails.append((rel, ln, n, want, got, line[:90]))
print(f"   claims matched={oks} mismatched={len(fails)}")
for x in fails:
    print("    MISMATCH:", x)

print("\nE2c. 'byte-identical duplicate of X' claims verified by hash on disk")
byte = re.compile(r"byte-identical duplicate of ([\w\-. ()]+?\.(?:docx|pdf))", re.I)
anchor = re.compile(r"anchor of the byte-identical ([\w\-.()/ 0-9]+?) group", re.I)
viol = []
tot = 0
for e in data["files"]:
    for text in [e.get("archive_reason") or ""]:
        for m in byte.finditer(text):
            tot += 1
            tname = m.group(1).strip()
            te = byname.get(tname)
            if te is None:
                viol.append(("target-not-found", e["current_path"], tname))
                continue
            a = ROOT / e["current_path"]
            b = ROOT / te["current_path"]
            if not a.is_file() or not b.is_file():
                viol.append(("missing-file", e["current_path"], te["current_path"]))
                continue
            ha, hb = h(a), h(b)
            if ha != hb:
                viol.append(("HASH-DIFFERS", e["current_path"], te["current_path"], ha[:16], hb[:16]))
print("   byte-identical claims found:", tot, "violations:", len(viol))
for x in viol:
    print("    ", x)

print("\nE2d. recompute duplicate grouping from disk and compare to manifest sha256 fields")
from collections import defaultdict
disk = defaultdict(list)
for e in data["files"]:
    disk[h(ROOT / e["current_path"])].append(Path(e["current_path"]).name)
disagree = [e["current_path"] for e in data["files"] if h(ROOT / e["current_path"]) != e["sha256"]]
print("   manifest sha256 fields disagreeing with disk:", len(disagree), disagree)
groups = {k: v for k, v in disk.items() if len(v) > 1}
print("   disk duplicate groups:", len(groups))
for k, v in groups.items():
    print("    ", k[:12], sorted(v))

print("\nE2e. claims of 'text identical' / 'identical text' in archive reasons — verify by extracted text")
idtext = re.compile(r"(?:re-saved copy with text identical to|text matches|with identical text to)\s+([\w\-. ()]+?\.(?:docx|pdf))", re.I)
docx_text = {}


def dtext(rel):
    if rel not in docx_text:
        import zipfile
        from xml.etree import ElementTree as ET
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with zipfile.ZipFile(ROOT / rel) as z:
            tree = ET.fromstring(z.read("word/document.xml"))
        docx_text[rel] = "\n".join(
            "".join(n.text or "" for n in par.findall(".//w:t", ns)).strip()
            for par in tree.findall(".//w:p", ns)
        )
    return docx_text[rel]


def ptext(rel):
    key = "pdf:" + rel
    if key not in docx_text:
        docx_text[key] = pdftotext(ROOT / rel)
    return docx_text[key]


bad = []
checked = 0
for e in data["files"]:
    for m in idtext.finditer(e.get("archive_reason") or ""):
        tname = m.group(1).strip()
        te = byname.get(tname)
        if te is None:
            bad.append(("target-missing", e["current_path"], tname))
            continue
        def txt(entry):
            r = entry["current_path"]
            return ptext(r) if r.lower().endswith(".pdf") else dtext(r)
        a, b = txt(e), txt(te)
        checked += 1
        na = re.sub(r"\s+", "", a)
        nb = re.sub(r"\s+", "", b)
        if na != nb:
            bad.append(("TEXT-DIFFERS", e["current_path"], tname, len(na), len(nb)))
print("   text-identity claims checked:", checked, "violations:", len(bad))
for x in bad:
    print("    ", x)
