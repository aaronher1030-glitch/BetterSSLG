import re, sys
from pathlib import Path
import yaml

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
VAULT_PREFIXES = ("01 Dashboards/", "02 Activities/", "03 School Records/",
                  "04 External Memoranda/", "05 General Records/", "80 Assets/")

def vault_md():
    out = []
    for p in ROOT.rglob("*.md"):
        rel = p.relative_to(ROOT).as_posix()
        if any(rel.startswith(k) for k in VAULT_PREFIXES):
            out.append((rel, p))
    return sorted(out)

def fm(text):
    if not text.startswith("---"):
        return None
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end])

notes = vault_md()
print("E11a vault md count:", len(notes))

record_notes = []
for rel, p in notes:
    t = p.read_text(encoding="utf-8", errors="replace")
    try:
        d = fm(t)
    except Exception:
        d = None
    if isinstance(d, dict) and "record_id" in d:
        record_notes.append((rel, p, t, d))
print("E11b notes with record_id property (record notes):", len(record_notes))

not_stated = []
printed = []
for rel, p, t, d in record_notes:
    m = re.search(r">\s*\*\*Document ID:\*\*\s*(.+)", t)
    rid = d.get("record_id")
    if m is None:
        printed.append((rel, "NO DOCUMENT ID LINE", rid))
        continue
    val = m.group(1).strip()
    if val.startswith("Not stated"):
        not_stated.append((rel, rid))
    else:
        printed.append((rel, val, rid))
print("E11c notes rendering 'Document ID: Not stated in source':", len(not_stated))
for rel, rid in not_stated:
    print("   ", rel, "| record_id=", repr(rid))
print("E11d notes rendering a Document ID value:", len(printed))
mismatch = [(r, v, i) for r, v, i in printed if str(v).strip(' "`') != str(i)]
print("E11e printed value != frontmatter record_id:", len(mismatch))
for r, v, i in mismatch[:10]:
    print("   ", r, v, i)

# provenance disclosure wording
PROV = re.compile(r"filename|file name|derived|inferred|assigned by|not printed|not stated in the file", re.I)
hits = []
for rel, p, t, d in record_notes:
    for line in t.splitlines():
        if PROV.search(line):
            hits.append((rel, line.strip()))
print("E11f record-note lines containing provenance wording:", len(hits))
for rel, line in hits:
    print("   ", rel, "::", line[:160])

# same probe across ALL vault md (incl. hubs, dashboards, archive index)
allhits = []
for rel, p in notes:
    t = p.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(t.splitlines(), 1):
        if PROV.search(line):
            allhits.append((rel, i, line.strip()))
print("E11g ALL vault-md lines with provenance wording:", len(allhits))
for rel, i, line in allhits:
    print("   ", rel, ":", i, "::", line[:180])

# underscore ids rendered as Document ID and absent from own sources -> recount
UND = re.compile(r"^[A-Z]+_\d.*|.*_\d{4}_\d{3}.*")
underscore_printed = []
for rel, val, rid in printed:
    if isinstance(rid, str) and "_" in rid:
        underscore_printed.append((rel, rid))
print("E11h notes printing an underscore-form record_id as Document ID:", len(underscore_printed))
for rel, rid in sorted(underscore_printed, key=lambda x: x[1]):
    print("   ", rid, "|", rel)
