"""Final review E1: inventory of falsifiable claims in the manifest."""
import json
import re
from pathlib import Path

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
recs = {r["key"]: r for r in data["records"]}
acts = {a["key"]: a for a in data["activities"]}
files = {e["key"]: e for e in data["files"]}

pageclaim = re.compile(r"\b(\d+)\s*(-\s*\d+\s*)?page", re.I)
byteclaim = re.compile(r"byte-identical duplicate of ([^.;]+)", re.I)

print("E1a. page-count claims")
for r in data["records"]:
    for x in r["key_details"] + (r.get("review_reasons") or []):
        for m in pageclaim.finditer(x):
            print(f"   [{r['key']}] says {m.group(0)!r} -> {x[:120]}")
for a in data["activities"]:
    for x in ([a.get("summary") or ""] + (a.get("outcomes") or []) + (a.get("review_reasons") or [])):
        for m in pageclaim.finditer(x):
            print(f"   [activity {a['key']}] {m.group(0)} :: {x[:100]}")

print()
print("E1b. 'byte-identical duplicate of X' claims (role=duplicate)")
bad = []
byhash = {}
for e in data["files"]:
    byhash.setdefault(e["sha256"], []).append(e)
for e in data["files"]:
    if e["role"] != "duplicate":
        continue
    m = byteclaim.search(e["archive_reason"] or "")
    if not m:
        continue
    target = m.group(1).strip()
    tp = next((x for x in data["files"] if Path(x["original_path"]).name == target
               or Path(x["current_path"]).name == target), None)
    if tp is None:
        bad.append((e["key"], target, "TARGET NOT IN MANIFEST"))
        continue
    same = tp["sha256"] == e["sha256"]
    if not same:
        bad.append((e["key"], target, "HASH DIFFERS", e["sha256"][:12], tp["sha256"][:12]))
print("   violations:", len(bad))
for x in bad:
    print("     ", x)
n_dupclaims = sum(1 for e in data["files"] if byteclaim.search(e["archive_reason"] or ""))
print("   total byte-identical claims:", n_dupclaims)

print()
print("E1c. duplicate/staged entries whose reason mentions a same-hash sibling")
for e in data["files"]:
    if e["role"] not in ("duplicate", "staged", "revision"):
        continue
    for sib in byhash[e["sha256"]]:
        pass
grp_sizes = {k: len(v) for k, v in byhash.items() if len(v) > 1}
print("   hash groups:", {Path(p).name for k in grp_sizes for p in [", ".join(x['original_path'] for x in byhash[k])]})

print()
print("E1d. adviser / principal names appearing in claims")
namepat = re.compile(r"(Adviser|adviser|Sir |Ma'am |Mrs\.|Ms\.|Mr\.|Hon\.|Principal)[^\n]{0,90}")
for r in data["records"]:
    for x in r["key_details"]:
        for m in namepat.finditer(x):
            print(f"   [{r['key']}] {m.group(0)[:100]}")

print()
print("E1e. date-bearing claims per record vs frontmatter")
for r in data["records"]:
    print(f"   {r['key']}: date={r['date']} event={r['event_date']} record_id={r['record_id']!r} status={r['status']} sources={[files[k]['original_path'] for k in r['source_keys']]}")
