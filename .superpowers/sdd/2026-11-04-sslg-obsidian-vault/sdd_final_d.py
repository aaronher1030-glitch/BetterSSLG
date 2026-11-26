import json, re, yaml
from pathlib import Path
from collections import Counter, defaultdict
ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
recs, acts, files = data["records"], data["activities"], data["files"]

print("D1. note_path/hub_path uniqueness")
np = [r["note_path"] for r in recs]; hp = [a["hub_path"] for a in acts]
print("  record note_paths:", len(np), "distinct:", len(set(np)), "| hubs:", len(hp), "distinct:", len(set(hp)))
print("  duplicated paths:", [p for p, c in Counter(np + hp).items() if c > 1], "overlap:", sorted(set(np) & set(hp)))

print("D2. current files claimed by records")
cnt = defaultdict(list)
for r in recs:
    for k in r["source_keys"]: cnt[k].append(r["key"])
print("  current files not claimed:", [e["key"] for e in files if e["role"] in ("primary","alternative-format") and not cnt[e["key"]]])
print("  current files claimed >1:", {k: v for k, v in cnt.items() if len(v) > 1})
print("  primaries per record:", Counter(sum(1 for k in r["source_keys"] if next(e for e in files if e["key"]==k)["role"]=="primary") for r in recs))

print("D3. role bookkeeping")
for role in ("asset","staged","revision","duplicate"):
    sub=[e for e in files if e["role"]==role]
    print(f"  {role}: {len(sub)} with record_key={sum(1 for e in sub if e.get('record_key'))} with archive_reason={sum(1 for e in sub if e.get('archive_reason'))}")

print("D4. related reciprocity")
keys={r["key"] for r in recs}; rel={r["key"]:set(r["related"]) for r in recs}
print("  directed edges:", sum(len(v) for v in rel.values()))
print("  asymmetric:", [(a,b) for a in rel for b in rel[a] if a not in rel.get(b,set())])
print("  self refs:", [a for a in rel if a in rel[a]], "unknown keys:", [(a,b) for a in rel for b in rel[a] if b not in keys])

print("D5/D6. hub-record references")
akeys={a["key"] for a in acts}
print("  records -> unknown activity:", [r["key"] for r in recs if r["activity"] and r["activity"] not in akeys])
nolink=[]; fm_bad=[]
for a in acts:
    txt=(ROOT/a["hub_path"]).read_text(encoding="utf-8")
    for r in recs:
        if r["activity"]==a["key"] and r["note_path"] not in txt: nolink.append((a["key"],r["key"]))
for r in recs:
    txt=(ROOT/r["note_path"]).read_text(encoding="utf-8")
    m=re.search(r'(?m)^activity:\s*"(.*)"',txt)
    if r["activity"] is None:
        if m and m.group(1): fm_bad.append((r["key"],"nonempty activity for null manifest",m.group(1)))
    else:
        hub=next(a for a in acts if a["key"]==r["activity"])["hub_path"]
        if not m or hub not in m.group(1): fm_bad.append((r["key"],"activity fm != hub",m.group(1) if m else None,expected:=hub))
print("  hubs missing member:",nolink)
print("  frontmatter activity problems:",fm_bad)

print("D7. tags")
bad=[]; alltags=Counter()
for r in recs:
    fm=(ROOT/r["note_path"]).read_text(encoding="utf-8").split("---\n")[1]
    tg=re.findall(r"^  - (.+)$",fm.split("tags:\n")[-1],re.M)
    if not tg or tg[0]!="sslg": bad.append((r["key"],tg))
    alltags.update(tg)
print("  not led by sslg:",bad,"| vocabulary:",dict(alltags))

print("D8. .base YAML")
base=yaml.safe_load((ROOT/"01 Dashboards/SSLG Records.base").read_text(encoding="utf-8"))
print("  parses OK. top keys:",list(base))
print("  global filters:",base["filters"])
print("  views:",[(v["name"],v["type"]) for v in base["views"]])
for v in base["views"]: print("   ",v["name"],v.get("filters"),"order items:",len(v.get("order") or []))

print("D9. Scheduler leakage into Bases")
sched_md=[p for p in (ROOT/"Scheduler_v1-main").rglob("*.md")]
leak=[p.relative_to(ROOT).as_posix() for p in sched_md if re.search(r'(?m)^type:\s*"?record"?',p.read_text(encoding="utf-8",errors="replace"))]
print("  Scheduler .md:",len(sched_md),"with type: record:",len(leak),leak)

print("D10. count statements")
for f,pat in {"START HERE.md":r"(\d+) activities, (\d+) logical records",
              "01 Dashboards/Activity Dashboard.md":r"(\d+) activities, (\d+) logical records",
              "01 Dashboards/Review Queue.md":r"Needs review: (\d+) records, (\d+) activities"}.items():
    m=re.search(pat,(ROOT/f).read_text(encoding="utf-8")); print("  ",f,m.groups() if m else None)
fr=[r for r in recs if r["status"]=="needs-review" or r["review_reasons"]]
fa=[a for a in acts if a["status"]=="needs-review" or a["review_reasons"]]
print("   manifest activities",len(acts),"records",len(recs),"| flagged records",len(fr),"flagged activities",len(fa))
print("   Bases 'Needs review' (status==needs-review):",sum(1 for r in recs if r["status"]=="needs-review"))
print("   flagged-but-not-needs-review records:",[r["key"] for r in fr if r["status"]!="needs-review"])
print("   flagged-but-not-needs-review activities:",[a["key"] for a in fa if a["status"]!="needs-review"])

print("D11. Activity Dashboard Records column")
txt=(ROOT/"01 Dashboards/Activity Dashboard.md").read_text(encoding="utf-8")
rows=[l for l in txt.splitlines() if l.startswith("| [[")]
per={}
for l in rows:
    c=[x.strip() for x in l.strip("|").split("|")]
    per[re.match(r"\[\[.*?\|(.*)\]\]",c[0]).group(1)]=int(c[5])
mper={a["title"]:sum(1 for r in recs if r["activity"]==a["key"]) for a in acts}
print("  rows:",len(rows),"mismatches:",{k:(per.get(k),v) for k,v in mper.items() if per.get(k)!=v})
print("  column sum:",sum(per.values()),"records with activity:",sum(1 for r in recs if r["activity"]))

print("D12/D13. Timeline")
tl=(ROOT/"01 Dashboards/Timeline.md").read_text(encoding="utf-8")
sched=tl.split("## Activity schedule")[1].split("## Activity and meeting dates")[0]
ev=tl.split("## Activity and meeting dates")[1].split("## Record issuance dates")[0]
iss=tl.split("## Record issuance dates")[1].split("### Records with no issuance date")[0]
nod=tl.split("### Records with no issuance date")[1]
def d(block,col=0): return [[x.strip() for x in l.strip("|").split("|")][col] for l in block.splitlines() if re.match(r"^\| \d{4}-",l)]
print("  activity rows:",len([l for l in sched.splitlines() if l.startswith("| 2") or l.startswith("| N")]))
print("  event rows:",len(d(ev)),"sorted:",d(ev)==sorted(d(ev)))
print("  issuance rows:",len(d(iss)),"sorted:",d(iss)==sorted(d(iss)))
print("  no-issuance bullets:",len([l for l in nod.splitlines() if l.startswith("- [")]))
print("  manifest: acts",len(acts),"w/ event_date",sum(1 for r in recs if r["event_date"]),
      "w/ date",sum(1 for r in recs if r["date"]),"w/o date",sum(1 for r in recs if not r["date"]))
print("  issuance+none =",len(d(iss))+len([l for l in nod.splitlines() if l.startswith("- [")]))
srows=[[x.strip() for x in l.strip("|").split("|")][0] for l in sched.splitlines() if l.startswith("| ")]
print("  schedule col order:",srows)

print("D14. Document Library folders")
dl=(ROOT/"01 Dashboards/Document Library.md").read_text(encoding="utf-8")
for c in re.findall(r"- `([^`]+)/`",dl): print("   claim",c,"exists:",(ROOT/c).is_dir())
print("   05 General Records claimed:", "05 General Records" in dl, "on disk:", (ROOT/"05 General Records").exists())

print("D15. Review Queue reasons verbatim")
q=(ROOT/"01 Dashboards/Review Queue.md").read_text(encoding="utf-8")
mr=[(e["key"],x[:80]) for e in recs+acts for x in (e.get("review_reasons") or []) if x not in q]
print("  reasons absent:",len(mr),mr)
mt=[e["key"] for e in recs+acts if (e.get("review_reasons") or e["status"]=="needs-review") and e["title"] not in q]
print("  flagged titles absent:",mt,"| '### [[' headings:",q.count("### [["))
print("  record headings:",len([l for l in q.split('## Activities needing review')[0].splitlines() if l.startswith('### [')]))
print("  activity headings:",len([l for l in q.split('## Activities needing review')[1].splitlines() if l.startswith('### [')]))
