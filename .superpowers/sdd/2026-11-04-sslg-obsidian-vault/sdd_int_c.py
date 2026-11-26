import json, os, re, sys, collections, posixpath

ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
def norm(p): return (p or "").replace("\\", "/")

# ---------- A: sslg_content.json vs File Manifest.json ----------
man = json.load(open(os.path.join(ROOT, "90 Archive", "File Manifest.json"), encoding="utf-8-sig"))
con = json.load(open(os.path.join(ROOT, "tools", "sslg_content.json"), encoding="utf-8-sig"))
print("A1 manifest top keys:", sorted(man.keys()), " counts:", {k: len(v) for k, v in man.items()})
print("A1 content  top keys:", sorted(con.keys()), " counts:", {k: len(v) for k, v in con.items()})
for section in ("files", "protected_files", "records", "activities"):
    a, b = man.get(section), con.get(section)
    same = json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    print(f"A2 section {section}: identical={same}")
    if not same and isinstance(a, list) and isinstance(b, list):
        sa = {json.dumps(x, sort_keys=True) for x in a}
        sb = {json.dumps(x, sort_keys=True) for x in b}
        print("     only in manifest:", len(sa - sb), [str(x)[:160] for x in list(sa - sb)[:5]])
        print("     only in content :", len(sb - sa), [str(x)[:160] for x in list(sb - sa)[:5]])

# ---------- vault inventory ----------
SKIP = {".git", "__pycache__", ".obsidian", "node_modules"}
allfiles = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP]
    for fn in filenames:
        allfiles[norm(os.path.relpath(os.path.join(dirpath, fn), ROOT))] = os.path.getsize(
            os.path.join(dirpath, fn))

VAULT_ZONES = ("01 Dashboards", "02 Activities", "03 Governance", "04 External Memoranda",
               "05 General Records", "80 Assets", "90 Archive", "99 Templates")
vault_md = sorted(k for k in allfiles if k.endswith(".md") and k.split("/")[0] in VAULT_ZONES)
vault_md.append("START HERE.md")
vault_md = sorted(set(vault_md))
print("\nB1 vault .md files:", len(vault_md))
print("B2 md outside vault zones:", [k for k in allfiles if k.endswith(".md") and k not in vault_md])
print("B3 non-md files inside vault zones:", sorted(k for k in allfiles
       if not k.endswith(".md") and k.split("/")[0] in VAULT_ZONES and not k.endswith(".json")))
print("B4 80 Assets contents:", [k for k in allfiles if k.startswith("80 Assets")])
print("B5 99 Templates contents:", [k for k in allfiles if k.startswith("99 Templates")])
print("B6 90 Archive non-docx/pdf files:", [k for k in allfiles if k.startswith("90 Archive")
       and os.path.splitext(k)[1].lower() not in (".docx", ".pdf")])

# ---------- wikilink / md-link resolution ----------
WL = re.compile(r"!?\[\[([^\[\]]+?)\]\]")
ML = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
orig_basenames = {os.path.basename(norm(e["original_path"])).lower() for e in man["files"]}
cur_basenames = {os.path.basename(norm(e["current_path"])).lower() for e in man["files"]}
md_paths = {k.lower() for k in allfiles if k.endswith(".md")}
md_stems = {posixpath.basename(k)[:-3] for k in md_paths}
base_lowers = {k.lower() for k in allfiles}

stale_dup, rootless_src, unresolved = [], [], []
link_map = collections.defaultdict(set)   # target -> sources referencing it

for p in vault_md:
    try:
        text = open(os.path.join(ROOT, p), encoding="utf-8").read()
    except Exception as ex:
        print("READFAIL", p, ex); continue
    d = posixpath.dirname(p)
    for m in WL.finditer(text):
        t = m.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if not t: continue
        line = text[:m.start()].count("\n") + 1
        link_map[t].add((p, line))
        low = t.lower()
        if "_DUPLICATES_TO_DELETE" in t:
            stale_dup.append((p, line, t))
        if low in orig_basenames and "/" not in t:
            rootless_src.append((p, line, t))
        # resolve: exact path, path+.md, note-folder-relative, or unique basename (Obsidian shortest path)
        cand = [t, t + ".md", posixpath.normpath(posixpath.join(d, t)), posixpath.normpath(posixpath.join(d, t + ".md"))]
        hit = any(c.lower() in base_lowers for c in cand)
        bn = posixpath.basename(t).lower()
        if not hit and bn.endswith((".docx", ".pdf", ".md", ".base")):
            hit = bn in base_lowers or sum(1 for k in base_lowers if posixpath.basename(k) == bn) > 0
        if not hit and not bn.endswith((".docx", ".pdf", ".base")):
            hit = bn in md_stems or (bn + ".md") in md_paths
        if not hit:
            unresolved.append((p, line, t))
    for m in ML.finditer(text):
        t = m.group(1).strip()
        if t.startswith(("http", "mailto:", "#")): continue
        t = t.split("#")[0]
        line = text[:m.start()].count("\n") + 1
        dec = __import__("urllib.parse").parse.unquote(t)
        cand = [dec, posixpath.normpath(posixpath.join(d, dec))]
        hit = any(c.lower() in base_lowers for c in cand)
        link_map[dec].add((p, line))
        if not hit:
            unresolved.append((p, line, "MDLINK:" + t))

print("\nC1 '_DUPLICATES_TO_DELETE' references in vault md:", len(stale_dup))
for x in stale_dup[:30]: print("   ", x)
print("C2 root-level (prefix-less) source-file wikilinks:", len(rootless_src))
for x in rootless_src[:40]: print("   ", x)
print("C3 unresolved link targets:", len(unresolved))
for x in unresolved[:60]: print("   ", x)

# any mention of old layout words in md
for term in ("_DUPLICATES_TO_DELETE", "TODO", "FIXME", "TBD", "loose", "root folder"):
    hits = []
    for p in vault_md:
        try: text = open(os.path.join(ROOT, p), encoding="utf-8").read()
        except Exception: continue
        if term.lower() in text.lower():
            hits.append(p)
    if hits: print(f"C4 mentions of {term!r}:", hits[:20])

# ---------- reachability ----------
corpus_parts = []
for p in vault_md:
    try: corpus_parts.append(open(os.path.join(ROOT, p), encoding="utf-8").read())
    except Exception: pass
for p in [k for k in allfiles if k.endswith(".base")]:
    corpus_parts.append(open(os.path.join(ROOT, p.replace("/", os.sep)), encoding="utf-8").read())
corpus = "\n".join(corpus_parts).lower()

def is_reached(k):
    bn = posixpath.basename(k).lower()
    stem = bn[:-3] if bn.endswith(".md") else bn
    return (k.lower() in corpus) or (bn in corpus) or (stem in corpus)

created = [k for k in allfiles if k.split("/")[0] in VAULT_ZONES or k == "START HERE.md"
           or k.endswith(".base")]
created = sorted(set(created))
unreach = [k for k in created if not is_reached(k)]
print("\nD1 created (vault-zone) files:", len(created))
print("D2 unreachable files:", len(unreach))
for x in unreach: print("   ", x)

