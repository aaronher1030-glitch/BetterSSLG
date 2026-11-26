import json
import re
import shutil
import subprocess
import unittest
import zipfile
from pathlib import Path

from tools.sslg_migration import collect_baseline


ROOT = Path(__file__).resolve().parents[2]
CONTENT_PATH = ROOT / "tools" / "sslg_content.json"
ROLES = {"primary", "alternative-format", "revision", "duplicate", "staged", "asset"}
RECORD_TYPES = {
    "proposal", "completion-report", "memorandum", "meeting-notice",
    "excuse-letter", "request", "governance-policy",
}


def related_asymmetries(records):
    by_key = {record["key"]: record for record in records}
    return [(record["key"], other)
            for record in records
            for other in record["related"]
            if other in by_key and record["key"] not in by_key[other]["related"]]


IDENTITY_REASON = re.compile(r"(?:byte-identical|text identical)(?: duplicate)?(?: of| to) (.+)$")
EXECUTION_CLAIM = re.compile(r"(?<![A-Za-z])Signed\b[^.\n]*?\b(?:under|by)\b")


def normalise(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def id_candidates(record_id: str):
    forms = {record_id, record_id.replace(" ", "-"), record_id.replace(" ", "_")}
    match = re.search(r"No\.\s*(\d{3}),?\s*s\.\s*(\d{4})", record_id)
    if match:
        forms.add(f"No. {match.group(1)}, s. {match.group(2)}")
    return {normalise(form) for form in forms if normalise(form)}


SIGNATURE_EVIDENCE = re.compile(rb"/Alt\s*\(\s*signature\s*\)|/ByteRange", re.I)


def has_execution_evidence(path: Path) -> bool:
    if "signed" in path.as_posix().lower():
        return True
    try:
        return bool(SIGNATURE_EVIDENCE.search(path.read_bytes()))
    except OSError:
        return False


def source_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as package:
            xml = package.read("word/document.xml").decode("utf-8", "ignore")
        return re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", xml))
    if path.suffix.lower() == ".pdf" and shutil.which("pdftotext"):
        return subprocess.run(["pdftotext", str(path), "-"], capture_output=True,
                              text=True, encoding="utf-8", errors="ignore").stdout or ""
    return ""


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


    def test_every_activity_names_organizers(self):
        for activity in self.activities:
            self.assertTrue(activity.get("organizers"), activity["key"])

    def test_record_sources_order_primary_first_and_pdf_last(self):
        files = {entry["key"]: entry for entry in self.files}
        for record in self.records:
            sources = [files[key] for key in record["source_keys"]]
            self.assertEqual(sources[0]["role"], "primary", record["key"])
            formats = [Path(entry["current_path"]).suffix.lower() for entry in sources]
            if ".pdf" in formats:
                self.assertEqual(formats[-1], ".pdf", record["key"])


    def test_duplicate_reasons_point_at_a_real_same_hash_file_without_cycles(self):
        by_name = {Path(entry["original_path"]).name: entry for entry in self.files}
        for entry in self.files:
            reason = entry["archive_reason"]
            if not reason.startswith("byte-identical duplicate of "):
                continue
            target = reason[len("byte-identical duplicate of "):].strip()
            self.assertIn(target, by_name, entry["original_path"])
            self.assertEqual(by_name[target]["sha256"], entry["sha256"], entry["original_path"])
            self.assertNotEqual(target, Path(entry["original_path"]).name, entry["original_path"])
            forward = by_name[target]["archive_reason"]
            self.assertFalse(forward.startswith("byte-identical duplicate of ")
                             and forward[len("byte-identical duplicate of "):].strip()
                             == Path(entry["original_path"]).name,
                             f"circular pair: {entry['original_path']} <-> {target}")

    def test_related_links_are_mutual(self):
        self.assertEqual(related_asymmetries([{"key": "x", "related": ["y"]},
                                             {"key": "y", "related": []}]), [("x", "y")])
        self.assertEqual(related_asymmetries(self.records), [])

    def test_current_paths_are_unique_and_match_the_role_rules(self):
        paths = [entry["current_path"] for entry in self.files]
        self.assertEqual(len(paths), len(set(paths)))
        for entry in self.files:
            archived = entry["current_path"].startswith("90 Archive/")
            self.assertEqual(entry["role"] in {"revision", "duplicate", "staged"}, archived,
                             entry["original_path"])

    def test_no_record_source_is_placed_in_the_archive(self):
        by_key = {entry["key"]: entry for entry in self.files}
        for record in self.records:
            for key in record["source_keys"]:
                self.assertFalse(by_key[key]["current_path"].startswith("90 Archive/"),
                                 f"{record['key']} -> {by_key[key]['current_path']}")

    def test_signed_status_requires_source_evidence(self):
        by_key = {entry["key"]: entry for entry in self.files}
        for record in self.records:
            if record["status"] != "signed":
                continue
            paths = [by_key[key]["current_path"] for key in record["source_keys"]]
            self.assertTrue(any(has_execution_evidence(ROOT / path) for path in paths),
                            f"{record['key']} claims signed without source evidence: {paths}")

    def test_no_prose_asserts_execution_without_source_evidence(self):
        by_key = {entry["key"]: entry for entry in self.files}
        for record in self.records:
            prose = [record["summary"], *record["key_details"], *record["review_reasons"]]
            paths = [by_key[key]["current_path"] for key in record["source_keys"]]
            evidence = any(has_execution_evidence(ROOT / path) for path in paths)
            for claim in prose:
                found = EXECUTION_CLAIM.search(claim)
                if found and not evidence:
                    self.fail(f"{record['key']} asserts signing ({found.group(0)!r}) with no signed source: {paths}")

    def test_declared_id_provenance_matches_the_record_source_text(self):
        by_key = {entry["key"]: entry for entry in self.files}
        for record in self.records:
            provenance = record.get("id_provenance")
            if not record["record_id"]:
                self.assertEqual(provenance, "not-stated", record["key"])
                continue
            self.assertIn(provenance, ("printed", "filename"), record["key"])
            texts = [source_text(ROOT / by_key[key]["current_path"]) for key in record["source_keys"]]
            checked = [text for text in texts if text.strip()]
            if not checked:
                continue
            blob = normalise(" ".join(checked))
            grounded = any(candidate in blob for candidate in id_candidates(record["record_id"]))
            if provenance == "printed":
                self.assertTrue(grounded, f"{record['key']} is labelled printed but no readable source carries it")
            else:
                self.assertFalse(grounded, f"{record['key']} is labelled filename-derived but a source prints it")

    def test_identity_reasons_name_a_resolvable_anchor(self):
        for entry in self.files:
            match = IDENTITY_REASON.search(entry["archive_reason"])
            if not match:
                continue
            for anchor in [part.strip() for part in match.group(1).split(" and ")]:
                if "/" in anchor:
                    candidates = [other for other in self.files if other["current_path"] == anchor]
                else:
                    candidates = [other for other in self.files
                                  if Path(other["current_path"]).name == anchor
                                  or Path(other["original_path"]).name == anchor]
                others = [other for other in candidates if other["current_path"] != entry["current_path"]]
                self.assertTrue(others, f"{entry['current_path']} cites no other file as {anchor!r}")
                if "byte-identical" in entry["archive_reason"]:
                    self.assertTrue(any(other["sha256"] == entry["sha256"] for other in others),
                                    f"{entry['current_path']} is not byte-identical to {anchor}")
                if len(candidates) > 1:
                    self.assertIn("/", anchor,
                                  f"{entry['current_path']}: {anchor} matches several files, cite a path")


if __name__ == "__main__":
    unittest.main()
