import json
from pathlib import Path

from tools.sslg_notes import fmt, wikilink

BASES_YAML = """filters:
  and:
    - 'file.folder != "Scheduler_v1-main"'
    - 'file.folder != "99 Templates"'
views:
  - type: table
    name: All records
    filters:
      and:
        - 'type == "record"'
    order:
      - title
      - record_type
      - record_id
      - date
      - event_date
      - activity
      - status
      - source_file
  - type: table
    name: Proposals
    filters:
      and:
        - 'type == "record"'
        - 'record_type == "proposal"'
    order: [title, event_date, activity, status, source_file]
  - type: table
    name: Completion reports
    filters:
      and:
        - 'type == "record"'
        - 'record_type == "completion-report"'
    order: [title, event_date, activity, status, source_file]
  - type: table
    name: Memoranda
    filters:
      and:
        - 'type == "record"'
        - 'record_type == "memorandum"'
    order: [title, record_id, date, status, source_file]
  - type: table
    name: Needs review
    filters:
      and:
        - 'type == "record"'
        - 'needs_review == "yes"'
    order: [title, record_type, record_id, source_file]
  - type: table
    name: Activities needing review
    filters:
      and:
        - 'type == "activity"'
        - 'needs_review == "yes"'
    order: [title, start_date, status, venue]
"""

UNCHANGED_NOTICE = ("Original documents remain unchanged. Summaries are navigation aids; "
                    "use the Original document section for the complete official formatting.")

BASE_VIEWS = ("All records", "Proposals", "Completion reports", "Memoranda", "Needs review",
              "Activities needing review")

COLLECTION_LABELS = {
    "governance": "Governance",
    "external": "External Memoranda",
    "general": "General Records",
}

COLLECTION_FOLDERS = {
    "activities": ("02 Activities/", "activity hubs with their `Notes/` and `Sources/`."),
    "governance": ("03 Governance/", "SSLG policies, committees, and internal memoranda."),
    "external": ("04 External Memoranda/", "national, division, and cluster references."),
    "general": ("05 General Records/", "meetings and requests not tied to one activity."),
}

TEMPLATE_RECORD_SECTIONS = ("## Summary", "## Key details", "## Related records",
                            "## Revision history", "## Original document")


def _sorted_by_date(items, key):
    return sorted(items, key=lambda item: (0 if item.get(key) else 1, item.get(key) or "", item["title"]))


def render_home(data: dict) -> str:
    activities = data["activities"]
    records = data["records"]
    lines = [
        "---", "type: dashboard", "title: \"START HERE\"", "tags:", "  - sslg", "---", "",
        "# SSLG vault — START HERE", "",
        f"Benigno S. Aquino National High School SSLG records for School Year 2026–2027: "
        f"{len(activities)} activities, {len(records)} logical records.", "",
        "> [!info] How to read this vault",
        f"> {UNCHANGED_NOTICE}", "", "## Reading routes", "",
        f"- {wikilink('01 Dashboards/Activity Dashboard.md', 'Activity Dashboard')} — one hub per activity, with its trail.",
        f"- {wikilink('01 Dashboards/Document Library.md', 'Document Library')} — filterable Bases tables of every record.",
        f"- {wikilink('01 Dashboards/Timeline.md', 'Timeline')} — activity dates kept apart from issuance dates.",
        f"- {wikilink('01 Dashboards/Review Queue.md', 'Review Queue')} — unresolved version and relationship questions.", "",
        "## Collections", "",
    ]
    for collection, label in COLLECTION_LABELS.items():
        members = [record for record in records if record["collection"] == collection]
        lines.append(f"### {label}")
        lines.append("")
        if members:
            for record in _sorted_by_date(members, "event_date"):
                lines.append(f"- {wikilink(record['note_path'], record['title'])} — {record['status']}")
        else:
            lines.append("No records are filed in this collection.")
        lines.append("")
    lines.extend(["## Activities", ""])
    for activity in _sorted_by_date(activities, "start_date"):
        lines.append(f"- {wikilink(activity['hub_path'], activity['title'])} — {activity['status']}")
    lines.extend(["", "## Archive and templates", "",
                  f"- {wikilink('90 Archive/Archive Index.md', 'Archive Index')} — where every original "
                  "file came from, where it is now, and its SHA-256.",
                  f"- {wikilink('90 Archive/File Manifest.json', 'File Manifest')} — the same inventory in "
                  "machine-readable form.",
                  f"- {wikilink('99 Templates/Activity Template.md', 'Activity Template')} — start a new activity hub.",
                  f"- {wikilink('99 Templates/Record Template.md', 'Record Template')} — start a new record note.", ""])
    lines.extend(["## Not part of this vault", "",
                  "`Scheduler_v1-main/` is a separate application kept in place unchanged; "
                  "its files are excluded from these dashboards and from the Bases views.", "",
                  "`tools/` holds the scripts that build and validate these notes and `docs/` holds this "
                  "project's spec and plan. Neither contains SSLG records.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_activity_dashboard(data: dict) -> str:
    activities = _sorted_by_date(data["activities"], "start_date")
    counts = {}
    for record in data["records"]:
        counts[record["activity"]] = counts.get(record["activity"], 0) + 1
    lines = [
        "---", "type: dashboard", "title: \"Activity Dashboard\"", "tags:", "  - sslg", "---", "",
        "# Activity Dashboard", "", "> [!info]", f"> {UNCHANGED_NOTICE}", "",
        f"{len(activities)} activities, {len(data['records'])} logical records. "
        "Sorted by activity start date; activities without a stated date appear last.", "",
        "| Activity | Start date | End date | School year | Status | Records | Venue |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for activity in activities:
        lines.append(
            f"| {wikilink(activity['hub_path'], activity['title'])} "
            f"| {fmt(activity['start_date'])} | {fmt(activity['end_date'])} "
            f"| {fmt(activity['school_year'])} | {activity['status']} "
            f"| {counts.get(activity['key'], 0)} | {fmt(activity['venue'])} |"
        )
    lines.extend(["", "## Where to go from here", "",
                  f"- Records by type: {wikilink('01 Dashboards/Document Library.md', 'Document Library')}",
                  f"- Dates in order: {wikilink('01 Dashboards/Timeline.md', 'Timeline')}",
                  f"- Open questions: {wikilink('01 Dashboards/Review Queue.md', 'Review Queue')}", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_timeline(data: dict) -> str:
    records = data["records"]
    hubs = {activity["key"]: activity for activity in data["activities"]}
    activities = _sorted_by_date(data["activities"], "start_date")
    events = _sorted_by_date([r for r in records if r.get("event_date")], "event_date")
    issued = _sorted_by_date([r for r in records if r.get("date")], "date")
    undated = sorted([r for r in records if not r.get("date")], key=lambda r: r["title"])
    lines = [
        "---", "type: dashboard", "title: \"Timeline\"", "tags:", "  - sslg", "---", "",
        "# Timeline", "", "> [!info]",
        "> Activity and meeting dates are the dates an event happened. Record dates are the dates a document",
        "> was issued. The two are kept in separate tables so they are never read as one another.", "",
        "## Activity schedule", "", "| Start | End | Activity | Status | Venue |", "| --- | --- | --- | --- | --- |",
    ]
    for activity in activities:
        lines.append(f"| {fmt(activity['start_date'])} | {fmt(activity['end_date'])} "
                     f"| {wikilink(activity['hub_path'], activity['title'])} "
                     f"| {activity['status']} | {fmt(activity['venue'])} |")
    lines.extend(["", "## Activity and meeting dates", "",
                  "| Event date | Record | Type | Activity | Status |",
                  "| --- | --- | --- | --- | --- |"])
    for record in events:
        hub = hubs.get(record.get("activity"))
        lines.append(f"| {fmt(record['event_date'])} | {wikilink(record['note_path'], record['title'])} "
                     f"| {record['record_type']} "
                     f"| {wikilink(hub['hub_path'], hub['title']) if hub else 'Not tied to one activity'} "
                     f"| {record['status']} |")
    lines.extend(["", "## Record issuance dates", "", "| Record date | Record | Type | Status |",
                  "| --- | --- | --- | --- |"])
    for record in issued:
        lines.append(f"| {fmt(record['date'])} | {wikilink(record['note_path'], record['title'])} "
                     f"| {record['record_type']} | {record['status']} |")
    if undated:
        lines.extend(["", "### Records with no issuance date stated in source", ""])
        lines.extend(f"- {wikilink(record['note_path'], record['title'])}" for record in undated)
    return "\n".join(lines).rstrip() + "\n"


def render_review_queue(data: dict) -> str:
    flagged_activities = [a for a in data["activities"]
                          if a["status"] == "needs-review" or a.get("review_reasons")]
    flagged_records = [r for r in data["records"]
                       if r["status"] == "needs-review" or r.get("review_reasons")]
    lines = [
        "---", "type: dashboard", "title: \"Review Queue\"", "tags:", "  - sslg", "---", "",
        "# Review Queue", "", "> [!warning]",
        "> Every entry below is an open question about a primary version, a date, or a relationship.",
        "> Nothing here has been decided by guesswork; the source document is still the authority.", "",
        f"Needs review: {len(flagged_records)} records, {len(flagged_activities)} activities.", "",
        "## Records needing review", "",
    ]
    if flagged_records:
        for record in sorted(flagged_records, key=lambda r: r["title"]):
            lines.append(f"### {wikilink(record['note_path'], record['title'])}")
            lines.append("")
            lines.append(f"- Record type: {fmt(record.get('record_type'))}")
            lines.append(f"- Document ID: {fmt(record.get('record_id'))}")
            lines.append(f"- Status: {record['status']}")
            lines.append("- Open questions:")
            lines.extend(f"  - {reason}" for reason in record["review_reasons"])
            lines.append("")
    else:
        lines.extend(["No records need review.", ""])
    lines.extend(["## Activities needing review", ""])
    if flagged_activities:
        for activity in sorted(flagged_activities, key=lambda a: a["title"]):
            lines.append(f"### {wikilink(activity['hub_path'], activity['title'])}")
            lines.append("")
            lines.append(f"- Status: {activity['status']}")
            lines.append("- Open questions:")
            lines.extend(f"  - {reason}" for reason in activity["review_reasons"])
            lines.append("")
    else:
        lines.extend(["No activities need review.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_document_library(data: dict) -> str:
    records = data["records"]
    lines = [
        "---", "type: dashboard", "title: \"Document Library\"", "tags:", "  - sslg", "---", "",
        "# Document Library", "", "> [!info]", f"> {UNCHANGED_NOTICE}", "",
        "## Native Bases views", "", "Each view filters and sorts record notes and activity hubs live; "
        "open a row to read the note and its original document. The two review views match "
        "01 Dashboards/Review Queue.md exactly.", "",
    ]
    for view in BASE_VIEWS:
        lines.append(f"- **{view}**")
    lines.extend(["", "## Records base", "", "![[01 Dashboards/SSLG Records.base]]", "",
                  "## Folders", ""])
    for collection, (folder, description) in COLLECTION_FOLDERS.items():
        if any(record["collection"] == collection for record in records):
            lines.append(f"- `{folder}` — {description}")
    lines.extend(["- `80 Assets/` — images and supporting attachments.",
                  "- `90 Archive/` — superseded revisions, verified duplicates, and preserved staging files.",
                  "- `99 Templates/` — reusable activity and record templates.", "",
                  "`Scheduler_v1-main/` is a separate application and is excluded from every view.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_record_template() -> str:
    lines = [
        "---", "type: record", "title: \"{{title}}\"", "record_type: \"\"", "record_id: \"\"",
        "id_provenance: \"not-stated\"",
        "date: \"{{date:YYYY-MM-DD}}\"", "event_date: \"\"", "school_year: \"\"",
        "status: draft", "needs_review: \"no\"", "activity: \"\"", "source_file: \"\"", "source_path: \"\"",
        "source_format: \"\"", "sources:", "  - file: \"\"", "    path: \"\"",
        "    format: \"\"", "    role: primary", "related:", "  []", "tags:", "  - sslg", "---", "",
        "# {{title}}", "", "Part of the activity hub or collection this record belongs to.", "",
        "> [!info] At a glance",
        "> **Document ID:**",
        "> **Type:**",
        "> **Record date:** Not stated in source",
        "> **Event date:** Not stated in source",
        "> **School year:**",
        "> **Status:** draft", "",
        TEMPLATE_RECORD_SECTIONS[0], "", "Summarise only what the source states. "
        "Leave anything absent as `Not stated in source`.", "",
        TEMPLATE_RECORD_SECTIONS[1], "", "- Add one bullet per documented detail.", "",
        TEMPLATE_RECORD_SECTIONS[2], "", "No related records established from the supplied sources.", "",
        TEMPLATE_RECORD_SECTIONS[3], "", "No archived versions are associated with this record.", "",
        TEMPLATE_RECORD_SECTIONS[4], "",
        "DOCX files are linked with a prominent open link because Obsidian does not preview them. "
        "PDF files are embedded so the signed copy reads inside the vault.", "",
        "Record the exact source filename, its vault-relative path, and its format here.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_activity_template() -> str:
    lines = [
        "---", "type: activity", "title: \"{{title}}\"", "start_date: \"\"", "end_date: \"\"",
        "school_year: \"\"", "status: planned", "needs_review: \"no\"", "venue: \"\"", "tags:",
        "  - sslg", "  - activity", "---", "",
        "# {{title}}", "",
        "> [!info] At a glance",
        "> **Dates:** Not stated in source",
        "> **Venue:** Not stated in source",
        "> **Organizers:** Not stated in source",
        "> **School year:**",
        "> **Status:** planned",
        "> **Linked records:**", "",
        "## Summary", "", "One short source-derived paragraph. Leave anything the sources do not state "
        "as `Not stated in source`.", "",
        "## Activity trail", "", "Reading order: proposal, then meeting notices, letters, and requests, "
        "then memoranda, then the completion report.", "",
        "| Stage | Record | Type | Status |", "| --- | --- | --- | --- |",
        "|  |  |  |  |", "",
        "## Outcomes and follow-up", "", "State outcomes, challenges, actions, and recommendations "
        "only when the source records them.", "",
        "## Related governance", "", "List the policies or memoranda that explicitly govern this activity, "
        "citing the reference that appears in the source.", "",
        "## Original files", "", "List the record note for each source document, then the exact "
        "source filename beneath it.", "",
        "## Missing stages", "", "Name the stages no linked record covers: proposal, meeting notices, "
        "letters, and requests, memoranda, or the completion report.",
    ]
    return "\n".join(lines).rstrip() + "\n"


NAVIGATION_RENDERERS = {
    "START HERE.md": render_home,
    "01 Dashboards/Activity Dashboard.md": render_activity_dashboard,
    "01 Dashboards/Document Library.md": render_document_library,
    "01 Dashboards/Timeline.md": render_timeline,
    "01 Dashboards/Review Queue.md": render_review_queue,
    "01 Dashboards/SSLG Records.base": lambda data: BASES_YAML,
    "99 Templates/Activity Template.md": lambda data: render_activity_template(),
    "99 Templates/Record Template.md": lambda data: render_record_template(),
    ".obsidian/templates.json": lambda data: json.dumps({"folder": "99 Templates"}, indent=2) + "\n",
}

NAVIGATION_PATHS = tuple(NAVIGATION_RENDERERS)


def generate_navigation(root: Path, data: dict) -> list:
    outputs = [(root / path, renderer(data)) for path, renderer in NAVIGATION_RENDERERS.items()]
    collisions = [str(path) for path, _ in outputs if path.exists()]
    if collisions:
        raise FileExistsError("Refusing to overwrite navigation files:\n" + "\n".join(collisions))
    written = []
    for path, text in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written
