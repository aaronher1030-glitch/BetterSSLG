# Task 3 review package (non-git workspace: full file contents, no diff)
## Review scope
- Task brief: .superpowers\sdd\2026-11-04-sslg-obsidian-vault\task-3-brief.md
- Report: .superpowers\sdd\2026-11-04-sslg-obsidian-vault\task-3-report.md
- Spec: docs/superpowers/specs/2026-11-04-sslg-obsidian-vault-design.md

---
## tools/tests/test_sslg_notes.py (160 lines)

```python
import json
import tempfile
import unittest
from pathlib import Path

from tools.sslg_notes import generate_notes, render_activity, render_record


DATA = {
    "activities": [{
        "key": "activity-a", "title": "Activity A", "hub_path": "02 Activities/Activity A/Activity A.md",
        "start_date": "2026-07-22", "end_date": None, "school_year": "2026-2027",
        "status": "completed", "venue": "Hall", "summary": "Source-derived activity summary.",
        "outcomes": ["Documented outcome."], "review_reasons": [],
    }],
    "records": [{
        "key": "record-a", "title": "Proposal A",
        "note_path": "02 Activities/Activity A/Notes/Proposal A.md", "record_type": "proposal",
        "record_id": "AP_TEST_001", "date": None, "event_date": "2026-07-22",
        "school_year": "2026-2027", "status": "final", "activity": "activity-a",
        "collection": "activities", "summary": "Source-derived proposal summary.",
        "key_details": ["Documented detail."], "source_keys": ["word-source", "pdf-source"],
        "related": [], "review_reasons": [],
    }],
    "files": [
        {"key": "word-source", "original_path": "original.docx", "current_path": "02 Activities/Activity A/Sources/original.docx", "sha256": "a" * 64, "role": "primary", "record_key": "record-a", "archive_reason": ""},
        {"key": "pdf-source", "original_path": "signed.pdf", "current_path": "02 Activities/Activity A/Sources/signed.pdf", "sha256": "b" * 64, "role": "alternative-format", "record_key": "record-a", "archive_reason": ""},
        {"key": "old-copy", "original_path": "old.docx", "current_path": "90 Archive/Revisions/old.docx", "sha256": "c" * 64, "role": "revision", "record_key": "record-a", "archive_reason": "Superseded by final version."},
    ],
}


def record(key, title, record_type, note_path, **overrides):
    data = {
        "key": key, "title": title, "note_path": note_path, "record_type": record_type,
        "record_id": None, "date": None, "event_date": None, "school_year": "2026-2027",
        "status": "final", "activity": "activity-a", "collection": "activities",
        "summary": f"{title} summary.", "key_details": [], "source_keys": [f"{key}-docx"],
        "related": [], "review_reasons": [],
    }
    data.update(overrides)
    return data


def source(key, record_key, name, role="primary"):
    return {
        "key": key, "original_path": name,
        "current_path": f"02 Activities/Activity A/Sources/{name}",
        "sha256": "0" * 64, "role": role, "record_key": record_key, "archive_reason": "",
    }


MULTI = {
    "activities": [{
        "key": "activity-a", "title": "Activity A", "hub_path": "02 Activities/Activity A/Activity A.md",
        "start_date": "2026-09-01", "end_date": None, "school_year": "2026-2027",
        "status": "needs-review", "venue": "Hall", "summary": "Activity summary.",
        "outcomes": [], "review_reasons": ["Conflicting dates in source."],
    }],
    "records": [
        record("cr", "Completion Report", "completion-report",
               "02 Activities/Activity A/Notes/Completion Report.md"),
        record("mn", "Notice of Meeting", "meeting-notice",
               "02 Activities/Activity A/Notes/Notice of Meeting.md"),
        record("ap", "Proposal", "proposal", "02 Activities/Activity A/Notes/Proposal.md"),
        record("om", "Memorandum", "memorandum", "02 Activities/Activity A/Notes/Memorandum.md"),
    ],
    "files": [
        source("ap-docx", "ap", "ap.docx"), source("mn-docx", "mn", "mn.docx"),
        source("om-docx", "om", "om.docx"), source("cr-docx", "cr", "cr.docx"),
    ],
}


class NoteTests(unittest.TestCase):
    def test_record_has_traceable_metadata_and_original_document_last(self):
        text = render_record(DATA["records"][0], DATA)
        self.assertIn('record_id: "AP_TEST_001"', text)
        self.assertIn('source_path: "02 Activities/Activity A/Sources/original.docx"', text)
        self.assertIn("[[02 Activities/Activity A/Sources/original.docx|Open original DOCX: original.docx]]", text)
        self.assertIn("![[02 Activities/Activity A/Sources/signed.pdf]]", text)
        self.assertIn("[[90 Archive/Revisions/old.docx|old.docx]]", text)
        self.assertEqual(text.rstrip().splitlines()[-1], "![[02 Activities/Activity A/Sources/signed.pdf]]")
        self.assertEqual([line for line in text.splitlines() if line.startswith("## ")][-1], "## Original document")

    def test_activity_links_record_and_documents_missing_stages(self):
        text = render_activity(DATA["activities"][0], DATA)
        self.assertIn("[[02 Activities/Activity A/Notes/Proposal A.md|Proposal A]]", text)
        self.assertIn("Documented outcome.", text)
        self.assertIn("Not present in the supplied records", text)

    def test_record_lists_every_current_source_representation(self):
        text = render_record(DATA["records"][0], DATA)
        self.assertIn('  - file: "original.docx"', text)
        self.assertIn("    role: alternative-format", text)
        self.assertIn('  - file: "signed.pdf"', text)
        self.assertIn("source_format: docx", text)

    def test_record_states_missing_values_instead_of_guessing(self):
        text = render_record(DATA["records"][0], DATA)
        self.assertIn("date: null", text)
        self.assertIn("> **Record date:** Not stated in source", text)
        self.assertIn("No related records established from the supplied sources.", text)

    def test_record_flags_review_without_inventing_content(self):
        record_data = dict(DATA["records"][0], review_reasons=["Two copies disagree on the date."])
        text = render_record(record_data, DATA)
        self.assertIn("> [!warning] Review required", text)
        self.assertIn("> Two copies disagree on the date.", text)

    def test_activity_trail_orders_proposal_before_letters_then_completion(self):
        text = render_activity(MULTI["activities"][0], MULTI)
        rows = [line for line in text.splitlines() if line.startswith("|") and "[[" in line]
        order = [next(entry["title"] for entry in MULTI["records"]
                      if entry["note_path"] in line) for line in rows]
        self.assertEqual(order, ["Proposal", "Notice of Meeting", "Memorandum", "Completion Report"])
        self.assertIn("Every trail stage has a linked record.", text)

    def test_activity_lists_linked_source_files_under_original_files(self):
        text = render_activity(MULTI["activities"][0], MULTI)
        section = text.split("## Original files")[1]
        self.assertIn("  - [[02 Activities/Activity A/Sources/ap.docx|ap.docx]]", section)
        self.assertIn("  - [[02 Activities/Activity A/Sources/cr.docx|cr.docx]]", section)
        self.assertNotIn("[\n[\n0", section)

    def test_activity_reports_missing_stages_only_for_absent_record_types(self):
        single = json.loads(json.dumps(MULTI))
        single["records"] = [entry for entry in single["records"] if entry["key"] == "ap"]
        single["files"] = [entry for entry in single["files"] if entry["record_key"] == "ap"]
        text = render_activity(single["activities"][0], single)
        self.assertIn("Not present in the supplied records: meeting notices, letters, and requests.", text)
        self.assertIn("Not present in the supplied records: completion report.", text)
        self.assertNotIn("Not present in the supplied records: proposal.", text)
        self.assertIn("No outcomes are stated in the supplied records.", text)
        self.assertIn("> Conflicting dates in source.", text)

    def test_original_document_labels_each_current_format(self):
        text = render_record(DATA["records"][0], DATA)
        section = text.split("## Original document")[1]
        self.assertIn("**Primary DOCX (editable source): original.docx**", section)
        self.assertIn("Obsidian does not preview DOCX files", section)
        self.assertIn("**Alternative-format PDF (readable in Obsidian): signed.pdf**", section)

    def test_generate_notes_writes_every_note_and_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = generate_notes(root, MULTI)
            self.assertEqual(len(written), 5)
            for path in written:
                self.assertTrue(path.exists())
                self.assertTrue(path.read_text(encoding="utf-8").startswith("---\n"))
            self.assertEqual(sorted(p.name for p in written),
                             ["Activity A.md", "Completion Report.md", "Memorandum.md",
                              "Notice of Meeting.md", "Proposal.md"])
            with self.assertRaises(FileExistsError):
                generate_notes(root, MULTI)


if __name__ == "__main__":
    unittest.main()

```

---
## tools/tests/test_sslg_content.py (Task 2 file, one test appended) (79 lines)

```python
import json
import unittest
from pathlib import Path

from tools.sslg_migration import collect_baseline


ROOT = Path(__file__).resolve().parents[2]
CONTENT_PATH = ROOT / "tools" / "sslg_content.json"
ROLES = {"primary", "alternative-format", "revision", "duplicate", "staged", "asset"}
RECORD_TYPES = {
    "proposal", "completion-report", "memorandum", "meeting-notice",
    "excuse-letter", "request", "governance-policy",
}


class ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
        cls.files = cls.data["files"]
        cls.records = cls.data["records"]
        cls.activities = cls.data["activities"]

    def test_every_baseline_file_is_accounted_for_exactly_once(self):
        original_paths = [entry["original_path"] for entry in self.files]
        migrated_manifest = ROOT / "90 Archive" / "File Manifest.json"
        if migrated_manifest.exists():
            migrated = json.loads(migrated_manifest.read_text(encoding="utf-8"))
            baseline = sorted(entry["original_path"] for entry in migrated["files"])
        else:
            baseline = collect_baseline(ROOT)
        self.assertEqual(sorted(original_paths), baseline)
        self.assertEqual(len(original_paths), len(set(original_paths)))

    def test_file_entries_have_current_paths_hashes_and_roles(self):
        for entry in self.files:
            self.assertIn(entry["role"], ROLES)
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(entry["current_path"])
            self.assertNotEqual(entry["role"], "primary" if entry["original_path"].startswith("_DUPLICATES_TO_DELETE/") else "")

    def test_record_sources_and_relationships_resolve(self):
        file_keys = {entry["key"] for entry in self.files}
        record_keys = {record["key"] for record in self.records}
        activity_keys = {activity["key"] for activity in self.activities}
        for record in self.records:
            self.assertIn(record["record_type"], RECORD_TYPES)
            self.assertTrue(record["source_keys"])
            self.assertLessEqual(set(record["source_keys"]), file_keys)
            self.assertLessEqual(set(record["related"]), record_keys)
            self.assertNotIn(record["key"], record["related"])
            if record["activity"] is not None:
                self.assertIn(record["activity"], activity_keys)
            if record["status"] == "needs-review":
                self.assertTrue(record["review_reasons"])

    def test_every_non_asset_file_maps_to_a_logical_record_or_archive_reason(self):
        record_keys = {record["key"] for record in self.records}
        for entry in self.files:
            if entry["role"] == "asset":
                self.assertIsNone(entry.get("record_key"))
            else:
                self.assertIn(entry.get("record_key"), record_keys)
                self.assertTrue(entry.get("archive_reason") or entry["role"] in {"primary", "alternative-format"})


    def test_record_sources_order_primary_first_and_pdf_last(self):
        files = {entry["key"]: entry for entry in self.files}
        for record in self.records:
            sources = [files[key] for key in record["source_keys"]]
            self.assertEqual(sources[0]["role"], "primary", record["key"])
            formats = [Path(entry["current_path"]).suffix.lower() for entry in sources]
            if ".pdf" in formats:
                self.assertEqual(formats[-1], ".pdf", record["key"])


if __name__ == "__main__":
    unittest.main()

```

---
## tools/sslg_notes.py (204 lines)

```python
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
        f"date: {yaml_string(record['date'])}", f"event_date: {yaml_string(record['event_date'])}",
        f"school_year: {yaml_string(record['school_year'])}", f"status: {record['status']}",
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
        f"> **Document ID:** {fmt(record['record_id'])}",
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
        f"status: {activity['status']}", f"venue: {yaml_string(activity['venue'])}",
        "tags:", "  - sslg", "  - activity", "---", "", f"# {activity['title']}", "",
        "> [!info] At a glance",
        f"> **Dates:** {fmt(activity['start_date'])}"
        + (f" – {activity['end_date']}" if activity["end_date"] else ""),
        f"> **Venue:** {fmt(activity['venue'])}",
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
    lines.extend(["", "## Missing stages", ""])
    if missing:
        lines.extend(f"Not present in the supplied records: {item}." for item in missing)
    else:
        lines.append("Every trail stage has a linked record.")
    lines.extend(["", "## Original files", ""])
    if linked:
        for record_entry in _ordered_trail(linked):
            lines.append(f"- {wikilink(record_entry['note_path'], record_entry['title'])}")
            for key in record_entry["source_keys"]:
                path = files[key]["current_path"]
                lines.append(f"  - {wikilink(path, Path(path).name)}")
    else:
        lines.append("No original files are linked to this activity yet.")
    if activity["review_reasons"]:
        lines.extend(["", "> [!warning] Review required"])
        lines.extend(f"> {reason}" for reason in activity["review_reasons"])
    return "\n".join(lines).rstrip() + "\n"


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
    collisions = [str(path) for path, _ in outputs if path.exists()]
    if collisions:
        raise FileExistsError("Refusing to overwrite notes:\n" + "\n".join(collisions))
    written = []
    for path, text in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written

```

---
## Generated note samples (spot-check rendering)

### 02 Activities/Project ECOLEAD/Project ECOLEAD.md

```markdown
---
type: activity
title: "Project ECOLEAD"
start_date: null
end_date: null
school_year: "2026-2027"
status: ongoing
venue: "Benigno S. Aquino National High School premises"
tags:
  - sslg
  - activity
---

# Project ECOLEAD

> [!info] At a glance
> **Dates:** Not stated in source
> **Venue:** Benigno S. Aquino National High School premises
> **School year:** 2026-2027
> **Status:** ongoing
> **Linked records:** 3

## Summary

Project ECOLEAD, the Learner Government Coordinating Council school clean-up and environmental stewardship programme implemented twice a month throughout S.Y. 2026-2027.

## Activity trail

| Stage | Record | Type | Status |
| --- | --- | --- | --- |
| proposal | [[02 Activities/Project ECOLEAD/Notes/Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD.md|Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD]] | proposal | final |
| related memoranda | [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD.md|Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD]] | memorandum | needs-review |
| related memoranda | [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD.md|Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD]] | memorandum | needs-review |

## Outcomes and follow-up

- Clean-up activity designed for twice-monthly implementation with participating clubs and organizations.

## Missing stages

Not present in the supplied records: meeting notices, letters, and requests.
Not present in the supplied records: completion report.

## Original files

- [[02 Activities/Project ECOLEAD/Notes/Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD.md|Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD]]
  - [[02 Activities/Project ECOLEAD/Sources/AP_SSLG_2026_002.docx|AP_SSLG_2026_002.docx]]
- [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD.md|Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD]]
  - [[02 Activities/Project ECOLEAD/Sources/OM_SSLG_2026_002.docx|OM_SSLG_2026_002.docx]]
- [[02 Activities/Project ECOLEAD/Notes/Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD.md|Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD]]
  - [[02 Activities/Project ECOLEAD/Sources/OM_SSLG_2026_002 (7).docx|OM_SSLG_2026_002 (7).docx]]

> [!warning] Review required
> No completion report is present in this collection.
> Memorandum copies state different implementation start dates: 31 July, 7 August, 22 September and 30 September 2026.

```

### 02 Activities/National Students Day 2026/Notes/Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration.md

```markdown
---
type: record
title: "Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration"
record_type: proposal
record_id: "AP_SSLG_2026_007"
date: null
event_date: "2026-11-17"
school_year: "2026-2027"
status: final
activity: "[[02 Activities/National Students Day 2026/National Students Day 2026.md]]"
source_file: "AP_SSLG_2026_007_AnnexD_proofread.docx"
source_path: "02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD_proofread.docx"
source_format: docx
sources:
  - file: "AP_SSLG_2026_007_AnnexD_proofread.docx"
    path: "02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD_proofread.docx"
    format: docx
    role: primary
  - file: "AP_SSLG_2026_007_AnnexD.pdf"
    path: "02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD.pdf"
    format: pdf
    role: alternative-format
related:
  []
tags:
  - sslg
  - proposal
---

# Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration

Part of [[02 Activities/National Students Day 2026/National Students Day 2026.md|National Students Day 2026]].

> [!info] At a glance
> **Document ID:** AP_SSLG_2026_007
> **Type:** proposal
> **Record date:** Not stated in source
> **Event date:** 2026-11-17
> **School year:** 2026-2027
> **Status:** final

## Summary

Proposal for the 2026 National Students' Day celebration on 17-18 November 2026 under the theme Beyond Limits, Beyond Ordinary: The Aquinian Spirit, with the Annex D division submission version.

## Key details

- Anchored on Republic Act No. 11369, the National Students' Day Act.
- Annex D version adds a zumba segment from 3:00 P.M. to 5:00 P.M. with tickets and SPTA involvement.
- Proofread version cleans the title block and competition list.

## Related records

No related records established from the supplied sources.

## Revision history

- [[90 Archive/Duplicates/AP_SSLG_2026_007 (1).docx|AP_SSLG_2026_007 (1).docx]] — duplicate: byte-identical duplicate of AP_SSLG_2026_007.docx
- [[90 Archive/Duplicates/AP_SSLG_2026_007 (2).docx|AP_SSLG_2026_007 (2).docx]] — duplicate: byte-identical duplicate of AP_SSLG_2026_007.docx
- [[90 Archive/Revisions/AP_SSLG_2026_007.docx|AP_SSLG_2026_007.docx]] — revision: base proposal text without the Annex D programme additions
- [[90 Archive/Revisions/AP_SSLG_2026_007_AnnexD.docx|AP_SSLG_2026_007_AnnexD.docx]] — revision: Annex D division submission version superseded by AP_SSLG_2026_007_AnnexD_proofread.docx

## Original document

**Primary DOCX (editable source): AP_SSLG_2026_007_AnnexD_proofread.docx**
Obsidian does not preview DOCX files; the link opens the original file directly.

[[02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD_proofread.docx|Open original DOCX: AP_SSLG_2026_007_AnnexD_proofread.docx]]

**Alternative-format PDF (readable in Obsidian): AP_SSLG_2026_007_AnnexD.pdf**

![[02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD.pdf]]

```

### 03 Governance/Memorandum No. 001, s. 2026 - SSLG Standing Committees (27 May 2026).md

(not present)
