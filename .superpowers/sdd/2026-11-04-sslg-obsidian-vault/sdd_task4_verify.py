import hashlib
import io
import json
import sys
import unittest.mock
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path("C:/Users/Ma Christine/Downloads/SSLG MEMOS")
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402  (PyYAML 6.0.3 verified installed)
from tools import sslg_navigation as nav  # noqa: E402

DATA = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))

outputs = {
    "START HERE.md": nav.render_home(DATA),
    "01 Dashboards/Activity Dashboard.md": nav.render_activity_dashboard(DATA),
    "01 Dashboards/Document Library.md": nav.render_document_library(),
    "01 Dashboards/Timeline.md": nav.render_timeline(DATA),
    "01 Dashboards/Review Queue.md": nav.render_review_queue(DATA),
    "01 Dashboards/SSLG Records.base": nav.BASES_YAML,
    "99 Templates/Activity Template.md": nav.render_activity_template(),
    "99 Templates/Record Template.md": nav.render_record_template(),
    ".obsidian/templates.json": json.dumps({"folder": "99 Templates"}, indent=2) + "\n",
}

print("== 1. Generated files on disk match renderer output byte-for-byte ==")
for rel, text in outputs.items():
    disk = (ROOT / rel).read_text(encoding="utf-8")
    print(f"{rel}: {'MATCH' if disk == text else 'DIFFER'}")
    if disk != text:
        print("   disk sha:", hashlib.sha256(disk.encode()).hexdigest()[:12],
              "render sha:", hashlib.sha256(text.encode()).hexdigest()[:12])

print("\n== 2. NAVIGATION_PATHS consistency ==")
print("keys == set(NAVIGATION_PATHS):", set(outputs) == set(nav.NAVIGATION_PATHS))
print("NAVIGATION_PATHS used by generate_navigation:",
      "generate_navigation" in open(ROOT / "tools/sslg_navigation.py", encoding="utf-8").read().split("def generate_navigation")[1].replace("NAVIGATION_PATHS", "X") is False)
src_gen = open(ROOT / "tools/sslg_navigation.py", encoding="utf-8").read().split("def generate_navigation")[1]
print("   reference to NAVIGATION_PATHS inside generate_navigation:", "NAVIGATION_PATHS" in src_gen)

print("\n== 3. BASES_YAML parses as YAML; structure check ==")
base_doc = yaml.safe_load(outputs["01 Dashboards/SSLG Records.base"])
print("parsed OK:", type(base_doc).__name__)
print("global filter:", base_doc["filters"])
views = {v["name"]: v for v in base_doc["views"]}
print("view names:", list(views))
brief_order = {
    "All records": ["title", "record_type", "record_id", "date", "event_date", "activity", "status", "source_file"],
    "Proposals": ["title", "event_date", "activity", "status", "source_file"],
    "Completion reports": ["title", "event_date", "activity", "status", "source_file"],
    "Memoranda": ["title", "record_id", "date", "status", "source_file"],
    "Needs review": ["title", "record_type", "record_id", "source_file"],
}
for name, order in brief_order.items():
    v = views[name]
    ok = v["type"] == "table" and v["order"] == order and v["filters"]["and"][0] == 'type == "record"'
    print(f"  {name}: type/order/view-filter ok = {ok}")
print("  Needs review second filter:", views["Needs review"]["filters"]["and"])
print("  Proposals second filter:", views["Proposals"]["filters"]["and"])
print("  Completion second filter:", views["Completion reports"]["filters"]["and"])
print("  Memoranda second filter:", views["Memoranda"]["filters"]["and"])

print("\n== 4. Templates frontmatter parses as YAML ==")
for rel in ("99 Templates/Activity Template.md", "99 Templates/Record Template.md"):
    fm = outputs[rel].split("---\n")[1]
    parsed = yaml.safe_load(fm)
    print(rel, "->", parsed)

print("\n== 5. Exact required copy strings ==")
required = ("Original documents remain unchanged. Summaries are navigation aids; "
            "use the Original document section for the complete official formatting.")
print("UNCHANGED_NOTICE exact:", nav.UNCHANGED_NOTICE == required)
print("in START HERE:", required in outputs["START HERE.md"])
print("embed in Document Library:", "![[01 Dashboards/SSLG Records.base]]" in outputs["01 Dashboards/Document Library.md"])

print("\n== 6. Review Queue coverage vs content.json ==")
rq = outputs["01 Dashboards/Review Queue.md"]
recs_flagged = [r for r in DATA["records"] if r["status"] == "needs-review" or r.get("review_reasons")]
acts_flagged = [a for a in DATA["activities"] if a["status"] == "needs-review" or a.get("review_reasons")]
print(f"flagged records: {len(recs_flagged)}, flagged activities: {len(acts_flagged)}")
print("header line:", [l for l in rq.splitlines() if l.startswith("Needs review:")])
missing = []
for r in recs_flagged:
    if f"[[{r['note_path']}|{r['title']}]]" not in rq:
        missing.append(("record link", r["title"]))
    for reason in r["review_reasons"]:
        if reason not in rq:
            missing.append(("record reason", r["title"], reason[:60]))
for a in acts_flagged:
    if f"[[{a['hub_path']}|{a['title']}]]" not in rq:
        missing.append(("activity link", a["title"]))
    for reason in a["review_reasons"]:
        if reason not in rq:
            missing.append(("activity reason", a["title"], reason[:60]))
print("missing entries:", missing if missing else "NONE — all flagged records/activities and every reason present")
# any needs-review record WITHOUT reasons would crash the list comprehension? check
no_reason = [r["title"] for r in DATA["records"] if r["status"] == "needs-review" and not r["review_reasons"]]
print("needs-review records with empty reasons:", no_reason)
no_reason_a = [a["title"] for a in DATA["activities"] if a["status"] == "needs-review" and not a["review_reasons"]]
print("needs-review activities with empty reasons:", no_reason_a)

print("\n== 7. Activity Dashboard counts & order ==")
ad = outputs["01 Dashboards/Activity Dashboard.md"]
counts = {}
for r in DATA["records"]:
    if r["activity"]:
        counts[r["activity"]] = counts.get(r["activity"], 0) + 1
rows = [l for l in ad.splitlines() if l.startswith("| [[02 Activities")]
print("row count:", len(rows))
ok = True
prev = None
for row, a in zip(rows, sorted(DATA["activities"], key=lambda x: (0 if x["start_date"] else 1, x["start_date"] or "", x["title"]))):
    want = f"| {counts.get(a['key'], 0)} |"
    if want not in row:
        ok = False
        print("count mismatch", a["title"], want, row)
    d = a["start_date"]
    if prev is not None and d and prev and d < prev:
        ok = False
        print("order violation", a["title"])
    if d is not None and prev is None and False:
        pass
    prev = d if (prev is None or (d and prev)) else prev
print("counts+order consistent:", ok)
dated = [a for a in DATA["activities"] if a["start_date"]]
undated = [a for a in DATA["activities"] if not a["start_date"]]
print("undated activities all appear last:",
      rows.index(next(r for r in rows if "Cluster IV SSLG Federation Leadership Training Camp.md|" in r)) == len(dated))
print("last rows count check:", len(rows) - len(dated) == len(undated))
print("activity-tied records:", sum(counts.values()), "untied:", len(DATA["records"]) - sum(counts.values()))

print("\n== 8. START HERE counts and collection sort ==")
sh = outputs["START HERE.md"]
print("counts line:", [l for l in sh.splitlines() if "logical records" in l])
gov = [r for r in DATA["records"] if r["collection"] == "governance"]
ext = [r for r in DATA["records"] if r["collection"] == "external"]
gen = [r for r in DATA["records"] if r["collection"] == "general"]
print("governance:", len(gov), "external:", len(ext), "general:", len(gen))
expected_sorted = sorted(gov, key=lambda r: (0 if r["event_date"] else 1, r["event_date"] or "", r["title"]))
gov_order = [l for l in sh.splitlines() if l.startswith("- [[03 Governance")]
for line, r in zip(gov_order, expected_sorted):
    if f"|{r['title']}]]" not in line:
        print("governance order violation:", line)
ext_order = [l for l in sh.splitlines() if l.startswith("- [[04 External")]
expected_ext = sorted(ext, key=lambda r: (0 if r["event_date"] else 1, r["event_date"] or "", r["title"]))
for line, r in zip(ext_order, expected_ext):
    if f"|{r['title']}]]" not in line:
        print("external order violation:", line)
print("governance event_dates:", [(r["title"][:30], r["event_date"]) for r in gov])
print("external event_dates:", [(r["title"][:30], r["event_date"]) for r in ext])

print("\n== 9. Timeline separation & determinism ==")
tl = outputs["01 Dashboards/Timeline.md"]
sched = tl.split("## Activity schedule")[1].split("## Activity and meeting dates")[0]
events = tl.split("## Activity and meeting dates")[1].split("## Record issuance dates")[0]
issu = tl.split("## Record issuance dates")[1]
ev_rows = [l for l in events.splitlines() if l.startswith("| ") and "[[" in l]
iss_rows = [l for l in issu.splitlines() if l.startswith("| ") and "[[" in l]
print("event rows:", len(ev_rows), "issuance rows:", len(iss_rows))
with_event = [r for r in DATA["records"] if r.get("event_date")]
with_date = [r for r in DATA["records"] if r.get("date")]
print("records with event_date:", len(with_event), "records with date:", len(with_date))
# check event table keys use event_date column only
viol = [r["title"] for r in with_event if f"| {r['event_date']} |" not in "\n".join(ev_rows)]
print("event rows missing/wrong-date:", viol)
viol2 = [r["title"] for r in with_date if f"| {r['date']} |" not in "\n".join(iss_rows)]
print("issuance rows missing/wrong-date:", viol2)
# sortedness
def rowdate(rows):
    return [l.split("|")[1].strip() for l in rows]
evd = rowdate(ev_rows)
isd = rowdate(iss_rows)
print("event dates nondecreasing:", all(a <= b for a, b in zip(evd, evd[1:])), evd[:4], "...")
print("issuance dates nondecreasing:", all(a <= b for a, b in zip(isd, isd[1:])) if "Not stated" not in isd else "check")
print("issuance dates:", isd)
undated_list = issu.split("### Records with no issuance date")[1] if "### Records with no issuance date" in issu else ""
und = [r for r in DATA["records"] if not r.get("date")]
print("undated records:", len(und), "listed bullets:", len([l for l in undated_list.splitlines() if l.startswith("- [[")]))
# records with date but no event date should not appear in event table
both_check = [r for r in DATA["records"] if r.get("date") and not r.get("event_date")]
for r in both_check:
    if f"| {r['date']} | [[{r['note_path']}" in "\n".join(ev_rows):
        print("LEAK: issuance date used in event table:", r["title"])
print("double-listed (date and event_date) records:",
      len([r for r in DATA["records"] if r.get("date") and r.get("event_date")]))

print("\n== 10. Determinism: re-render equals first render ==")
again = nav.render_activity_dashboard(DATA) == ad and nav.render_timeline(DATA) == tl and nav.render_home(DATA) == sh
print("stable:", again)

print("\n== 11. Preflight check in generate_navigation ==")
import tempfile
tmp = Path(tempfile.mkdtemp())
try:
    written = nav.generate_navigation(tmp, DATA)
    before = {p: p.read_text(encoding="utf-8") for p in written}
    try:
        nav.generate_navigation(tmp, DATA)
        print("second run raised FileExistsError: NO")
    except FileExistsError as e:
        print("second run raised FileExistsError: YES")
    after = {p: p.read_text(encoding="utf-8") for p in written}
    print("existing files untouched on refused run:", before == after)
    # partial-write test: pre-existing collision in one path only
    tmp2 = Path(tempfile.mkdtemp())
    (tmp2 / "START HERE.md").write_text("PRESERVE", encoding="utf-8")
    try:
        nav.generate_navigation(tmp2, DATA)
        print("collision run raised: NO")
    except FileExistsError as err:
        print("collision run raised: YES ->", str(err).splitlines()[0])
    print("collided file preserved:", (tmp2 / "START HERE.md").read_text(encoding="utf-8") == "PRESERVE")
    print("no other files written when refused:", sorted(p.relative_to(tmp2).as_posix() for p in tmp2.rglob("*") if p.is_file()))
    # mutation check: remove sort -> does dashboard test fail?
finally:
    pass

print("\n== 12. Mutation checks against test suite ==")
import tools.tests.test_sslg_navigation as tsn

def run_tests():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(tsn)
    stream = unittest.TestResult()
    res = suite.run()
    return res

orig_sorted = nav._sorted_by_date
def unsorted(items, key):
    return list(items)
nav._sorted_by_date = unsorted
r = run_tests()
print("without sorting: run=", r.testsRun, "failures+errors=", len(r.failures) + len(r.errors))
for t, tb in r.failures + r.errors:
    print("   fails:", t.id)
nav._sorted_by_date = orig_sorted

orig_gen = nav.generate_navigation
def no_preflight(root, data):
    written = []
    for path, text in [(root / rel, outputs[rel]) for rel in nav.NAVIGATION_PATHS]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written
nav.generate_navigation = no_preflight
r = run_tests()
print("without preflight: failures+errors=", len(r.failures) + len(r.errors), [t.id for t, _ in r.failures + r.errors])
nav.generate_navigation = orig_gen

# remove collection loop from home
r = run_tests()
print("baseline re-run: run=", r.testsRun, "failures+errors=", len(r.failures) + len(r.errors))
