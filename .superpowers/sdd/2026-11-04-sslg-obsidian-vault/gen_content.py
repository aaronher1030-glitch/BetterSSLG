"""Scratch builder for tools/sslg_content.json (not a vault artifact)."""
import importlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from tools.sslg_migration import collect_baseline, sha256

ROOT = Path(__file__).resolve().parents[3]

ACT = {
    "brigada-eskwela-2026": "Brigada Eskwela 2026",
    "club-fair-2026": "Club Fair 2026",
    "grade7-representative-election-2026": "SSLG Grade 7 Representative Elections 2026",
    "club-officers-election-2026": "Election of Registered School Clubs and Organizations 2026",
    "gpoa-crafting-2026": "Crafting of the SSLG General Plan of Action 2026",
    "leaders-induction-2026": "Onto the Next - Leaders Induction 2026",
    "project-ecolead-2026": "Project ECOLEAD",
    "project-tinig-2026": "Project TINIG",
    "project-liwanag-2026": "Project LIWANAG",
    "foundation-day-2026": "Foundation Day 2026",
    "world-teachers-day-2026": "World Teachers Day 2026",
    "national-students-day-2026": "National Students Day 2026",
    "cluster-iv-training-camp-2026": "Cluster IV SSLG Federation Leadership Training Camp",
    "short-film-festival-2026": "Municipal Short Film Festival 2026",
    "earthquake-drill-2026": "Earthquake Drill 2026",
    "digital-device-survey-2026": "Nationwide Online Survey on Digital Device Use",
}

COLLECTION_DIR = {
    "activities": "02 Activities",
    "governance": "03 Governance",
    "external": "04 External Memoranda",
    "general": "05 General Records",
    "revision": "90 Archive/Revisions",
    "duplicate": "90 Archive/Duplicates",
    "staged": "90 Archive/Staging",
}

SCHOOL_BODY = ("Supreme Secondary Learner Government (SSLG) and Learner Government "
               "Coordinating Council (LGCC), Benigno S. Aquino National High School")
ORGANIZER_OVERRIDES = {
    "cluster-iv-training-camp-2026": "Cluster IV SSLG Federation",
    "short-film-festival-2026": "Local Government Unit of Concepcion Social Welfare office",
    "digital-device-survey-2026": ("National Federation of SSLG, relayed by the Division SSLG "
                                   "Federation, Cluster IV Federation and the school SSLG"),
    "brigada-eskwela-2026": SCHOOL_BODY + ", with registered clubs and organizations",
    "earthquake-drill-2026": SCHOOL_BODY + ", with Red Cross Youth members",
}


def organizers_for(key):
    return [ORGANIZER_OVERRIDES.get(key, SCHOOL_BODY)]


def activity_rows():
    out = []
    for module in ("sdd_act_a", "sdd_act_b"):
        mod = importlib.import_module(module)
        out.extend(mod.ROWS)
    activities = []
    for key, start, end, venue, status, summary, outcomes, review in out:
        activities.append({
            "key": key,
            "title": ACT[key],
            "hub_path": f"02 Activities/{ACT[key]}/{ACT[key]}.md",
            "start_date": start,
            "end_date": end,
            "school_year": "2026-2027",
            "status": status,
            "venue": venue,
            "summary": summary,
            "organizers": organizers_for(key),
            "outcomes": outcomes,
            "review_reasons": review,
        })
    return activities


def record_rows():
    out = []
    for module in ("sdd_rec_a", "sdd_rec_b", "sdd_rec_c", "sdd_rec_d", "sdd_rec_e"):
        mod = importlib.import_module(module)
        out.extend(mod.ROWS)
    records = {}
    for key, title, rtype, rid, date, event, activity, collection, status, review, summary, details, related in out:
        records[key] = {
            "key": key,
            "title": title,
            "note_path": note_path(collection, activity, title),
            "record_type": rtype,
            "record_id": rid,
            "date": date,
            "event_date": event,
            "school_year": "2026-2027",
            "status": status,
            "activity": activity,
            "collection": collection,
            "summary": summary,
            "key_details": details,
            "source_keys": [],
            "related": related,
            "review_reasons": review,
        }
    return records


def source_text(path):
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as package:
            xml = package.read("word/document.xml").decode("utf-8", "ignore")
        return re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", xml))
    if path.suffix.lower() == ".pdf" and shutil.which("pdftotext"):
        return subprocess.run(["pdftotext", str(path), "-"], capture_output=True,
                              text=True, encoding="utf-8", errors="ignore").stdout or ""
    return ""


def normalise(text):
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def id_candidates(record_id):
    forms = {record_id, record_id.replace(" ", "-"), record_id.replace(" ", "_")}
    match = re.search(r"No\.\s*(\d{3}),?\s*s\.\s*(\d{4})", record_id)
    if match:
        forms.add(f"No. {match.group(1)}, s. {match.group(2)}")
    return {normalise(form) for form in forms if normalise(form)}


def declare_provenance(records, file_index):
    for record in records.values():
        if not record["record_id"]:
            record["id_provenance"] = "not-stated"
            continue
        texts = [source_text(ROOT / file_index[key]["current_path"]) for key in record["source_keys"]]
        readable = [text for text in texts if text.strip()]
        if not readable:
            record["id_provenance"] = "filename"
            continue
        blob = normalise(" ".join(readable))
        printed = any(candidate in blob for candidate in id_candidates(record["record_id"]))
        record["id_provenance"] = "printed" if printed else "filename"


def note_path(collection, activity, title):
    slug = title
    for char in '/\\:*?"<>|':
        slug = slug.replace(char, "-")
    if collection == "activities":
        return f"02 Activities/{ACT[activity]}/Notes/{slug}.md"
    return f"{COLLECTION_DIR[collection]}/{slug}.md"


def delivered_inventory():
    """Post-move the originals are gone from their pre-move paths, so the shipped
    File Manifest supplies the measured hashes and placed paths for them."""
    path = ROOT / "90 Archive" / "File Manifest.json"
    if not path.exists():
        return {}
    shipped = json.loads(path.read_text(encoding="utf-8"))
    return {entry["original_path"]: entry for entry in shipped["files"]}


def build():
    records = record_rows()
    files = []
    seen = set()
    shipped = delivered_inventory()
    for module in ("sdd_file_a", "sdd_file_b", "sdd_file_c", "sdd_file_d"):
        mod = importlib.import_module(module)
        for original, role, record, reason in mod.ROWS:
            if original in seen:
                raise SystemExit(f"duplicate file entry: {original}")
            seen.add(original)
            if record is not None and record not in records:
                raise SystemExit(f"unknown record for {original}: {record}")
            if (ROOT / original).exists():
                digest = sha256(ROOT / original)
            elif original in shipped:
                digest = shipped[original]["sha256"]
            else:
                raise SystemExit(f"source neither on disk nor in the delivered manifest: {original}")
            stem = Path(original).name
            key = stem.lower().replace(" ", "-")
            while key in {entry["key"] for entry in files}:
                key = f"{key}-staging"
            entry = {
                "key": key,
                "original_path": original,
                "sha256": digest,
                "role": role,
                "record_key": record,
                "archive_reason": reason,
            }
            if role == "asset":
                entry["current_path"] = f"80 Assets/{stem}"
            elif role in {"revision", "duplicate", "staged"}:
                entry["current_path"] = f"{COLLECTION_DIR[role]}/{stem}"
            else:
                rec = records[record]
                folder = ACT[rec["activity"]] if rec["collection"] == "activities" else COLLECTION_DIR[rec["collection"]]
                base = f"02 Activities/{folder}" if rec["collection"] == "activities" else folder
                entry["current_path"] = f"{base}/Sources/{stem}"
                rec["source_keys"].append(key)
            if shipped and shipped[original]["current_path"] != entry["current_path"]:
                raise SystemExit(f"placement disagrees with the delivered manifest: {original}")
            files.append(entry)

    file_index = {entry["key"]: entry for entry in files}
    expected = sorted(shipped) if shipped else sorted(collect_baseline(ROOT))
    missing = sorted(set(expected) - seen)
    extra = sorted(seen - set(expected))
    if missing or extra:
        raise SystemExit(f"coverage mismatch\nmissing={missing}\nextra={extra}")

    for record in records.values():
        if not record["source_keys"]:
            raise SystemExit(f"record without sources: {record['key']}")
        record["source_keys"].sort(key=lambda key: (
            0 if file_index[key]["role"] == "primary" else 1,
            1 if file_index[key]["current_path"].lower().endswith(".pdf") else 0,
        ))
        unknown = sorted(set(record["related"]) - set(records))
        if unknown:
            raise SystemExit(f"unknown related keys for {record['key']}: {unknown}")
        if record["status"] == "needs-review" and not record["review_reasons"]:
            raise SystemExit(f"needs-review without reason: {record['key']}")
    declare_provenance(records, file_index)

    protected = []
    for path in sorted((ROOT / "Scheduler_v1-main").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            protected.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)})

    data = {
        "activities": activity_rows(),
        "records": [records[key] for key in sorted(records)],
        "files": files,
        "protected_files": protected,
    }
    (ROOT / "tools" / "sslg_content.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(data['activities'])} activities, {len(data['records'])} records, "
          f"{len(data['files'])} files, {len(protected)} protected")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    build()
