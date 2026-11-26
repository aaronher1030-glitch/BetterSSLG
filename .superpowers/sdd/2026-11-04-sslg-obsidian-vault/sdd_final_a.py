"""Final review A: preservation and reversibility measurements (read-only)."""
import json
import hashlib
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
SCRATCH = ROOT / ".superpowers/sdd/2026-11-04-sslg-obsidian-vault"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "90 Archive/File Manifest.json").read_text(encoding="utf-8"))
baseline = json.loads((SCRATCH / "pre-move-baseline.json").read_text(encoding="utf-8"))

print("A1. content.json files == File Manifest.json files:", data["files"] == manifest["files"])
print("    activities equal:", data["activities"] == manifest["activities"],
      "records equal:", data["records"] == manifest["records"],
      "protected equal:", data["protected_files"] == manifest["protected_files"])

missing, mismatched = [], []
for e in data["files"]:
    p = ROOT / e["current_path"]
    if not p.is_file():
        missing.append(e["current_path"])
    elif sha256(p) != e["sha256"]:
        mismatched.append(e["current_path"])
print(f"A2. files entries={len(data['files'])} missing current_path={len(missing)} hash mismatch={len(mismatched)}")
for x in missing + mismatched:
    print("   BAD:", x)

print("A3. roles:", Counter(e["role"] for e in data["files"]))

bfiles = baseline["files"]
print("A4. baseline: count field =", baseline["count"], "entries =", len(bfiles),
      "(dict path->sha256)" if isinstance(bfiles, dict) else "(list)")
bl_paths = sorted(bfiles)
bl_hashes = [bfiles[p] for p in bl_paths]

current_by_hash = defaultdict(list)
for e in data["files"]:
    current_by_hash[e["sha256"]].append(e["current_path"])

lost = [(p, h) for p, h in zip(bl_paths, bl_hashes) if h not in current_by_hash]
print(f"A6. baseline paths whose recorded hash no longer exists anywhere in manifest hashes: {len(lost)}")
for x in lost:
    print("   LOST:", x)

mo = sorted(e["original_path"] for e in data["files"])
print("A7. baseline original paths == manifest original paths:", bl_paths == mo)
if bl_paths != mo:
    print("   only-baseline:", sorted(set(bl_paths) - set(mo)))
    print("   only-manifest:", sorted(set(mo) - set(bl_paths)))

diff = []
e_by_orig = {e["original_path"]: e for e in data["files"]}
for p in bl_paths:
    e = e_by_orig.get(p)
    if e and e["sha256"] != bfiles[p]:
        diff.append((p, bfiles[p], e["sha256"]))
print("A8. baseline vs manifest hash disagreements per original path:", len(diff))
for x in diff:
    print("   DIFF:", x)

loose = sorted(p.name for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in {".docx", ".pdf"})
print("A9. loose DOCX/PDF at vault root:", len(loose), loose)

byhash = defaultdict(list)
for e in data["files"]:
    byhash[e["sha256"]].append(e["current_path"])
dupgroups = {h: ps for h, ps in byhash.items() if len(ps) > 1}
print("A10. hash groups with >1 manifest entry:", len(dupgroups),
      "files in those groups:", sum(len(v) for v in dupgroups.values()),
      "distinct hashes total:", len(byhash))
unfound = [p for ps in dupgroups.values() for p in ps if not (ROOT / p).is_file()]
print("     duplicate-group members missing on disk:", len(unfound), unfound)

allsrc = []
for p in ROOT.rglob("*"):
    if p.is_file() and p.suffix.lower() in {".docx", ".pdf", ".png"}:
        rp = p.relative_to(ROOT).as_posix()
        if not rp.startswith(("Scheduler_v1-main/", "docs/", "tools/", ".superpowers/", ".obsidian/")):
            allsrc.append(rp)
print("A11. on-disk DOCX/PDF/PNG in vault scope:", len(allsrc), "| manifest entries:", len(data["files"]))
cur = {e["current_path"] for e in data["files"]}
print("     on-disk but not in manifest:", sorted(set(allsrc) - cur))
print("     in manifest but not on disk scan:", sorted(cur - set(allsrc)))

for d in ("_DUPLICATES_TO_DELETE", "OM_SSLG_2026_001", "05 General Records"):
    dp = ROOT / d
    print(f"A12. {d}: exists={dp.exists()} children={len(list(dp.rglob('*'))) if dp.exists() else '-'}")

# A13: original_path still at original location (i.e., unmoved entries) and moves actually happened
moved = [e for e in data["files"] if e["original_path"] != e["current_path"]]
print("A13. entries where current_path != original_path:", len(moved), "unchanged:", len(data["files"]) - len(moved))
still_there = [e["original_path"] for e in moved if (ROOT / e["original_path"]).exists()]
print("     stale original paths still present (would mean copy not move):", len(still_there), still_there)

# A14: protected tree drift (Scheduler + docs)
sched = [e for e in data["protected_files"]]
print("A14. protected_files entries:", len(sched))
sched_now = []
for p in (ROOT / "Scheduler_v1-main").rglob("*"):
    if p.is_file():
        sched_now.append(p.relative_to(ROOT).as_posix())
decl = {e["path"] for e in sched}
print("     scheduler files on disk:", len(sched_now), "declared:", len(decl))
print("     on disk but undeclared:", sorted(set(sched_now) - decl))
print("     declared but missing:", sorted(decl - set(sched_now)))
bad = []
for e in sched:
    p = ROOT / e["path"]
    if not p.is_file() or sha256(p) != e["sha256"]:
        bad.append(e["path"])
print("     protected hash drift:", len(bad), bad)

docs_now = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs").rglob("*") if p.is_file())
print("A15. docs/ files on disk:", len(docs_now), docs_now)
tools_now = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "tools").rglob("*") if p.is_file() and "__pycache__" not in str(p))
print("A16. tools/ files (excl pycache):", len(tools_now), tools_now)
