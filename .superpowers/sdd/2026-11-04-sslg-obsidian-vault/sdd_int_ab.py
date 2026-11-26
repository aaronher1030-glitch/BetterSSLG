import json, hashlib, os, sys, collections

ROOT = r"C:\Users\Ma Christine\Downloads\SSLG MEMOS"
SCRATCH = os.path.join(ROOT, ".superpowers", "sdd", "2026-11-04-sslg-obsidian-vault")
SKIP_DIRS = {".git", "__pycache__", ".obsidian", "node_modules", ".venv", "venv", "dist", ".next"}

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def norm(p):
    return (p or "").replace("\\", "/").lstrip("./")

man = json.load(open(os.path.join(ROOT, "90 Archive", "File Manifest.json"), encoding="utf-8-sig"))
base = json.load(open(os.path.join(SCRATCH, "pre-move-baseline.json"), encoding="utf-8-sig"))

# ---- enumerate every file on disk once ----
disk = {}   # relpath -> sha
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        rp = norm(os.path.relpath(os.path.join(dirpath, fn), ROOT))
        try:
            disk[rp] = sha(os.path.join(dirpath, fn))
        except Exception as e:
            disk[rp] = "ERROR:" + str(e)

print("TOTAL FILES ON DISK (excl skip dirs):", len(disk))
print("top-level dirs seen:", sorted({k.split('/')[0] for k in disk if '/' in k}))
print("scratch dir file count:", sum(1 for k in disk if k.lower().startswith(".superpowers")))

# ---- CHECK 1a: manifest current_path exists + hash matches ----
missing, mismatched = [], []
for e in man["files"]:
    cp = norm(e["current_path"])
    if cp not in disk:
        missing.append((e["key"], cp))
    elif disk[cp] != e["sha256"]:
        mismatched.append((e["key"], cp, e["sha256"], disk[cp]))
print("\n[1a] manifest entries:", len(man["files"]))
print("[1a] current_path MISSING:", len(missing))
for x in missing: print("   ", x)
print("[1a] current_path HASH MISMATCH:", len(mismatched))
for x in mismatched: print("   ", x)

# duplicate current_path entries?
c = collections.Counter(norm(e["current_path"]) for e in man["files"])
dups = {k: n for k, n in c.items() if n > 1}
print("[1a] repeated current_path values:", dups)

# ---- CHECK 1b: manifest original_path vs baseline keys ----
mk = sorted(norm(e["original_path"]) for e in man["files"])
bk = sorted(norm(k) for k in base["files"])
print("\n[1b] baseline keys == manifest original_paths:", mk == bk)
print("[1b]   only in baseline:", [x for x in bk if x not in set(mk)])
print("[1b]   only in manifest:", [x for x in mk if x not in set(bk)])

# hash agreement per original path
hd = [(k, base["files"][k], dict((norm(e["original_path"]), e["sha256"]) for e in man["files"]).get(k)) for k in bk]
bad = [x for x in hd if x[1] != x[2]]
print("[1b] baseline/manifest hash disagreements:", len(bad))
for x in bad[:10]: print("   ", x)

# ---- CHECK 1c: every baseline hash still exists somewhere on disk ----
by_orig = {}
for e in man["files"]:
    by_orig.setdefault(norm(e["original_path"]), []).append(e)
diskhashes = collections.Counter(disk.values())
unmatched = []
for k, h in base["files"].items():
    if h not in diskhashes:
        unmatched.append((k, h))
print("\n[1c] baseline HASHES not found anywhere on disk:", len(unmatched))
for x in unmatched: print("   ", x)

# also: does each original PATH still sit at root (i.e. was anything left behind / not moved)?
still_at_root = [k for k in bk if k in disk]
print("[1c] baseline original_paths STILL at their original location:", len(still_at_root))
for x in still_at_root: print("   ", x)

# ---- CHECK 2: protected files ----
prot = man["protected_files"]
pm, pc = [], []
for e in prot:
    p = norm(e["path"])
    if p not in disk:
        pm.append(e["path"])
    elif disk[p] != e["sha256"]:
        pc.append((e["path"], e["sha256"], disk[p]))
protc = collections.Counter(norm(e["path"]) for e in prot)
print("[2] repeated protected paths:", {k: v for k, v in protc.items() if v > 1})
print("[2] zone coverage of protected:", collections.Counter(norm(e["path"]).split("/")[0] for e in prot))
print("\n[2] protected entries:", len(prot))
print("[2] protected MISSING:", len(pm))
for x in pm: print("   ", x)
print("[2] protected HASH MISMATCH:", len(pc))
for x in pc: print("   ", x)

for zone in ("Scheduler_v1-main", "docs", "tools"):
    zp = [norm(e["path"]) for e in prot if norm(e["path"]).startswith(zone + "/")]
    zd = [k for k in disk if k.startswith(zone + "/")]
    extra = sorted(set(zd) - set(zp))
    miss = sorted(set(zp) - set(zd))
    print(f"[2] zone {zone}: protected={len(zp)} on-disk={len(zd)} extra_vs_protected={len(extra)} missing={len(miss)}")
    if zone != "tools":
        for x in extra[:40]: print("      EXTRA:", x)
    for x in miss[:40]: print("      MISSING:", x)
    if zone == "tools":
        for x in extra[:60]: print("      (tools not a protected zone) :", x)
