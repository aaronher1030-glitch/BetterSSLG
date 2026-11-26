### Task 2: Reviewed Content and File Manifest

**Files:**
- Create: `tools/sslg_content.json`
- Create: `tools/tests/test_sslg_content.py`
- Reference: every root DOCX/PDF, `_DUPLICATES_TO_DELETE`, and `OM_SSLG_2026_001/*.png`
- Reference: `docs/superpowers/specs/2026-11-04-sslg-obsidian-vault-design.md`

**Interfaces:**
- Consumes: `collect_baseline` and `sha256` from Task 1; source text extracted read-only from DOCX XML and PDF pages.
- Produces: top-level `activities`, `records`, `files`, and `protected_files` collections consumed by Tasks 3–5.

- [ ] **Step 1: Write a failing real-inventory coverage test**

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

- [ ] **Step 2: Run the test and verify the missing-manifest failure**

Run: `python -m unittest tools.tests.test_sslg_content -v`  
Expected: FAIL because `tools/sslg_content.json` does not exist.

- [ ] **Step 3: Extract source facts without modifying documents**

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

- [ ] **Step 4: Author the complete reviewed JSON content manifest**

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

- [ ] **Step 5: Run content tests and manually audit ambiguous records**

Run: `python -m unittest tools.tests.test_sslg_content -v`  
Expected: PASS with all 93 root Word/PDF files, all staged files, and all eight PNGs covered exactly once.

Manually compare every `needs-review` entry against its source. Confirm that the induction proposal-to-completion relationship is based on matching title/date/subject, that OM numbering/date conflicts are flagged, and that no current DOCX/PDF pair with material content differences is silently treated as alternative formats. Record Checkpoint 2.

---
