import json, os, re, collections, posixpath

ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
man = json.load(open(os.path.join(ROOT, "90 Archive", "File Manifest.json"), encoding="utf-8-sig"))
ad = {e["key"]: e for e in man["activities"]}
def R(p): return open(os.path.join(ROOT, p.replace("/", os.sep)), encoding="utf-8").read()

SKIP = {".git", "__pycache__", ".obsidian", "node_modules", "Scheduler_v1-main", "docs", ".superpowers", "tools"}
corpus = {}
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        rp = os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")
        if rp.endswith((".md", ".base")):
            corpus[rp] = R(rp)
print("corpus files (md+base, self zones):", len(corpus))

created = sorted(set(list(corpus.keys()) +
                     [k for k in (posixpath.normpath(e["current_path"]) for e in man["files"])
                      if not k.endswith((".docx", ".pdf", ".png"))]))
extra_created = [k for k in corpus if k == "01 Dashboards/SSLG Records.base"]
targets = sorted(set(list(corpus.keys()) + ["90 Archive/File Manifest.json"]))
print("candidate created artifacts:", len(targets))

unreach = []
for k in targets:
    lk = k.lower(); bn = posixpath.basename(lk)
    stem = bn[:-3] if bn.endswith(".md") else bn
    hits = []
    for other, text in corpus.items():
        if other == k: continue
        tl = text.lower()
        if lk in tl or bn in tl or (stem and stem in tl):
            hits.append(other)
    if k.endswith(".json"):
        hits = [h for h in hits]
    if not hits:
        unreach.append(k)
print("\nR1 unreachable (self-reference removed):", len(unreach))
for x in unreach: print("   ", x)

# how each reachable artifact is reached - first non-self referencer
print("\nR2 referencers of the archive/dashboard surface:")
for probe in ["90 Archive/Archive Index.md", "90 Archive/File Manifest.json", "01 Dashboards/Review Queue.md",
              "01 Dashboards/Document Library.md", "01 Dashboards/Activity Dashboard.md",
              "01 Dashboards/Timeline.md", "99 Templates/Record Template.md", "99 Templates/Activity Template.md",
              "01 Dashboards/SSLG Records.base"]:
    bn = posixpath.basename(probe).lower()
    stem = bn[:-3] if bn.endswith(".md") else bn
    hits = [o for o, t in corpus.items() if o != probe and (probe.lower() in t.lower() or bn in t.lower() or stem in t.lower())]
    print(f"   {probe}  <-  {hits[:5]} ({len(hits)})")

# ---------- trail count fix ----------
print("\nB) Activity Dashboard trail column (fixed split) vs manifest records-per-activity")
truth = collections.Counter(e["activity"] for e in man["records"] if e["activity"])
dt = R("01 Dashboards/Activity Dashboard.md")
mism = []
rows = 0
for line in dt.splitlines():
    if not line.startswith("| [[02 Activities/"): continue
    rows += 1
    inner = re.sub(r"\[\[([^\]]+)\|([^\]]+)\]\]", r"\2", line)
    cells = [c.strip() for c in inner.strip().strip("|").split("|")]
    title = cells[0]
    key = next((k for k, v in ad.items() if v["title"] == title), None)
    claimed = cells[5]; real = truth.get(key)
    if str(real) != claimed: mism.append((title, claimed, real))
print("  rows:", rows, "mismatches:", len(mism), mism[:10])
print("  dashboard trail sum:", sum(int(re.sub(r"\[\[[^\]]+\]\]", "", l).split("|")[6].strip())
      for l in dt.splitlines() if l.startswith("| [[02 Activities/")))
print("  manifest records with activity set:", sum(truth.values()), "records total:", len(man["records"]))

# ---------- hub trails ----------
print("\nB2) hub trail tables vs manifest")
bad_hub = []
for e in man["activities"]:
    t = R(e["hub_path"])
    for rec in man["records"]:
        if rec["activity"] == e["key"]:
            if rec["note_path"] not in t: bad_hub.append((e["title"], rec["note_path"]))
print("  hub missing its own record note:", len(bad_hub), bad_hub[:6])
orphan = [rec["title"] for rec in man["records"] if rec["activity"] and rec["activity"] not in ad]
print("  records pointing at unknown activity:", orphan)

# ---------- template links (never validated by the tool) ----------
print("\nG) template + archive-index link integrity (outside validator scope)")
WL = re.compile(r"!?\[\[([^\[\]]+?)\]\]")
allf = {posixpath.normpath(p).lower() for p in os.path.join(ROOT, k) for k in []}
disk = set()
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in {".git", "__pycache__", ".obsidian", "node_modules"}]
    for f in fn: disk.add(posixpath.basename(os.path.join(dp, f)).lower())
for p in ["99 Templates/Record Template.md", "99 Templates/Activity Template.md", "90 Archive/Archive Index.md"]:
    t = R(p)
    tg = sorted({m.group(1).split("|")[0].split("#")[0].strip() for m in WL.finditer(t)})
    print(f"   {p}: {len(tg)} unique wikilinks, placeholders={len(re.findall(r'(?m)^(?:title|record_id|date|source_path):\\s*$', t))}")
    print("      targets:", tg[:8])
    print("      headings:", re.findall(r"(?m)^#{1,3} .+$", t)[:8])
