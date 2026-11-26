import json, re
from pathlib import Path
ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
recs, acts = data["records"], data["activities"]
NOTE_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def cells(line):
    out, buf, depth, i = [], "", 0, 0
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    while i < len(s):
        if s.startswith("[[", i):
            depth += 1; buf += "[["; i += 2; continue
        if s.startswith("]]", i):
            depth = max(0, depth - 1); buf += "]]"; i += 2; continue
        ch = s[i]
        if ch == "|" and depth == 0:
            out.append(buf.strip()); buf = ""
        else:
            buf += ch
        i += 1
    out.append(buf.strip())
    return out


# per-activity status check on Activity Dashboard
txt = (ROOT / "01 Dashboards/Activity Dashboard.md").read_text(encoding="utf-8")
rows = [l for l in txt.splitlines() if l.startswith("| [[")]
dash = {}
for l in rows:
    c = cells(l)
    m = NOTE_LINK.match(c[0])
    dash[m.group(2)] = {"start": c[1], "end": c[2], "sy": c[3], "status": c[4], "n": int(c[5]), "venue": c[6]}
mism = {}
for a in acts:
    d = dash.get(a["title"])
    if d is None:
        mism[a["title"]] = "MISSING ROW"; continue
    exp = {"start": a["start_date"] or "Not stated in source",
           "end": a["end_date"] or "Not stated in source",
           "sy": a["school_year"], "status": a["status"],
           "n": sum(1 for r in recs if r["activity"] == a["key"]),
           "venue": a["venue"] or "Not stated in source"}
    bad = {k: (d[k], v) for k, v in exp.items() if d[k] != v}
    if bad:
        mism[a["title"]] = bad
print("X1. Activity Dashboard cell-level mismatches vs manifest:", mism or "none")

tl = (ROOT / "01 Dashboards/Timeline.md").read_text(encoding="utf-8")
ev = tl.split("## Activity and meeting dates")[1].split("## Record issuance dates")[0]
iss = tl.split("## Record issuance dates")[1].split("### Records with no issuance date")[0]
nod = tl.split("### Records with no issuance date")[1]
er = [l for l in ev.splitlines() if l.startswith("| 2")]
ir = [l for l in iss.splitlines() if l.startswith("| 2")]
nb = [l for l in nod.splitlines() if l.startswith("- [[")]
allnote = {r["note_path"] for r in recs}
hubs = {a["hub_path"] for a in acts}
md = {r["note_path"]: r for r in recs}
ev_l = {NOTE_LINK.search(cells(l)[1]).group(1) for l in er}
iss_l = {NOTE_LINK.search(cells(l)[1]).group(1) for l in ir}
nod_l = {NOTE_LINK.search(l).group(1) for l in nb}
print("X2. timeline note sets: event", len(ev_l), "issuance", len(iss_l), "no-date", len(nod_l))
print("  event-dated records absent from event table:", sorted({r['note_path'] for r in recs if r['event_date']} - ev_l))
print("  dated records absent from issuance table:", sorted({r['note_path'] for r in recs if r['date']} - iss_l))
print("  no-date bullets that do have a date:", sorted(nod_l - {r['note_path'] for r in recs if not r['date']}))
print("  notes in no timeline table:", sorted(allnote - ev_l - iss_l - nod_l))
bad_i = [(cells(l)[0], md[NOTE_LINK.search(cells(l)[1]).group(1)]["date"]) for l in ir
         if md[NOTE_LINK.search(cells(l)[1]).group(1)]["date"] != cells(l)[0]]
bad_e = [(cells(l)[0], md[NOTE_LINK.search(cells(l)[1]).group(1)]["event_date"]) for l in er
         if md[NOTE_LINK.search(cells(l)[1]).group(1)]["event_date"] != cells(l)[0]]
print("X3. issuance cell-date != manifest date:", bad_i or "none")
print("  event cell-date != manifest event_date:", bad_e or "none")
print("X4. timeline activity-schedule rows:", len([l for l in tl.split('## Activity schedule')[1].split('## Activity and meeting dates')[0].splitlines() if l.startswith('| 2') or l.startswith('| Not')]))

dl = (ROOT / "01 Dashboards/Document Library.md").read_text(encoding="utf-8")
print("X5. Document Library folder claims")
for c in re.findall(r"- `([^`]+)/`", dl):
    p = ROOT / c
    n_md = len(list(p.rglob("*.md"))) if p.is_dir() else -1
    n_src = len([x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in (".docx", ".pdf", ".png")]) if p.is_dir() else -1
    print(f"   '{c}' exists={p.is_dir()} md={n_md} sources={n_src}")
print("   05 General Records mentioned:", "05 General Records" in dl, "on disk:", (ROOT / "05 General Records").exists())
print("   Bases embed present:", "![[01 Dashboards/SSLG Records.base]]" in dl)

q = (ROOT / "01 Dashboards/Review Queue.md").read_text(encoding="utf-8")
print("X6. Review Queue")
mr = [(e["key"], x[:60]) for e in recs + acts for x in (e.get("review_reasons") or []) if x not in q]
print("  reasons absent verbatim:", len(mr), mr)
flag = [e for e in recs + acts if e.get("review_reasons") or e["status"] == "needs-review"]
print("  flagged:", len(flag), "titles absent:", [e["key"] for e in flag if e["title"] not in q])
h1, h2 = q.split("## Activities needing review")
print("  record headings:", len([l for l in h1.splitlines() if l.startswith("### [[")]),
      "activity headings:", len([l for l in h2.splitlines() if l.startswith("### [[")]))
print("  heading targets resolve:", all(NOTE_LINK.match(l[4:]).group(1) in (allnote | hubs) for l in q.splitlines() if l.startswith("### [")))
print("  claim line:", [l for l in q.splitlines() if l.startswith("Needs review")])
print("  needs-review w/o reasons:", [r["key"] for r in recs if r["status"] == "needs-review" and not r["review_reasons"]])
print("  activity 'missing stage' reasons also in hub Missing stages?",
      sum(1 for a in acts for x in (a.get("review_reasons") or []) if x in (ROOT / a["hub_path"]).read_text(encoding="utf-8")),
      "of", sum(len(a.get("review_reasons") or []) for a in acts))

print("X7. START HERE routes vs spec list")
sh = (ROOT / "START HERE.md").read_text(encoding="utf-8")
for t in ["Activity Dashboard", "Document Library", "Timeline", "Review Queue", "Governance", "External Memoranda"]:
    print("   route", t, ":", ("|" + t + "]") in sh or (t in sh))
print("   governance member links:", len([l for l in sh.splitlines() if l.startswith("- [[03 Governance/")]))
print("   external member links:", len([l for l in sh.splitlines() if l.startswith("- [[04 External Memoranda/")]))
print("   activity links:", len([l for l in sh.splitlines() if l.startswith("- [[02 Activities/")]))
print("   80 Assets / 90 Archive / 99 Templates mentioned:",
      "80 Assets" in sh, "90 Archive" in sh, "99 Templates" in sh)

print("X8. Templates on disk vs renderer output")
import sys
sys.path.insert(0, str(ROOT))
from tools import sslg_navigation as nav
from tools import sslg_notes as notes_mod
rt = (ROOT / "99 Templates/Record Template.md").read_text(encoding="utf-8")
at = (ROOT / "99 Templates/Activity Template.md").read_text(encoding="utf-8")
print("   disk record template == render_record_template():", rt == nav.render_record_template())
print("   disk activity template == render_activity_template():", at == nav.render_activity_template())
h2s = [l for l in rt.splitlines() if l.startswith("## ")]
print("   record template H2 order:", h2s)
print("   record template final H2 == '## Original document':", h2s[-1] == "## Original document")
need = ("type", "title", "record_type", "record_id", "date", "event_date", "school_year",
        "activity", "status", "source_file", "source_path", "source_format", "sources", "related", "tags")
fm = rt.split("---\n")[1]
print("   missing template properties:", [p for p in need if not re.search(r"(?m)^" + p + ":", fm)])
print("   template unresolved wikilinks:", NOTE_LINK.findall(rt), NOTE_LINK.findall(at))
ah2 = [l for l in at.splitlines() if l.startswith("## ")]
print("   activity template H2 order:", ah2)
for s in ["At a glance", "Activity trail", "Outcomes and follow-up", "Missing stages", "Original files"]:
    print(f"      activity template has '{s}':", any(s in x for x in ah2))
print("   {{tokens}}:", re.findall(r"\{\{[^}]+\}\}", rt + at))
# generated-note section names for comparison
sample = recs[0]
gen = (ROOT / sample["note_path"]).read_text(encoding="utf-8")
print("   generated note H2 order:", [l for l in gen.splitlines() if l.startswith("## ")])
gh = (ROOT / acts[0]["hub_path"]).read_text(encoding="utf-8")
print("   generated hub H2 order:", [l for l in gh.splitlines() if l.startswith("## ")])
