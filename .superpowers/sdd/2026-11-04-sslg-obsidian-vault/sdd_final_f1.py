"""Final review F1: reachability (clean scope), collision disclosure, nfsslg date evidence."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
WIKI = re.compile(r"!?\[\[([^\]|#]+)")


def relp(p):
    return p.relative_to(ROOT).as_posix()


md = [p for p in ROOT.rglob("*.md")
      if not relp(p).startswith((".superpowers/", "docs/", "Scheduler_v1-main/", ".obsidian/"))]
base = [p for p in ROOT.rglob("*.base") if not relp(p).startswith((".superpowers/", "docs/"))]
scope = md + base
print("F1a. clean vault scope: md =", len(md), "| base =", len(base))

index = {}
for p in scope:
    for t in WIKI.findall(p.read_text(encoding="utf-8", errors="replace")):
        t = t.strip().rstrip(".md")
        index.setdefault(t, set()).add(relp(p))
        index.setdefault(Path(t).name, set()).add(relp(p))


def inbound(target):
    a = index.get(target, set())
    b = index.get(Path(target).name, set())
    return sorted((a | b) - {target})


print("\nF1b. inbound links (excluding self) for navigation and asset targets")
targets = ["90 Archive/Archive Index.md", "99 Templates/Activity Template.md", "99 Templates/Record Template.md"]
targets += sorted(e["current_path"] for e in data["files"] if e["current_path"].startswith("80 Assets/"))
targets += ["01 Dashboards/SSLG Records.base", "START HERE.md"]
for t in targets:
    ib = inbound(t)
    print(f"   inbound={len(ib):2d} | {t} | {ib}")

print("\nF1c. text evidence for OM-NFSSLG-2026-001 (primary is image-only)")
merged = ROOT / "90 Archive/Revisions/Memorandum-OM-NFSSLG-2026-001_signed-2-merged.pdf"
t = subprocess.run(["pdftotext", str(merged), "-"], capture_output=True).stdout.decode("utf-8", "replace")
flat = re.sub(r"\s+", " ", t)
print("   merged PDF extracted chars:", len(t.strip()))
print("   contains 'OM-NFSSLG-2026-001':", bool(re.search(r"OM[\s\-]?NFSSLG[\s\-]?2026[\s\-]?001", flat, re.I)))
print("   contains a 25 August date:", bool(re.search(r"25\s+(?:th\s+)?August\s+2026|August\s+25,?\s+2026", flat, re.I)))
for m in re.finditer(r"25\s+(?:th\s+)?August\s+2026|August\s+25,?\s+2026", flat, re.I):
    print("      ...", flat[max(0, m.start() - 120):m.end() + 60])
sig = ROOT / "04 External Memoranda/Sources/Memorandum-OM-NFSSLG-2026-001_signed-2.pdf"
ts = subprocess.run(["pdftotext", str(sig), "-"], capture_output=True).stdout.decode("utf-8", "replace")
print("   primary signed PDF extracted chars:", len(ts.strip()), "(0 = image-only, matches note disclosure)")

print("\nF1d. number-collision disclosure in the ECOLEAD / survey notes")
keys = ["om-sslg-2026-002-ecolead", "om-sslg-2026-002-survey-aug27", "om-sslg-2026-002-survey-aug28", "om-sslg-2026-003-ecolead"]
recs = {r["key"]: r for r in data["records"]}
for k in keys:
    t = (ROOT / recs[k]["note_path"]).read_text(encoding="utf-8")
    hits = [l.strip() for l in t.splitlines() if re.search(r"collision|same number|number\b.*conflict|not a citation|different sequence", l, re.I)]
    print(f"   [{k}] disclosure lines: {len(hits)}")
    for h in hits:
        print("       ", h[:175])

print("\nF1e. needs-review coverage sets")
rs = [r for r in data["records"] if r["status"] == "needs-review"]
rr = [r for r in data["records"] if r.get("review_reasons")]
asl = [a for a in data["activities"] if a["status"] == "needs-review"]
arr = [a for a in data["activities"] if a.get("review_reasons")]
print("   records: status needs-review", len(rs), "| with reasons", len(rr),
      "| status-only (not in queue obligations)", [r['key'] for r in rs if not r.get('review_reasons')],
      "| reasons-only (other status)", [(r['key'], r['status']) for r in rr if r['status'] != 'needs-review'])
print("   activities: status needs-review", len(asl), "| with reasons", len(arr),
      "| reasons-only", [(a['key'], a['status']) for a in arr if a['status'] != 'needs-review'])
print("   statuses of the reasons-only activities:", Counter := dict(((a['status'], sum(1 for x in arr if x['status'] == a['status'])) for a in arr)))

print("\nF1f. do the 11 reasons-only activities appear in Review Queue headings?")
queue = (ROOT / "01 Dashboards/Review Queue.md").read_text(encoding="utf-8")
heads = re.findall(r"^###\s+\[\[(.+?)\]\]", queue, re.M)
print("   queue '###' link headings:", len(heads))
missing = [a["hub_path"] for a in arr if not any(a["hub_path"].rstrip(".md") in h or Path(a["hub_path"]).stem in h for h in heads)]
print("   flagged activities with no queue heading:", missing)
missing_r = [r["note_path"] for r in rr if not any(r["note_path"].rstrip(".md") in h or Path(r["note_path"]).stem in h for h in heads)]
print("   flagged records with no queue heading:", missing_r)
