import json, os, re, collections, yaml

ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
man = json.load(open(os.path.join(ROOT, "90 Archive", "File Manifest.json"), encoding="utf-8-sig"))
rd = {e["key"]: e for e in man["records"]}
ad = {e["key"]: e for e in man["activities"]}
fd = {e["key"]: e for e in man["files"]}
def R(p): return open(os.path.join(ROOT, p.replace("/", os.sep)), encoding="utf-8").read()
def fm(t):
    parts = t.split("---\n", 2)
    return yaml.safe_load(parts[1]) if len(parts) > 2 else {}

# ---------- A: frontmatter truth for all declared notes ----------
print("A) frontmatter scan of record notes")
tvals, rtvals, stvals = collections.Counter(), collections.Counter(), collections.Counter()
bad_srcpath, bad_sourcefile, no_embed = [], [], []
for e in man["records"]:
    t = R(e["note_path"]); d = fm(t)
    tvals[d.get("type")] += 1; rtvals[d.get("record_type")] += 1; stvals[d.get("status")] += 1
    sp = d.get("source_path"); sf = d.get("source_file")
    srcs = d.get("sources") or []
    paths = [sp] + [s.get("source_path") for s in srcs if isinstance(s, dict)] + \
            [s.get("path") for s in srcs if isinstance(s, dict)]
    paths = [p for p in paths if isinstance(p, str)]
    for p in set(paths):
        if not os.path.exists(os.path.join(ROOT, p.replace("/", os.sep))):
            bad_srcpath.append((e["note_path"], p))
    if not paths:
        bad_srcpath.append((e["note_path"], "NO source_path in frontmatter"))
    final_h = re.findall(r"(?m)^## (.+)$", t)
    fin = t[t.rindex("## " + final_h[-1]):] if final_h else ""
    for k in e["source_keys"]:
        cp = fd[k]["current_path"]
        if cp in fin and not re.search(r"!?\[\[[^\]]*" + re.escape(os.path.basename(cp)) + r"[^\]]*\]\]", fin):
            no_embed.append((e["note_path"], cp, "plain text, not a link/embed"))
    if sf and os.path.basename(sf) not in fin:
        no_embed.append((e["note_path"], sf, "source_file not in final section"))
print("  type values:", dict(tvals))
print("  record_type values:", dict(rtvals))
print("  status values:", dict(stvals))
print("  frontmatter source_path that do NOT resolve:", len(bad_srcpath))
for x in bad_srcpath[:12]: print("     ", x)
print("  sources mentioned in final section WITHOUT wikilink/embed syntax:", len(no_embed))
for x in no_embed[:12]: print("     ", x)
print("A2 hub frontmatter type values:", dict(collections.Counter(
    fm(R(e["hub_path"])).get("type") for e in man["activities"])))
print("A3 base filters need type=='record' -> record notes with type 'record':", tvals.get("record"),
      "| needs-review status in notes:", stvals.get("needs-review"),
      "| manifest records status needs-review:", sum(1 for e in man["records"] if e["status"] == "needs-review"))
for rt in ("proposal", "completion-report", "memorandum"):
    print(f"   record_type {rt}: frontmatter={rtvals.get(rt)} manifest={sum(1 for e in man['records'] if e['record_type']==rt)}")

# ---------- B: Activity Dashboard trail counts ----------
print("\nB) Activity Dashboard trail-count column vs manifest")
dt = R("01 Dashboards/Activity Dashboard.md")
truth = collections.Counter(e["activity"] for e in man["records"])
rows = 0; mism = []
for line in dt.splitlines():
    m = re.match(r"^\|\s*\[\[02 Activities/([^|\]]+?)/[^|]+\.md\|([^\]]+)\]\]\s*\|", line)
    if not m: continue
    rows += 1
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    key = None
    for k, v in ad.items():
        if v["title"] == cells[0] or v["hub_path"].endswith("/" + os.path.basename(m.group(1)) + ".md"):
            key = k; break
    claimed = cells[5] if len(cells) > 5 else "?"
    real = truth.get(key)
    if str(real) != claimed: mism.append((cells[0], claimed, real, key))
print("  activity rows parsed:", rows, "(manifest activities: 16)")
print("  trail-count mismatches:", len(mism))
for x in mism[:20]: print("     ", x)
print("  sum of activity-scoped records in manifest:", sum(v for k, v in truth.items() if k),
      "| records with activity=None:", sum(1 for e in man["records"] if not e["activity"]))

# ---------- C: Timeline coverage ----------
print("\nC) Timeline coverage")
tt = R("01 Dashboards/Timeline.md")
print("  claim lines in first 20:")
for i, ln in enumerate(tt.splitlines()[:20], 1):
    if ln.strip(): print(f"     {i}: {ln.strip()[:160]}")
missing_hub = [e["title"] for e in man["activities"] if e["hub_path"] not in tt]
missing_rec = [e["title"] for e in man["records"] if e["note_path"] not in tt]
print("  activities absent from Timeline:", missing_hub)
print("  records absent from Timeline:", len(missing_rec), missing_rec[:10])

# ---------- D: Review Queue strict reason coverage ----------
print("\nD) Review Queue strict coverage")
q = R("01 Dashboards/Review Queue.md")
print("  claim lines 1-16:")
for i, ln in enumerate(q.splitlines()[:16], 1):
    if ln.strip(): print(f"     {i}: {ln.strip()[:160]}")
def nz(s): return re.sub(r"\s+", " ", s or "").strip()
qnorm = nz(q)
entries = [(e, "record") for e in man["records"]] + [(e, "activity") for e in man["activities"]]
flagged = [(e, k) for e, k in entries if e["review_reasons"]]
print("  flagged entries in manifest:", len(flagged),
      "(records:", sum(1 for e, k in flagged if k == "record"),
      "activities:", sum(1 for e, k in flagged if k == "activity"), ")")
no_title, no_reason, total_reasons, miss_reasons = [], [], 0, []
for e, kind in flagged:
    if nz(e["title"]) not in qnorm: no_title.append((kind, e["title"]))
    for r in e["review_reasons"]:
        total_reasons += 1
        if nz(r) not in qnorm: miss_reasons.append((kind, e["title"], r[:90]))
print("  flagged entries whose TITLE is absent from queue:", no_title)
print("  total reasons in manifest:", total_reasons, "| reasons absent from queue:", len(miss_reasons))
for x in miss_reasons[:15]: print("     ", x)
# independent: notes whose own frontmatter says needs-review
nreview_notes = [e["note_path"] for e in man["records"] if fm(R(e["note_path"])).get("status") == "needs-review"]
hreview_notes = [e["hub_path"] for e in man["activities"] if fm(R(e["hub_path"])).get("status") == "needs-review"]
notin = [p for p in nreview_notes + hreview_notes if os.path.basename(p) not in q]
print("  notes with frontmatter status needs-review:", len(nreview_notes), "hubs:", len(hreview_notes))
print("  of those, absent from Review Queue:", notin)
queue_titles = re.findall(r"(?m)^### \[\[([^\]|]+)", q)
print("  queue ### headings:", len(queue_titles))
declared = {os.path.basename(e["note_path"]) for e in man["records"]} | {os.path.basename(e["hub_path"]) for e in man["activities"]}
print("  queue headings not matching any declared note:", [h for h in queue_titles if os.path.basename(h) not in declared])

# ---------- E: START HERE counts vs manifest ----------
print("\nE) START HERE links")
sh = R("START HERE.md")
print("  hub links present:", sum(1 for e in man["activities"] if e["hub_path"] in sh), "/16")
print("  record-note links present:", sum(1 for e in man["records"] if e["note_path"] in sh), "/36")

# ---------- F: Archive Index completeness (spec line 156) ----------
print("\nF) Archive Index.md")
ai = R("90 Archive/Archive Index.md")
lines = [ln for ln in ai.splitlines() if ln.strip().startswith("|")]
print("  table lines:", len(lines))
missing_cur = [e["current_path"] for e in man["files"] if e["current_path"] not in ai]
missing_sha = [e["key"] for e in man["files"] if e["sha256"] not in ai]
missing_orig = [e["original_path"] for e in man["files"] if os.path.basename(e["original_path"]) not in ai]
print("  current_path absent from Archive Index:", len(missing_cur), missing_cur[:6])
print("  sha256 absent from Archive Index:", len(missing_sha), missing_sha[:6])
print("  original filename absent:", len(missing_orig), missing_orig[:6])

# ---------- G: template reachability ----------
print("\nG) templates")
corpus = {}
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in {".git", "__pycache__", ".obsidian", "Scheduler_v1-main", "docs", ".superpowers", "node_modules"}]
    for f in fn:
        if f.endswith((".md", ".base")):
            rp = os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")
            corpus[rp] = R(rp)
for name in ("Activity Template", "Record Template", "File Manifest", "Archive Index", "SSLG Records.base", "START HERE"):
    where = [p for p, t in corpus.items() if name.lower() in t.lower() and name.lower() not in p.lower()]
    print(f"  '{name}' referenced in: {where[:6]}")
pngs = [f"80 Assets/OM_SSLG_2026_001-{i}.png" for i in range(1, 9)]
for p in pngs:
    refs = [q for q, t in corpus.items() if os.path.basename(p) in t]
    print("  asset", p, "referenced by:", refs[:3], "count:", len(refs))
