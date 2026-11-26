import json
from pathlib import Path


TRAIL_STAGES = (
    ("proposal", "proposal"),
    (("meeting-notice", "excuse-letter", "request"), "meeting notices, letters, and requests"),
    ("memorandum", "related memoranda"),
    ("completion-report", "completion report"),
)


def yaml_string(value) -> str:
    return "null" if value is None else json.dumps(str(value), ensure_ascii=False)


def wikilink(path: str, label: str | None = None) -> str:
    return f"[[{path}|{label}]]" if label else f"[[{path}]]"


def indexes(data: dict):
    activities = {item["key"]: item for item in data["activities"]}
    records = {item["key"]: item for item in data["records"]}
    files = {item["key"]: item for item in data["files"]}
    return activities, records, files


def fmt(value) -> str:
    return "Not stated in source" if value in (None, "") else str(value)


def review_flag(item: dict) -> str:
    return "yes" if item.get("review_reasons") or item.get("status") == "needs-review" else "no"


FILENAME_ID_NOTE = "(derived from the source filename; the document text does not print an identifier)"


def document_id_line(record: dict) -> str:
    if record["record_id"] and record.get("id_provenance") == "filename":
        return f"> **Document ID:** {record['record_id']} {FILENAME_ID_NOTE}"
    return f"> **Document ID:** {fmt(record['record_id'])}"


def render_record(record: dict, data: dict) -> str:
    activities, records, files = indexes(data)
    sources = [files[key] for key in record["source_keys"]]
    primary = sources[0]
    archived = [
        item for item in data["files"]
        if item.get("record_key") == record["key"] and item["key"] not in record["source_keys"]
    ]
    activity = activities.get(record["activity"])
    lines = [
        "---", "type: record", f"title: {yaml_string(record['title'])}",
        f"record_type: {record['record_type']}", f"record_id: {yaml_string(record['record_id'])}",
        f"id_provenance: {yaml_string(record.get('id_provenance'))}",
        f"date: {yaml_string(record['date'])}", f"event_date: {yaml_string(record['event_date'])}",
        f"school_year: {yaml_string(record['school_year'])}", f"status: {record['status']}",
        f"needs_review: {yaml_string(review_flag(record))}",
        f"activity: {yaml_string(wikilink(activity['hub_path']) if activity else '')}",
        f"source_file: {yaml_string(Path(primary['current_path']).name)}",
        f"source_path: {yaml_string(primary['current_path'])}",
        f"source_format: {Path(primary['current_path']).suffix[1:].lower()}", "sources:",
    ]
    for source in sources:
        lines.extend([
            f"  - file: {yaml_string(Path(source['current_path']).name)}",
            f"    path: {yaml_string(source['current_path'])}",
            f"    format: {Path(source['current_path']).suffix[1:].lower()}",
            f"    role: {source['role']}",
        ])
    lines.extend(["related:"])
    if record["related"]:
        lines.extend(f"  - {yaml_string(wikilink(records[key]['note_path']))}" for key in record["related"])
    else:
        lines.append("  []")
    lines.extend(["tags:", "  - sslg", f"  - {record['record_type']}", "---", "", f"# {record['title']}", ""])
    if activity:
        lines.extend([f"Part of {wikilink(activity['hub_path'], activity['title'])}.", ""])
    else:
        lines.extend([f"Part of the {record['collection'].replace('-', ' ')} collection.", ""])
    lines.extend([
        "> [!info] At a glance",
        document_id_line(record),
        f"> **Type:** {record['record_type']}",
        f"> **Record date:** {fmt(record['date'])}",
        f"> **Event date:** {fmt(record['event_date'])}",
        f"> **School year:** {fmt(record['school_year'])}",
        f"> **Status:** {record['status']}", "", "## Summary", "", record["summary"], "",
        "## Key details", "",
    ])
    lines.extend(f"- {detail}" for detail in record["key_details"])
    lines.extend(["", "## Related records", ""])
    if record["related"]:
        lines.extend(f"- {wikilink(records[key]['note_path'], records[key]['title'])}" for key in record["related"])
    else:
        lines.append("No related records established from the supplied sources.")
    lines.extend(["", "## Revision history", ""])
    if archived:
        lines.extend(
            f"- {wikilink(item['current_path'], Path(item['current_path']).name)} — {item['role']}: {item['archive_reason']}"
            for item in archived
        )
    else:
        lines.append("No archived versions are associated with this record.")
    if record["review_reasons"]:
        lines.extend(["", "> [!warning] Review required"])
        lines.extend(f"> {reason}" for reason in record["review_reasons"])
    lines.extend(["", "## Original document", ""])
    for source in sources:
        path = source["current_path"]
        name = Path(path).name
        role_label = "Primary" if source["role"] == "primary" else "Alternative-format"
        if path.lower().endswith(".pdf"):
            lines.extend([f"**{role_label} PDF (readable in Obsidian): {name}**", "", f"![[{path}]]", ""])
        else:
            lines.extend([f"**{role_label} DOCX (editable source): {name}**",
                          "Obsidian does not preview DOCX files; the link opens the original file directly.",
                          "", wikilink(path, f"Open original DOCX: {name}"), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_activity(activity: dict, data: dict) -> str:
    _, _, files = indexes(data)
    linked = [record for record in data["records"] if record["activity"] == activity["key"]]
    present = {record["record_type"] for record in linked}
    lines = [
        "---", "type: activity", f"title: {yaml_string(activity['title'])}",
        f"start_date: {yaml_string(activity['start_date'])}",
        f"end_date: {yaml_string(activity['end_date'])}",
        f"school_year: {yaml_string(activity['school_year'])}",
        f"status: {activity['status']}", f"needs_review: {yaml_string(review_flag(activity))}",
        f"venue: {yaml_string(activity['venue'])}",
        "tags:", "  - sslg", "  - activity", "---", "", f"# {activity['title']}", "",
        "> [!info] At a glance",
        f"> **Dates:** {fmt(activity['start_date'])}"
        + (f" – {activity['end_date']}" if activity["end_date"] else ""),
        f"> **Venue:** {fmt(activity['venue'])}",
        f"> **Organizers:** {_organizers_line(activity)}",
        f"> **School year:** {fmt(activity['school_year'])}",
        f"> **Status:** {activity['status']}",
        f"> **Linked records:** {len(linked)}", "", "## Summary", "", activity["summary"], "",
        "## Activity trail", "",
    ]
    if linked:
        lines.extend(["| Stage | Record | Type | Status |", "| --- | --- | --- | --- |"])
        for record in _ordered_trail(linked):
            lines.append(
                f"| {_stage_label(record['record_type'])} "
                f"| {wikilink(record['note_path'], record['title'])} "
                f"| {record['record_type']} | {record['status']} |"
            )
    else:
        lines.append("No records are linked to this activity yet.")
    missing = [label for stages, label in TRAIL_STAGES if not _stage_present(stages, present)]
    lines.extend(["", "## Outcomes and follow-up", ""])
    if activity["outcomes"]:
        lines.extend(f"- {outcome}" for outcome in activity["outcomes"])
    else:
        lines.append("No outcomes are stated in the supplied records.")
    lines.extend(["", "## Related governance", ""])
    governance = _related_governance(linked, data)
    if governance:
        for record_entry in governance:
            lines.append(f"- {wikilink(record_entry['note_path'], record_entry['title'])}")
    else:
        lines.append("No governing policy or memorandum is referenced by the linked records.")
    lines.extend(["", "## Original files", ""])
    if linked:
        for record_entry in _ordered_trail(linked):
            lines.append(f"- {wikilink(record_entry['note_path'], record_entry['title'])}")
            for key in record_entry["source_keys"]:
                path = files[key]["current_path"]
                lines.append(f"  - {wikilink(path, Path(path).name)}")
    else:
        lines.append("No original files are linked to this activity yet.")
    lines.extend(["", "## Missing stages", ""])
    if missing:
        lines.extend(f"Not present in the supplied records: {item}." for item in missing)
    else:
        lines.append("Every trail stage has a linked record.")
    if activity["review_reasons"]:
        lines.extend(["", "> [!warning] Review required"])
        lines.extend(f"> {reason}" for reason in activity["review_reasons"])
    return "\n".join(lines).rstrip() + "\n"


def _organizers_line(activity: dict) -> str:
    organizers = activity.get("organizers") or []
    return ", ".join(organizers) if organizers else "Not stated in the supplied records"


def _related_governance(linked: list, data: dict) -> list:
    _, records, _ = indexes(data)
    linked_keys = {record["key"] for record in linked}
    found = {}
    for record in linked:
        for key in record["related"]:
            other = records.get(key)
            if other is not None and other["collection"] in {"governance", "external"}:
                found[other["key"]] = other
    for other in data["records"]:
        if other["collection"] in {"governance", "external"} and linked_keys & set(other["related"]):
            found[other["key"]] = other
    return sorted(found.values(), key=lambda item: item["title"])


def _stage_present(stages, present: set) -> bool:
    wanted = stages if isinstance(stages, tuple) else (stages,)
    return any(stage in present for stage in wanted)


def _stage_rank(record_type: str) -> int:
    for rank, (stages, _) in enumerate(TRAIL_STAGES):
        if record_type in (stages if isinstance(stages, tuple) else (stages,)):
            return rank
    return len(TRAIL_STAGES)


def _stage_label(record_type: str) -> str:
    for stages, label in TRAIL_STAGES:
        if record_type in (stages if isinstance(stages, tuple) else (stages,)):
            return label
    return record_type


def _ordered_trail(linked: list) -> list:
    return sorted(linked, key=lambda record: (_stage_rank(record["record_type"]),
                                              record["date"] or record["event_date"] or "9999-99-99",
                                              record["title"]))


def generate_notes(root: Path, data: dict) -> list:
    outputs = []
    for activity in data["activities"]:
        outputs.append((root / activity["hub_path"], render_activity(activity, data)))
    for record in data["records"]:
        outputs.append((root / record["note_path"], render_record(record, data)))
    seen_paths = set()
    duplicates = []
    for path, _ in outputs:
        identity = str(path).casefold()
        if identity in seen_paths:
            duplicates.append(f"{path} is claimed more than once")
        seen_paths.add(identity)
    collisions = [str(path) for path, _ in outputs if path.exists()]
    if duplicates:
        raise FileExistsError("Refusing to overwrite notes:\n" + "\n".join(sorted(set(duplicates))))
    if collisions:
        raise FileExistsError("Refusing to overwrite notes:\n" + "\n".join(collisions))
    written = []
    for path, text in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written
