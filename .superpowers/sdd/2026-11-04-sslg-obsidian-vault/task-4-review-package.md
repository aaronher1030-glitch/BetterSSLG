===== FILE: tools/sslg_navigation.py (323 lines) =====
import json
from pathlib import Path

from tools.sslg_notes import fmt, wikilink

NAVIGATION_PATHS = (
    "START HERE.md",
    "01 Dashboards/Activity Dashboard.md",
    "01 Dashboards/Document Library.md",
    "01 Dashboards/Timeline.md",
    "01 Dashboards/Review Queue.md",
    "01 Dashboards/SSLG Records.base",
    "99 Templates/Activity Template.md",
    "99 Templates/Record Template.md",
    ".obsidian/templates.json",
)

BASES_YAML = """filters:
  and:
    - 'file.folder != "Scheduler_v1-main"'
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
        - 'status == "needs-review"'
    order: [title, record_type, record_id, source_file]
"""

UNCHANGED_NOTICE = ("Original documents remain unchanged. Summaries are navigation aids; "
                    "use the Original document section for the complete official formatting.")

BASE_VIEWS = ("All records", "Proposals", "Completion reports", "Memoranda", "Needs review")

COLLECTION_LABELS = {
    "governance": "Governance",
    "external": "External Memoranda",
    "general": "General Records",
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
    lines.extend(["", "## Not part of this vault", "",
                  "`Scheduler_v1-main/` is a separate application kept in place unchanged; "
                  "its files are excluded from these dashboards and from the Bases views.", ""])
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


def render_document_library() -> str:
    lines = [
        "---", "type: dashboard", "title: \"Document Library\"", "tags:", "  - sslg", "---", "",
        "# Document Library", "", "> [!info]", f"> {UNCHANGED_NOTICE}", "",
        "## Native Bases views", "", "Each view filters and sorts record notes live; "
        "open a row to read the note and its original document.", "",
    ]
    for view in BASE_VIEWS:
        lines.append(f"- **{view}**")
    lines.extend(["", "## Records base", "", "![[01 Dashboards/SSLG Records.base]]", "",
                  "## Folders", "",
                  "- `02 Activities/` — activity hubs with their `Notes/` and `Sources/`.",
                  "- `03 Governance/` — SSLG policies, committees, and internal memoranda.",
                  "- `04 External Memoranda/` — national, division, and cluster references.",
                  "- `05 General Records/` — meetings and requests not tied to one activity.",
                  "- `80 Assets/` — images and supporting attachments.",
                  "- `90 Archive/` — superseded revisions, verified duplicates, and preserved staging files.",
                  "- `99 Templates/` — reusable activity and record templates.", "",
                  "`Scheduler_v1-main/` is a separate application and is excluded from every view.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_record_template() -> str:
    lines = [
        "---", "type: record", "title: \"{{title}}\"", "record_type: \"\"", "record_id: \"\"",
        "date: \"{{date:YYYY-MM-DD}}\"", "event_date: \"\"", "school_year: \"\"",
        "status: draft", "activity: \"\"", "source_file: \"\"", "source_path: \"\"",
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
        "school_year: \"\"", "status: planned", "venue: \"\"", "tags:", "  - sslg", "  - activity", "---", "",
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
        "| proposal |  |  |  |", "",
        "## Outcomes and follow-up", "", "State outcomes, challenges, actions, and recommendations "
        "only when the source records them.", "",
        "## Related governance", "", "List the policies or memoranda that explicitly govern this activity, "
        "citing the reference that appears in the source.", "",
        "## Original files", "", "List the record note for each source document, then the exact "
        "source filename beneath it.", "",
        "## Missing stages", "", "Not present in the supplied records: proposal.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def generate_navigation(root: Path, data: dict) -> list:
    outputs = [
        (root / "START HERE.md", render_home(data)),
        (root / "01 Dashboards/Activity Dashboard.md", render_activity_dashboard(data)),
        (root / "01 Dashboards/Document Library.md", render_document_library()),
        (root / "01 Dashboards/Timeline.md", render_timeline(data)),
        (root / "01 Dashboards/Review Queue.md", render_review_queue(data)),
        (root / "01 Dashboards/SSLG Records.base", BASES_YAML),
        (root / "99 Templates/Activity Template.md", render_activity_template()),
        (root / "99 Templates/Record Template.md", render_record_template()),
        (root / ".obsidian/templates.json", json.dumps({"folder": "99 Templates"}, indent=2) + "\n"),
    ]
    collisions = [str(path) for path, _ in outputs if path.exists()]
    if collisions:
        raise FileExistsError("Refusing to overwrite navigation files:\n" + "\n".join(collisions))
    written = []
    for path, text in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written

===== FILE: tools/tests/test_sslg_navigation.py (165 lines) =====
import json
import tempfile
import unittest
from pathlib import Path

from tools.sslg_navigation import (
    BASES_YAML,
    generate_navigation,
    render_activity_dashboard,
    render_activity_template,
    render_document_library,
    render_home,
    render_record_template,
    render_review_queue,
    render_timeline,
)


DATA = {
    "activities": [
        {
            "key": "act-b", "title": "Later Activity", "hub_path": "02 Activities/Later Activity/Later Activity.md",
            "start_date": "2026-09-15", "end_date": None, "school_year": "2026-2027", "status": "ongoing",
            "venue": "Hall", "summary": "Second.", "outcomes": [], "review_reasons": ["Venue is stated twice differently."],
        },
        {
            "key": "act-a", "title": "First Activity", "hub_path": "02 Activities/First Activity/First Activity.md",
            "start_date": "2026-07-22", "end_date": None, "school_year": "2026-2027", "status": "completed",
            "venue": "Multi-Purpose Hall", "summary": "First.", "outcomes": [], "review_reasons": [],
        },
    ],
    "records": [
        {
            "key": "r-open", "title": "Conflicted Memorandum", "note_path": "03 Governance/Conflicted.md",
            "record_type": "memorandum", "record_id": "OM_X_001", "date": None, "event_date": "2026-08-02",
            "school_year": "2026-2027", "status": "needs-review", "activity": None, "collection": "governance",
            "summary": "Conflicting.", "key_details": [], "source_keys": [], "related": [],
            "review_reasons": ["Two sources use different memorandum numbers."],
        },
        {
            "key": "r-signed", "title": "Signed Proposal", "note_path": "02 Activities/Later Activity/Notes/Signed Proposal.md",
            "record_type": "proposal", "record_id": "AP_X_002", "date": "2026-09-01", "event_date": "2026-09-15",
            "school_year": "2026-2027", "status": "signed", "activity": "act-b", "collection": "activities",
            "summary": "Fine.", "key_details": [], "source_keys": [], "related": [], "review_reasons": [],
        },
    ],
    "files": [],
    "protected_files": [],
}


class NavigationTests(unittest.TestCase):
    def test_home_exposes_all_reading_routes(self):
        text = render_home({"activities": [], "records": [], "files": []})
        for label in ("Activity Dashboard", "Document Library", "Timeline", "Review Queue", "Governance", "External Memoranda"):
            self.assertIn(label, text)
        self.assertIn("Original documents remain unchanged", text)

    def test_bases_has_native_views_and_excludes_scheduler(self):
        self.assertIn('type == "record"', BASES_YAML)
        self.assertIn('file.folder != "Scheduler_v1-main"', BASES_YAML)
        for view in ("All records", "Proposals", "Completion reports", "Memoranda", "Needs review"):
            self.assertIn(view, BASES_YAML)

    def test_review_queue_contains_reason_and_record_link(self):
        data = {
            "activities": [], "files": [],
            "records": [{
                "key": "r", "title": "Conflicted Memorandum", "note_path": "03 Governance/Conflicted.md",
                "status": "needs-review", "review_reasons": ["Two sources use different memorandum numbers."],
            }],
        }
        text = render_review_queue(data)
        self.assertIn("[[03 Governance/Conflicted.md|Conflicted Memorandum]]", text)
        self.assertIn("Two sources use different memorandum numbers.", text)

    def test_review_queue_lists_needs_review_activities_too(self):
        text = render_review_queue(DATA)
        self.assertIn("[[02 Activities/Later Activity/Later Activity.md|Later Activity]]", text)
        self.assertIn("Venue is stated twice differently.", text)
        self.assertNotIn("First Activity", text)

    def test_activity_dashboard_sorts_by_start_date_and_links_hubs(self):
        text = render_activity_dashboard(DATA)
        rows = [line for line in text.splitlines() if line.startswith("| [[02 Activities")]
        self.assertIn("First Activity.md|First Activity", rows[0])
        self.assertIn("Later Activity.md|Later Activity", rows[1])
        self.assertIn("2026-07-22", rows[0])
        undated = render_activity_dashboard(
            {"activities": [dict(DATA["activities"][0], start_date=None)] + DATA["activities"],
             "records": [], "files": []})
        undated_rows = [line for line in undated.splitlines() if line.startswith("| [[02 Activities")]
        self.assertIn("Not stated in source", undated_rows[-1])

    def test_timeline_separates_record_dates_from_event_dates(self):
        text = render_timeline(DATA)
        self.assertIn("## Activity schedule", text)
        self.assertIn("## Activity and meeting dates", text)
        self.assertIn("## Record issuance dates", text)
        issuance = text.split("## Record issuance dates")[1]
        events = [line for line in text.split("## Activity and meeting dates")[1]
                  .split("## Record issuance dates")[0].splitlines()
                  if line.startswith("|") and "[[" in line and not line.startswith("| ---")]
        issued = [line for line in issuance.splitlines()
                  if line.startswith("|") and "[[" in line and not line.startswith("| ---")]
        self.assertEqual(len(events), 2)
        self.assertEqual(len(issued), 1)
        self.assertIn("Signed Proposal.md|Signed Proposal", issued[0])
        self.assertIn("2026-09-01", issued[0])
        self.assertIn("Conflicted Memorandum", issuance)
        self.assertIn("no issuance date stated in source", issuance)

    def test_document_library_embeds_bases_and_explains_views(self):
        text = render_document_library()
        self.assertIn("![[01 Dashboards/SSLG Records.base]]", text)
        for view in ("All records", "Proposals", "Completion reports", "Memoranda", "Needs review"):
            self.assertIn(view, text)

    def test_templates_mirror_generated_notes_without_example_links(self):
        record_text = render_record_template()
        for prop in ("type: record", "record_type:", "record_id:", "date:", "event_date:", "school_year:",
                     "status:", "activity:", "source_file:", "source_path:", "source_format:", "related:", "tags:"):
            self.assertIn(prop, record_text)
        self.assertIn("{{title}}", record_text)
        self.assertIn("{{date:YYYY-MM-DD}}", record_text)
        self.assertEqual([line for line in record_text.splitlines() if line.startswith("## ")][-1],
                         "## Original document")
        self.assertNotIn("[[", record_text)
        activity_text = render_activity_template()
        for heading in ("## Activity trail", "## Outcomes and follow-up", "## Related governance",
                        "## Original files", "## Missing stages"):
            self.assertIn(heading, activity_text)
        self.assertEqual([line for line in activity_text.splitlines() if line.startswith("## ")],
                         ["## Summary", "## Activity trail", "## Outcomes and follow-up",
                          "## Related governance", "## Original files", "## Missing stages"])
        self.assertIn("> [!info] At a glance", activity_text)
        self.assertIn("> **Organizers:**", activity_text)
        self.assertIn("type: activity", activity_text)
        self.assertNotIn("[[", activity_text)

    def test_generate_navigation_writes_exactly_nine_files_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = generate_navigation(root, DATA)
            relative = sorted(str(path.relative_to(root).as_posix()) for path in written)
            self.assertEqual(relative, [
                ".obsidian/templates.json",
                "01 Dashboards/Activity Dashboard.md",
                "01 Dashboards/Document Library.md",
                "01 Dashboards/Review Queue.md",
                "01 Dashboards/SSLG Records.base",
                "01 Dashboards/Timeline.md",
                "99 Templates/Activity Template.md",
                "99 Templates/Record Template.md",
                "START HERE.md",
            ])
            self.assertEqual(json.loads((root / ".obsidian/templates.json").read_text(encoding="utf-8")),
                             {"folder": "99 Templates"})
            self.assertIn("Later Activity", (root / "01 Dashboards/Review Queue.md").read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                generate_navigation(root, DATA)


if __name__ == "__main__":
    unittest.main()

===== FILE: START HERE.md (64 lines) =====
---
type: dashboard
title: "START HERE"
tags:
  - sslg
---

# SSLG vault — START HERE

Benigno S. Aquino National High School SSLG records for School Year 2026–2027: 16 activities, 36 logical records.

> [!info] How to read this vault
> Original documents remain unchanged. Summaries are navigation aids; use the Original document section for the complete official formatting.

## Reading routes

- [[01 Dashboards/Activity Dashboard.md|Activity Dashboard]] — one hub per activity, with its trail.
- [[01 Dashboards/Document Library.md|Document Library]] — filterable Bases tables of every record.
- [[01 Dashboards/Timeline.md|Timeline]] — activity dates kept apart from issuance dates.
- [[01 Dashboards/Review Queue.md|Review Queue]] — unresolved version and relationship questions.

## Collections

### Governance

- [[03 Governance/Draft Memorandum - Standing Committee Distribution (Number and Date Blank).md|Draft Memorandum - Standing Committee Distribution (Number and Date Blank)]] — draft
- [[03 Governance/Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (25 May 2026).md|Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (25 May 2026)]] — final
- [[03 Governance/Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (27 May 2026).md|Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (27 May 2026)]] — final
- [[03 Governance/Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy.md|Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy]] — final

### External Memoranda

- [[04 External Memoranda/Cluster Federation Memorandum OM-CFSSLG-2026-003 - Nationwide Online Survey on Digital Device Use.md|Cluster Federation Memorandum OM-CFSSLG-2026-003 - Nationwide Online Survey on Digital Device Use]] — reference
- [[04 External Memoranda/Division Memorandum OM-DFSSLG-2026-003 - LGCC Mobilization for Brigada Eskwela 2026.md|Division Memorandum OM-DFSSLG-2026-003 - LGCC Mobilization for Brigada Eskwela 2026]] — reference
- [[04 External Memoranda/Division Memorandum OM-DFSSLG-2026-007 - Campus Journalism and SSLG Partnership.md|Division Memorandum OM-DFSSLG-2026-007 - Campus Journalism and SSLG Partnership]] — reference
- [[04 External Memoranda/Division Memorandum OM-DFSSLG-2026-010 - Nationwide Online Survey on Digital Device Use in Schools.md|Division Memorandum OM-DFSSLG-2026-010 - Nationwide Online Survey on Digital Device Use in Schools]] — reference
- [[04 External Memoranda/National Federation Memorandum OM-NFSSLG-2026-001 - Nationwide Online Survey on Digital Device Use in Schools.md|National Federation Memorandum OM-NFSSLG-2026-001 - Nationwide Online Survey on Digital Device Use in Schools]] — signed

### General Records

No records are filed in this collection.

## Activities

- [[02 Activities/Brigada Eskwela 2026/Brigada Eskwela 2026.md|Brigada Eskwela 2026]] — completed
- [[02 Activities/Club Fair 2026/Club Fair 2026.md|Club Fair 2026]] — completed
- [[02 Activities/SSLG Grade 7 Representative Elections 2026/SSLG Grade 7 Representative Elections 2026.md|SSLG Grade 7 Representative Elections 2026]] — completed
- [[02 Activities/Election of Registered School Clubs and Organizations 2026/Election of Registered School Clubs and Organizations 2026.md|Election of Registered School Clubs and Organizations 2026]] — completed
- [[02 Activities/Earthquake Drill 2026/Earthquake Drill 2026.md|Earthquake Drill 2026]] — completed
- [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Crafting of the SSLG General Plan of Action 2026.md|Crafting of the SSLG General Plan of Action 2026]] — completed
- [[02 Activities/Municipal Short Film Festival 2026/Municipal Short Film Festival 2026.md|Municipal Short Film Festival 2026]] — completed
- [[02 Activities/Onto the Next - Leaders Induction 2026/Onto the Next - Leaders Induction 2026.md|Onto the Next - Leaders Induction 2026]] — completed
- [[02 Activities/Nationwide Online Survey on Digital Device Use/Nationwide Online Survey on Digital Device Use.md|Nationwide Online Survey on Digital Device Use]] — ongoing
- [[02 Activities/National Students Day 2026/National Students Day 2026.md|National Students Day 2026]] — planned
- [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Cluster IV SSLG Federation Leadership Training Camp.md|Cluster IV SSLG Federation Leadership Training Camp]] — needs-review
- [[02 Activities/Foundation Day 2026/Foundation Day 2026.md|Foundation Day 2026]] — planned
- [[02 Activities/Project ECOLEAD/Project ECOLEAD.md|Project ECOLEAD]] — ongoing
- [[02 Activities/Project LIWANAG/Project LIWANAG.md|Project LIWANAG]] — ongoing
- [[02 Activities/Project TINIG/Project TINIG.md|Project TINIG]] — ongoing
- [[02 Activities/World Teachers Day 2026/World Teachers Day 2026.md|World Teachers Day 2026]] — needs-review

## Not part of this vault

`Scheduler_v1-main/` is a separate application kept in place unchanged; its files are excluded from these dashboards and from the Bases views.

===== FILE: 01 Dashboards/Activity Dashboard.md (38 lines) =====
---
type: dashboard
title: "Activity Dashboard"
tags:
  - sslg
---

# Activity Dashboard

> [!info]
> Original documents remain unchanged. Summaries are navigation aids; use the Original document section for the complete official formatting.

16 activities, 36 logical records. Sorted by activity start date; activities without a stated date appear last.

| Activity | Start date | End date | School year | Status | Records | Venue |
| --- | --- | --- | --- | --- | --- | --- |
| [[02 Activities/Brigada Eskwela 2026/Brigada Eskwela 2026.md|Brigada Eskwela 2026]] | 2026-06-01 | 2026-06-05 | 2026-2027 | completed | 3 | Benigno S. Aquino National High School |
| [[02 Activities/Club Fair 2026/Club Fair 2026.md|Club Fair 2026]] | 2026-06-01 | Not stated in source | 2026-2027 | completed | 1 | Benigno S. Aquino National High School |
| [[02 Activities/SSLG Grade 7 Representative Elections 2026/SSLG Grade 7 Representative Elections 2026.md|SSLG Grade 7 Representative Elections 2026]] | 2026-06-16 | 2026-06-25 | 2026-2027 | completed | 4 | Multi-Purpose Hall; Oreta Gymnasium |
| [[02 Activities/Election of Registered School Clubs and Organizations 2026/Election of Registered School Clubs and Organizations 2026.md|Election of Registered School Clubs and Organizations 2026]] | 2026-06-17 | Not stated in source | 2026-2027 | completed | 1 | Benigno S. Aquino National High School |
| [[02 Activities/Earthquake Drill 2026/Earthquake Drill 2026.md|Earthquake Drill 2026]] | 2026-06-24 | Not stated in source | 2026-2027 | completed | 1 | Benigno S. Aquino National High School |
| [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Crafting of the SSLG General Plan of Action 2026.md|Crafting of the SSLG General Plan of Action 2026]] | 2026-07-03 | Not stated in source | 2026-2027 | completed | 3 | Supreme Secondary Learner Government Office |
| [[02 Activities/Municipal Short Film Festival 2026/Municipal Short Film Festival 2026.md|Municipal Short Film Festival 2026]] | 2026-07-13 | Not stated in source | 2026-2027 | completed | 1 | Concepcion, Tarlac |
| [[02 Activities/Onto the Next - Leaders Induction 2026/Onto the Next - Leaders Induction 2026.md|Onto the Next - Leaders Induction 2026]] | 2026-07-22 | Not stated in source | 2026-2027 | completed | 2 | Multi-Purpose Hall |
| [[02 Activities/Nationwide Online Survey on Digital Device Use/Nationwide Online Survey on Digital Device Use.md|Nationwide Online Survey on Digital Device Use]] | 2026-08-25 | Not stated in source | 2026-2027 | ongoing | 5 | Online |
| [[02 Activities/National Students Day 2026/National Students Day 2026.md|National Students Day 2026]] | 2026-11-17 | 2026-11-18 | 2026-2027 | planned | 1 | Benigno S. Aquino National High School |
| [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Cluster IV SSLG Federation Leadership Training Camp.md|Cluster IV SSLG Federation Leadership Training Camp]] | Not stated in source | Not stated in source | 2026-2027 | needs-review | 2 | Not stated in source |
| [[02 Activities/Foundation Day 2026/Foundation Day 2026.md|Foundation Day 2026]] | Not stated in source | Not stated in source | 2026-2027 | planned | 1 | Benigno S. Aquino National High School |
| [[02 Activities/Project ECOLEAD/Project ECOLEAD.md|Project ECOLEAD]] | Not stated in source | Not stated in source | 2026-2027 | ongoing | 3 | Benigno S. Aquino National High School premises |
| [[02 Activities/Project LIWANAG/Project LIWANAG.md|Project LIWANAG]] | Not stated in source | Not stated in source | 2026-2027 | ongoing | 1 | Not stated in source |
| [[02 Activities/Project TINIG/Project TINIG.md|Project TINIG]] | Not stated in source | Not stated in source | 2026-2027 | ongoing | 1 | Not stated in source |
| [[02 Activities/World Teachers Day 2026/World Teachers Day 2026.md|World Teachers Day 2026]] | Not stated in source | Not stated in source | 2026-2027 | needs-review | 1 | Benigno S. Aquino National High School |

## Where to go from here

- Records by type: [[01 Dashboards/Document Library.md|Document Library]]
- Dates in order: [[01 Dashboards/Timeline.md|Timeline]]
- Open questions: [[01 Dashboards/Review Queue.md|Review Queue]]

===== FILE: 01 Dashboards/Document Library.md (37 lines) =====
---
type: dashboard
title: "Document Library"
tags:
  - sslg
---

# Document Library

> [!info]
> Original documents remain unchanged. Summaries are navigation aids; use the Original document section for the complete official formatting.

## Native Bases views

Each view filters and sorts record notes live; open a row to read the note and its original document.

- **All records**
- **Proposals**
- **Completion reports**
- **Memoranda**
- **Needs review**

## Records base

![[01 Dashboards/SSLG Records.base]]

## Folders

- `02 Activities/` — activity hubs with their `Notes/` and `Sources/`.
- `03 Governance/` — SSLG policies, committees, and internal memoranda.
- `04 External Memoranda/` — national, division, and cluster references.
- `05 General Records/` — meetings and requests not tied to one activity.
- `80 Assets/` — images and supporting attachments.
- `90 Archive/` — superseded revisions, verified duplicates, and preserved staging files.
- `99 Templates/` — reusable activity and record templates.

`Scheduler_v1-main/` is a separate application and is excluded from every view.

===== FILE: 01 Dashboards/Timeline.md (102 lines) =====
---
type: dashboard
title: "Timeline"
tags:
  - sslg
---

# Timeline

> [!info]
> Activity and meeting dates are the dates an event happened. Record dates are the dates a document
> was issued. The two are kept in separate tables so they are never read as one another.

## Activity schedule

| Start | End | Activity | Status | Venue |
| --- | --- | --- | --- | --- |
| 2026-06-01 | 2026-06-05 | [[02 Activities/Brigada Eskwela 2026/Brigada Eskwela 2026.md|Brigada Eskwela 2026]] | completed | Benigno S. Aquino National High School |
| 2026-06-01 | Not stated in source | [[02 Activities/Club Fair 2026/Club Fair 2026.md|Club Fair 2026]] | completed | Benigno S. Aquino National High School |
| 2026-06-16 | 2026-06-25 | [[02 Activities/SSLG Grade 7 Representative Elections 2026/SSLG Grade 7 Representative Elections 2026.md|SSLG Grade 7 Representative Elections 2026]] | completed | Multi-Purpose Hall; Oreta Gymnasium |
| 2026-06-17 | Not stated in source | [[02 Activities/Election of Registered School Clubs and Organizations 2026/Election of Registered School Clubs and Organizations 2026.md|Election of Registered School Clubs and Organizations 2026]] | completed | Benigno S. Aquino National High School |
| 2026-06-24 | Not stated in source | [[02 Activities/Earthquake Drill 2026/Earthquake Drill 2026.md|Earthquake Drill 2026]] | completed | Benigno S. Aquino National High School |
| 2026-07-03 | Not stated in source | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Crafting of the SSLG General Plan of Action 2026.md|Crafting of the SSLG General Plan of Action 2026]] | completed | Supreme Secondary Learner Government Office |
| 2026-07-13 | Not stated in source | [[02 Activities/Municipal Short Film Festival 2026/Municipal Short Film Festival 2026.md|Municipal Short Film Festival 2026]] | completed | Concepcion, Tarlac |
| 2026-07-22 | Not stated in source | [[02 Activities/Onto the Next - Leaders Induction 2026/Onto the Next - Leaders Induction 2026.md|Onto the Next - Leaders Induction 2026]] | completed | Multi-Purpose Hall |
| 2026-08-25 | Not stated in source | [[02 Activities/Nationwide Online Survey on Digital Device Use/Nationwide Online Survey on Digital Device Use.md|Nationwide Online Survey on Digital Device Use]] | ongoing | Online |
| 2026-11-17 | 2026-11-18 | [[02 Activities/National Students Day 2026/National Students Day 2026.md|National Students Day 2026]] | planned | Benigno S. Aquino National High School |
| Not stated in source | Not stated in source | [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Cluster IV SSLG Federation Leadership Training Camp.md|Cluster IV SSLG Federation Leadership Training Camp]] | needs-review | Not stated in source |
| Not stated in source | Not stated in source | [[02 Activities/Foundation Day 2026/Foundation Day 2026.md|Foundation Day 2026]] | planned | Benigno S. Aquino National High School |
| Not stated in source | Not stated in source | [[02 Activities/Project ECOLEAD/Project ECOLEAD.md|Project ECOLEAD]] | ongoing | Benigno S. Aquino National High School premises |
| Not stated in source | Not stated in source | [[02 Activities/Project LIWANAG/Project LIWANAG.md|Project LIWANAG]] | ongoing | Not stated in source |
| Not stated in source | Not stated in source | [[02 Activities/Project TINIG/Project TINIG.md|Project TINIG]] | ongoing | Not stated in source |
| Not stated in source | Not stated in source | [[02 Activities/World Teachers Day 2026/World Teachers Day 2026.md|World Teachers Day 2026]] | needs-review | Benigno S. Aquino National High School |

## Activity and meeting dates

| Event date | Record | Type | Activity | Status |
| --- | --- | --- | --- | --- |
| 2026-05-15 | [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Notes/Notice of Meeting NOM-SSLG-2026-001 - Cluster IV Leadership Training Camp Preparation.md|Notice of Meeting NOM-SSLG-2026-001 - Cluster IV Leadership Training Camp Preparation]] | meeting-notice | [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Cluster IV SSLG Federation Leadership Training Camp.md|Cluster IV SSLG Federation Leadership Training Camp]] | final |
| 2026-05-16 | [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Notes/Notice of Meeting - Cluster IV Leadership Training Camp and Organizational Alignment (16 May 2026).md|Notice of Meeting - Cluster IV Leadership Training Camp and Organizational Alignment (16 May 2026)]] | meeting-notice | [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Cluster IV SSLG Federation Leadership Training Camp.md|Cluster IV SSLG Federation Leadership Training Camp]] | final |
| 2026-05-31 | [[02 Activities/Brigada Eskwela 2026/Notes/Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela 2026 and LGCC Standing Committees.md|Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela 2026 and LGCC Standing Committees]] | meeting-notice | [[02 Activities/Brigada Eskwela 2026/Brigada Eskwela 2026.md|Brigada Eskwela 2026]] | final |
| 2026-06-01 | [[02 Activities/Club Fair 2026/Notes/Activity Completion Report ACR-SSLG-2026-003 - Club Fair 2026.md|Activity Completion Report ACR-SSLG-2026-003 - Club Fair 2026]] | completion-report | [[02 Activities/Club Fair 2026/Club Fair 2026.md|Club Fair 2026]] | final |
| 2026-06-05 | [[02 Activities/Brigada Eskwela 2026/Notes/Activity Completion Report ACR-SSLG-2026-001 - Brigada Eskwela 2026.md|Activity Completion Report ACR-SSLG-2026-001 - Brigada Eskwela 2026]] | completion-report | [[02 Activities/Brigada Eskwela 2026/Brigada Eskwela 2026.md|Brigada Eskwela 2026]] | final |
| 2026-06-07 | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela Post-Evaluation and SSLG GPOA.md|Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela Post-Evaluation and SSLG GPOA]] | meeting-notice | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Crafting of the SSLG General Plan of Action 2026.md|Crafting of the SSLG General Plan of Action 2026]] | final |
| 2026-06-17 | [[02 Activities/Election of Registered School Clubs and Organizations 2026/Notes/Activity Completion Report ACR-SSLG-2026-004 - Election of Registered School Clubs and Organizations.md|Activity Completion Report ACR-SSLG-2026-004 - Election of Registered School Clubs and Organizations]] | completion-report | [[02 Activities/Election of Registered School Clubs and Organizations 2026/Election of Registered School Clubs and Organizations 2026.md|Election of Registered School Clubs and Organizations 2026]] | final |
| 2026-06-24 | [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Excuse Letter EL-SSLG-2026-004 - SSLG Grade 7 Representative Miting de Avance.md|Excuse Letter EL-SSLG-2026-004 - SSLG Grade 7 Representative Miting de Avance]] | excuse-letter | [[02 Activities/SSLG Grade 7 Representative Elections 2026/SSLG Grade 7 Representative Elections 2026.md|SSLG Grade 7 Representative Elections 2026]] | final |
| 2026-06-24 | [[02 Activities/Earthquake Drill 2026/Notes/Excuse Letter EL-SSLG-2026-005 - Earthquake Drill.md|Excuse Letter EL-SSLG-2026-005 - Earthquake Drill]] | excuse-letter | [[02 Activities/Earthquake Drill 2026/Earthquake Drill 2026.md|Earthquake Drill 2026]] | final |
| 2026-06-25 | [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Activity Completion Report ACR-SSLG-2026-002 - SSLG Grade 7 Representative Elections.md|Activity Completion Report ACR-SSLG-2026-002 - SSLG Grade 7 Representative Elections]] | completion-report | [[02 Activities/SSLG Grade 7 Representative Elections 2026/SSLG Grade 7 Representative Elections 2026.md|SSLG Grade 7 Representative Elections 2026]] | final |
| 2026-06-25 | [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections.md|Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections]] | excuse-letter | [[02 Activities/SSLG Grade 7 Representative Elections 2026/SSLG Grade 7 Representative Elections 2026.md|SSLG Grade 7 Representative Elections 2026]] | needs-review |
| 2026-07-03 | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Activity Completion Report ACR-SSLG-2026-005 - Crafting of the General Plan of Action (GPOA).md|Activity Completion Report ACR-SSLG-2026-005 - Crafting of the General Plan of Action (GPOA)]] | completion-report | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Crafting of the SSLG General Plan of Action 2026.md|Crafting of the SSLG General Plan of Action 2026]] | final |
| 2026-07-03 | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Notice of Meeting NOM-SSLG-2026-004 - SSLG General Plan of Action Presentation.md|Notice of Meeting NOM-SSLG-2026-004 - SSLG General Plan of Action Presentation]] | meeting-notice | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Crafting of the SSLG General Plan of Action 2026.md|Crafting of the SSLG General Plan of Action 2026]] | signed |
| 2026-07-13 | [[02 Activities/Municipal Short Film Festival 2026/Notes/Excuse Letter EL-SSLG-2026-010 - Municipal Short Film Festival.md|Excuse Letter EL-SSLG-2026-010 - Municipal Short Film Festival]] | excuse-letter | [[02 Activities/Municipal Short Film Festival 2026/Municipal Short Film Festival 2026.md|Municipal Short Film Festival 2026]] | final |
| 2026-07-22 | [[02 Activities/Onto the Next - Leaders Induction 2026/Notes/Activity Completion Report ACR-SSLG-2026-006 - Onto the Next- Leaders Induction Ceremony.md|Activity Completion Report ACR-SSLG-2026-006 - Onto the Next: Leaders Induction Ceremony]] | completion-report | [[02 Activities/Onto the Next - Leaders Induction 2026/Onto the Next - Leaders Induction 2026.md|Onto the Next - Leaders Induction 2026]] | final |
| 2026-07-22 | [[02 Activities/Onto the Next - Leaders Induction 2026/Notes/Activity Proposal AP-SSLG-2026-001 - Onto the Next- Leaders 2026-2027 Induction Ceremony.md|Activity Proposal AP-SSLG-2026-001 - Onto the Next: Leaders 2026-2027 Induction Ceremony]] | proposal | [[02 Activities/Onto the Next - Leaders Induction 2026/Onto the Next - Leaders Induction 2026.md|Onto the Next - Leaders Induction 2026]] | final |
| 2026-07-31 | [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD.md|Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD]] | memorandum | [[02 Activities/Project ECOLEAD/Project ECOLEAD.md|Project ECOLEAD]] | needs-review |
| 2026-08-07 | [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD.md|Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD]] | memorandum | [[02 Activities/Project ECOLEAD/Project ECOLEAD.md|Project ECOLEAD]] | needs-review |
| 2026-10-02 | [[02 Activities/World Teachers Day 2026/Notes/Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration.md|Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration]] | proposal | [[02 Activities/World Teachers Day 2026/World Teachers Day 2026.md|World Teachers Day 2026]] | needs-review |
| 2026-11-17 | [[02 Activities/National Students Day 2026/Notes/Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration.md|Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration]] | proposal | [[02 Activities/National Students Day 2026/National Students Day 2026.md|National Students Day 2026]] | final |

## Record issuance dates

| Record date | Record | Type | Status |
| --- | --- | --- | --- |
| 2026-05-14 | [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Notes/Notice of Meeting - Cluster IV Leadership Training Camp and Organizational Alignment (16 May 2026).md|Notice of Meeting - Cluster IV Leadership Training Camp and Organizational Alignment (16 May 2026)]] | meeting-notice | final |
| 2026-05-14 | [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Notes/Notice of Meeting NOM-SSLG-2026-001 - Cluster IV Leadership Training Camp Preparation.md|Notice of Meeting NOM-SSLG-2026-001 - Cluster IV Leadership Training Camp Preparation]] | meeting-notice | final |
| 2026-05-16 | [[04 External Memoranda/Division Memorandum OM-DFSSLG-2026-003 - LGCC Mobilization for Brigada Eskwela 2026.md|Division Memorandum OM-DFSSLG-2026-003 - LGCC Mobilization for Brigada Eskwela 2026]] | memorandum | reference |
| 2026-05-25 | [[03 Governance/Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (25 May 2026).md|Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (25 May 2026)]] | memorandum | final |
| 2026-05-27 | [[03 Governance/Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (27 May 2026).md|Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (27 May 2026)]] | memorandum | final |
| 2026-05-29 | [[02 Activities/Brigada Eskwela 2026/Notes/Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela 2026 and LGCC Standing Committees.md|Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela 2026 and LGCC Standing Committees]] | meeting-notice | final |
| 2026-06-05 | [[04 External Memoranda/Division Memorandum OM-DFSSLG-2026-007 - Campus Journalism and SSLG Partnership.md|Division Memorandum OM-DFSSLG-2026-007 - Campus Journalism and SSLG Partnership]] | memorandum | reference |
| 2026-06-06 | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela Post-Evaluation and SSLG GPOA.md|Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela Post-Evaluation and SSLG GPOA]] | meeting-notice | final |
| 2026-06-22 | [[03 Governance/Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy.md|Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy]] | governance-policy | final |
| 2026-06-23 | [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Excuse Letter EL-SSLG-2026-004 - SSLG Grade 7 Representative Miting de Avance.md|Excuse Letter EL-SSLG-2026-004 - SSLG Grade 7 Representative Miting de Avance]] | excuse-letter | final |
| 2026-06-23 | [[02 Activities/Earthquake Drill 2026/Notes/Excuse Letter EL-SSLG-2026-005 - Earthquake Drill.md|Excuse Letter EL-SSLG-2026-005 - Earthquake Drill]] | excuse-letter | final |
| 2026-06-23 | [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections.md|Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections]] | excuse-letter | needs-review |
| 2026-06-25 | [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Request for Use of the Multi-Purpose Hall - Grade 7 Representatives Vote Consolidation.md|Request for Use of the Multi-Purpose Hall - Grade 7 Representatives Vote Consolidation]] | request | final |
| 2026-07-02 | [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Notice of Meeting NOM-SSLG-2026-004 - SSLG General Plan of Action Presentation.md|Notice of Meeting NOM-SSLG-2026-004 - SSLG General Plan of Action Presentation]] | meeting-notice | signed |
| 2026-07-13 | [[02 Activities/Municipal Short Film Festival 2026/Notes/Excuse Letter EL-SSLG-2026-010 - Municipal Short Film Festival.md|Excuse Letter EL-SSLG-2026-010 - Municipal Short Film Festival]] | excuse-letter | final |
| 2026-07-28 | [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD.md|Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD]] | memorandum | needs-review |
| 2026-08-03 | [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD.md|Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD]] | memorandum | needs-review |
| 2026-08-25 | [[04 External Memoranda/National Federation Memorandum OM-NFSSLG-2026-001 - Nationwide Online Survey on Digital Device Use in Schools.md|National Federation Memorandum OM-NFSSLG-2026-001 - Nationwide Online Survey on Digital Device Use in Schools]] | memorandum | signed |
| 2026-08-26 | [[04 External Memoranda/Division Memorandum OM-DFSSLG-2026-010 - Nationwide Online Survey on Digital Device Use in Schools.md|Division Memorandum OM-DFSSLG-2026-010 - Nationwide Online Survey on Digital Device Use in Schools]] | memorandum | reference |
| 2026-08-27 | [[02 Activities/Nationwide Online Survey on Digital Device Use/Notes/Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (27 August 2026).md|Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (27 August 2026)]] | memorandum | needs-review |
| 2026-08-28 | [[02 Activities/Nationwide Online Survey on Digital Device Use/Notes/Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (28 August 2026).md|Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (28 August 2026)]] | memorandum | signed |
| 2026-09-01 | [[04 External Memoranda/Cluster Federation Memorandum OM-CFSSLG-2026-003 - Nationwide Online Survey on Digital Device Use.md|Cluster Federation Memorandum OM-CFSSLG-2026-003 - Nationwide Online Survey on Digital Device Use]] | memorandum | reference |

### Records with no issuance date stated in source

- [[02 Activities/Brigada Eskwela 2026/Notes/Activity Completion Report ACR-SSLG-2026-001 - Brigada Eskwela 2026.md|Activity Completion Report ACR-SSLG-2026-001 - Brigada Eskwela 2026]]
- [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Activity Completion Report ACR-SSLG-2026-002 - SSLG Grade 7 Representative Elections.md|Activity Completion Report ACR-SSLG-2026-002 - SSLG Grade 7 Representative Elections]]
- [[02 Activities/Club Fair 2026/Notes/Activity Completion Report ACR-SSLG-2026-003 - Club Fair 2026.md|Activity Completion Report ACR-SSLG-2026-003 - Club Fair 2026]]
- [[02 Activities/Election of Registered School Clubs and Organizations 2026/Notes/Activity Completion Report ACR-SSLG-2026-004 - Election of Registered School Clubs and Organizations.md|Activity Completion Report ACR-SSLG-2026-004 - Election of Registered School Clubs and Organizations]]
- [[02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Activity Completion Report ACR-SSLG-2026-005 - Crafting of the General Plan of Action (GPOA).md|Activity Completion Report ACR-SSLG-2026-005 - Crafting of the General Plan of Action (GPOA)]]
- [[02 Activities/Onto the Next - Leaders Induction 2026/Notes/Activity Completion Report ACR-SSLG-2026-006 - Onto the Next- Leaders Induction Ceremony.md|Activity Completion Report ACR-SSLG-2026-006 - Onto the Next: Leaders Induction Ceremony]]
- [[02 Activities/Onto the Next - Leaders Induction 2026/Notes/Activity Proposal AP-SSLG-2026-001 - Onto the Next- Leaders 2026-2027 Induction Ceremony.md|Activity Proposal AP-SSLG-2026-001 - Onto the Next: Leaders 2026-2027 Induction Ceremony]]
- [[02 Activities/Project ECOLEAD/Notes/Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD.md|Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD]]
- [[02 Activities/Project TINIG/Notes/Activity Proposal AP-SSLG-2026-003 - Project TINIG.md|Activity Proposal AP-SSLG-2026-003 - Project TINIG]]
- [[02 Activities/Project LIWANAG/Notes/Activity Proposal AP-SSLG-2026-004 - Project LIWANAG.md|Activity Proposal AP-SSLG-2026-004 - Project LIWANAG]]
- [[02 Activities/Foundation Day 2026/Notes/Activity Proposal AP-SSLG-2026-005 - Foundation Day 2026.md|Activity Proposal AP-SSLG-2026-005 - Foundation Day 2026]]
- [[02 Activities/World Teachers Day 2026/Notes/Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration.md|Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration]]
- [[02 Activities/National Students Day 2026/Notes/Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration.md|Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration]]
- [[03 Governance/Draft Memorandum - Standing Committee Distribution (Number and Date Blank).md|Draft Memorandum - Standing Committee Distribution (Number and Date Blank)]]

===== FILE: 01 Dashboards/Review Queue.md (168 lines) =====
---
type: dashboard
title: "Review Queue"
tags:
  - sslg
---

# Review Queue

> [!warning]
> Every entry below is an open question about a primary version, a date, or a relationship.
> Nothing here has been decided by guesswork; the source document is still the authority.

Needs review: 8 records, 13 activities.

## Records needing review

### [[02 Activities/Foundation Day 2026/Notes/Activity Proposal AP-SSLG-2026-005 - Foundation Day 2026.md|Activity Proposal AP-SSLG-2026-005 - Foundation Day 2026]]

- Record type: proposal
- Document ID: AP_SSLG_2026_005
- Status: needs-review
- Open questions:
  - The single proposal copy states no activity date, so the Foundation Day schedule cannot be recorded from the source.

### [[02 Activities/World Teachers Day 2026/Notes/Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration.md|Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration]]

- Record type: proposal
- Document ID: AP_SSLG_2026_006
- Status: needs-review
- Open questions:
  - The three 'revised' copies state 2 October 2026 while AP_SSLG_2026_006 (3).docx states 5 October 2026; neither copy is signed and no later authority resolves the conflict.
  - Programme items also differ: the revised copies list an LGCC collaborative performance by named groups, the 5 October copy lists a generic LGCC performance.

### [[03 Governance/Draft Memorandum - Standing Committee Distribution (Number and Date Blank).md|Draft Memorandum - Standing Committee Distribution (Number and Date Blank)]]

- Record type: memorandum
- Document ID: No. ____, s. 2026
- Status: draft
- Open questions:
  - Document number and date are left blank and the memorandum issues from the Vice President rather than the President; no record establishes that it was released.

### [[02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections.md|Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections]]

- Record type: excuse-letter
- Document ID: EL_SSLG_2026_005
- Status: needs-review
- Open questions:
  - Two different letters dated 23 June 2026 both carry the number EL_SSLG_2026_005: one for the earthquake drill and one for the Grade 7 Representative Elections.

### [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD.md|Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD]]

- Record type: memorandum
- Document ID: OM SSLG No. 002, s. 2026
- Status: needs-review
- Open questions:
  - Five copies all numbered No. 002, s. 2026 carry different issuance dates (28 July, 21 September, 23 September 2026) and different implementation start dates (31 July, 22 September, 30 September 2026); none is signed and no later document resolves which issuance is operative.
  - Copies differ materially in content: OM_SSLG_2026_002 (1).docx and OM_SSLG_2026_002 (2).docx replace the body with the populated area rotation schedule and monitoring officer assignment matrix tables and omit the assessment rubric, recognition clause, OM-SSLG-2026-001 guidelines and General Provisions that appear only in OM_SSLG_2026_002.docx.

### [[02 Activities/Nationwide Online Survey on Digital Device Use/Notes/Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (27 August 2026).md|Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (27 August 2026)]]

- Record type: memorandum
- Document ID: OM SSLG No. 002, s. 2026
- Status: needs-review
- Open questions:
  - Memorandum No. 002, s. 2026 is used both for the Project ECOLEAD issuance of 28 July 2026 and for this survey issuance; the number alone cannot identify the record.
  - Six DOCX copies of the 27 August survey differ: some include the annex list and parental-consent paragraph and some do not.

### [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD.md|Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD]]

- Record type: memorandum
- Document ID: OM SSLG No. 003, s. 2026
- Status: needs-review
- Open questions:
  - Two copies dated 3 August 2026 with identical text carry conflicting numbers: OM_SSLG_2026_002 (7).docx reads No. 003 while OM_SSLG_2026_002 (8).docx reads No. 002; no silent winner was chosen.
  - The file names also disagree with the numbers printed inside the documents.

### [[03 Governance/Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy.md|Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy]]

- Record type: governance-policy
- Document ID: OM-SSLG-IA-2026-001
- Status: final
- Open questions:
  - The template still carries the placeholder '[School Name]' in the letterhead, so the issuing school was never filled in on this copy.

## Activities needing review

### [[02 Activities/Brigada Eskwela 2026/Brigada Eskwela 2026.md|Brigada Eskwela 2026]]

- Status: completed
- Open questions:
  - No activity proposal for Brigada Eskwela 2026 is present in this collection.

### [[02 Activities/Club Fair 2026/Club Fair 2026.md|Club Fair 2026]]

- Status: completed
- Open questions:
  - No activity proposal or authorising memorandum for the Club Fair is present in this collection.

### [[02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Cluster IV SSLG Federation Leadership Training Camp.md|Cluster IV SSLG Federation Leadership Training Camp]]

- Status: needs-review
- Open questions:
  - No document states the camp date, venue or outcome.
  - No proposal, authorising memorandum or completion report for the camp itself is present.

### [[02 Activities/Earthquake Drill 2026/Earthquake Drill 2026.md|Earthquake Drill 2026]]

- Status: completed
- Open questions:
  - Only the excuse letter documents this activity in the collection.

### [[02 Activities/Election of Registered School Clubs and Organizations 2026/Election of Registered School Clubs and Organizations 2026.md|Election of Registered School Clubs and Organizations 2026]]

- Status: completed
- Open questions:
  - No activity proposal for this election is present in this collection.

### [[02 Activities/Foundation Day 2026/Foundation Day 2026.md|Foundation Day 2026]]

- Status: planned
- Open questions:
  - No activity date is stated in the proposal.
  - No completion report is present in this collection.

### [[02 Activities/Municipal Short Film Festival 2026/Municipal Short Film Festival 2026.md|Municipal Short Film Festival 2026]]

- Status: completed
- Open questions:
  - No completion report is present in this collection.

### [[02 Activities/National Students Day 2026/National Students Day 2026.md|National Students Day 2026]]

- Status: planned
- Open questions:
  - No completion report is present in this collection.

### [[02 Activities/Nationwide Online Survey on Digital Device Use/Nationwide Online Survey on Digital Device Use.md|Nationwide Online Survey on Digital Device Use]]

- Status: ongoing
- Open questions:
  - No submission, canvassing or completion evidence is present in the collection; the memoranda state only the 4 September 2026 deadline.

### [[02 Activities/Project ECOLEAD/Project ECOLEAD.md|Project ECOLEAD]]

- Status: ongoing
- Open questions:
  - No completion report is present in this collection.
  - Memorandum copies state different implementation start dates: 31 July, 7 August, 22 September and 30 September 2026.

### [[02 Activities/Project LIWANAG/Project LIWANAG.md|Project LIWANAG]]

- Status: ongoing
- Open questions:
  - No completion report is present in this collection.

### [[02 Activities/Project TINIG/Project TINIG.md|Project TINIG]]

- Status: ongoing
- Open questions:
  - No completion report is present in this collection.

### [[02 Activities/World Teachers Day 2026/World Teachers Day 2026.md|World Teachers Day 2026]]

- Status: needs-review
- Open questions:
  - Proposal copies state conflicting celebration dates: 2 October 2026 in the files labelled 'revised' and 5 October 2026 in AP_SSLG_2026_006 (3).docx.
  - No completion report is present in this collection.

===== FILE: 01 Dashboards/SSLG Records.base (46 lines) =====
filters:
  and:
    - 'file.folder != "Scheduler_v1-main"'
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
        - 'status == "needs-review"'
    order: [title, record_type, record_id, source_file]

===== FILE: 99 Templates/Activity Template.md (50 lines) =====
---
type: activity
title: "{{title}}"
start_date: ""
end_date: ""
school_year: ""
status: planned
venue: ""
tags:
  - sslg
  - activity
---

# {{title}}

> [!info] At a glance
> **Dates:** Not stated in source
> **Venue:** Not stated in source
> **Organizers:** Not stated in source
> **School year:**
> **Status:** planned
> **Linked records:**

## Summary

One short source-derived paragraph. Leave anything the sources do not state as `Not stated in source`.

## Activity trail

Reading order: proposal, then meeting notices, letters, and requests, then memoranda, then the completion report.

| Stage | Record | Type | Status |
| --- | --- | --- | --- |
| proposal |  |  |  |

## Outcomes and follow-up

State outcomes, challenges, actions, and recommendations only when the source records them.

## Related governance

List the policies or memoranda that explicitly govern this activity, citing the reference that appears in the source.

## Original files

List the record note for each source document, then the exact source filename beneath it.

## Missing stages

Not present in the supplied records: proposal.

===== FILE: 99 Templates/Record Template.md (57 lines) =====
---
type: record
title: "{{title}}"
record_type: ""
record_id: ""
date: "{{date:YYYY-MM-DD}}"
event_date: ""
school_year: ""
status: draft
activity: ""
source_file: ""
source_path: ""
source_format: ""
sources:
  - file: ""
    path: ""
    format: ""
    role: primary
related:
  []
tags:
  - sslg
---

# {{title}}

Part of the activity hub or collection this record belongs to.

> [!info] At a glance
> **Document ID:**
> **Type:**
> **Record date:** Not stated in source
> **Event date:** Not stated in source
> **School year:**
> **Status:** draft

## Summary

Summarise only what the source states. Leave anything absent as `Not stated in source`.

## Key details

- Add one bullet per documented detail.

## Related records

No related records established from the supplied sources.

## Revision history

No archived versions are associated with this record.

## Original document

DOCX files are linked with a prominent open link because Obsidian does not preview them. PDF files are embedded so the signed copy reads inside the vault.

Record the exact source filename, its vault-relative path, and its format here.

===== FILE: .obsidian/templates.json (3 lines) =====
{
  "folder": "99 Templates"
}
