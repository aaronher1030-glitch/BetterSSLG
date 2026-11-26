import json, os, re, sys, collections

ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
os.chdir(ROOT)
V = json.load(open("90 Archive/File Manifest.json", encoding="utf-8"))
T = json.load(open("tools/sslg_content.json", encoding="utf-8"))
files = {f["key"]: f for f in V["files"]}
tfiles = {f["key"]: f for f in T["files"]}
trecs = {r["key"]: r for r in T["records"]}
vrecs = {r["key"]: r for r in V["records"]}

print("=== MIRROR CHECK: manifest vs tools/sslg_content.json ===")
print("same records:", V["records"] == T["records"])
print("same files:", V["files"] == T["files"])
print("same activities:", V["activities"] == T["activities"])
diffs = [k for k in vrecs if k not in trecs] + [k for k in trecs if k not in vrecs]
print("record key mismatch:", diffs)
for k in vrecs:
    if k in trecs and vrecs[k] != trecs[k]:
        dk = [f for f in vrecs[k] if vrecs[k][f] != trecs[k].get(f)]
        print("DIFF", k, dk)

print()
print("=== source_keys multiplicity ===")
cnt = collections.Counter(len(r["source_keys"]) for r in V["records"])
print(cnt)
for r in V["records"]:
    if len(r["source_keys"]) > 1:
        print(r["key"], r["source_keys"])

print()
print("=== CHECK 1a/1b/1c: heading position + sources present ===")
problems = collections.defaultdict(list)
H2 = re.compile(r"^##\s+(.*)$", re.M)
for r in V["records"]:
    np = r["note_path"]
    if not os.path.exists(np):
        problems["note-missing"].append((np, "note file absent"))
        continue
    txt = open(np, encoding="utf-8").read()
    h2 = H2.findall(txt)
    if not h2:
        problems["no-h2"].append((np, "no level-two heading"))
        continue
    if h2[-1] != "Original document":
        problems["not-last-h2"].append((np, "last H2 = %r" % h2[-1]))
    idx = txt.rfind("\n## Original document")
    sec = txt[idx:] if idx >= 0 else ""
    # resolve source keys
    for sk in r["source_keys"]:
        fe = files.get(sk)
        if fe is None:
            problems["unknown-source-key"].append((np, sk))
            continue
        cp = fe["current_path"]
        name = os.path.basename(cp)
        stem = os.path.splitext(name)[0]
        fmt = os.path.splitext(name)[1].lstrip(".").lower()
        low = sec.lower()
        # appear as link or embed: reference the current_path or the basename
        present = (cp.replace("\\", "/").lower() in low) or (name.lower() in low)
        if not present:
            problems["src-not-in-section"].append((np, "%s role=%s" % (cp, fe["role"])))
        # embed/link form rules
        if fmt == "pdf":
            if ("![[%s" % cp.replace("\\", "/")) not in sec and ("![[%s" % name) not in sec and ("![[%s|" % stem) not in sec:
                embeds = re.findall(r"!\[\[[^\]]*\]\]", sec)
                ok = any(name.lower() in e.lower() or cp.replace("\\", "/").lower() in e.lower() for e in embeds)
                if not ok:
                    problems["pdf-not-embedded"].append((np, cp + " | " + " ; ".join(embeds)[:200]))
        elif fmt == "docx":
            links = re.findall(r"(?<!\!)\[\[([^\]]*)\]\]", sec)
            mine = [l for l in links if name.lower() in l.lower() or cp.replace("\\", "/").lower() in l.lower()]
            if not mine:
                problems["docx-no-open-link"].append((np, cp))
            else:
                lab_ok = any(name.lower() in l for l in mine)
                if not lab_ok:
                    problems["docx-label-missing-filename"].append((np, mine))

for k, v in sorted(problems.items()):
    print("\n--", k, len(v))
    for np, d in v:
        print("   ", np, "::", d)
if not problems:
    print("no 1a/1b/1c problems")
