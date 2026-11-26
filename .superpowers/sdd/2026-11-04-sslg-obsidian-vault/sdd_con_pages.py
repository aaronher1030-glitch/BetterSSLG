import json, os, re, hashlib, zipfile, collections
ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
os.chdir(ROOT)
V = json.load(open("90 Archive/File Manifest.json", encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()

print("=== staged self-reference: actual hashes ===")
pairs = [
 ("90 Archive/Staging/OM-DFSSLG-2026-003-1.pdf", "04 External Memoranda/Sources/OM-DFSSLG-2026-003-1.pdf"),
 ("90 Archive/Staging/OM_SSLG_2026_002..docx", "90 Archive/Revisions/OM_SSLG_2026_002..docx"),
 ("90 Archive/Staging/OM_SSLG_2026_002..docx", "02 Activities/Nationwide Online Survey on Digital Device Use/Sources/OM_SSLG_2026_002..docx"),
]
for a,b in pairs:
    ea, eb = os.path.exists(a), os.path.exists(b)
    print("  %s | exists=%s | sha=%s" % (a, ea, sha(a)[:16] if ea else "-"))
    print(("    vs %s exists=%s sha=%s  IDENTICAL=%s" % (b, eb, sha(b)[:16] if eb else "-", (sha(a)==sha(b)) if (ea and eb) else "n/a")))

print()
print("=== all staged-role files ===")
for f in V["files"]:
    if f["role"]=="staged":
        print("  ", f["key"], "|", f["current_path"], "|", f["archive_reason"])

print()
def pagecount(p):
    data = open(p,"rb").read()
    n_pages = len(re.findall(rb"/Type\s*/Page(?![s/])", data))
    counts = [int(x) for x in re.findall(rb"/Count\s+(\d+)", data)]
    return n_pages, (max(counts) if counts else None)

print("=== PDF page counts for every PDF on disk (all copies) ===")
pdfs = sorted([f["current_path"] for f in V["files"] if f["current_path"].lower().endswith(".pdf")] +
              [f["current_path"] for f in V["files"] if f["current_path"].lower().endswith(".pdf")])
seen=set()
for p in pdfs:
    if p in seen: continue
    seen.add(p)
    if not os.path.exists(p):
        print("  ABSENT", p); continue
    n,c = pagecount(p)
    print("  %-95s /Type/Page=%-3s max/Count=%-4s sha=%s" % (os.path.basename(p), n, c, sha(p)[:10]))
