# SSLG Obsidian Vault Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a readable, activity-centered Obsidian vault in which every summary note ends with its unchanged original DOCX/PDF source and every moved or archived file remains accounted for.

**Architecture:** A reviewed JSON content manifest is the single source of truth for source-file moves, activity hubs, record summaries, relationships, and review flags. Small standard-library Python tools perform checksummed moves, render Markdown/native Bases navigation, and validate preservation, coverage, and links; content generation and filesystem migration remain separate so no source moves occur until the manifest passes review.

**Tech Stack:** Python 3 standard library (`pathlib`, `json`, `hashlib`, `unittest`, `tempfile`), Markdown, YAML frontmatter, Obsidian wikilinks, PDF embeds, and native Bases.

**Spec:** `docs/superpowers/specs/2026-11-04-sslg-obsidian-vault-design.md`

## Global Constraints

- Keep original documents unchanged; generated summaries must never be confused with original source text.
- Delete nothing and do not overwrite any destination file.
- Archive superseded revisions and exact duplicates; preserve the pre-existing `_DUPLICATES_TO_DELETE` material as staging material.
- The final section of every record note must be `## Original document`, with PDF embeds and prominent DOCX links.
- Use explicit vault-relative source paths and exact source filenames for AI traceability.
- Use only native Obsidian features; no community plugins, uploads, or external services.
- Do not edit, move, or reorganize `Scheduler_v1-main`.
- Do not invent dates, relationships, outcomes, approvals, or version authority; use `needs-review` and the Review Queue for uncertainty.
- This workspace is not a git repository. Replace commit steps with named validation checkpoints; do not initialize git or create commits.
- The user explicitly authorized automatic continuation. Do not pause for further design or execution approval.

## File Structure

- `tools/sslg_migration.py`: baseline discovery, SHA-256, move preflight, reversible moves, manifest and archive-index output.
- `tools/sslg_notes.py`: record-note and activity-hub rendering from reviewed content data.
- `tools/sslg_navigation.py`: homepage, dashboard, native Bases, review-queue, and template rendering.
- `tools/validate_sslg_vault.py`: final checksum, note-coverage, source-placement, wikilink, review-queue, and protected-tree validation.
- `tools/sslg_content.json`: reviewed activity, record, source-file, relationship, and protected-tree data; the only content input shared by the tools.
- `tools/tests/test_sslg_migration.py`: preservation and move-safety tests.
- `tools/tests/test_sslg_content.py`: real-inventory coverage and content-schema tests.
- `tools/tests/test_sslg_notes.py`: record/activity rendering tests.
- `tools/tests/test_sslg_navigation.py`: homepage, Bases, template, and review-view tests.
- `tools/tests/test_validate_sslg_vault.py`: broken-link, missing-source, checksum, and final-section tests.
- `START HERE.md`: generated reader entry point.
- `01 Dashboards/`: generated activity, document, timeline, review, and Bases navigation.
- `02 Activities/`, `03 Governance/`, `04 External Memoranda/`, `05 General Records/`: generated notes and preserved sources.
- `80 Assets/`: preserved PNG attachments.
- `90 Archive/`: preserved revisions, duplicates, staging material, `Archive Index.md`, and `File Manifest.json`.
- `99 Templates/`: reusable activity and record templates.
- `.obsidian/templates.json`: core Templates folder configuration only; leave other Obsidian configuration unchanged.

---

### Task 1: Checksummed Migration Engine

**Files:**
- Create: `tools/sslg_migration.py`
- Create: `tools/tests/test_sslg_migration.py`

**Interfaces:**
- Consumes: the existing vault root and a `files` list whose entries contain `key`, `original_path`, `current_path`, `sha256`, `role`, and optional `record_key`.
- Produces: `sha256(path: Path) -> str`, `collect_baseline(root: Path) -> list[str]`, `preflight_moves(root: Path, files: list[dict]) -> list[str]`, `apply_moves(root: Path, files: list[dict]) -> None`, `write_manifest(root: Path, data: dict) -> None`, and `write_archive_index(root: Path, files: list[dict]) -> None`.

- [x] **Step 1: Write failing preservation and collision tests**

```python
import json
import tempfile
import unittest
from pathlib import Path

from tools.sslg_migration import apply_moves, collect_baseline, preflight_moves, sha256


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "source.docx").write_bytes(b"original-docx")
        (self.root / "_DUPLICATES_TO_DELETE").mkdir()
        (self.root / "_DUPLICATES_TO_DELETE" / "copy.pdf").write_bytes(b"copy-pdf")
        (self.root / "OM_SSLG_2026_001").mkdir()
        (self.root / "OM_SSLG_2026_001" / "page.png").write_bytes(b"png")
        (self.root / "Scheduler_v1-main").mkdir()
        (self.root / "Scheduler_v1-main" / "App.py").write_text("unchanged", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def entry(self, **overrides):
        value = {
            "key": "source-docx",
            "original_path": "source.docx",
            "current_path": "02 Activities/Example/Sources/source.docx",
            "sha256": sha256(self.root / "source.docx"),
            "role": "primary",
            "record_key": "example-record",
        }
        value.update(overrides)
        return value

    def test_baseline_includes_only_sslg_source_and_staging_files(self):
        self.assertEqual(
            collect_baseline(self.root),
            ["OM_SSLG_2026_001/page.png", "_DUPLICATES_TO_DELETE/copy.pdf", "source.docx"],
        )

    def test_move_preserves_bytes_and_records_original_hash(self):
        files = [self.entry()]
        self.assertEqual(preflight_moves(self.root, files), [])
        apply_moves(self.root, files)
        destination = self.root / files[0]["current_path"]
        self.assertEqual(destination.read_bytes(), b"original-docx")
        self.assertEqual(sha256(destination), files[0]["sha256"])
        self.assertFalse((self.root / "source.docx").exists())

    def test_preflight_rejects_existing_destination_and_bad_hash(self):
        collision = self.entry()
        destination = self.root / collision["current_path"]
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"do-not-overwrite")
        bad_hash = self.entry(sha256="0" * 64)
        errors = preflight_moves(self.root, [collision, bad_hash])
        self.assertTrue(any("destination exists" in error for error in errors))
        self.assertTrue(any("checksum mismatch" in error for error in errors))
        self.assertEqual(destination.read_bytes(), b"do-not-overwrite")

    def test_preflight_rejects_path_escape_and_duplicate_destinations(self):
        escape = self.entry(current_path="../outside.docx")
        first = self.entry(key="first")
        second = self.entry(key="second", original_path="_DUPLICATES_TO_DELETE/copy.pdf")
        second["current_path"] = first["current_path"]
        second["sha256"] = sha256(self.root / second["original_path"])
        errors = preflight_moves(self.root, [escape, first, second])
        self.assertTrue(any("unsafe path" in error for error in errors))
        self.assertTrue(any("duplicate destination" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the tests and verify the import failure**

Run: `python -m unittest tools.tests.test_sslg_migration -v`  
Expected: FAIL because `tools.sslg_migration` does not exist.

- [x] **Step 3: Implement safe path handling, discovery, hashing, and preflight**

```python
from hashlib import sha256 as file_hash
from pathlib import Path, PurePosixPath
import json


def sha256(path: Path) -> str:
    digest = file_hash()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def collect_baseline(root: Path) -> list[str]:
    paths = []
    for path in root.iterdir():
        if path.is_file() and path.suffix.lower() in {".docx", ".pdf"}:
            paths.append(path.relative_to(root).as_posix())
    for folder in (root / "_DUPLICATES_TO_DELETE", root / "OM_SSLG_2026_001"):
        if folder.exists():
            paths.extend(
                path.relative_to(root).as_posix()
                for path in folder.rglob("*")
                if path.is_file()
            )
    return sorted(paths)


def preflight_moves(root: Path, files: list[dict]) -> list[str]:
    errors = []
    destinations = set()
    for entry in files:
        original = entry["original_path"]
        current = entry["current_path"]
        if not safe_relative(original) or not safe_relative(current):
            errors.append(f"unsafe path: {entry['key']}")
            continue
        source = root / original
        destination = root / current
        if current in destinations:
            errors.append(f"duplicate destination: {current}")
        destinations.add(current)
        if not source.is_file():
            errors.append(f"missing source: {original}")
            continue
        if sha256(source) != entry["sha256"]:
            errors.append(f"checksum mismatch: {original}")
        if original != current and destination.exists():
            errors.append(f"destination exists: {current}")
    return sorted(errors)
```

- [x] **Step 4: Implement reversible moves and deterministic audit output**

```python
def apply_moves(root: Path, files: list[dict]) -> None:
    errors = preflight_moves(root, files)
    if errors:
        raise ValueError("Move preflight failed:\n" + "\n".join(errors))
    moved = []
    try:
        for entry in files:
            if entry["original_path"] == entry["current_path"]:
                continue
            source = root / entry["original_path"]
            destination = root / entry["current_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
            moved.append((source, destination))
            if sha256(destination) != entry["sha256"]:
                raise IOError(f"post-move checksum mismatch: {destination}")
    except Exception as error:
        rollback_errors = []
        for source, destination in reversed(moved):
            try:
                if source.exists():
                    raise IOError(f"rollback destination exists: {source}")
                source.parent.mkdir(parents=True, exist_ok=True)
                destination.rename(source)
            except Exception as rollback_error:
                rollback_errors.append(str(rollback_error))
        message = f"Move failed and rollback was attempted: {error}"
        if rollback_errors:
            message += "; rollback errors: " + "; ".join(rollback_errors)
        raise RuntimeError(message) from error


def write_manifest(root: Path, data: dict) -> None:
    destination = root / "90 Archive" / "File Manifest.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_archive_index(root: Path, files: list[dict]) -> None:
    destination = root / "90 Archive" / "Archive Index.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    lines = [
        "# Archive Index",
        "",
        "All material is preserved. SHA-256 values identify the original bytes.",
        "",
        "| Role | Original path | Current path | Record | SHA-256 |",
        "|---|---|---|---|---|",
    ]
    for entry in sorted(files, key=lambda item: (item["role"], item["original_path"])):
        lines.append(
            f"| {entry['role']} | {entry['original_path']} | {entry['current_path']} "
            f"| {entry.get('record_key', '')} | `{entry['sha256']}` |"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [x] **Step 5: Run migration tests and record Checkpoint 1**

Run: `python -m unittest tools.tests.test_sslg_migration -v`  
Expected: all migration tests PASS; the fixture proving collision refusal remains unchanged. Do not run migration against the real vault yet.

---

### Task 2: Reviewed Content and File Manifest

**Files:**
- Create: `tools/sslg_content.json`
- Create: `tools/tests/test_sslg_content.py`
- Reference: every root DOCX/PDF, `_DUPLICATES_TO_DELETE`, and `OM_SSLG_2026_001/*.png`
- Reference: `docs/superpowers/specs/2026-11-04-sslg-obsidian-vault-design.md`

**Interfaces:**
- Consumes: `collect_baseline` and `sha256` from Task 1; source text extracted read-only from DOCX XML and PDF pages.
- Produces: top-level `activities`, `records`, `files`, and `protected_files` collections consumed by Tasks 3–5.

- [x] **Step 1: Write a failing real-inventory coverage test**

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


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the test and verify the missing-manifest failure**

Run: `python -m unittest tools.tests.test_sslg_content -v`  
Expected: FAIL because `tools/sslg_content.json` does not exist.

- [x] **Step 3: Extract source facts without modifying documents**

Use Python's `zipfile.ZipFile` and `xml.etree.ElementTree` to read `word/document.xml` from every DOCX. Read every PDF's pages with the file-reading tool. Build a worksheet containing filename, exact document identifier, issuance date, event date, title/subject, activity title, venue, status evidence, related references, revision labels, and SHA-256. Do not treat filename numbers alone as relationship evidence.

Run this extraction command from the vault root:

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
for path in sorted(Path(".").glob("*.docx")):
    with ZipFile(path) as archive:
        tree = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = []
    for paragraph in tree.findall(".//w:p", ns):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns)).strip()
        if text:
            paragraphs.append(text)
    print(f"\n### {path.name}\n" + "\n".join(paragraphs))
PY
```

Expected: source text appears in tool output only; no DOCX is rewritten.

- [x] **Step 4: Author the complete reviewed JSON content manifest**

Use this exact schema; repeat it for every activity, logical record, and baseline file. Clean display titles, but preserve exact filenames and identifiers. Use `null` for unknown dates and `needs-review` with a concrete reason for unresolved authority or relationships.

```json
{
  "activities": [
    {
      "key": "leaders-induction-2026",
      "title": "Onto the Next: Leaders 2026–2027 Induction Ceremony",
      "hub_path": "02 Activities/Onto the Next - Leaders Induction 2026/Onto the Next - Leaders Induction 2026.md",
      "start_date": "2026-07-22",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Multi-Purpose Hall",
      "summary": "Induction of newly elected student leaders and Parent-Teacher Association officers for School Year 2026–2027.",
      "outcomes": [
        "Newly elected student leaders were formally inducted.",
        "The ceremony promoted collaboration and responsible leadership."
      ],
      "review_reasons": []
    }
  ],
  "records": [
    {
      "key": "ap-sslg-2026-001",
      "title": "Activity Proposal AP-SSLG-2026-001 — Leaders Induction Ceremony",
      "note_path": "02 Activities/Onto the Next - Leaders Induction 2026/Notes/AP-SSLG-2026-001.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_001",
      "date": null,
      "event_date": "2026-07-22",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "leaders-induction-2026",
      "collection": "activities",
      "summary": "Proposal for the July 22 induction ceremony, with leadership recognition, officer orientation, unity, and service as its central purposes.",
      "key_details": [
        "Scheduled from 8:00 A.M. to 12:00 N.N. at the Multi-Purpose Hall.",
        "Includes formal induction, leadership commitment, and collaboration among student organizations."
      ],
      "source_keys": ["ap-001-docx"],
      "related": ["acr-sslg-2026-006"],
      "review_reasons": []
    }
  ],
  "files": [
    {
      "key": "ap-001-docx",
      "original_path": "AP_SSLG_2026_001.docx",
      "current_path": "02 Activities/Onto the Next - Leaders Induction 2026/Sources/AP_SSLG_2026_001.docx",
      "sha256": "eab63947f6b3df809d0bb9c003bebd640296472e1702fe4b5b43102cae0b3958",
      "role": "primary",
      "record_key": "ap-sslg-2026-001",
      "archive_reason": ""
    }
  ],
  "protected_files": [
    {
      "path": "Scheduler_v1-main/run_app.py",
      "sha256": "4118bedb804dcc62e63eced85f4c4727a5b605533af4ecf572c53f88db74042e"
    }
  ]
}
```

Compute every other hash with `sha256(path)` and include every Scheduler file in `protected_files`, not only the example. Keep both DOCX and PDF as `primary`/`alternative-format` when they are current representations of one logical record. Put superseded versions, exact duplicates, and pre-existing staging files in their approved Archive paths with concise `archive_reason` values.

- [x] **Step 5: Run content tests and manually audit ambiguous records**

Run: `python -m unittest tools.tests.test_sslg_content -v`  
Expected: PASS with all 93 root Word/PDF files, all staged files, and all eight PNGs covered exactly once.

Manually compare every `needs-review` entry against its source. Confirm that the induction proposal-to-completion relationship is based on matching title/date/subject, that OM numbering/date conflicts are flagged, and that no current DOCX/PDF pair with material content differences is silently treated as alternative formats. Record Checkpoint 2.

---

### Task 3: Record Notes and Activity Hubs

**Files:**
- Create: `tools/sslg_notes.py`
- Create: `tools/tests/test_sslg_notes.py`
- Read: `tools/sslg_content.json`

**Interfaces:**
- Consumes: the Task 2 `activities`, `records`, and `files` collections.
- Produces: `wikilink(path: str, label: str | None = None) -> str`, `render_record(record: dict, data: dict) -> str`, `render_activity(activity: dict, data: dict) -> str`, and `generate_notes(root: Path, data: dict) -> list[Path]`.

- [x] **Step 1: Write failing source-placement and relationship tests**

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

- [x] **Step 2: Run tests and verify the import failure**

Run: `python -m unittest tools.tests.test_sslg_notes -v`  
Expected: FAIL because `tools.sslg_notes` does not exist.

- [x] **Step 3: Implement deterministic rendering**

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

- [x] **Step 4: Implement activity hubs and no-overwrite generation**

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

- [x] **Step 5: Run note tests, then generate notes in the real vault without moving sources**

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

**Files:**
- Create: `tools/sslg_navigation.py`
- Create: `tools/tests/test_sslg_navigation.py`
- Create through the renderer: `START HERE.md`, `01 Dashboards/*`, `99 Templates/*`, `.obsidian/templates.json`

**Interfaces:**
- Consumes: Task 2 content data and Task 3 note paths.
- Produces: `render_home(data: dict) -> str`, `render_activity_dashboard(data: dict) -> str`, `render_timeline(data: dict) -> str`, `render_review_queue(data: dict) -> str`, `render_document_library() -> str`, `render_record_template() -> str`, `render_activity_template() -> str`, and `generate_navigation(root: Path, data: dict) -> list[Path]`.

- [x] **Step 1: Write failing navigation tests**

```python
import unittest
from tools.sslg_navigation import BASES_YAML, render_home, render_review_queue


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


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and verify the import failure**

Run: `python -m unittest tools.tests.test_sslg_navigation -v`  
Expected: FAIL because `tools.sslg_navigation` does not exist.

- [x] **Step 3: Implement native Bases and navigation pages**

Use this exact standalone Bases document, adding only valid ordering fields:

```yaml
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
```

`render_home` must link `START HERE` to all dashboards and collections and include the callout text `Original documents remain unchanged. Summaries are navigation aids; use the Original document section for the complete official formatting.` Activity and timeline pages must be deterministic tables sorted by `start_date` and by `event_date`/`date`, respectively. Review Queue must include every needs-review activity and record with all reasons. Document Library embeds `![[01 Dashboards/SSLG Records.base]]` and explains the available views.

- [x] **Step 4: Implement reusable templates and no-overwrite output**

The record template must contain the same property names and section order as generated notes, using core Templates tokens `{{title}}`, `{{date:YYYY-MM-DD}}`, and empty values for source-specific fields. Its final heading must be `## Original document`. The activity template must contain the approved At a glance, Activity trail, Outcomes and follow-up, Missing stages, and Original files sections. Do not place unresolved example wikilinks in templates.

`generate_navigation` writes exactly:

```text
START HERE.md
01 Dashboards/Activity Dashboard.md
01 Dashboards/Document Library.md
01 Dashboards/Timeline.md
01 Dashboards/Review Queue.md
01 Dashboards/SSLG Records.base
99 Templates/Activity Template.md
99 Templates/Record Template.md
.obsidian/templates.json
```

It must preflight all destinations and refuse to overwrite any existing file. `.obsidian/templates.json` contains `{"folder": "99 Templates"}`.

- [x] **Step 5: Run tests, generate navigation, and record Checkpoint 4**

Run: `python -m unittest tools.tests.test_sslg_navigation -v`  
Expected: PASS.

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
from tools.sslg_navigation import generate_navigation
root = Path.cwd()
data = json.loads((root / "tools/sslg_content.json").read_text(encoding="utf-8"))
paths = generate_navigation(root, data)
print(f"Generated {len(paths)} navigation and template files")
PY
```

Expected: nine new files, with no other `.obsidian` configuration modified.

---

### Task 5: Final Validator

**Files:**
- Create: `tools/validate_sslg_vault.py`
- Create: `tools/tests/test_validate_sslg_vault.py`
- Read: all generated notes and `tools/sslg_content.json`

**Interfaces:**
- Consumes: Task 2 content data, Task 3 notes, Task 4 navigation, and Task 1 checksums.
- Produces: `wikilink_targets(text: str) -> list[str]`, `validate_vault(root: Path, data: dict) -> list[str]`, and a CLI returning exit code 1 on any error and 0 only when all checks pass.

- [x] **Step 1: Write failing validator tests**

```python
import tempfile
import unittest
from pathlib import Path

from tools.validate_sslg_vault import validate_vault, wikilink_targets


class ValidatorTests(unittest.TestCase):
    def test_extracts_links_and_embeds_without_aliases_or_headings(self):
        self.assertEqual(
            wikilink_targets("[[Folder/Note.md|Label]] and ![[Folder/File.pdf#page=2]]"),
            ["Folder/Note.md", "Folder/File.pdf"],
        )

    def test_reports_missing_source_wrong_final_section_and_broken_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            note = root / "record.md"
            note.write_text("---\ntype: record\n---\n# Record\n[[Missing.md]]\n## Summary\n", encoding="utf-8")
            data = {
                "activities": [], "protected_files": [],
                "records": [{
                    "key": "r", "note_path": "record.md", "title": "Record", "status": "final",
                    "source_keys": ["f"], "related": [], "review_reasons": [], "activity": None,
                }],
                "files": [{
                    "key": "f", "current_path": "missing.docx", "sha256": "a" * 64,
                    "record_key": "r", "role": "primary",
                }],
            }
            errors = validate_vault(root, data)
            self.assertTrue(any("missing file" in error for error in errors))
            self.assertTrue(any("broken wikilink" in error for error in errors))
            self.assertTrue(any("final section" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and verify the import failure**

Run: `python -m unittest tools.tests.test_validate_sslg_vault -v`  
Expected: FAIL because `tools.validate_sslg_vault` does not exist.

- [x] **Step 3: Implement complete read-only validation**

Use this link parser and extend `validate_vault` to return an error string for every failed acceptance criterion rather than stopping at the first error.

```python
import re
from pathlib import Path
from tools.sslg_migration import safe_relative, sha256

WIKILINK = re.compile(r"!?\[\[([^\]]+)\]\]")


def wikilink_targets(text: str) -> list[str]:
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
```

Validation must check:

- Every `files` entry exists at `current_path`, is safe, and matches `sha256`.
- Every `protected_files` entry still exists at the same path and matches its baseline hash.
- Every activity hub and record note exists; every record note has `type: record`, required metadata, and `## Original document` as its final level-two heading.
- Every current source key appears as a link or embed inside that final section.
- Every generated non-template Markdown wikilink resolves; strip aliases and headings first.
- Every related record key resolves and reciprocal activity references are consistent.
- Every needs-review activity and record appears in Review Queue with its reasons.
- The real root no longer contains loose DOCX/PDF files; `_DUPLICATES_TO_DELETE` contains no files, and all former contents are represented in the manifest. Empty source directories may remain because no directories are deleted.
- `Scheduler_v1-main` has no extra or missing files relative to `protected_files`.
- Native Bases contains the required views and excludes Scheduler.

Print `VALIDATION PASSED: <counts>` only when the error list is empty; otherwise print every error and exit 1.

- [x] **Step 4: Run validator tests and record Checkpoint 5**

Run: `python -m unittest tools.tests.test_validate_sslg_vault -v`  
Expected: PASS. Then run `python tools/validate_sslg_vault.py`; it should currently FAIL only because sources have not moved and navigation/source destinations are incomplete. Do not proceed until Task 5's unit tests pass.

---

### Task 6: Apply Migration and Verify the Finished Vault

**Files:**
- Modify by the migration only: paths listed in `tools/sslg_content.json`
- Create: `90 Archive/File Manifest.json`, `90 Archive/Archive Index.md`
- Verify: all vault outputs and all acceptance criteria in the spec

**Interfaces:**
- Consumes: all prior tasks' tested interfaces and reviewed manifest.
- Produces: the finished, checksummed, interconnected Obsidian vault.

- [x] **Step 1: Run the complete pre-migration test suite**

Run: `python -m unittest discover -s tools/tests -v`  
Expected: all unit and content tests PASS. The real-vault validator is intentionally excluded until after migration.

- [x] **Step 2: Reconfirm preflight before the first real move**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
from tools.sslg_migration import preflight_moves
root = Path.cwd()
data = json.loads((root / "tools/sslg_content.json").read_text(encoding="utf-8"))
errors = preflight_moves(root, data["files"])
print("\n".join(errors) if errors else f"PREFLIGHT PASSED: {len(data['files'])} files")
raise SystemExit(bool(errors))
PY
```

Expected: `PREFLIGHT PASSED` with zero missing sources, checksum mismatches, unsafe paths, collisions, or duplicate destinations. If any error occurs, stop migration and fix the manifest or tests; do not bypass preflight.

- [x] **Step 3: Apply the authorized reversible moves**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
from tools.sslg_migration import apply_moves, write_archive_index, write_manifest
root = Path.cwd()
data = json.loads((root / "tools/sslg_content.json").read_text(encoding="utf-8"))
apply_moves(root, data["files"])
write_manifest(root, data)
write_archive_index(root, data["files"])
print(f"Moved and verified {len(data['files'])} source/asset files; no files deleted")
PY
```

Expected: every original is either at its approved primary/alternative-format path or preserved in Archive/Assets; any exception triggers the implemented rollback attempt and is reported.

- [x] **Step 4: Run final automated validation**

Run: `python tools/validate_sslg_vault.py`  
Expected: `VALIDATION PASSED` with zero broken links, checksum mismatches, missing notes, missing original-document sections, absent review entries, or Scheduler changes.

Also run: `python -m unittest discover -s tools/tests -v`  
Expected: all tests still PASS after migration. The content-coverage test reads the original-path list from `File Manifest.json` once migration has occurred, while the final validator independently checks every current path and checksum.

- [ ] **Step 5: Inspect representative output and Obsidian rendering** — PARTIALLY PERFORMED, left open deliberately.

Read the homepage, one activity hub with a proposal and completion report, one DOCX-only note, one note with DOCX and PDF sources, one needs-review note, the Archive Index, and both templates. Confirm the original document is visually last and all summaries are source-derived. **Done**: all of the above read, and `## Original document` machine-confirmed as the last level-two heading in 36/36 notes.

Open `START HERE.md` in Obsidian if desktop-app control is available and inspect the Activity Dashboard, Document Library, Timeline, Review Queue, one PDF embed, and one DOCX external-open link. If Obsidian UI control is unavailable, state exactly that visual rendering and external-open behavior were not exercised; do not claim those checks passed. **NOT PERFORMED**: Obsidian was never opened. Visual rendering, `.base` view display, PDF embed appearance, DOCX external-open behaviour and graph layout are unexercised; only file-level structure, link resolution and validation were verified.

- [x] **Step 6: Report completion with evidence and remaining UI-only caveats**

Report counts of activities, logical record notes, primary/alternative sources, archived revisions, verified duplicates, staged files, and assets. Link `START HERE.md`, the Review Queue, and the Archive Index. State the validation commands and results, confirm no source was deleted or edited, and identify any unperformed Obsidian UI check explicitly.
