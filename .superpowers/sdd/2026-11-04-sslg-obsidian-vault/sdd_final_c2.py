"""Final review C2: refined stale-reference / ambiguity measurements (read-only)."""
import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
files = data["files"]
basenames = defaultdict(list)
for e in files:
    basenames[Path(e["current_path"]).name.lower()].append(e["current_path"])
    basenames[Path(e["original_path"]).name.lower()].append(e["current_path"])
WIKI = re.compile(r"!?\[\[([^\]]+?)\]\]")

md = [p for p in ROOT.rglob("*.md")
      if not str(p.relative_to(ROOT)).startswith((".superpowers/", "docs/", "Scheduler_v1-main/", ".obsidian/"))]
basecount = defaultdict(int)
for e in files:
    basecount[Path(e["current_path"]).name.lower()] += 1

ambiguous = {n for n, lst in basenames.items() if len(set(lst)) > 1}
print("C2a. basenames that map to >1 manifest current_path:", len(ambiguous))
for n in sorted(ambiguous):
    print("   ", n, "->", sorted(set(basenames[n])))

print("\nC2b. wikilink targets that are BARE basenames (Obsidian 'shortest path' links)")
bare = []
for p in md:
    rel = p.relative_to(ROOT).as_posix()
    if rel == "90 Archive/Archive Index.md":
        continue
    t = p.read_text(encoding="utf-8")
    for m in WIKI.finditer(t):
        tgt = m.group(1).split("|")[0].split("#")[0].strip()
        if "/" not in tgt and re.search(r"\.(docx|pdf|png)$", tgt, re.I):
            key = tgt.lower()
            bare.append((rel, tgt, len(set(basenames.get(key, []))), "AMBIGUOUS" if key in ambiguous else ""))
print("   count:", len(bare))
for b in bare[:20]:
    print("   ", b)

print("\nC2c. prose (frontmatter stripped, links removed) that still names an original filename")
NAMEPAT = re.compile(r"\b[A-Z0-9][A-Za-z0-9._\-\s]{0,60}?\.(?:docx|pdf|png)\b", re.I)
rows = []
for p in md:
    rel = p.relative_to(ROOT).as_posix()
    if rel == "90 Archive/Archive Index.md":
        continue
    t = p.read_text(encoding="utf-8")
    body = re.sub(r"^---.*?\n---\n", "", t, flags=re.S)
    stripped = WIKI.sub(" ", body)
    for line in stripped.splitlines():
        for m in NAMEPAT.finditer(line):
            tok = m.group(0).strip()
            key = tok.lower()
            if key in basenames:
                rows.append((rel, tok, "resolvable-as-bare" if len(set(basenames[key])) == 1 else
                             ("AMBIGUOUS" if key in ambiguous else "NOT-ON-DISK")))
from collections import Counter
print("   mentions:", len(rows), Counter(r[2] for r in rows))
per = Counter(r[0] for r in rows)
print("   files with mentions:", len(per))
for f, c in per.most_common(12):
    print("      ", c, f)
print("   sample:")
for r in rows[:12]:
    print("      ", r)

print("\nC2d. references to pre-migration root paths (stale originals)")
stale = []
for p in md:
    rel = p.relative_to(ROOT).as_posix()
    if rel == "90 Archive/Archive Index.md":
        continue
    t = p.read_text(encoding="utf-8")
    for e in files:
        op = e["original_path"]
        if op == e["current_path"]:
            continue
        for m in re.finditer(re.escape(op), t):
            stale.append((rel, op))
print("   stale original-path mentions outside Archive Index:", len(stale))
for s in stale[:15]:
    print("   ", s)

print("\nC2e. records with no activity: filing location vs spec 05 General Records")
for r in data["records"]:
    if not r.get("activity"):
        print("   ", r["key"], r["record_type"], "|", r["note_path"])
