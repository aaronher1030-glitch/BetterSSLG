"""Final review B3: metadata vocabulary, date formats, hub/manifest agreement, tags (read-only)."""
import json
import re
import yaml
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
data = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))
RT = {"proposal", "completion-report", "memorandum", "meeting-notice", "excuse-letter", "request", "governance-policy"}
ST = {"draft", "final", "signed", "reference", "needs-review"}
AST = {"planned", "ongoing", "completed", "needs-review"}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def props(path):
    t = (ROOT / path).read_text(encoding="utf-8")
    if not t.startswith("---\n"):
        return {}, t
    end = t.index("\n---\n", 3)
    try:
        return (yaml.safe_load(t[3:end + 1]) or {}), t[end + 4:]
    except Exception as e:
        return {"__parse_error__": str(e)}, t


print("B3a. vocabulary")
bad = []
for r in data["records"]:
    p, _ = props(r["note_path"])
    if "__parse_error__" in p:
        bad.append((r["key"], "yaml", p["__parse_error__"]))
        continue
    if p.get("record_type") not in RT:
        bad.append((r["key"], "record_type", p.get("record_type")))
    if p.get("status") not in ST:
        bad.append((r["key"], "status", p.get("status")))
    if p.get("type") != "record":
        bad.append((r["key"], "type", p.get("type")))
    for k in ("date", "event_date"):
        v = p.get(k)
        if v not in (None, "") and not ISO.match(str(v)):
            bad.append((r["key"], k, v))
    sy = str(p.get("school_year"))
    if sy not in ("None", "") and not re.match(r"^\d{4}-\d{4}$", sy):
        bad.append((r["key"], "school_year", sy))
    tg = p.get("tags") or []
    if not isinstance(tg, list) or not tg or tg[0] != "sslg":
        bad.append((r["key"], "tags", tg))
    man = {k: r.get(k) for k in ("record_type", "status", "date", "event_date", "school_year", "record_id", "source_file", "source_path")}
    for k, v in man.items():
        got = p.get(k)
        if (v if v is not None else None) != (got if got not in ("",) else None):
            bad.append((r["key"], "manifest-vs-note " + k, (got, v)))
print("   record problems:", len(bad))
for b in bad[:15]:
    print("      ", b)

print("\nB3b. hubs")
hbad = []
for a in data["activities"]:
    p, body = props(a["hub_path"])
    if "__parse_error__" in p:
        hbad.append((a["key"], "yaml", p["__parse_error__"]))
        continue
    if p.get("type") != "activity":
        hbad.append((a["key"], "type", p.get("type")))
    if p.get("status") != a["status"]:
        hbad.append((a["key"], "status", (p.get("status"), a["status"])))
    if p.get("status") not in AST:
        hbad.append((a["key"], "status-vocab", p.get("status")))
    for k in ("start_date", "end_date"):
        v = p.get(k)
        if v not in (None, "") and not ISO.match(str(v)):
            hbad.append((a["key"], k, v))
    if str(p.get("start_date")) != str(a.get("start_date")):
        hbad.append((a["key"], "start_date manifest-vs-hub", (p.get("start_date"), a.get("start_date"))))
    if str(p.get("end_date") or "") != str(a.get("end_date") or ""):
        hbad.append((a["key"], "end_date manifest-vs-hub", (p.get("end_date"), a.get("end_date"))))
    if p.get("title") != a["title"]:
        hbad.append((a["key"], "title", (p.get("title"), a["title"])))
    tg = p.get("tags") or []
    if not tg or tg[0] != "sslg":
        hbad.append((a["key"], "tags", tg))
print("   hub problems:", len(hbad))
for b in hbad[:15]:
    print("      ", b)

print("\nB3c. activity property on record notes")
prob = []
for r in data["records"]:
    p, _ = props(r["note_path"])
    act = p.get("activity")
    if r["activity"]:
        hub = [x for x in data["activities"] if x["key"] == r["activity"]][0]["hub_path"]
        if not act or hub not in str(act):
            prob.append((r["key"], "activity prop", act, hub))
    elif act:
        prob.append((r["key"], "activity set but manifest null", act, None))
print("   problems:", len(prob), prob[:5])

print("\nB3d. tags vocabulary across the 52 notes")
allt = Counter()
for r in data["records"]:
    p, _ = props(r["note_path"])
    for t in (p.get("tags") or []):
        allt[t] += 1
for a in data["activities"]:
    p, _ = props(a["hub_path"])
    for t in (p.get("tags") or []):
        allt[t] += 1
print("   ", dict(allt))
print("   notes whose tags do not start with sslg:", sum(1 for k in [r["note_path"] for r in data["records"]] + [a["hub_path"] for a in data["activities"]] if (props(k)[0].get("tags") or [""])[0] != "sslg"))
