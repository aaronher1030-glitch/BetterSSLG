"""Final review C + D: link integrity beyond validator, reachability, template checks."""
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
WIKI = re.compile(r"!?\[\[([^\]]+?)\]\]")
MDLINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
CODEPATH = re.compile(r"`([^`\n]*?/[^`\n]*?)`")

rec_notes = {r["note_path"] for r in data["records"]}
hub_notes = {a["hub_path"] for a in data["activities"]}
nav = {"START HERE.md", "01 Dashboards/Activity Dashboard.md",
       "01 Dashboards/Document Library.md", "01 Dashboards/Timeline.md",
       "01 Dashboards/Review Queue.md", "90 Archive/Archive Index.md",
       "99 Templates/Activity Template.md", "99 Templates/Record Template.md"}
scan_scope = rec_notes | hub_notes | nav

on_disk = set()
for p in ROOT.rglob("*"):
    if p.is_file():
        rp = p.relative_to(ROOT).as_posix()
        if not rp.startswith((".superpowers/", ".obsidian/")) and "__pycache__" not in rp:
            on_disk.add(rp)

names_on_disk = {Path(x).name for x in on_disk}


def resolves(t):
    t = t.split("|")[0].split("#")[0].strip()
    if not t:
        return True
    if (ROOT / t).exists():
        return True
    if not Path(t).suffix and (ROOT / (t + ".md")).exists():
        return True
    if Path(t).name in names_on_disk:
        return "byname"
    return False


print("C1. wikilinks in files the validator does NOT scan")
for rel in ["90 Archive/Archive Index.md", "99 Templates/Activity Template.md",
            "99 Templates/Record Template.md"]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    tgts = WIKI.findall(text)
    broken = [t for t in tgts if resolves(t) is False]
    print(f"  {rel}: {len(tgts)} wikilinks, unresolvable={len(broken)} {broken}")

allmd = sorted(x for x in on_disk if x.endswith((".md", ".base"))
               and not x.startswith(("Scheduler_v1-main/", "docs/", "tools/", ".superpowers/")))
print("C2. md/base files in vault scope:", len(allmd))
bad_total = []
for rel in allmd:
    text = (ROOT / rel).read_text(encoding="utf-8")
    for t in WIKI.findall(text):
        if resolves(t) is False:
            bad_total.append((rel, t))
print("  unresolvable wikilinks across every vault md/base:", len(bad_total))
for x in bad_total[:40]:
    print("    ", x)

print("C3. path-shaped strings (code spans / md links) that must resolve")
pathlike_bad = []
for rel in allmd:
    text = (ROOT / rel).read_text(encoding="utf-8")
    for m in list(CODEPATH.findall(text)) + list(MDLINK.findall(text)):
        s = m.strip()
        if not s or s.startswith(("http", "mailto", "#")) or "/" not in s:
            continue
        if not ((ROOT / s).exists() or Path(s).name in names_on_disk):
            pathlike_bad.append((rel, s))
print("  non-resolving path-shaped strings:", len(pathlike_bad))
for x in pathlike_bad[:60]:
    print("    ", x)

print("C4. standalone original root-filename mentions")
orig = sorted({e["original_path"] for e in data["files"]})
hits = []
for rel in allmd:
    text = (ROOT / rel).read_text(encoding="utf-8")
    for name in orig:
        base = Path(name).name
        for m in re.finditer(r"(?<![\w/.\-])" + re.escape(base) + r"(?![\w.\-])", text):
            ctx = text[max(0, m.start() - 80):m.end() + 5].replace("\n", " ")
            preceded_by_dir = bool(re.search(r"[\w\-\.]/\s*$", text[max(0, m.start()-60):m.start()]))
            hits.append((rel, base, preceded_by_dir, ctx[-85:]))
print("  mentions:", len(hits), "of which appear as a bare (root-style) name:",
      sum(1 for h in hits if not h[2]))
for h in hits:
    if not h[2]:
        print("     BARE:", h[0], "|", h[1], "|", h[3])

print("C5. reachability of every created file")
linkers = {}
for rel in allmd:
    text = (ROOT / rel).read_text(encoding="utf-8")
    for t in WIKI.findall(text):
        t = t.split("|")[0].split("#")[0].strip()
        linkers.setdefault(t, set()).add(rel)
        linkers.setdefault(Path(t).name, set()).add(rel)
arch = (ROOT / "90 Archive/Archive Index.md").read_text(encoding="utf-8")
unreach = []
for rel in sorted(scan_scope):
    inc = (linkers.get(rel, set()) | linkers.get(Path(rel).name, set())) - {rel}
    plain = Path(rel).name in arch or rel in arch
    if not inc and not plain:
        unreach.append(rel)
print("  created files with no inbound reference:", len(unreach))
for x in unreach:
    print("    UNREACHED:", x)

print("C6. inbound counts for navigation pages")
for rel in sorted(nav) + ["01 Dashboards/SSLG Records.base"]:
    refs = (linkers.get(rel, set()) | linkers.get(Path(rel).name, set())) - {rel}
    print(f"  {rel}: inbound={len(refs)} {sorted(refs)[:5]} inArchiveIndex={Path(rel).name in arch}")

print("C7. 80 Assets PNG reachability")
for p in sorted(x for x in on_disk if x.startswith("80 Assets/")):
    refs = (linkers.get(p, set()) | linkers.get(Path(p).name, set())) - {p}
    print(f"  {p}: inbound={len(refs)} {sorted(refs)[:3]}")

print("C8. archive files vs Archive Index rows")
archfiles = sorted(x for x in on_disk if x.startswith("90 Archive/")
                   and not x.endswith((".md", ".json")))
norow = [x for x in archfiles if Path(x).name not in arch]
print("  archive files:", len(archfiles), "| not named in index:", len(norow), norow)
rows = [l for l in arch.splitlines() if l.startswith("| ") and l.count("|") == 5]
print("  index table data rows (excl header/sep):", len(rows))

print("C9. manifest paths present in Archive Index")
missing = [e["current_path"] for e in data["files"] if Path(e["current_path"]).name not in arch]
print("  manifest files not named in Archive Index:", len(missing), missing)
missing_orig = [e["original_path"] for e in data["files"] if Path(e["original_path"]).name not in arch]
print("  original names not named in Archive Index:", len(missing_orig), missing_orig)
