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
            on_disk = sorted(path.relative_to(root).as_posix() for path in root.rglob("*.md"))
            expected = sorted([MULTI["activities"][0]["hub_path"]]
                              + [entry["note_path"] for entry in MULTI["records"]])
            self.assertEqual(on_disk, expected)
            self.assertEqual(sorted(path.relative_to(root).as_posix() for path in written), expected)
            for path in written:
                self.assertTrue(path.read_text(encoding="utf-8").startswith("---\n"))
            with self.assertRaises(FileExistsError):
                generate_notes(root, MULTI)

    def test_generate_notes_leaves_no_partially_written_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / MULTI["activities"][0]["hub_path"]
            first.parent.mkdir(parents=True)
            first.write_text("existing\n", encoding="utf-8")
            before = sorted(str(p) for p in root.rglob("*.md"))
            with self.assertRaises(FileExistsError):
                generate_notes(root, MULTI)
            self.assertEqual(sorted(str(p) for p in root.rglob("*.md")), before)
            self.assertEqual(first.read_text(encoding="utf-8"), "existing\n")

    def test_generate_notes_refuses_two_records_resolving_to_one_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = json.loads(json.dumps(DATA))
            twin = json.loads(json.dumps(data["records"][0]))
            twin["key"] = "record-a-twin"
            twin["title"] = "Proposal a"
            twin["note_path"] = "02 activities/Activity A/Notes/Proposal A.md"
            data["records"].append(twin)
            for entry in data["files"]:
                if entry["key"] == "word-source":
                    entry["source_key"] = entry["key"]
            with self.assertRaises(FileExistsError):
                generate_notes(root, data)
            self.assertEqual(list(root.rglob("*.md")), [])

    def test_review_backlog_is_a_filterable_property(self):
        clean = render_record(DATA["records"][0], DATA)
        self.assertIn('needs_review: "no"', clean.split("---")[1])
        flagged = render_record(dict(DATA["records"][0], status="final",
                                     review_reasons=["Two copies carry different numbers."]), DATA)
        self.assertIn('needs_review: "yes"', flagged.split("---")[1])
        hub = render_activity(MULTI["activities"][0], MULTI)
        self.assertIn('needs_review: "yes"', hub.split("---")[1])
        calm = render_activity(DATA["activities"][0], DATA)
        self.assertIn('needs_review: "no"', calm.split("---")[1])

    def test_document_id_discloses_filename_derived_provenance(self):
        derived = render_record(dict(DATA["records"][0], id_provenance="filename"), DATA)
        self.assertIn('id_provenance: "filename"', derived.split("---\n")[1])
        self.assertIn("> **Document ID:** AP_TEST_001 (derived from the source filename; "
                      "the document text does not print an identifier)", derived)
        printed = render_record(dict(DATA["records"][0], id_provenance="printed"), DATA)
        self.assertIn('id_provenance: "printed"', printed.split("---\n")[1])
        self.assertIn("> **Document ID:** AP_TEST_001", printed)
        self.assertNotIn("derived from the source filename", printed)

    def test_record_frontmatter_declares_every_required_property(self):
        text = render_record(DATA["records"][0], DATA)
        frontmatter = text.split("---\n")[1]
        for key in ("type", "title", "record_type", "record_id", "id_provenance", "date", "event_date",
                    "school_year", "activity", "status", "needs_review", "source_file", "source_path",
                    "source_format", "sources", "related", "tags"):
            self.assertRegex(frontmatter, rf"(?m)^{key}:")

    def test_activity_hub_shows_organizers_and_related_governance(self):
        data = json.loads(json.dumps(DATA))
        data["activities"][0]["organizers"] = ["Supreme Secondary Learner Government (SSLG)"]
        governance = record("gov-memo", "Division Memorandum", "memorandum",
                            "04 External Memoranda/Division Memorandum.md",
                            collection="external", activity=None)
        governance["related"] = ["record-a"]
        data["records"].append(governance)
        data["files"].append(source("gov-docx", "gov-memo", "gov.docx"))
        forward = record("gov-policy", "Governance Memorandum", "memorandum",
                         "03 Governance/Governance Memorandum.md",
                         collection="governance", activity=None)
        data["records"].append(forward)
        data["files"].append(source("policy-docx", "gov-policy", "policy.docx"))
        data["records"][0]["related"] = ["gov-policy"]
        text = render_activity(data["activities"][0], data)
        self.assertIn("**Organizers:** Supreme Secondary Learner Government (SSLG)", text)
        self.assertIn("## Related governance", text)
        self.assertIn("[[04 External Memoranda/Division Memorandum.md|Division Memorandum]]", text)
        self.assertIn("[[03 Governance/Governance Memorandum.md|Governance Memorandum]]", text)


if __name__ == "__main__":
    unittest.main()
