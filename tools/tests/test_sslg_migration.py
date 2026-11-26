import json
import tempfile
import unittest
from pathlib import Path

from tools.sslg_migration import (
    apply_moves,
    collect_baseline,
    preflight_moves,
    sha256,
    write_archive_index,
    write_manifest,
)


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

    def test_preflight_rejects_windows_drive_relative_original_path(self):
        unsafe = self.entry(original_path="C:evil/source.docx")
        errors = preflight_moves(self.root, [unsafe])
        self.assertIn("unsafe path: source-docx", errors)

    def test_audit_writers_create_then_refuse_to_overwrite(self):
        files = [self.entry()]
        write_manifest(self.root, {"files": files})
        write_archive_index(self.root, files)
        manifest_path = self.root / "90 Archive" / "File Manifest.json"
        index_path = self.root / "90 Archive" / "Archive Index.md"
        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8")), {"files": files})
        self.assertIn(files[0]["original_path"], index_path.read_text(encoding="utf-8"))
        with self.assertRaises(FileExistsError):
            write_manifest(self.root, {"files": files})
        with self.assertRaises(FileExistsError):
            write_archive_index(self.root, files)


if __name__ == "__main__":
    unittest.main()
