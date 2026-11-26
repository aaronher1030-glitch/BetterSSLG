import json
import tempfile
import unittest
from pathlib import Path

from tools.sslg_navigation import (
    BASES_YAML,
    NAVIGATION_PATHS,
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
        for route in ("[[01 Dashboards/Activity Dashboard.md|Activity Dashboard]]",
                      "[[01 Dashboards/Document Library.md|Document Library]]",
                      "[[01 Dashboards/Timeline.md|Timeline]]",
                      "[[01 Dashboards/Review Queue.md|Review Queue]]"):
            self.assertIn(route, text)
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
        text = render_document_library(DATA)
        self.assertIn("![[01 Dashboards/SSLG Records.base]]", text)
        for view in ("All records", "Proposals", "Completion reports", "Memoranda", "Needs review"):
            self.assertIn(view, text)

    def test_review_queue_lists_every_reason_of_an_entity(self):
        data = {
            "activities": [], "files": [],
            "records": [{
                "key": "r", "title": "Two Question Memorandum", "note_path": "03 Governance/Two.md",
                "status": "needs-review",
                "review_reasons": ["The first reason names one number.",
                                  "The second reason names another number."],
            }],
        }
        text = render_review_queue(data)
        self.assertIn("The first reason names one number.", text)
        self.assertIn("The second reason names another number.", text)

    def test_review_queue_includes_records_flagged_only_by_reason(self):
        data = {
            "activities": [], "files": [],
            "records": [{
                "key": "r", "title": "Final But Questioned", "note_path": "03 Governance/Questioned.md",
                "status": "final", "review_reasons": ["The letterhead keeps the [School Name] placeholder."],
            }],
        }
        text = render_review_queue(data)
        self.assertIn("[[03 Governance/Questioned.md|Final But Questioned]]", text)
        self.assertIn("The letterhead keeps the [School Name] placeholder.", text)

    def test_timeline_rows_are_sorted_by_date(self):
        def record(key, date, event_date):
            return {"key": key, "title": key, "note_path": f"03 Governance/{key}.md",
                    "record_type": "memorandum", "record_id": "", "date": date,
                    "event_date": event_date, "school_year": "2026-2027", "status": "final",
                    "activity": None, "collection": "governance", "summary": "", "key_details": [],
                    "source_keys": [], "related": [], "review_reasons": []}
        data = dict(DATA)
        data["records"] = [record("Late", "2026-10-05", "2026-12-01"),
                          record("Early", "2026-06-01", "2026-07-01"),
                          record("Middle", "2026-08-08", "2026-09-09")]
        data["activities"] = [dict(a, start_date=None) if a["key"] == "act-b" else a
                              for a in DATA["activities"]] + [
            {"key": "act-c", "title": "Zeta Activity", "hub_path": "02 Activities/Zeta/Zeta.md",
             "start_date": "2026-08-10", "end_date": None, "school_year": "2026-2027", "status": "planned",
             "venue": "", "summary": "", "outcomes": [], "review_reasons": []}]
        text = render_timeline(data)

        def dates(section, end):
            body = text.split(section)[1].split(end)[0]
            return [line.split("|")[1].strip() for line in body.splitlines()
                    if line.startswith("| 20") or line.startswith("| None") or line.startswith("| Not")]
        events = dates("## Activity and meeting dates", "## Record issuance dates")
        issued = dates("## Record issuance dates", "### Records with")
        schedule = dates("## Activity schedule", "## Activity and meeting dates")
        self.assertEqual(events, ["2026-07-01", "2026-09-09", "2026-12-01"])
        self.assertEqual(issued, ["2026-06-01", "2026-08-08", "2026-10-05"])
        self.assertEqual(schedule[:3], ["2026-07-22", "2026-08-10", "Not stated in source"])

    def test_home_links_collection_members(self):
        text = render_home(DATA)
        self.assertIn("[[03 Governance/Conflicted.md|Conflicted Memorandum]]", text)

    def test_document_library_lists_only_collections_that_hold_records(self):
        text = render_document_library(DATA)
        self.assertIn("`03 Governance/`", text)
        self.assertIn("`02 Activities/`", text)
        self.assertNotIn("`05 General Records/`", text)
        general = dict(DATA)
        general["records"] = list(DATA["records"]) + [
            {"key": "r-gen", "title": "General Item", "note_path": "05 General Records/General Item.md",
             "record_type": "request", "record_id": "", "date": None, "event_date": None,
             "school_year": "2026-2027", "status": "final", "activity": None, "collection": "general",
             "summary": "", "key_details": [], "source_keys": [], "related": [], "review_reasons": []}]
        self.assertIn("`05 General Records/`", render_document_library(general))

    def test_templates_mirror_generated_notes_without_example_links(self):
        record_text = render_record_template()
        for prop in ("type: record", "record_type:", "record_id:", "id_provenance: \"not-stated\"",
                     "date:", "event_date:", "school_year:",
                     "status:", "needs_review:", "activity:", "source_file:", "source_path:", "source_format:",
                     "related:", "tags:"):
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

    def test_activity_template_does_not_pre_fill_a_stage_claim(self):
        activity_text = render_activity_template()
        self.assertNotIn("Not present in the supplied records:", activity_text)
        self.assertNotIn("| proposal |", activity_text)

    def test_home_names_the_non_record_working_folders(self):
        text = render_home(DATA)
        self.assertIn("`tools/`", text)
        self.assertIn("`docs/`", text)

    def test_bases_excludes_the_templates_folder_too(self):
        self.assertIn('file.folder != "99 Templates"', BASES_YAML)

    def test_needs_review_views_filter_on_the_review_flag(self):
        self.assertIn('needs_review == "yes"', BASES_YAML)
        self.assertIn("name: Activities needing review", BASES_YAML)
        self.assertIn('type == "activity"', BASES_YAML)

    def test_document_library_describes_the_activities_review_view(self):
        text = render_document_library(DATA)
        self.assertIn("Activities needing review", text)

    def test_home_links_the_archive_and_template_artifacts(self):
        text = render_home(DATA)
        for target in ("[[90 Archive/Archive Index.md|Archive Index]]",
                       "[[90 Archive/File Manifest.json|File Manifest]]",
                       "[[99 Templates/Activity Template.md|Activity Template]]",
                       "[[99 Templates/Record Template.md|Record Template]]"):
            self.assertIn(target, text)

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
            self.assertEqual(sorted(NAVIGATION_PATHS), relative)
            self.assertEqual(json.loads((root / ".obsidian/templates.json").read_text(encoding="utf-8")),
                             {"folder": "99 Templates"})
            self.assertIn("Later Activity", (root / "01 Dashboards/Review Queue.md").read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                generate_navigation(root, DATA)


if __name__ == "__main__":
    unittest.main()
