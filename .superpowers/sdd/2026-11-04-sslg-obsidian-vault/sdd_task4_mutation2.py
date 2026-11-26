import io
import json
import sys
import unittest
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path("C:/Users/Ma Christine/Downloads/SSLG MEMOS")
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402
from tools import sslg_navigation as nav  # noqa: E402
import tools.tests.test_sslg_navigation as tsn  # noqa: E402

DATA = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(tsn)
    res = unittest.TestResult()
    suite(res)
    return res


def report(label, r):
    fails = sorted({str(t).split()[0] for t, _ in r.failures + r.errors})
    print(f"{label}: run={r.testsRun} failures+errors={len(fails)} -> {fails}")


# --- Proper mutation C: renderer emits only the FIRST review reason ---
def render_review_queue_first_only(data):
    flagged_activities = [a for a in data["activities"]
                          if a["status"] == "needs-review" or a.get("review_reasons")]
    flagged_records = [r for r in data["records"]
                       if r["status"] == "needs-review" or r.get("review_reasons")]
    lines = ["# Review Queue", ""]
    for record in sorted(flagged_records, key=lambda r: r["title"]):
        lines.append(f"### [[{record['note_path']}|{record['title']}]]")
        lines.extend(f"  - {reason}" for reason in record["review_reasons"][:1])
    for activity in sorted(flagged_activities, key=lambda a: a["title"]):
        lines.append(f"### [[{activity['hub_path']}|{activity['title']}]]")
        lines.extend(f"  - {reason}" for reason in activity["review_reasons"][:1])
    return "\n".join(lines) + "\n"


tsn.render_review_queue = render_review_queue_first_only
report("C2 first-reason-only renderer:", run_tests())
tsn.render_review_queue = nav.render_review_queue

# --- Proper mutation D: status-only inclusion (drops reason-but-not-needs-review) ---
def render_review_queue_status_only(data):
    flagged_activities = [a for a in data["activities"] if a["status"] == "needs-review"]
    flagged_records = [r for r in data["records"] if r["status"] == "needs-review"]
    lines = ["# Review Queue", ""]
    for record in sorted(flagged_records, key=lambda r: r["title"]):
        lines.append(f"### [[{record['note_path']}|{record['title']}]]")
        lines.extend(f"  - {reason}" for reason in record["review_reasons"])
    for activity in sorted(flagged_activities, key=lambda a: a["title"]):
        lines.append(f"### [[{activity['hub_path']}|{activity['title']}]]")
        lines.extend(f"  - {reason}" for reason in activity["review_reasons"])
    return "\n".join(lines) + "\n"


tsn.render_review_queue = render_review_queue_status_only
report("D2 status-only renderer:", run_tests())
tsn.render_review_queue = nav.render_review_queue

# --- Proper mutation: render_timeline without sorting (renderer body copied) ---
def render_timeline_unsorted(data):
    records = data["records"]
    activities = list(data["activities"])  # unsorted, in data order
    events = [r for r in records if r.get("event_date")]
    issued = [r for r in records if r.get("date")]
    undated = [r for r in records if not r.get("date")]
    hubs = {a["key"]: a for a in data["activities"]}
    lines = ["# Timeline", "## Activity schedule", "| --- |"]
    for a in activities:
        lines.append(f"| {a['start_date']} | [[{a['hub_path']}|{a['title']}]] |")
    lines.append("## Activity and meeting dates")
    for r in events:
        hub = hubs.get(r.get("activity"))
        lines.append(f"| {r['event_date']} | [[{r['note_path']}|{r['title']}]] "
                     f"| [[{hub['hub_path']}|{hub['title']}]] |" if hub else
                     f"| {r['event_date']} | [[{r['note_path']}|{r['title']}]] |Not tied|")
    lines.append("## Record issuance dates")
    for r in issued:
        lines.append(f"| {r['date']} | [[{r['note_path']}|{r['title']}]] |")
    if undated:
        lines.append("### Records with no issuance date stated in source")
        for r in undated:
            lines.append(f"- [[{r['note_path']}|{r['title']}]]")
    return "\n".join(lines) + "\n"


tsn.render_timeline = render_timeline_unsorted
report("Timeline unsorted renderer:", run_tests())
tsn.render_timeline = nav.render_timeline

# --- baseline re-confirm untouched ---
report("baseline:", run_tests())

# --- Section I fixed: template vs generated note frontmatter ---
rec_note = (ROOT / next(r["note_path"] for r in DATA["records"] if r["collection"] == "governance")).read_text(encoding="utf-8")
note_props = list(yaml.safe_load(rec_note.split("---\n")[1]).keys())
tpl_text = (ROOT / "99 Templates/Record Template.md").read_text(encoding="utf-8")
tpl_props = list(yaml.safe_load(tpl_text.split("---\n")[1]).keys())
print("record note props :", note_props)
print("template props    :", tpl_props)
print("same names+order  :", note_props == tpl_props)
note_secs = [l for l in rec_note.splitlines() if l.startswith("## ")]
tpl_secs = [l for l in tpl_text.splitlines() if l.startswith("## ")]
print("note sections:", note_secs)
print("tpl sections :", tpl_secs)
print("section order match:", note_secs == tpl_secs)

hub_text = (ROOT / DATA["activities"][0]["hub_path"]).read_text(encoding="utf-8")
hub_secs = [l for l in hub_text.splitlines() if l.startswith("## ")]
atpl = (ROOT / "99 Templates/Activity Template.md").read_text(encoding="utf-8")
atpl_secs = [l for l in atpl.splitlines() if l.startswith("## ")]
print("hub sections:", hub_secs)
print("hub template order match:", hub_secs == atpl_secs)
print("hub At a glance:", [l for l in hub_text.splitlines() if l.startswith("> **")])
print("hub frontmatter props:", list(yaml.safe_load(hub_text.split('---\n')[1]).keys()))
print("atpl frontmatter    :", list(yaml.safe_load(atpl.split('---\n')[1]).keys()))
# organizers present in real data?
orgs = {a["title"]: a["organizers"] for a in DATA["activities"]}
print("activities with organizers:", sum(1 for v in orgs.values() if v), "of", len(orgs))
# check a hub that has organizers shows them
for a in DATA["activities"]:
    if a["organizers"]:
        t = (ROOT / a["hub_path"]).read_text(encoding="utf-8")
        line = [l for l in t.splitlines() if l.startswith("> **Organizers")]
        print("example organizers line:", line)
        break

# --- Multi-reason entities in real data (guarded by tests?) ---
multi_rec = [(r["title"], len(r["review_reasons"])) for r in DATA["records"] if len(r.get("review_reasons", [])) > 1]
multi_act = [(a["title"], len(a["review_reasons"])) for a in DATA["activities"] if len(a.get("review_reasons", [])) > 1]
print("records with >1 reason:", multi_rec)
print("activities with >1 reason:", multi_act)
# do reason-only (non needs-review status) entities exist?
reason_only_recs = [r["title"] for r in DATA["records"] if r["status"] != "needs-review" and r.get("review_reasons")]
reason_only_acts = [a["title"] for a in DATA["activities"] if a["status"] != "needs-review" and a.get("review_reasons")]
print("reason-only records:", reason_only_recs)
print("reason-only activities count:", len(reason_only_acts))

# --- NAVIGATION_PATHS usage ---
for p in ROOT.rglob("*.py"):
    if "Scheduler_v1-main" in str(p):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "NAVIGATION_PATHS" in t:
        print("NAVIGATION_PATHS referenced in", p.relative_to(ROOT))

# --- 05 General Records ---
g5 = ROOT / "05 General Records"
print("05 General Records exists:", g5.exists(),
      "children:", sorted(c.name for c in g5.iterdir()) if g5.exists() else None)

# --- Review-required callout placement in queue vs record notes: check one needs-review record note has reasons too
rn = next(r for r in DATA["records"] if len(r.get("review_reasons", [])) > 1)
note = (ROOT / rn["note_path"]).read_text(encoding="utf-8")
print("all reasons of", rn["title"][:40], "in its note:", all(x in note for x in rn["review_reasons"]))
