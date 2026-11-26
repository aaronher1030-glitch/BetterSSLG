"""Final review E7: remaining measurements (ID provenance, reversibility, archive index, claims)."""
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
recs = data["records"]
acts = data["activities"]
files = data["files"]
fk = {e["key"]: e for e in files}
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def docx_all_text(p: Path) -> str:
    parts = []
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        for n in ["word/document.xml"] + [x for x in names if re.match(r"word/(header|footer)\d*\.xml$", x)]:
            if n not in names:
                continue
            root = ET.fromstring(z.read(n))
            parts.append("".join(t.text or "" for t in root.iter("{%s}t" % NS["w"])))
    return "\n".join(parts)


print("E7a. provenance of underscore-style record_id values (search body + headers + footers)")
ids_missing = []
for r in recs:
    rid = r.get("record_id")
    if not rid or not re.match(r"^[A-Z]+_SSLG", rid):
        continue
    txts = []
    for k in r["source_keys"]:
        e = fk[k]
        p = ROOT / e["current_path"]
        if p.suffix.lower() == ".docx":
            txts.append(docx_all_text(p))
        else:
            import subprocess
            txts.append(subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace"))
    blob = "\n".join(txts).replace("\u2019", "'")
    variants = {rid, rid.replace("_", "-"), rid.replace("_SSLG", "-SSLG-")}
    hit = next((v for v in variants if v in blob), None)
    if hit is None:
        # does the doc print any 'No. NNN' style self-numbering?
        nums = re.findall(r"\bNo\.?\s*0*\d{1,3}\b", blob)
        ids_missing.append((r["key"], rid, nums[:3]))
print(f"   underscore ids absent from own sources (incl. headers/footers): {len(ids_missing)}")
for k, rid, nums in ids_missing:
    print("      ", k, rid, "printed No.-tokens:", nums)

print("\nE7b. reversibility bookkeeping")
op = [e["original_path"] for e in files]
cp = [e["current_path"] for e in files]
print("   entries:", len(files), "distinct original_path:", len(set(op)), "distinct current_path:", len(set(cp)))
dupop = sorted({p for p in op if op.count(p) > 1})
print("   repeated original_path:", dupop)
print("   any current_path equal to another entry's original_path (rename hazard):",
      sorted({e['current_path'] for e in files if e['current_path'] in set(op) and files.index(e)} - {e['current_path'] for e in files if e['current_path'] == e['original_path']}))
missing = [e for e in files if not (ROOT / e["current_path"]).is_file()]
print("   current_path missing on disk:", len(missing))
print("   entries where current_path==original_path:", sum(1 for e in files if e["current_path"] == e["original_path"]))

print("\nE7c. 80 Assets PNG references anywhere in vault md/base")
pngs = sorted(e["current_path"] for e in files if e["current_path"].startswith("80 Assets/"))
allmd = [p for p in ROOT.rglob("*") if p.suffix in (".md", ".base")
         and not str(p.relative_to(ROOT)).startswith((".superpowers/", "docs/", "Scheduler_v1-main/", ".obsidian/"))]
blob = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in allmd)
for png in pngs:
    n = png.split("/")[-1]
    print("   ", png, "full-path refs:", blob.count(png), "basename refs:", blob.count(n))

print("\nE7d. Archive Index.md structure")
ai = (ROOT / "90 Archive/Archive Index.md").read_text(encoding="utf-8")
lines = ai.splitlines()
hex64 = [l for l in lines if re.search(r"\b[0-9a-f]{64}\b", l)]
print("   lines:", len(lines), "| lines containing a 64-hex checksum:", len(hex64))
print("   markdown table rows:", sum(1 for l in lines if l.strip().startswith("|")))
print("   first 14 lines:")
for l in lines[:14]:
    print("      |", l[:150])
both = [l for l in hex64 if "`" in l]
print("   checksum lines with backticked paths:", len(both))
# how many checksum lines carry both an original and a current path?
pair = [l for l in hex64 if l.count("/") >= 2]
print("   checksum lines containing >=2 path separators (original+current mapping):", len(pair))
uniq_hashes = set(re.findall(r"\b[0-9a-f]{64}\b", ai))
manifest_hashes = {e["sha256"] for e in files}
print("   distinct hashes in index:", len(uniq_hashes), "| not in manifest:", len(uniq_hashes - manifest_hashes))

print("\nE7e. 'identical text' style claims, verbatim")
pat = re.compile(r"identical text|text identical|same text|text is identical|carries the same", re.I)
found = 0
for p in allmd:
    for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if pat.search(l):
            found += 1
            print("   ", p.relative_to(ROOT).as_posix(), f":{i}", l.strip()[:170])
for e in files:
    rs = e.get("archive_reason") or ""
    if pat.search(rs):
        print("    MANIFEST", e["current_path"], "->", rs[:160])
print("   md claim lines:", found)

print("\nE7f. Review Queue claim lines and vocabulary")
rq = (ROOT / "01 Dashboards/Review Queue.md").read_text(encoding="utf-8")
for i, l in enumerate(rq.splitlines(), 1):
    if re.search(r"\d+\s+records", l) or l.startswith("# "):
        print("   ", f":{i}", l.strip()[:150])

print("\nE7g. SSLG Records.base raw")
print((ROOT / "01 Dashboards/SSLG Records.base").read_text(encoding="utf-8"))
