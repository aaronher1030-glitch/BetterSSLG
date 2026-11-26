import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_sslg_vault import validate_vault, wikilink_targets


def write_reconciliation_artifacts(root, data):
    """Write the delivered inventory and archive index that must agree with `data`."""
    archive = root / "90 Archive"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "File Manifest.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    lines = ["# Archive Index", "", "| Role | Original path | Current path | Record | SHA-256 |", "|---|---|---|---|---|"]
    for entry in data["files"]:
        lines.append(f"| {entry['role']} | {entry['original_path']} | {entry['current_path']} "
                     f"| {entry['record_key']} | `{entry['sha256']}` |")
    (archive / "Archive Index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


class ValidatorTests(unittest.TestCase):
    def test_extracts_links_and_embeds_without_aliases_or_headings(self):
        self.assertEqual(
            wikilink_targets("[[Folder/Note.md|Label]] and ![[Folder/File.pdf#page=2]]"),
            ["Folder/Note.md", "Folder/File.pdf"],
        )

    def test_reports_missing_source_wrong_final_section_and_broken_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            note_path = root / "record.md"
            note_path.write_text("---\ntype: record\n---\n# Record\n[[Missing.md]]\n## Summary\n", encoding="utf-8")
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
            self.assertTrue(any("id_provenance" in error for error in errors))

    def test_passes_when_every_check_is_satisfied(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "02 Activities/Alpha/Alpha/src.docx"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"payload")
            (root / "record.md").write_text(
                "---\ntype: record\ntitle: \"Record\"\nrecord_type: proposal\nrecord_id: \"\"\n"
                "id_provenance: not-stated\n"
                "date: null\nevent_date: null\nschool_year: \"2026-2027\"\nactivity: null\n"
                "status: final\nneeds_review: \"no\"\nsource_file: \"src.docx\"\nsource_path: \"02 Activities/Alpha/Alpha/src.docx\"\n"
                "source_format: docx\nsources:\n  - file: \"src.docx\"\nrelated: []\ntags:\n  - sslg\n---\n"
                "# Record\n\n## Summary\n\ntext\n\n## Original document\n\n"
                "[[02 Activities/Alpha/Alpha/src.docx|Open original DOCX: src.docx]]\n", encoding="utf-8")
            (root / "01 Dashboards").mkdir()
            (root / "01 Dashboards/Review Queue.md").write_text("# Review Queue\n", encoding="utf-8")
            (root / "01 Dashboards/SSLG Records.base").write_text(
                "views:\n  - type: table\n    name: All records\n  - type: table\n    name: Proposals\n"
                "  - type: table\n    name: Completion reports\n  - type: table\n    name: Memoranda\n"
                "  - type: table\n    name: Needs review\n"
                "filters:\n  and:\n    - 'file.folder != \"Scheduler_v1-main\"'\n", encoding="utf-8")
            (root / "Scheduler_v1-main").mkdir()
            (root / "Scheduler_v1-main" / "keep.py").write_text("x\n", encoding="utf-8")
            data = {
                "activities": [], "protected_files": [{"path": "Scheduler_v1-main/keep.py", "sha256": None}],
                "records": [{
                    "key": "r", "note_path": "record.md", "title": "Record", "status": "final",
                    "source_keys": ["f"], "related": [], "review_reasons": [], "activity": None,
                }],
                "files": [{"key": "f", "current_path": "02 Activities/Alpha/Alpha/src.docx", "sha256": None,
                           "record_key": "r", "role": "primary", "original_path": "src.docx"}],
            }
            from tools.sslg_migration import sha256
            data["files"][0]["sha256"] = sha256(root / "02 Activities/Alpha/Alpha/src.docx")
            data["protected_files"][0]["sha256"] = sha256(root / "Scheduler_v1-main" / "keep.py")
            write_reconciliation_artifacts(root, data)
            self.assertEqual(validate_vault(root, data), [])

    def test_requires_the_delivered_manifest_to_agree_with_the_validated_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "02 Activities/Alpha/Alpha/src.docx"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"payload")
            (root / "record.md").write_text("---\ntype: record\n---\n# Record\n\n## Original document\n\n"
                                            "[[02 Activities/Alpha/Alpha/src.docx]]\n", encoding="utf-8")
            from tools.sslg_migration import sha256
            data = {
                "activities": [], "protected_files": [],
                "records": [{"key": "r", "note_path": "record.md", "title": "Record", "status": "final",
                             "source_keys": ["f"], "related": [], "review_reasons": [], "activity": None}],
                "files": [{"key": "f", "current_path": "02 Activities/Alpha/Alpha/src.docx",
                           "sha256": sha256(source), "record_key": "r", "role": "primary",
                           "original_path": "src.docx"}],
            }
            write_reconciliation_artifacts(root, data)
            (root / "01 Dashboards").mkdir()
            (root / "01 Dashboards/Review Queue.md").write_text("# Review Queue\n", encoding="utf-8")
            (root / "01 Dashboards/SSLG Records.base").write_text(
                "".join(f"views:\n  - type: table\n    name: {v}\n" for v in
                        ("All records", "Proposals", "Completion reports", "Memoranda", "Needs review"))
                + 'filters:\n  and:\n    - \'file.folder != "Scheduler_v1-main"\'\n', encoding="utf-8")
            baseline_errors = validate_vault(root, data)
            self.assertFalse(any("File Manifest" in e or "Archive Index" in e for e in baseline_errors),
                             baseline_errors)
            drifted = json.loads(json.dumps(data))
            drifted["files"][0]["current_path"] = "02 Activities/Elsewhere/other.docx"
            (root / "90 Archive/File Manifest.json").write_text(json.dumps(drifted), encoding="utf-8")
            errors = validate_vault(root, data)
            self.assertTrue(any("File Manifest" in e for e in errors), errors)
            (root / "90 Archive/Archive Index.md").write_text("# Archive Index\n\nno rows\n", encoding="utf-8")
            errors = validate_vault(root, data)
            self.assertTrue(any("Archive Index" in e for e in errors), errors)
            (root / "90 Archive/File Manifest.json").unlink()
            errors = validate_vault(root, data)
            self.assertTrue(any("File Manifest" in e for e in errors), errors)

    def test_detects_checksum_drift_and_scheduler_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src.docx").write_bytes(b"payload")
            (root / "record.md").write_text(
                "---\ntype: record\n---\n# Record\n\n## Original document\n\n[[src.docx]]\n", encoding="utf-8")
            (root / "Scheduler_v1-main").mkdir()
            (root / "Scheduler_v1-main" / "keep.py").write_bytes(b"x\n")
            from tools.sslg_migration import sha256
            data = {
                "activities": [],
                "protected_files": [{"path": "Scheduler_v1-main/keep.py", "sha256": "0" * 64}],
                "records": [{
                    "key": "r", "note_path": "record.md", "title": "Record", "status": "final",
                    "source_keys": ["f"], "related": [], "review_reasons": [], "activity": None,
                }],
                "files": [{"key": "f", "current_path": "src.docx", "sha256": "0" * 64,
                           "record_key": "r", "role": "primary", "original_path": "src.docx"}],
            }
            good = sha256(root / "src.docx")
            errors = validate_vault(root, data)
            self.assertTrue(any("checksum" in e for e in errors), errors)
            (root / "src.docx").write_bytes(b"payload")
            data["files"][0]["sha256"] = good
            data["protected_files"][0]["sha256"] = sha256(root / "Scheduler_v1-main" / "keep.py")
            (root / "Scheduler_v1-main" / "extra.py").write_bytes(b"y\n")
            errors = validate_vault(root, data)
            self.assertTrue(any("Scheduler" in e for e in errors), errors)

    def test_requires_hub_and_review_queue_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = {
                "activities": [{"key": "a", "title": "Alpha", "hub_path": "02 Activities/Alpha/Alpha.md",
                                "status": "needs-review", "review_reasons": ["No venue is stated."]}],
                "records": [{
                    "key": "r", "note_path": "record.md", "title": "Record", "status": "needs-review",
                    "source_keys": [], "related": [], "review_reasons": ["Two numbers conflict."],
                    "activity": "a",
                }],
                "files": [], "protected_files": [],
            }
            (root / "record.md").write_text(
                "---\ntype: record\n---\n# Record\n\n## Original document\n\nnone\n", encoding="utf-8")
            queue = root / "01 Dashboards/Review Queue.md"
            queue.parent.mkdir(parents=True)
            queue.write_text("# Review Queue\n\nmissing content\n", encoding="utf-8")
            errors = validate_vault(root, data)
            self.assertTrue(any("missing activity hub" in e for e in errors), errors)
            self.assertTrue(any("Review Queue omits" in e for e in errors), errors)
            hub = root / "02 Activities/Alpha/Alpha.md"
            hub.parent.mkdir(parents=True)
            hub.write_text("---\ntype: activity\n---\n# Alpha\n\n[[record.md]]\n", encoding="utf-8")
            queue.write_text("# Review Queue\n\nRecord\nTwo numbers conflict.\nAlpha\nNo venue is stated.\n",
                             encoding="utf-8")
            errors = validate_vault(root, data)
            self.assertFalse(any("Review Queue omits" in e for e in errors), errors)
            self.assertFalse(any("activity hub" in e or "does not link record" in e for e in errors), errors)

    def test_rejects_loose_root_documents_and_unresolved_related_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "loose.docx").write_bytes(b"x")
            (root / "record.md").write_text(
                "---\ntype: record\n---\n# Record\n\n## Original document\n\nnone\n", encoding="utf-8")
            data = {
                "activities": [], "files": [], "protected_files": [],
                "records": [{
                    "key": "r", "note_path": "record.md", "title": "Record", "status": "final",
                    "source_keys": [], "related": ["ghost"], "review_reasons": [], "activity": None,
                }],
            }
            errors = validate_vault(root, data)
            self.assertTrue(any("loose" in e for e in errors), errors)
            self.assertTrue(any("related" in e for e in errors), errors)

    def test_ignores_scratch_markdown_and_allows_one_way_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scratch = root / ".superpowers/sdd/plan"
            scratch.mkdir(parents=True)
            (scratch / "task-1-brief.md").write_text("[[02 Activities/Activ/Notes/Ghost.md]]\n", encoding="utf-8")
            (root / "a.md").write_text("---\ntype: record\n---\n# A\n\n## Original document\n\nx\n", encoding="utf-8")
            (root / "b.md").write_text("---\ntype: record\n---\n# B\n\n## Original document\n\nx\n", encoding="utf-8")
            data = {
                "activities": [], "files": [], "protected_files": [],
                "records": [
                    {"key": "a", "note_path": "a.md", "title": "A", "status": "final", "source_keys": [],
                     "related": ["b"], "review_reasons": [], "activity": None},
                    {"key": "b", "note_path": "b.md", "title": "B", "status": "final", "source_keys": [],
                     "related": [], "review_reasons": [], "activity": None},
                ],
            }
            errors = validate_vault(root, data)
            self.assertFalse(any("scratch" in e or "task-1-brief" in e for e in errors), errors)
            self.assertFalse(any("reciprocal" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
