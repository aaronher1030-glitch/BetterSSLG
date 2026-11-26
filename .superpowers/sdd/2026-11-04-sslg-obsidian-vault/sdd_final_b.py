"""Final review B: spec compliance of the 36 record notes and 16 activity hubs."""
import json
import re
from pathlib import Path

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
files = {e["key"]: e for e in data["files"]}
records = data["records"]
activities = data["activities"]

WIKI = re.compile(r"!?\[\[([^\]]+?)\]\]")
H2 = re.compile(r"^## \S", re.M)


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.index("\n---\n", 3)
    return text[3:end + 1], text[end + 4:]


problems = []
rec_paths = {r["note_path"] for r in records}
hub_paths = {a["hub_path"] for a in activities}

# on-disk md inventory (vault scope)
md = []
for p in ROOT.rglob("*.md"):
    rp = p.relative_to(ROOT).as_posix()
    if rp.startswith((".superpowers/", "docs/", "Scheduler_v1-main/")):
        continue
    md.append(rp)
print("B0. markdown files on disk (vault scope, excl .obsidian):", len(md))
print("    declared record notes:", len(rec_paths), "declared hubs:", len(hub_paths))
und = sorted(set(md) - rec_paths - hub_paths - {
    "START HERE.md", "01 Dashboards/Activity Dashboard.md", "01 Dashboards/Document Library.md",
    "01 Dashboards/Timeline.md", "01 Dashboards/Review Queue.md", "90 Archive/Archive Index.md",
    "99 Templates/Activity Template.md", "99 Templates/Record Template.md"})
print("    on-disk md not declared and not known navigation:", und)
miss = sorted(rec_paths | hub_paths - set(md))
print("    declared notes absent on disk:", sorted((rec_paths | hub_paths) - set(md)))

# ---- record notes ----
cur_roles = {"primary", "alternative-format"}
for r in records:
    nid = r["key"]
    p = ROOT / r["note_path"]
    if not p.is_file():
        problems.append(f"[{nid}] note missing on disk")
        continue
    text = p.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        problems.append(f"[{nid}] no frontmatter")
        fm = ""

    # 1. last level-two heading
    h2s = H2.findall(body)
    h2s = [ln for ln in body.splitlines() if ln.startswith("## ")]
    if not h2s or h2s[-1].strip() != "## Original document":
        problems.append(f"[{nid}] final H2 is {h2s[-1:]!r}, not '## Original document'")

    # 2. Original document section content
    idx = body.rfind("\n## Original document")
    od = body[idx:] if idx >= 0 else ""

    # current sources per manifest: source_keys
    src = [files[k] for k in r["source_keys"]]
    for s in src:
        cp = s["current_path"]
        name = Path(cp).name
        inlink = f"[[{cp}" in od or f"[[{cp}]]" in od
        inembed = f"![[{cp}]]" in od
        if not inlink:
            # try bare-name link
            bare = any(t.split("|")[0].split("#")[0].strip() in (cp, name) for t in WIKI.findall(od))
            if not bare:
                problems.append(f"[{nid}] source {cp} NOT linked/embedded inside Original document section")
                continue
        if cp.lower().endswith(".pdf") and not inembed:
            problems.append(f"[{nid}] PDF source {cp} present but not embedded as ![[...]]")
        if cp.lower().endswith(".docx"):
            if "![[%s]]" % cp in od:
                problems.append(f"[{nid}] DOCX source {cp} embedded (should be a link)")
            if f"[[{cp}|Open original DOCX: {name}]]" not in od:
                problems.append(f"[{nid}] DOCX {cp} lacks explicit 'Open original DOCX: {name}' link with exact filename")

    # 3. any file on disk mapping to this record with current role but NOT in source_keys
    extra = [e for e in data["files"]
             if e.get("record_key") == nid and e["role"] in cur_roles and e["key"] not in r["source_keys"]]
    if extra:
        problems.append(f"[{nid}] current-role files not listed in source_keys: {[e['key'] for e in extra]}")
    # and whether they still appear in the Original document section
    for e in extra:
        if e["current_path"] not in od:
            problems.append(f"[{nid}] unlisted current file {e['current_path']} also absent from Original document section")

    # 4. frontmatter source_path / source_format truthfulness
    sp = re.search(r'^source_path:\s*"?(.*?)"?$', fm, re.M)
    sf = re.search(r'^source_format:\s*"?(.*?)"?$', fm, re.M)
    sfile = re.search(r'^source_file:\s*"?(.*?)"?$', fm, re.M)
    if not sp or not sf:
        problems.append(f"[{nid}] frontmatter missing source_path/source_format")
    else:
        spv, sfv = sp.group(1), sf.group(1)
        if spv == "":
            problems.append(f"[{nid}] frontmatter source_path EMPTY")
        elif not (ROOT / spv).is_file():
            problems.append(f"[{nid}] frontmatter source_path does not exist: {spv}")
        elif Path(spv).suffix[1:].lower() != sfv:
            problems.append(f"[{nid}] source_format {sfv!r} != suffix of {spv}")
        elif sfile and Path(sfile.group(1)).name != Path(spv).name:
            problems.append(f"[{nid}] source_file {sfile.group(1)} != basename(source_path)")
        # primary source_path must be one of the record's sources
        if spv and spv not in {s["current_path"] for s in src}:
            problems.append(f"[{nid}] source_path {spv} is not among the record's own sources")
    if "type: record" not in fm:
        problems.append(f"[{nid}] frontmatter lacks type: record")
    # sources: block in fm lists each source
    for s in src:
        if s["current_path"] not in fm:
            problems.append(f"[{nid}] structured sources list omits {s['current_path']}")

print(f"B1. record notes checked: {len(records)}; problems so far: {len(problems)}")

# ---- hubs ----
recs_by_activity = {}
for r in records:
    recs_by_activity.setdefault(r["activity"], []).append(r)

for a in activities:
    p = ROOT / a["hub_path"]
    aid = a["key"]
    if not p.is_file():
        problems.append(f"[hub {aid}] missing on disk")
        continue
    text = p.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if "type: activity" not in (fm or ""):
        problems.append(f"[hub {aid}] frontmatter lacks type: activity")
    for r in recs_by_activity.get(aid, []):
        if f"[[{r['note_path']}" not in text:
            problems.append(f"[hub {aid}] does not link record note {r['note_path']}")
    # organizers stated
    if not re.search(r"rganizer", body):
        problems.append(f"[hub {aid}] no organizers statement found")
    h2s = [ln for ln in body.splitlines() if ln.startswith("## ")]
    if not h2s or h2s[-1].strip() != "## Missing stages":
        problems.append(f"[hub {aid}] final H2 is {h2s[-1:]!r}, not '## Missing stages'")
    print_missing = "Not present in the supplied records" in body

# orphan records: activity key not resolving
for r in records:
    if r["activity"] and r["activity"] not in {a["key"] for a in activities}:
        problems.append(f"[{r['key']}] activity key unresolved: {r['activity']}")

# records with no activity should live in 03/04
for r in records:
    if r["activity"] is None and r["note_path"].startswith("02 Activities/"):
        problems.append(f"[{r['key']}] no activity yet filed under 02 Activities")
    if r["activity"] is not None and not r["note_path"].startswith("02 Activities/"):
        problems.append(f"[{r['key']}] has activity {r['activity']} but filed at {r['note_path']}")

print(f"B2. hubs checked: {len(activities)}; records checked: {len(records)}")
print(f"B3. TOTAL PROBLEMS: {len(problems)}")
for x in problems:
    print("   -", x)

# hub-to-record coverage: every activity has >=1 record?
print("B4. activities with zero linked records:",
      [a["key"] for a in activities if not recs_by_activity.get(a["key"])])
print("B5. records per activity:", {a["key"]: len(recs_by_activity.get(a["key"], [])) for a in activities})
