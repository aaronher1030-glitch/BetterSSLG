import json, os, re, collections
import yaml

ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
os.chdir(ROOT)
V = json.load(open("90 Archive/File Manifest.json", encoding="utf-8"))
files = {f["key"]: f for f in V["files"]}
recs = V["records"]
acts = V["activities"]

print("=== 1c (fixed): DOCX open link label must contain exact filename; PDF embed ===")
bad = []
for r in recs:
    np = r["note_path"]
    txt = open(np, encoding="utf-8").read()
    sec = txt[txt.rfind("\n## Original document"):]
    for sk in r["source_keys"]:
        cp = files[sk]["current_path"]
        name = os.path.basename(cp)
        fmt = os.path.splitext(name)[1].lstrip(".").lower()
        if fmt == "docx":
            links = re.findall(r"(?<!\!)\[\[([^\]]*)\]\]", sec)
            mine = [l for l in links if name in l]
            if not mine:
                bad.append(("DOCX link missing", np, name)); continue
            label = mine[0].split("|", 1)[1] if "|" in mine[0] else ""
            if name not in label:
                bad.append(("DOCX label lacks exact filename", np, "%s | label=%r" % (name, label)))
        elif fmt == "pdf":
            emb = re.findall(r"!\[\[([^\]]*)\]\]", sec)
            mine = [e for e in emb if name in e]
            if not mine:
                bad.append(("PDF not embedded ![[ ]]", np, "%s | embeds=%r" % (name, emb)))
            else:
                print("   PDF embed OK:", np, "->", mine[0])
print("problems:", len(bad))
for b in bad: print("  !!", b)

print()
print("=== 1d: frontmatter source_file/source_path/source_format vs manifest + disk ===")
def load_fm(p):
    t = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    return yaml.safe_load(m.group(1)), t
fd = collections.defaultdict(list)
for r in recs:
    np = r["note_path"]
    fm, t = load_fm(np)
    sks = r["source_keys"]
    # primary-ish sources in note frontmatter
    srcs = fm.get("sources", [])
    sf, sp, sfmt = fm.get("source_file"), fm.get("source_path"), fm.get("source_format")
    # manifest expectation from first source key
    fe = files[sks[0]]
    exp_name = os.path.basename(fe["current_path"])
    exp_path = fe["current_path"]
    exp_fmt = os.path.splitext(exp_name)[1].lstrip(".").lower()
    if sf != exp_name: fd["source_file!=manifest"].append((np, "note=%r manifest=%r (key %s role %s)" % (sf, exp_name, sks[0], fe["role"])))
    if sp != exp_path: fd["source_path!=manifest"].append((np, "note=%r manifest=%r" % (sp, exp_path)))
    if sfmt != exp_fmt: fd["source_format!=manifest"].append((np, "note=%r exp=%r" % (sfmt, exp_fmt)))
    if not sp or not os.path.exists(sp): fd["source_path-absent-on-disk"].append((np, str(sp)))
    elif os.path.splitext(sp)[1].lstrip(".").lower() != sfmt: fd["suffix!=source_format"].append((np, "%s vs %s" % (sp, sfmt)))
    # every source_keys entry should have a frontmatter sources row
    note_paths = {s.get("path") for s in srcs}
    for sk in sks:
        cp = files[sk]["current_path"]
        if cp not in note_paths: fd["source_keys-row-missing-in-frontmatter"].append((np, cp))
    for s in srcs:
        p = s.get("path")
        if p and not os.path.exists(p): fd["frontmatter-source-path-absent"].append((np, p))
for k, v in sorted(fd.items()):
    print("--", k, len(v))
    for np, d in v: print("   ", np, "::", d)
if not fd: print("clean")

print()
print("=== ALL on-disk md/asset files referenced anywhere: existence sweep ===")
missing = []
for r in recs:
    t = open(r["note_path"], encoding="utf-8").read()
    for link in re.findall(r"!?\[\[([^\]|#]*)", t):
        l = link.strip()
        if not l: continue
        cand = l if l.endswith(".md") else l
        if not os.path.exists(cand) and not os.path.exists(os.path.join(ROOT, cand)):
            missing.append((r["note_path"], l))
print("broken wikilink targets:", len(missing))
seen = set()
for np, l in missing:
    if l in seen: continue
    seen.add(l); print("   BROKEN", np, "->", l)
