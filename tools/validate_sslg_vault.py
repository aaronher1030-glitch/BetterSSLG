"""Read-only acceptance checks for the finished SSLG vault."""
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.sslg_migration import safe_relative, sha256

WIKILINK = re.compile(r"!?\[\[([^\]]+)\]\]")
REQUIRED_NOTE_PROPERTIES = ("type", "title", "record_type", "record_id", "id_provenance", "date", "event_date",
                           "school_year", "status", "needs_review", "activity", "source_file", "source_path",
                           "source_format", "sources", "related", "tags")
REQUIRED_BASE_VIEWS = ("All records", "Proposals", "Completion reports", "Memoranda", "Needs review")
SOURCE_SUFFIXES = {".docx", ".pdf"}
VAULT_NOTE_PREFIXES = ("01 Dashboards/", "02 Activities/", "03 Governance/",
                       "04 External Memoranda/", "05 General Records/")


def _is_vault_note(relative: str) -> bool:
    if relative == "START HERE.md":
        return True
    return relative.startswith(VAULT_NOTE_PREFIXES) and not relative.startswith("01 Dashboards/SSLG Records")


def wikilink_targets(text: str) -> list:
    targets = []
    for match in WIKILINK.finditer(text):
        target = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            targets.append(target)
    return targets


def target_exists(root: Path, target: str) -> bool:
    if not safe_relative(target):
        return False
    direct = root / target
    return direct.exists() or (not direct.suffix and direct.with_suffix(".md").exists())


def _frontmatter(text: str) -> str:
    parts = text.split("---\n", 2)
    return parts[1] if len(parts) > 2 else ""


def _final_section(text: str) -> str:
    headings = [m.start() for m in re.finditer(r"(?m)^## ", text)]
    if not headings:
        return ""
    return text[headings[-1]:]


def _final_heading(text: str) -> str:
    headings = re.findall(r"(?m)^## (.+)$", text)
    return headings[-1].strip() if headings else ""


def validate_vault(root: Path, data: dict) -> list:
    errors = []
    root = Path(root)
    files = {entry["key"]: entry for entry in data["files"]}
    records = {entry["key"]: entry for entry in data["records"]}
    activities = {entry["key"]: entry for entry in data["activities"]}

    for entry in data["files"]:
        path = entry["current_path"]
        if not safe_relative(path):
            errors.append(f"unsafe current path for {entry['key']}: {path}")
            continue
        located = root / path
        if not located.exists():
            errors.append(f"missing file: {path} (manifest entry {entry['key']})")
            continue
        if sha256(located) != entry["sha256"]:
            errors.append(f"checksum mismatch: {path} (manifest entry {entry['key']})")

    for entry in data["protected_files"]:
        located = root / entry["path"]
        if not located.exists():
            errors.append(f"missing protected file: {entry['path']}")
        elif sha256(located) != entry["sha256"]:
            errors.append(f"checksum mismatch on protected file: {entry['path']}")
    scheduler = root / "Scheduler_v1-main"
    if scheduler.is_dir():
        expected = {entry["path"] for entry in data["protected_files"]
                    if entry["path"].startswith("Scheduler_v1-main/")}
        present = {path.relative_to(root).as_posix() for path in scheduler.rglob("*")
                   if path.is_file() and "__pycache__" not in path.parts}
        for extra in sorted(present - expected):
            errors.append(f"unexpected file under Scheduler_v1-main: {extra}")
        for absent in sorted(expected - present):
            errors.append(f"protected Scheduler file no longer present: {absent}")

    for activity in data["activities"]:
        hub = root / activity["hub_path"]
        if not hub.exists():
            errors.append(f"missing activity hub: {activity['hub_path']}")
            continue
        text = hub.read_text(encoding="utf-8")
        if "type: activity" not in _frontmatter(text):
            errors.append(f"hub without activity type: {activity['hub_path']}")
        for record_key in [record["key"] for record in data["records"] if record["activity"] == activity["key"]]:
            note_path = records[record_key]["note_path"]
            if note_path not in text:
                errors.append(f"hub {activity['hub_path']} does not link record {note_path}")

    for record in data["records"]:
        note = root / record["note_path"]
        if not note.exists():
            errors.append(f"missing record note: {record['note_path']}")
            continue
        text = note.read_text(encoding="utf-8")
        frontmatter = _frontmatter(text)
        for prop in REQUIRED_NOTE_PROPERTIES:
            if not re.search(rf"(?m)^{prop}:", frontmatter):
                errors.append(f"record note {record['note_path']} lacks property {prop}")
        if _final_heading(text) != "Original document":
            errors.append(f"record note {record['note_path']} final section is "
                          f"'{_final_heading(text)}' not 'Original document'")
            continue
        final = _final_section(text)
        for key in record["source_keys"]:
            path = files[key]["current_path"]
            if path not in final:
                errors.append(f"record note {record['note_path']} does not attach source {path}")

        for key in record["related"]:
            if key not in records:
                errors.append(f"record {record['key']} has unresolvable related key: {key}")
        if record["activity"] is not None and record["activity"] not in activities:
            errors.append(f"record {record['key']} points at unknown activity: {record['activity']}")

    declared_notes = {record["note_path"] for record in data["records"]}
    declared_notes.update(activity["hub_path"] for activity in data["activities"])
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if not (_is_vault_note(relative) or relative in declared_notes):
            continue
        text = path.read_text(encoding="utf-8")
        for target in wikilink_targets(text):
            if not target_exists(root, target):
                errors.append(f"broken wikilink in {relative}: {target}")

    queue_path = root / "01 Dashboards/Review Queue.md"
    queue = queue_path.read_text(encoding="utf-8") if queue_path.exists() else ""
    if not queue_path.exists():
        errors.append("missing Review Queue dashboard")
    for entry in list(data["records"]) + list(data["activities"]):
        reasons = entry.get("review_reasons") or []
        if not reasons:
            continue
        if entry["title"] not in queue:
            errors.append(f"Review Queue omits {entry['title']}")
        for reason in reasons:
            if reason not in queue:
                errors.append(f"Review Queue omits a reason of {entry['title']}: {reason}")

    loose = sorted(path.name for path in root.glob("*")
                   if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES)
    for name in loose:
        errors.append(f"loose source document still in the vault root: {name}")
    staging = root / "_DUPLICATES_TO_DELETE"
    if staging.exists() and any(staging.rglob("*")):
        errors.append("_DUPLICATES_TO_DELETE still contains files")

    base_path = root / "01 Dashboards/SSLG Records.base"
    if not base_path.exists():
        errors.append("missing native Bases document")
    else:
        base = base_path.read_text(encoding="utf-8")
        for view in REQUIRED_BASE_VIEWS:
            if f"name: {view}" not in base:
                errors.append(f"Bases lacks the {view} view")
        if 'file.folder != "Scheduler_v1-main"' not in base:
            errors.append("Bases does not exclude Scheduler_v1-main")

    delivered = root / "90 Archive" / "File Manifest.json"
    if not delivered.exists():
        errors.append("missing delivered inventory: 90 Archive/File Manifest.json")
    else:
        shipped = json.loads(delivered.read_text(encoding="utf-8"))
        for section in ("activities", "records", "files", "protected_files"):
            if shipped.get(section) != data[section]:
                errors.append(f"delivered File Manifest disagrees with the validated data: {section}")
    index_path = root / "90 Archive" / "Archive Index.md"
    if not index_path.exists():
        errors.append("missing Archive Index: 90 Archive/Archive Index.md")
    else:
        index = index_path.read_text(encoding="utf-8")
        for entry in data["files"]:
            if entry["current_path"] not in index:
                errors.append(f"Archive Index omits {entry['current_path']}")

    return errors


def main(argv=None) -> int:
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "tools" / "sslg_content.json").read_text(encoding="utf-8"))
    errors = validate_vault(root, data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"VALIDATION FAILED: {len(errors)} errors")
        return 1
    print(f"VALIDATION PASSED: {len(data['activities'])} activities, {len(data['records'])} records, "
          f"{len(data['files'])} files, {len(data['protected_files'])} protected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
