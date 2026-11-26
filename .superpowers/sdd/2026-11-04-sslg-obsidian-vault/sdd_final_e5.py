"""Final review E5: record_id presence in sources; signature-block claims; hub organizer claims."""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
fk = {e["key"]: e for e in data["files"]}
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CACHE = {}


def srctext(entry):
    p = ROOT / entry["current_path"]
    if p in CACHE:
        return CACHE[p]
    if entry["current_path"].lower().endswith(".pdf"):
        CACHE[p] = subprocess.run(["pdftotext", str(p), "-"], capture_output=True).stdout.decode("utf-8", "replace")
    else:
        with zipfile.ZipFile(p) as z:
            parts = [n for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)]
            buf = []
            for n in parts:
                tree = ET.fromstring(z.read(n))
                for par in tree.findall(".//w:p", NS):
                    t = "".join(x.text or "" for x in par.findall(".//w:t", NS)).strip()
                    if t:
                        buf.append(t)
            CACHE[p] = "\n".join(buf)
    return CACHE[p]


def norm(s):
    return re.sub(r"[^0-9a-z]+", "", s.lower())


print("E5a. record_id evidence: stated record_id present in the record's own sources?")
nofind = []
for r in data["records"]:
    rid = r["record_id"]
    texts = [norm(srctext(fk[k])) for k in r["source_keys"]]
    if not rid:
        nofind.append((r["key"], None, "record_id null", [fk[k]["current_path"] for k in r["source_keys"]]))
        continue
    cands = [rid, rid.replace("_", "-"), rid.replace("_", " "), rid.replace(" ", ""),
             rid.replace(" ", "-"), re.sub(r"^(OM|AP|ACR|NOM|EL)\s+", "", rid)]
    cands = [c for c in cands if norm(c)]
    hit = any(norm(c) in t for t in texts for c in cands)
    if not hit:
        m = re.search(r"\d{3}", rid or "")
        frag_ok = any(m and m.group(0) in t for t in texts) if m else False
        nofind.append((r["key"], rid, "NOT-VERBATIM" if not frag_ok else "NUMERIC-FRAGMENT-ONLY",
                       [fk[k]["current_path"] for k in r["source_keys"]]))
print(f"   records where record_id is NOT found in its own sources: {len(nofind)} / {len(data['records'])}")
for x in nofind:
    print("    ", x)

print("\nE5b. signature markers in OM_SSLG_2026_001 DOCX/PDFs")
for name in ["OM_SSLG_2026_001.docx", "OM_SSLG_2026_001.pdf", "OM_SSLG_2026_001 (8).docx", "OM_SSLG_2026_001.docx.pdf"]:
    e = next(x for x in data["files"] if Path(x["current_path"]).name == name)
    t = srctext(e)
    hits = sorted(set(x.lower() for x in re.findall(r"Prepared by|Noted by|Reviewed and|Concurred|Recommending Approval|Approved by", t, re.I)))
    tail = [l for l in t.splitlines() if l.strip()][-3:]
    print(f"   {name:28s} role={e['role']:18s} markers={hits}")
    print(f"      tail={tail}")

print("\nE5c. image-only PDFs and disclosure")
imageonly = [e["current_path"] for e in data["files"]
             if e["current_path"].lower().endswith(".pdf") and not re.sub(r"[\s\x0c]", "", srctext(e))]
print("   image-only PDFs:", len(imageonly), imageonly)
for r in data["records"]:
    prim = fk[r["source_keys"][0]]
    if prim["current_path"] in imageonly:
        note = (ROOT / r["note_path"]).read_text(encoding="utf-8")
        print("     ", r["key"], "| primary is image-only | discloses:",
              bool(re.search(r"image-only|no extractable text|scanned", note, re.I)))

print("\nE5d. hub organizer lines")
for a in data["activities"]:
    hub = (ROOT / a["hub_path"]).read_text(encoding="utf-8")
    line = re.search(r"^.*[Oo]rganiz.*$", hub, re.M)
    print(f"   {a['key']:34s} manifest={str(a.get('organizers'))[:60]!r}")
    print(f"      hub line: {(line.group(0)[:110] if line else 'NONE')}")

print("\nE5e. hub body carries venue/start/status")
for a in data["activities"]:
    hub = (ROOT / a["hub_path"]).read_text(encoding="utf-8")
    miss = [k for k, v in (("venue", a["venue"]), ("start", a["start_date"]), ("status", a["status"]))
            if v and v not in hub]
    if miss:
        print("   ", a["key"], "missing", miss)

print("\nE5f. record note At-a-glance dates vs manifest")
bad = []
for r in data["records"]:
    txt = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    d = re.search(r"\*\*Record date:\*\* ([^\n]+)", txt)
    e = re.search(r"\*\*Event date:\*\* ([^\n]+)", txt)
    if d.group(1).strip() != (r["date"] or "Not stated in source") or e.group(1).strip() != (r["event_date"] or "Not stated in source"):
        bad.append((r["key"], d.group(1), r["date"], e.group(1), r["event_date"]))
print("   mismatches:", len(bad), bad)

print("\nE5g. record note Document ID line vs manifest record_id")
bad = []
for r in data["records"]:
    txt = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    m = re.search(r"\*\*Document ID:\*\* ([^\n]+)", txt)
    exp = r["record_id"] or "Not stated in source"
    if not m or m.group(1).strip() != exp:
        bad.append((r["key"], m.group(1).strip() if m else None, exp))
print("   mismatches:", len(bad), bad)

print("\nE5h. stated issuance dates vs DATE lines in the primary source (all records with a date)")
prob = []
for r in data["records"]:
    if not r["date"]:
        continue
    e = fk[r["source_keys"][0]]
    t = srctext(e)
    y, mth, dd = r["date"].split("-")
    variants = {
        f"{y}-{int(mth):02d}-{int(dd):02d}", f"{int(dd)} {y}",
    }
    monthname = ["January","February","March","April","May","June","July","August","September","October","November","December"][int(mth)-1]
    pats = [rf"{monthname}\.?\s+{int(dd)}{{1,2}},?\s*{y}", rf"{int(dd)}{{1,2}}\s+{monthname}\.?\s+{y}",
            rf"{monthname[:3]}\.?\s+{int(dd)}{{1,2}},?\s*{y}", rf"{int(dd)}{{1,2}}[-/]\s*{int(mth)}{{1,2}}[-/]\s*{y}"]
    found = any(re.search(p, t, re.I) for p in pats)
    if not found:
        prob.append((r["key"], r["date"], e["current_path"]))
print("   dates not matched by a DATE-style pattern in the primary source:", len(prob))
for x in prob:
    print("     ", x)
