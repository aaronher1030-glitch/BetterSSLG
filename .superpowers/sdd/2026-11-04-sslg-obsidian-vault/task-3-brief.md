### Task 3: Record Notes and Activity Hubs

**Files:**
- Create: `tools/sslg_notes.py`
- Create: `tools/tests/test_sslg_notes.py`
- Read: `tools/sslg_content.json`

**Interfaces:**
- Consumes: the Task 2 `activities`, `records`, and `files` collections.
- Produces: `wikilink(path: str, label: str | None = None) -> str`, `render_record(record: dict, data: dict) -> str`, `render_activity(activity: dict, data: dict) -> str`, and `generate_notes(root: Path, data: dict) -> list[Path]`.

- [ ] **Step 1: Write failing source-placement and relationship tests**

```python
import unittest

from tools.sslg_notes import render_activity, render_record


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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify the import failure**

Run: `python -m unittest tools.tests.test_sslg_notes -v`  
Expected: FAIL because `tools.sslg_notes` does not exist.

- [ ] **Step 3: Implement deterministic rendering**

Use JSON string encoding for YAML scalar quoting, full vault-relative wikilinks, and the following public helpers. `metadata_lines` emits all required record properties, including singular primary-source fields plus a structured `sources` list for every current representation.

```python
import json
from pathlib import Path


def yaml_string(value) -> str:
    return "null" if value is None else json.dumps(str(value), ensure_ascii=False)


def wikilink(path: str, label: str | None = None) -> str:
    return f"[[{path}|{label}]]" if label else f"[[{path}]]"


def indexes(data: dict):
    activities = {item["key"]: item for item in data["activities"]}
    records = {item["key"]: item for item in data["records"]}
    files = {item["key"]: item for item in data["files"]}
    return activities, records, files


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
    lines.extend(["tags:", "  - sslg", "---", "", f"# {record['title']}", ""])
    if activity:
        lines.extend([f"Part of {wikilink(activity['hub_path'], activity['title'])}.", ""])
    lines.extend([
        "> [!info] At a glance",
        f"> **Document ID:** {record['record_id']}",
        f"> **Type:** {record['record_type']}",
        f"> **Record date:** {record['date'] or 'Not stated in source'}",
        f"> **Event date:** {record['event_date'] or 'Not stated in source'}",
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
        if path.lower().endswith(".pdf"):
            lines.extend([f"**{source['role']} PDF: {name}**", "", f"![[{path}]]", ""])
        else:
            lines.extend([f"**{source['role']} DOCX: {name}**", "", wikilink(path, f"Open original DOCX: {name}"), ""])
    return "\n".join(lines).rstrip() + "\n"
```

The final test expects the PDF embed to be the last line, so source ordering in test data is intentionally DOCX then PDF. In real data, put any PDF source last in `source_keys` so the final visible element is an embedded original.

- [ ] **Step 4: Implement activity hubs and no-overwrite generation**

`render_activity` must emit `type: activity`, `title`, `start_date`, `end_date`, `school_year`, `status`, and `venue`; an At a glance callout; the source-derived summary; an Activity trail ordered proposal → meeting-notice/excuse-letter/request → memorandum → completion-report; Outcomes and follow-up; Missing stages; and review callouts. Use the exact missing-stage sentence `Not present in the supplied records: <stage>.` Only list stages absent from that activity's linked records.

```python
def generate_notes(root: Path, data: dict) -> list[Path]:
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

- [ ] **Step 5: Run note tests, then generate notes in the real vault without moving sources**

Run: `python -m unittest tools.tests.test_sslg_notes -v`  
Expected: PASS.

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
from tools.sslg_notes import generate_notes
root = Path.cwd()
data = json.loads((root / "tools/sslg_content.json").read_text(encoding="utf-8"))
paths = generate_notes(root, data)
print(f"Generated {len(paths)} new activity and record notes")
PY
```

Expected: one hub per manifest activity and one note per logical record; source files have not moved yet. Record Checkpoint 3.

---

### Task 4: Homepage, Dashboards, Review Queue, and Templates
