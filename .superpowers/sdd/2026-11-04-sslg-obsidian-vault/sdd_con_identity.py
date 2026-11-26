import json, os, re, hashlib, zipfile, collections
ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
os.chdir(ROOT)
V = json.load(open("90 Archive/File Manifest.json", encoding="utf-8"))
files = V["files"]
by_base = collections.defaultdict(list)
for f in files:
    by_base[os.path.basename(f["current_path"]).lower()].append(f)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

_tcache = {}
def docx_text(p):
    if p in _tcache: return _tcache[p]
    try:
        z = zipfile.ZipFile(p)
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    except Exception as e:
        _tcache[p] = None; return None
    paras = []
    for pm in re.findall(r"<w:p[ >].*?</w:p>|<w:p/>", xml, re.S):
        txts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", pm, re.S)
        t = "".join(txts)
        t = re.sub(r"<[^>]+>", "", t)
        t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
               .replace("&#8217;", "\u2019").replace("&#8216;", "\u2018")
               .replace("&#8220;", "\u201c").replace("&#8221;", "\u201d"))
        t = re.sub(r"\s+", " ", t).strip()
        paras.append(t)
    norm = "\n".join(x for x in paras if x)
    _tcache[p] = norm
    return norm

def resolve(name):
    n = name.strip().lower()
    if n in by_base: return by_base[n][0]["current_path"]
    return None

pat = re.compile(r"byte-identical duplicate of (.+)$|text identical to (.+)$|byte-identical to (.+)$")
print("=== ALL identity claims (files[].archive_reason) ===")
ok = fail = unresolved = 0
fails = []
for f in files:
    ar = f.get("archive_reason") or ""
    m = pat.search(ar)
    if not m: continue
    kind = "byte" if ("byte-identical duplicate of" in ar or "byte-identical to" in ar) else "text"
    others_txt = m.group(1) or m.group(2) or m.group(3)
    # reason may list several anchors separated by ' and ' / '/'
    cands = [c for c in re.split(r"\s+and\s+|,\s*", others_txt) if c.strip()]
    p = f["current_path"]
    for c in cands:
        cp = resolve(c)
        if cp is None:
            unresolved += 1; fails.append(("UNRESOLVED", p, c)); continue
        if os.path.basename(cp).lower() == os.path.basename(p).lower():
            fails.append(("SELF-REFERENCE", p, c)); continue
        if kind == "byte":
            if sha(p) != sha(cp):
                fail += 1; fails.append(("BYTE-CLAIM-FALSE", p, "vs %s : %s != %s" % (cp, sha(p)[:16], sha(cp)[:16])))
            else: ok += 1
        else:
            a, b = docx_text(p), docx_text(cp)
            if a is None or b is None:
                fails.append(("TEXT-NOT-MEASURABLE", p, cp)); continue
            if a != b:
                fail += 1;
                # show first divergence
                d = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
                fails.append(("TEXT-CLAIM-FALSE", p, "vs %s | len %d/%d | first diff @%d: %r vs %r" % (cp, len(a), len(b), d, a[d:d+70], b[d:d+70])))
            else: ok += 1
print("claims verified true:", ok, " false:", fail, " unresolved:", unresolved, " other:", len(fails))
for x in fails:
    print("  !!", x[0], "|", x[1], "|", x[2])

print()
print("=== PDF page counts (raw /Type /Page scan) ===")
def pagecount(p):
    data = open(p, "rb").read()
    n = len(re.findall(rb"/Type\s*/Page[^s]", data))
    tot = len(re.findall(rb"/Count\s+(\d+)", data))
    m = max((int(x) for x in re.findall(rb"/Count\s+(\d+)", data)), default=None)
    return n, m

pdf_claims = collections.Counter()
pdf_index = {}
for p, c in [(f["current_path"], None) for f in files if f["current_path"].lower().endswith(".pdf")]:
    if os.path.exists(p):
        pdf_index[os.path.basename(p).lower()] = p
print("pdfs on disk indexed:", len(pdf_index))
