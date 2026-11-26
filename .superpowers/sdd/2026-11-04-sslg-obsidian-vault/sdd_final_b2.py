"""Final review B2: frontmatter <-> manifest agreement, date formats, hub properties (read-only)."""
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:/Users/Ma Christine/Downloads/SSLG MEMOS")
d = json.loads((ROOT / "tools/sslg_content.json").read_text(encoding="utf-8"))


def fm(path):
    t = (ROOT / path).read_text(encoding="utf-8")
    if not t.startswith("---\n"):
        return ""
    return t.split("\n")[1:t.split("\n").index("---", 1)]


def get(path, key):
    lines = fm(path)
    for l in lines:
        m = re.match(rf"^{re.escape(key)}:\s*(.*)$", l)
        if m:
            return m.group(1).strip().strip('"')
    return None


ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
bad = []
for r in d["records"]:
    p = r["note_path"]
    for key, exp in [("record_type", r["record_type"]), ("status", r["status"]), ("title", r["title"])]:
        got = get(p, key)
        if got != exp:
            bad.append((r["key"], key, got, exp))
    for key in ["date", "event_date", "school_year", "record_id"]:
        got = get(p, key)
        if got is None:
            bad.append((r["key"], key + " MISSING", None, None))
        elif got == "null":
            mf = r.get(key)
            if mf is not None:
                bad.append((r["key"], key + " null in note but set in manifest", got, mf))
        elif key in ("date", "event_date") and not ISO.match(got):
            bad.append((r["key"], key + " not ISO", got, None))
        elif key == "school_year" and not re.match(r"^\d{4}-\d{4}$", got):
            bad.append((r["key"], "school_year odd", got, None))
        elif key in ("date", "event_date", "record_id"):
            mf = r.get(key)
            if mf is not None and str(mf) != got:
                bad.append((r["key"], key + " value differs from manifest", got, mf))
    sf, sp = get(p, "source_file"), get(p, "source_path")
    m = re.search(r"(?m)^source_format:\s*(.*)$", "\n".join(fm(p)))
    sfm = m.group(1).strip().strip('"') if m else None
    if not (ROOT / sp).is_file():
        bad.append((r["key"], "source_path not on disk", sp, None))
    if Path(sp).name != sf:
        bad.append((r["key"], "source_file != basename(source_path)", sf, Path(sp).name))
    if sfm.lower() != Path(sp).suffix[1:].lower():
        bad.append((r["key"], "source_format != suffix", sfm, Path(sp).suffix))
    if sfm.lower() not in ("docx", "pdf"):
        bad.append((r["key"], "source_format outside spec (DOCX/PDF)", sfm, None))
    act = get(p, "activity")
    if r["activity"]:
        hub = [a for a in d["activities"] if a["key"] == r["activity"]][0]["hub_path"]
        if hub not in (act or ""):
            bad.append((r["key"], "activity property does not name the hub", act, hub))
    else:
        if act not in (None, "null", '""', ""):
            bad.append((r["key"], "activity set although manifest has none", act, None))

print("B2a. record frontmatter/manifest mismatches:", len(bad))
for b in bad:
    print("   ", b)

hbad = []
for a in d["activities"]:
    p = a["hub_path"]
    got = get(p, "status")
    if got != a["status"]:
        hbad.append((a["key"], "status", got, a["status"]))
    if get(p, "title") != a["title"]:
        hbad.append((a["key"], "title", get(p, "title"), a["title"]))
    sd = get(p, "start_date")
    if sd is None:
        hbad.append((a["key"], "start_date missing", None, a.get("start_date")))
    elif sd != "null" and not ISO.match(sd):
        hbad.append((a["key"], "start_date not ISO", sd, a.get("start_date")))
    ed, me = get(p, "end_date"), a.get("end_date")
    if (ed in (None, "null")) != (me is None):
        hbad.append((a["key"], "end_date presence", ed, me))
    elif ed not in (None, "null") and not ISO.match(ed):
        hbad.append((a["key"], "end_date not ISO", ed, me))
    if get(p, "type") != "activity":
        hbad.append((a["key"], "type", get(p, "type"), "activity"))
    if get(p, "school_year") != a.get("school_year"):
        hbad.append((a["key"], "school_year", get(p, "school_year"), a.get("school_year")))
print("\nB2b. hub frontmatter/manifest mismatches:", len(hbad))
for b in hbad:
    print("   ", b)

print("\nB2c. frontmatter sources list vs body 'Original document' attachment forms")
issues = []
for r in d["records"]:
    t = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    body = t.split("---\n", 2)[2]
    i = body.rfind("## Original document")
    sec = body[i:]
    embeds = re.findall(r"!\[\[([^\]|]+)", sec)
    links = re.findall(r"(?<!!)\[\[([^\]|]+)", sec)
    pdfs = [e for e in d["files"] if e["key"] in r["source_keys"] and e["current_path"].lower().endswith(".pdf")]
    docs = [e for e in d["files"] if e["key"] in r["source_keys"] and e["current_path"].lower().endswith(".docx")]
    for e in pdfs:
        if e["current_path"] not in embeds:
            issues.append((r["key"], "PDF not embedded", e["current_path"]))
    for e in docs:
        if e["current_path"] in embeds:
            issues.append((r["key"], "DOCX embedded (should be a link)", e["current_path"]))
        elif e["current_path"] not in links:
            issues.append((r["key"], "DOCX not linked", e["current_path"]))
    for x in embeds + links:
        if not (ROOT / x).is_file():
            issues.append((r["key"], "attachment target missing on disk", x))
    if len(pdfs) and not embeds:
        issues.append((r["key"], "note has PDFs but zero embeds", None))
print("   issues:", len(issues))
for x in issues[:15]:
    print("   ", x)

print("\nB2d. related: frontmatter list vs body Related records links")
prob = []
for r in d["records"]:
    t = (ROOT / r["note_path"]).read_text(encoding="utf-8")
    body = t.split("---\n", 2)[2]
    fml = "\n".join(fm(r["note_path"]))
    rel_lines = re.findall(r'^\s*-\s*"\[\[(.+?)\]\]"', fml, re.M)
    rel_targets = re.findall(r'(?:^## Related records\n)(.*?)(?:^## |\Z)', body, re.S | re.M)
    body_links = re.findall(r"\[\[([^\]|]+)", rel_targets[0]) if rel_targets else []
    for l in rel_lines:
        base = l.rsplit(".md", 1)[0] + ".md" if l.endswith(".md") else l
        if not any(base.endswith(Path(x).name) for x in body_links) and "No related" not in body and "no related" not in body.lower():
            prob.append((r["key"], "frontmatter related not rendered in body", l))
    if len(body_links) != len(rel_lines):
        prob.append((r["key"], f"body links {len(body_links)} != frontmatter {len(rel_lines)}", None))
print("   problems:", len(prob))
for p in prob[:12]:
    print("   ", p)
