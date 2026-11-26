import json, os, re
import yaml
ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
os.chdir(ROOT)
V = json.load(open("90 Archive/File Manifest.json", encoding="utf-8"))
acts = V["activities"]
recs = {r["key"]: r for r in V["records"]}
by_act = {}
for r in V["records"]:
    by_act.setdefault(r["activity"], []).append(r)

H2 = re.compile(r"^##\s+(.*)$", re.M)
print("=== HUB CHECK ===")
probs = []
for a in acts:
    hp = a["hub_path"]
    if not os.path.exists(hp):
        probs.append(("hub-absent", hp)); continue
    t = open(hp, encoding="utf-8").read()
    h2 = H2.findall(t)
    if not h2 or h2[-1] != "Missing stages":
        probs.append(("missing-stages-not-last", "%s last H2=%r all=%s" % (hp, h2[-1] if h2 else None, h2)))
    own = by_act.get(a["key"], [])
    for r in own:
        rel = os.path.relpath(r["note_path"], os.path.dirname(hp)).replace("\\", "/")
        base = os.path.basename(r["note_path"])
        stem = base[:-3]
        hit = (r["note_path"].replace("\\","/") in t) or (rel in t) or ("[[%s]]" % stem in t) or ("[[%s|" % stem in t)
        if not hit:
            probs.append(("hub-does-not-link-record", "%s -> %s" % (hp, r["note_path"])))
    print("hub ok? %-70s records=%d h2last=%r" % (a["key"], len(own), h2[-1] if h2 else None))

print()
print("PROBLEMS:", len(probs))
for p in probs: print("  !!", p)

print()
print("=== activity key coverage: records whose activity is not a hub key ===")
ak = {a["key"] for a in acts}
for r in V["records"]:
    if r["activity"] not in ak:
        print("   record activity not in activities:", r["key"], r["activity"])
print("=== hubs with zero records ===")
for a in acts:
    if not by_act.get(a["key"]): print("   EMPTY HUB:", a["key"], a["hub_path"])

print()
print("=== Missing stages body sample ===")
for a in acts[:3]:
    t = open(a["hub_path"], encoding="utf-8").read()
    sec = t[t.rfind("\n## Missing stages"):]
    print("---", a["hub_path"]); print(sec[:400])

print()
print("=== record types vs activity assignment (governance/external hubs?) ===")
for r in V["records"]:
    print("%-28s %-45s %s" % (r["record_type"], r["activity"], r["key"]))
