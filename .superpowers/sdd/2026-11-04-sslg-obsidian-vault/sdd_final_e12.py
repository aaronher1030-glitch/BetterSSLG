import re, json
from pathlib import Path
import yaml

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools" / "sslg_content.json").read_text(encoding="utf-8"))
records = data["records"]
print("F: records in content json:", len(records))
note_keys = [r["note_path"] for r in records]
missing = []
present = 0
for np in note_keys:
    p = ROOT / np
    if not p.exists():
        missing.append(("NOT ON DISK", np)); continue
    t = p.read_text(encoding="utf-8", errors="replace")
    ok = t.startswith("---")
    if not ok:
        missing.append(("NO FM START", np)); continue
    try:
        end = t.index("\n---", 3)
        d = yaml.safe_load(t[3:end])
    except Exception as e:
        missing.append(("PARSE FAIL " + type(e).__name__ + ":" + str(e)[:60], np)); continue
    if not isinstance(d, dict):
        missing.append(("FM NOT DICT", np)); continue
    if "record_id" not in d:
        missing.append(("NO record_id KEY", np))
    else:
        present += 1
print("notes with record_id key:", present, "of", len(note_keys))
for kind, np in missing:
    print("  ", kind, "|", np)

# md inventory by top folder
from collections import Counter
c = Counter()
for p in ROOT.rglob("*.md"):
    rel = p.relative_to(ROOT).as_posix()
    c[rel.split("/")[0]] += 1
print("md by top folder:", dict(c))
