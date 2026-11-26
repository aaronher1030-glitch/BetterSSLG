"""Final review D4: validator-independence probes (in-memory only; nothing is written)."""
import json
import copy
import sys
from pathlib import Path

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
sys.path.insert(0, str(ROOT))
from tools.validate_sslg_vault import validate_vault  # noqa: E402

data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
base = validate_vault(ROOT, data)
print("D4a. unmutated validate_vault(root, manifest) errors:", len(base), base[:3])

cases = {}

d = copy.deepcopy(data)
d["files"] = d["files"][1:]
cases["drop one file entry from the manifest (its bytes stay on disk)"] = validate_vault(ROOT, d)

d = copy.deepcopy(data)
r = d["records"][0]
r["related"] = []
cases["erase record 0's outgoing related links (breaks reciprocity)"] = validate_vault(ROOT, d)

d = copy.deepcopy(data)
owner_a = d["records"][0]["key"]
owner_b = d["records"][1]["key"]
k = d["records"][1]["source_keys"][0]
d["files"] = [dict(e, record_key=owner_a) if e["key"] == k else e for e in d["files"]]
d["records"][1]["source_keys"] = []
cases["re-assign record 1's primary file to record 0 (ownership/symmetry moved)"] = validate_vault(ROOT, d)

d = copy.deepcopy(data)
for a in d["activities"]:
    a["review_reasons"] = []
cases["clear all activity review_reasons (13 queue sections no longer required)"] = validate_vault(ROOT, d)

d = copy.deepcopy(data)
for e in d["protected_files"]:
    e["sha256"] = "0" * 64
cases["flip every protected-file hash in the manifest (disk unchanged)"] = validate_vault(ROOT, d)

d = copy.deepcopy(data)
d["records"] = d["records"][:1]
cases["drop 35 record notes from the manifest (files still on disk)"] = validate_vault(ROOT, d)

print("\nD4b. probe results (errors>0 means the validator notices the mutation)")
for name, errs in cases.items():
    print(f"   errors={len(errs):3d} | {name}")
    for e in errs[:2]:
        print("        e.g.", e[:110])

print("\nD4c. checks the validator does not perform (grep of its own source)")
src = (ROOT / "tools/validate_sslg_vault.py").read_text(encoding="utf-8")
for probe in ["pre-move-baseline", "baseline", "yaml", "reciproc", "![[", "related reciprocity", "05 General Records",
              "rglob", "count", "80 Assets", "needs-review"]:
    print(f"   mentions {probe!r}: {src.lower().count(probe.lower())}")
