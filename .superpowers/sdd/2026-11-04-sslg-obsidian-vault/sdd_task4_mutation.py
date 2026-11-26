import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path("C:/Users/Ma Christine/Downloads/SSLG MEMOS")
sys.path.insert(0, str(ROOT))

from tools import sslg_navigation as nav  # noqa: E402
import tools.tests.test_sslg_navigation as tsn  # noqa: E402

DATA = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(tsn)
    res = unittest.TestResult()
    suite(res)
    return res


def baseline():
    r = run_tests()
    print(f"  baseline: run={r.testsRun} failures={len(r.failures)} errors={len(r.errors)}")
    return r


def mutate_report(label, r):
    fails = [str(t).split()[0] for t, _ in r.failures + r.errors]
    print(f"{label}: run={r.testsRun} failures+errors={len(fails)} -> {sorted(set(fails))}")


print("== A. mutation: disable _sorted_by_date ==")
orig = nav._sorted_by_date
nav._sorted_by_date = lambda items, key: list(items)
mutate_report("no sorting:", run_tests())
nav._sorted_by_date = orig

print("== B. mutation: generate_navigation without preflight ==")
orig_gen = tsn.generate_navigation
def no_preflight(root, data):
    written = []
    for rel in nav.NAVIGATION_PATHS:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
        written.append(p)
    return written
tsn.generate_navigation = no_preflight
mutate_report("no preflight:", run_tests())
tsn.generate_navigation = orig_gen

print("== C. mutation: review queue keeps only first reason ==")
orig_rq = nav.render_review_queue
def first_reason_only(data):
    d = json.loads(json.dumps(data))
    for x in d["records"] + d["activities"]:
        if x.get("review_reasons"):
            x["review_reasons"] = x["review_reasons"][:1]
    return orig_rq(d)
tsn.render_review_queue = first_reason_only
r = run_tests()
mutate_report("only-first-reason:", r)
tsn.render_review_queue = orig_rq

print("== D. mutation: review queue filters status only (drops reason-only entities) ==")
def status_only(data):
    d = json.loads(json.dumps(data))
    d["records"] = [x for x in d["records"] if x["status"] != "needs-review" or not x.get("review_reasons")]
    return orig_rq({"activities": [a for a in data["activities"] if a["status"] == "needs-review" or a.get("review_reasons")],
                    "records": [x for x in data["records"] if x["status"] == "needs-review"],
                    "files": data["files"]})
tsn.render_review_queue = status_only
mutate_report("status-only:", run_tests())
tsn.render_review_queue = orig_rq

print("== E. mutation: home drops route lines but keeps headings ==")
orig_home = nav.render_home
def home_headings_only(data):
    text = orig_home(data)
    out = []
    for line in text.splitlines():
        if line.startswith("- [[").replace("- [[01 Dashboards/", "- [[KEEP"):
            pass
        if "- [[01 Dashboards/" in line:
            continue  # drop the four route bullets
        out.append(line)
    return "\n".join(out) + "\n"
tsn.render_home = home_headings_only
mutate_report("routes removed:", run_tests())
tsn.render_home = orig_home

def home_no_collections(data):
    text = orig_home(data)
    # remove the per-record listing lines under collection headings, keep headings
    out = []
    skip_links = set()
    for r_ in data.get("records", []):
        pass
    lines = text.splitlines()
    res = []
    for line in lines:
        if line.startswith("- [[03 Governance") or line.startswith("- [[04 External") or line.startswith("- [[05 General"):
            continue
        res.append(line)
    return "\n".join(res) + "\n"
tsn.render_home = home_no_collections
mutate_report("collection record-links removed (headings kept):", run_tests())
tsn.render_home = orig_home

print("== F. mutation: timeline merges issuance dates into event table ==")
orig_tl = nav.render_timeline
def merged(data):
    d = json.loads(json.dumps(data))
    for x in d["records"]:
        if not x.get("event_date") and x.get("date"):
            x["event_date"] = x["date"]
        if not x.get("date") and x.get("event_date"):
            x["date"] = x["event_date"]
    return orig_tl(d)
tsn.render_timeline = merged
mutate_report("dates cross-populated:", run_tests())
tsn.render_timeline = orig_tl

print("== G. mutation: template gets an example wikilink ==")
orig_rec_t = nav.render_record_template
tsn.render_record_template = lambda: orig_rec_t() + "\nSee [[Some Example Note]].\n"
mutate_report("example link added:", run_tests())
tsn.render_record_template = orig_rec_t

print("== H. token audit of templates ==")
for rel in ("99 Templates/Activity Template.md", "99 Templates/Record Template.md"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    tokens = sorted(set(re.findall(r"\{\{[^}]*\}\}", text)))
    print(rel, "tokens:", tokens, "| contains '[[':", "[[" in text)

print("== I. template properties vs generated notes on disk ==")
rec_note = None
for r in DATA["records"]:
    if r["collection"] == "governance":
        rec_note = (ROOT / r["note_path"]).read_text(encoding="utf-8")
        break
fm = rec_note.split("---\n")[1]
import yaml
props = list(yaml.safe_load(fm).keys())
tpl_props = list(yaml.safe_load((ROOT / "99 Templates/Record Template.md").read_text(encoding="utf-8")).split("---\n")[1].keys())
print("note props :", props)
print("template   :", tpl_props)
print("same names+order:", props == tpl_props)
secs = [l for l in rec_note.splitlines() if l.startswith("## ")]
print("note sections:", secs)

hub = (ROOT / DATA["activities"][0]["hub_path"]).read_text(encoding="utf-8")
hubs = [l for l in hub.splitlines() if l.startswith("## ")]
tpl_hub = [l for l in (ROOT / "99 Templates/Activity Template.md").read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
print("hub sections:", hubs)
print("tpl  sections:", tpl_hub)
print("hub order == template order:", hubs == tpl_hub)
print("hub At a glance lines:", [l for l in hub.splitlines() if l.startswith("> **")])
act = DATA["activities"][0]
print("organizers in data:", act["organizers"])

print("== J. NAVIGATION_PATHS usage across repo ==")
for p in ROOT.rglob("*.py"):
    if "Scheduler_v1-main" in str(p):
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "NAVIGATION_PATHS" in t:
        print("  referenced in", p.relative_to(ROOT))

print("== K. 05 General Records on disk ==")
g5 = ROOT / "05 General Records"
print("exists:", g5.exists(), "children:", [c.name for c in g5.iterdir()] if g5.exists() else None)

print("== L. duplicate-name risk: two records with same title? ==")
from collections import Counter
c = Counter(r["title"] for r in DATA["records"])
print("dupe titles:", {k: v for k, v in c.items() if v > 1})
