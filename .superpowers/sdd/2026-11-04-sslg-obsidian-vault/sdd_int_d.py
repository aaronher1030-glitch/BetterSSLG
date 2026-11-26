import json, os, re, collections, yaml

ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
man = json.load(open(os.path.join(ROOT, "90 Archive", "File Manifest.json"), encoding="utf-8-sig"))

print("== TRUTH FROM MANIFEST ==")
print("activities:", len(man["activities"]), "records:", len(man["records"]),
      "files:", len(man["files"]), "protected:", len(man["protected_files"]))
print("file roles:", collections.Counter(e["role"] for e in man["files"]))
print("file archive_reason kinds:", collections.Counter((e["archive_reason"] or "")[:40] for e in man["files"] if e["role"] != "primary"))
print("record types:", collections.Counter(e["record_type"] for e in man["records"]))
print("record status:", collections.Counter(e["status"] for e in man["records"]))
print("activity status:", collections.Counter(e["status"] for e in man["activities"]))
print("record collections:", collections.Counter(e["collection"] for e in man["records"]))
print("records with review_reasons:", sum(1 for e in man["records"] if e["review_reasons"]))
print("activities with review_reasons:", sum(1 for e in man["activities"] if e["review_reasons"]))
print("file suffixes:", collections.Counter(os.path.splitext(e["current_path"])[1].lower() for e in man["files"]))

# actual note files on disk
def listdir(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    return os.path.isdir(p)
zones = ["01 Dashboards", "02 Activities", "03 Governance", "04 External Memoranda",
         "05 General Records", "80 Assets", "90 Archive", "99 Templates"]
mds = []
for z in zones:
    for dp, dn, fn in os.walk(os.path.join(ROOT, z.replace("/", os.sep))):
        for f in fn:
            if f.endswith(".md"):
                mds.append(os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/"))
print("md per zone:", collections.Counter(m.split("/")[0] for m in mds))
print("record notes on disk (*/Notes/*.md):", sum(1 for m in mds if "/Notes/" in m))
print("hub notes on disk:", sum(1 for m in mds if m.split("/")[0] == "02 Activities"
                               and "/Notes/" not in m and "/Sources/" not in m))

print("\n== CHECK 5: numeric claims in navigation ==")
nav = ["START HERE.md", "01 Dashboards/Activity Dashboard.md", "01 Dashboards/Timeline.md",
       "01 Dashboards/Review Queue.md", "01 Dashboards/Document Library.md"]
NUM = re.compile(r"\b(\d{1,4})\b")
for p in nav:
    full = os.path.join(ROOT, p.replace("/", os.sep))
    if not os.path.exists(full):
        print("!! MISSING NAV FILE:", p); continue
    text = open(full, encoding="utf-8").read()
    print(f"\n--- {p} ({len(text)} chars, {text.count(chr(10))+1} lines) ---")
    for i, line in enumerate(text.splitlines(), 1):
        if NUM.search(line) and re.search(r"(?i)\b(activity|activit|record|document|file|memor|note|hub|source|page|item|total|count|duplicat|revis|asset|png|docx|pdf)\w*", line):
            print(f"  {i}: {line.strip()[:200]}")

print("\n== Document Library: folders claimed vs existing ==")
dl = os.path.join(ROOT, "01 Dashboards", "Document Library.md")
if os.path.exists(dl):
    t = open(dl, encoding="utf-8").read()
    cands = set(re.findall(r"[0-9]{2}\s[A-Za-z][^|\n\[\]`]{2,40}", t))
    existing = {z for z in zones if os.path.isdir(os.path.join(ROOT, z.replace("/", os.sep)))}
    print("folder-like tokens in Document Library:", sorted(cands))
    print("existing top-level vault folders:", sorted(existing))
    print("missing dirs that DO NOT exist on disk:",
          sorted(c for c in cands if re.sub(r"\s+", " ", c).strip() not in existing))
print("05 General Records exists on disk:", listdir("05 General Records"))

print("\n== BASE FILE ==")
bp = os.path.join(ROOT, "01 Dashboards", "SSLG Records.base")
raw = open(bp, encoding="utf-8").read()
try:
    doc = yaml.safe_load(raw)
    print("YAML parse: OK; top keys:", list(doc.keys()) if isinstance(doc, dict) else type(doc))
    views = doc.get("views") if isinstance(doc, dict) else None
    print("view count:", len(views) if isinstance(views, list) else "views not a list")
    if isinstance(views, list):
        for i, v in enumerate(views):
            print(f"  view[{i}] name={v.get('name')!r} type={v.get('type')!r}")
            print(f"      filters={v.get('filter') if 'filter' in v else v.get('filters')}")
            print(f"      order keys={[k for k in v.keys()]}")
    print("top-level excludes/formula:", {k: doc[k] for k in doc if k != "views"})
except Exception as ex:
    print("YAML PARSE FAILED:", ex)
print("Scheduler mention:", [ln for ln in raw.splitlines() if "Scheduler" in ln])
print("Templates mention:", [ln for ln in raw.splitlines() if "Template" in ln or "99" in ln])
