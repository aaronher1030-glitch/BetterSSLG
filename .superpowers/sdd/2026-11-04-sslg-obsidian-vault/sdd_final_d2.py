import json, re
from pathlib import Path
ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
recs, acts = data["records"], data["activities"]
NOTE_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def cells(line):
    """split a markdown table row on pipes that are outside [[ ]] / [ ] constructs"""
    out, buf, depth, i = [], "", 0, 0
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    while i < len(s):
        ch = s[i]
        if s.startswith("[[", i):
            depth += 1; buf += "[["; i += 2; continue
        if s.startswith("]]", i):
            depth = max(0, depth - 1); buf += "]]"; i += 2; continue
        if ch == "|" and depth == 0:
            out.append(buf.strip()); buf = ""
        else:
            buf += ch
        i += 1
    out.append(buf.strip())
    return out


print("D11 probe first row cells:", cells((ROOT / "01 Dashboards/Activity Dashboard.md").read_text(encoding="utf-8").splitlines()[16]))

txt = (ROOT / "01 Dashboards/Activity Dashboard.md").read_text(encoding="utf-8")
rows = [l for l in txt.splitlines() if l.startswith("| [[")]
per, starts, statuses = {}, [], []
for l in rows:
    c = cells(l)
    m = NOTE_LINK.match(c[0])
    per[m.group(2)] = int(c[5]); starts.append(c[1]); statuses.append(c[4])
mper = {a["title"]: sum(1 for r in recs if r["activity"] == a["key"]) for a in acts}
print("D11. Activity Dashboard rows:", len(rows), "manifest activities:", len(acts))
print("  mismatches Records column vs manifest:", {k: (per.get(k), v) for k, v in mper.items() if per.get(k) != v})
print("  unknown titles in dashboard:", sorted(set(per) - set(mper)))
print("  column sum:", sum(per.values()), "| records with an activity:", sum(1 for r in recs if r["activity"]), "| total records:", len(recs))
print("  start col:", starts)
print("  sorted with blanks last:", starts == sorted(starts, key=lambda s: (s == "Not stated in source", s)))
print("  status col:", statuses)
print("  manifest statuses:", [a["status"] for a in acts])

tl = (ROOT / "01 Dashboards/Timeline.md").read_text(encoding="utf-8")
sched = tl.split("## Activity schedule")[1].split("## Activity and meeting dates")[0]
ev = tl.split("## Activity and meeting dates")[1].split("## Record issuance dates")[0]
iss = tl.split("## Record issuance dates")[1].split("### Records with no issuance date")[0]
nod = tl.split("### Records with no issuance date")[1]
srows = [l for l in sched.splitlines() if l.startswith("| 2") or l.startswith("| Not")]
er = [l for l in ev.splitlines() if l.startswith("| 2")]
ir = [l for l in iss.splitlines() if l.startswith("| 2")]
nb = [l for l in nod.splitlines() if l.startswith("- [[")]
print("D12. Timeline: activity rows", len(srows), "| event rows", len(er), "| issuance rows", len(ir), "| no-date bullets", len(nb))
print("  manifest: activities", len(acts), "records w/ event_date", sum(1 for r in recs if r["event_date"]),
      "w/ date", sum(1 for r in recs if r["date"]), "w/o date", sum(1 for r in recs if not r["date"]))
print("  issuance rows + no-date bullets =", len(ir) + len(nb))
sv = [cells(l)[0] for l in srows]
print("D13. schedule sorted:", sv == sorted(sv, key=lambda s: (s == "Not stated in source", s)), sv)
print("  event dates:", [cells(l)[0] for l in er])
print("  event sorted:", [cells(l)[0] for l in er] == sorted(cells(l)[0] for l in er))
print("  issuance dates:", [cells(l)[0] for l in ir])
print("  issuance sorted:", [cells(l)[0] for l in ir] == sorted(cells(l)[0] for l in ir))
allnote = {r["note_path"] for r in recs}
hubs = {a["hub_path"] for a in acts}
ev_l = {NOTE_LINK.search(cells(l)[2]).group(1) for l in er} if er else set()
iss_l = {NOTE_LINK.search(cells(l)[1]).group(1) for l in ir}
nod_l = {NOTE_LINK.search(l).group(1) for l in nb}
print("  distinct notes in event table:", len(ev_l), "issuance:", len(iss_l), "no-date:", len(nod_l))
print("  records w/ event_date missing from event table:", sorted({r['note_path'] for r in recs if r['event_date']} - ev_l))
print("  records w/ date missing from issuance table:", sorted({r['note_path'] for r in recs if r['date']} - iss_l))
print("  no-date bullets that DO have a date:", sorted(nod_l - {r['note_path'] for r in recs if not r['date']}))
print("  notes appearing in NO timeline table at all:", sorted(allnote - ev_l - iss_l - nod_l))
# cross-check the event/issuance cell dates against manifest
md = {r["note_path"]: r for r in recs}
bad = [(cells(l)[0], md[NOTE_LINK.search(cells(l)[1]).group(1)]["date"]) for l in ir if md[NOTE_LINK.search(cells(l)[1]).group(1)]["date"] != cells(l)[0]]
print("  issuance table date disagreements:", bad)
bade = [(cells(l)[0], md[NOTE_LINK.search(cells(l)[1]).group(1)]["event_date"]) for l in er if md[NOTE_LINK.search(cells(l)[1]).group(1)]["event_date"] != cells(l)[0]]
print("  event table date disagreements:", bade)

dl = (ROOT / "01 Dashboards/Document Library.md").read_text(encoding="utf-8")
print("D14. Document Library folder claims")
for c in re.findall(r"- `([^`]+)/`", dl):
    p = ROOT / c
    print(f"   '{c}' exists={p.is_dir()} md={len(list(p.rglob('*.md'))) if p.is_dir() else '-'} src={len([x for x in p.rglob('*') if x.is_file() and x.suffix in ('.docx','.pdf','.png')]) if p.is_dir() else '-'}")
print("   05 General Records mentioned:", "05 General Records" in dl, "on disk:", (ROOT / "05 General Records").exists())

q = (ROOT / "01 Dashboards/Review Queue.md").read_text(encoding="utf-8")
print("D15. Review Queue")
mr = [(e["key"], x[:60]) for e in recs + acts for x in (e.get("review_reasons") or []) if x not in q]
print("  reasons absent verbatim:", len(mr), mr)
flag = [e for e in recs + acts if e.get("review_reasons") or e["status"] == "needs-review"]
print("  flagged entities:", len(flag), "titles absent:", [e["key"] for e in flag if e["title"] not in q])
h1, h2 = q.split("## Activities needing review")
print("  record headings:", len([l for l in h1.splitlines() if l.startswith("### [[")]),
      "activity headings:", len([l for l in h2.splitlines() if l.startswith("### [[")]))
print("  heading targets all resolve:", all(NOTE_LINK.match(l[4:]).group(1) in (allnote | hubs) for l in q.splitlines() if l.startswith("### [")))
print("  claim line:", [l for l in q.splitlines() if l.startswith("Needs review")])
print("  needs-review records lacking reasons:", [r["key"] for r in recs if r["status"] == "needs-review" and not r["review_reasons"]])
