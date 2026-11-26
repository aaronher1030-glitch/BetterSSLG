# Task 2 review package (non-git workspace: full file contents, no diff)

## tools/tests/test_sslg_content.py

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

## tools/sslg_content.json

{
  "activities": [
    {
      "key": "brigada-eskwela-2026",
      "title": "Brigada Eskwela 2026",
      "hub_path": "02 Activities/Brigada Eskwela 2026/Brigada Eskwela 2026.md",
      "start_date": "2026-06-01",
      "end_date": "2026-06-05",
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Benigno S. Aquino National High School",
      "summary": "School-wide Brigada Eskwela week that prepared facilities for the opening of classes through a kick-off parade, opening and closing ceremonies, and cleaning tasks assigned to registered clubs and organizations.",
      "outcomes": [
        "Kick-off parade and opening ceremony were conducted.",
        "Assigned areas were cleaned and prepared for the opening of classes.",
        "Collaboration among registered clubs and organizations was strengthened.",
        "The week concluded with a closing ceremony."
      ],
      "review_reasons": [
        "No activity proposal for Brigada Eskwela 2026 is present in this collection."
      ]
    },
    {
      "key": "club-fair-2026",
      "title": "Club Fair 2026",
      "hub_path": "02 Activities/Club Fair 2026/Club Fair 2026.md",
      "start_date": "2026-06-01",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Benigno S. Aquino National High School",
      "summary": "Club Fair that introduced school clubs and organizations to learners and supported membership selection and club officer elections.",
      "outcomes": [
        "Club Fair was conducted.",
        "Learners were encouraged to join clubs based on their interests.",
        "Officer elections within clubs and organizations were organized."
      ],
      "review_reasons": [
        "No activity proposal or authorising memorandum for the Club Fair is present in this collection."
      ]
    },
    {
      "key": "grade7-representative-election-2026",
      "title": "SSLG Grade 7 Representative Elections 2026",
      "hub_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/SSLG Grade 7 Representative Elections 2026.md",
      "start_date": "2026-06-16",
      "end_date": "2026-06-25",
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Multi-Purpose Hall; Oreta Gymnasium",
      "summary": "Election of the SSLG Grade 7 Representatives who serve as spokespeople of their year level, including the Miting de Avance and the proclamation of the winners.",
      "outcomes": [
        "Newly elected SSLG Grade 7 Representatives were proclaimed.",
        "Grade 7 learners took part in the democratic election process."
      ],
      "review_reasons": []
    },
    {
      "key": "club-officers-election-2026",
      "title": "Election of Registered School Clubs and Organizations 2026",
      "hub_path": "02 Activities/Election of Registered School Clubs and Organizations 2026/Election of Registered School Clubs and Organizations 2026.md",
      "start_date": "2026-06-17",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Benigno S. Aquino National High School",
      "summary": "Election of officers for registered school clubs and organizations following the completion of membership registration.",
      "outcomes": [
        "Officer elections were conducted for registered clubs and organizations.",
        "Each club obtained its own set of elected officers."
      ],
      "review_reasons": [
        "No activity proposal for this election is present in this collection."
      ]
    },
    {
      "key": "gpoa-crafting-2026",
      "title": "Crafting of the SSLG General Plan of Action 2026",
      "hub_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Crafting of the SSLG General Plan of Action 2026.md",
      "start_date": "2026-07-03",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Supreme Secondary Learner Government Office",
      "summary": "Crafting of the General Plan of Action (GPOA) for student organizations and clubs for S.Y. 2026-2027.",
      "outcomes": [
        "The SSLG GPOA for the academic year was crafted.",
        "Proposed programmes, projects and activities were established to guide the SSLG.",
        "Planning collaboration between SSLG officers and advisers was strengthened."
      ],
      "review_reasons": []
    },
    {
      "key": "leaders-induction-2026",
      "title": "Onto the Next - Leaders Induction 2026",
      "hub_path": "02 Activities/Onto the Next - Leaders Induction 2026/Onto the Next - Leaders Induction 2026.md",
      "start_date": "2026-07-22",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Multi-Purpose Hall",
      "summary": "Onto the Next: Leaders 2026-2027 Induction Ceremony formally installing newly elected club and organization officers and the new set of Parent-Teacher Association officers.",
      "outcomes": [
        "Newly elected student leaders were formally inducted.",
        "Student organizations collaborated in conducting the ceremony.",
        "Service-oriented leadership was emphasised in the programme messages."
      ],
      "review_reasons": []
    },
    {
      "key": "project-ecolead-2026",
      "title": "Project ECOLEAD",
      "hub_path": "02 Activities/Project ECOLEAD/Project ECOLEAD.md",
      "start_date": null,
      "end_date": null,
      "school_year": "2026-2027",
      "status": "ongoing",
      "venue": "Benigno S. Aquino National High School premises",
      "summary": "Project ECOLEAD, the Learner Government Coordinating Council school clean-up and environmental stewardship programme implemented twice a month throughout S.Y. 2026-2027.",
      "outcomes": [
        "Clean-up activity designed for twice-monthly implementation with participating clubs and organizations."
      ],
      "review_reasons": [
        "No completion report is present in this collection.",
        "Memorandum copies state different implementation start dates: 31 July, 7 August, 22 September and 30 September 2026."
      ]
    },
    {
      "key": "project-tinig-2026",
      "title": "Project TINIG",
      "hub_path": "02 Activities/Project TINIG/Project TINIG.md",
      "start_date": null,
      "end_date": null,
      "school_year": "2026-2027",
      "status": "ongoing",
      "venue": "Not stated in source",
      "summary": "Project TINIG: Transparent Information Network for Inclusive Governance, an information platform for SSLG announcements, reports and club documentation.",
      "outcomes": [
        "Platform proposed for publishing official SSLG announcements, updates and reports."
      ],
      "review_reasons": [
        "No completion report is present in this collection."
      ]
    },
    {
      "key": "project-liwanag-2026",
      "title": "Project LIWANAG",
      "hub_path": "02 Activities/Project LIWANAG/Project LIWANAG.md",
      "start_date": null,
      "end_date": null,
      "school_year": "2026-2027",
      "status": "ongoing",
      "venue": "Not stated in source",
      "summary": "Project LIWANAG, a year-long documentation project producing a digital Legacy Journal of student leadership work with quarterly features.",
      "outcomes": [
        "Documentation of student leader activities, accomplishments and contributions proposed for S.Y. 2026-2027."
      ],
      "review_reasons": [
        "No completion report is present in this collection."
      ]
    },
    {
      "key": "foundation-day-2026",
      "title": "Foundation Day 2026",
      "hub_path": "02 Activities/Foundation Day 2026/Foundation Day 2026.md",
      "start_date": null,
      "end_date": null,
      "school_year": "2026-2027",
      "status": "planned",
      "venue": "Benigno S. Aquino National High School",
      "summary": "Celebration of the school's 78th Foundation Day with student-led booths managed by recognized clubs and organizations.",
      "outcomes": [
        "Student-led booths managed by recognized clubs and organizations proposed."
      ],
      "review_reasons": [
        "No activity date is stated in the proposal.",
        "No completion report is present in this collection."
      ]
    },
    {
      "key": "world-teachers-day-2026",
      "title": "World Teachers Day 2026",
      "hub_path": "02 Activities/World Teachers Day 2026/World Teachers Day 2026.md",
      "start_date": null,
      "end_date": null,
      "school_year": "2026-2027",
      "status": "needs-review",
      "venue": "Benigno S. Aquino National High School",
      "summary": "2026 World Teachers' Day Celebration honouring the contributions of teachers, with a programme running from 6:30 A.M. to 10:30 A.M.",
      "outcomes": [
        "Programme of activities from 6:30 A.M. to 10:30 A.M. proposed."
      ],
      "review_reasons": [
        "Proposal copies state conflicting celebration dates: 2 October 2026 in the files labelled 'revised' and 5 October 2026 in AP_SSLG_2026_006 (3).docx.",
        "No completion report is present in this collection."
      ]
    },
    {
      "key": "national-students-day-2026",
      "title": "National Students Day 2026",
      "hub_path": "02 Activities/National Students Day 2026/National Students Day 2026.md",
      "start_date": "2026-11-17",
      "end_date": "2026-11-18",
      "school_year": "2026-2027",
      "status": "planned",
      "venue": "Benigno S. Aquino National High School",
      "summary": "2026 National Students' Day Celebration under the theme Beyond Limits, Beyond Ordinary: The Aquinian Spirit, anchored on Republic Act No. 11369.",
      "outcomes": [
        "Competitions, performances and interactive activities proposed for 17-18 November 2026.",
        "Annex D division-submission version prepared and then proofread."
      ],
      "review_reasons": [
        "No completion report is present in this collection."
      ]
    },
    {
      "key": "cluster-iv-training-camp-2026",
      "title": "Cluster IV SSLG Federation Leadership Training Camp",
      "hub_path": "02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Cluster IV SSLG Federation Leadership Training Camp.md",
      "start_date": null,
      "end_date": null,
      "school_year": "2026-2027",
      "status": "needs-review",
      "venue": "Not stated in source",
      "summary": "Cluster IV SSLG Federation Leadership Training Camp and the SSLG officer meetings convened to prepare for it.",
      "outcomes": [
        "Meetings on 15 and 16 May 2026 were convened to prepare for the camp and align on officer conduct."
      ],
      "review_reasons": [
        "No document states the camp date, venue or outcome.",
        "No proposal, authorising memorandum or completion report for the camp itself is present."
      ]
    },
    {
      "key": "short-film-festival-2026",
      "title": "Municipal Short Film Festival 2026",
      "hub_path": "02 Activities/Municipal Short Film Festival 2026/Municipal Short Film Festival 2026.md",
      "start_date": "2026-07-13",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Concepcion, Tarlac",
      "summary": "Municipal Short Film Festival short-film shooting organised by the Concepcion Local Government Unit Social Welfare office, which SSLG officers attended.",
      "outcomes": [
        "SSLG officers were excused from classes on 13 July 2026 from 1:00 P.M. to 5:00 P.M. to take part."
      ],
      "review_reasons": [
        "No completion report is present in this collection."
      ]
    },
    {
      "key": "earthquake-drill-2026",
      "title": "Earthquake Drill 2026",
      "hub_path": "02 Activities/Earthquake Drill 2026/Earthquake Drill 2026.md",
      "start_date": "2026-06-24",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "completed",
      "venue": "Benigno S. Aquino National High School",
      "summary": "School earthquake drill on 24 June 2026 that required SSLG officers and Red Cross Youth members to be excused from classes.",
      "outcomes": [
        "Participating clubs and organizations were excused from 8:45 A.M. onwards."
      ],
      "review_reasons": [
        "Only the excuse letter documents this activity in the collection."
      ]
    },
    {
      "key": "digital-device-survey-2026",
      "title": "Nationwide Online Survey on Digital Device Use",
      "hub_path": "02 Activities/Nationwide Online Survey on Digital Device Use/Nationwide Online Survey on Digital Device Use.md",
      "start_date": "2026-08-25",
      "end_date": null,
      "school_year": "2026-2027",
      "status": "ongoing",
      "venue": "Online",
      "summary": "Dissemination of the Nationwide Online Survey on Digital Device Use in Schools, cascaded from the National Federation through the Division and Cluster Federations to the school SSLG.",
      "outcomes": [
        "School-level Memorandum No. 002 issued in late August 2026 to convey the survey.",
        "Respondents below 18 years of age were directed to the Parental Consent Form annex."
      ],
      "review_reasons": [
        "Survey closing date and submission evidence are not stated in the documents."
      ]
    }
  ],
  "records": [
    {
      "key": "acr-sslg-2026-001",
      "title": "Activity Completion Report ACR-SSLG-2026-001 - Brigada Eskwela 2026",
      "note_path": "02 Activities/Brigada Eskwela 2026/Notes/Activity Completion Report ACR-SSLG-2026-001 - Brigada Eskwela 2026.md",
      "record_type": "completion-report",
      "record_id": "ACR_SSLG_2026_001",
      "date": null,
      "event_date": "2026-06-05",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "brigada-eskwela-2026",
      "collection": "activities",
      "summary": "Completion report for Brigada Eskwela 2026 held 1-5 June 2026 at Benigno S. Aquino National High School.",
      "key_details": [
        "Activity ran 1-5 June 2026 with cleaning areas assigned to registered clubs and organizations.",
        "Challenge recorded: limited time and varying workloads in the assigned areas.",
        "Concluded with a closing ceremony."
      ],
      "source_keys": [
        "acr_sslg_2026_001.docx"
      ],
      "related": [
        "nom-sslg-2026-003-may29",
        "om-dfsslg-2026-003",
        "om-cfsslg-2026-003"
      ],
      "review_reasons": []
    },
    {
      "key": "acr-sslg-2026-002",
      "title": "Activity Completion Report ACR-SSLG-2026-002 - SSLG Grade 7 Representative Elections",
      "note_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Activity Completion Report ACR-SSLG-2026-002 - SSLG Grade 7 Representative Elections.md",
      "record_type": "completion-report",
      "record_id": "ACR_SSLG_2026_002",
      "date": null,
      "event_date": "2026-06-25",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "grade7-representative-election-2026",
      "collection": "activities",
      "summary": "Completion report for the SSLG Grade 7 Representative Elections conducted 16-25 June 2026 at the Multi-Purpose Hall and Oreta Gymnasium.",
      "key_details": [
        "Newly elected Grade 7 Representatives were officially proclaimed.",
        "The planned Miting de Avance debate was omitted because the scheduled earthquake drill limited time.",
        "The programme proceeded with candidates' campaign speeches before the proclamation."
      ],
      "source_keys": [
        "acr_sslg_2026_002.docx"
      ],
      "related": [
        "el-sslg-2026-004",
        "el-sslg-2026-005-elections",
        "request-mph-jun25",
        "el-sslg-2026-005-drill"
      ],
      "review_reasons": []
    },
    {
      "key": "acr-sslg-2026-003",
      "title": "Activity Completion Report ACR-SSLG-2026-003 - Club Fair 2026",
      "note_path": "02 Activities/Club Fair 2026/Notes/Activity Completion Report ACR-SSLG-2026-003 - Club Fair 2026.md",
      "record_type": "completion-report",
      "record_id": "ACR_SSLG_2026_003",
      "date": null,
      "event_date": "2026-06-01",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "club-fair-2026",
      "collection": "activities",
      "summary": "Completion report for Club Fair 2026, which introduced school clubs and organizations and supported learner membership selection.",
      "key_details": [
        "Learners were encouraged to join clubs based on their interests.",
        "Officer elections within clubs and organizations were organized.",
        "Challenge recorded: insufficient instructions about the membership application process."
      ],
      "source_keys": [
        "acr_sslg_2026_003.docx"
      ],
      "related": [
        "acr-sslg-2026-004"
      ],
      "review_reasons": []
    },
    {
      "key": "acr-sslg-2026-004",
      "title": "Activity Completion Report ACR-SSLG-2026-004 - Election of Registered School Clubs and Organizations",
      "note_path": "02 Activities/Election of Registered School Clubs and Organizations 2026/Notes/Activity Completion Report ACR-SSLG-2026-004 - Election of Registered School Clubs and Organizations.md",
      "record_type": "completion-report",
      "record_id": "ACR_SSLG_2026_004",
      "date": null,
      "event_date": "2026-06-17",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "club-officers-election-2026",
      "collection": "activities",
      "summary": "Completion report for the 17 June 2026 election of officers of registered school clubs and organizations.",
      "key_details": [
        "Elections followed completion of the membership drive and registration.",
        "Some clubs were delayed by finalization of their registered members.",
        "Follow-up coordination and flexible timelines were applied."
      ],
      "source_keys": [
        "acr_sslg_2026_004.docx"
      ],
      "related": [
        "acr-sslg-2026-003"
      ],
      "review_reasons": []
    },
    {
      "key": "acr-sslg-2026-005",
      "title": "Activity Completion Report ACR-SSLG-2026-005 - Crafting of the General Plan of Action (GPOA)",
      "note_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Activity Completion Report ACR-SSLG-2026-005 - Crafting of the General Plan of Action (GPOA).md",
      "record_type": "completion-report",
      "record_id": "ACR_SSLG_2026_005",
      "date": null,
      "event_date": "2026-07-03",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "gpoa-crafting-2026",
      "collection": "activities",
      "summary": "Completion report for the 3 July 2026 crafting of the SSLG General Plan of Action at the SSLG Office.",
      "key_details": [
        "The SSLG GPOA for the academic year was crafted.",
        "Activities not aligned with learner needs or requiring more financial resources were excluded.",
        "Collaboration between SSLG officers and advisers was strengthened."
      ],
      "source_keys": [
        "acr_sslg_2026_005.docx"
      ],
      "related": [
        "nom-sslg-2026-003-jun06",
        "nom-sslg-2026-004"
      ],
      "review_reasons": []
    },
    {
      "key": "acr-sslg-2026-006",
      "title": "Activity Completion Report ACR-SSLG-2026-006 - Onto the Next: Leaders Induction Ceremony",
      "note_path": "02 Activities/Onto the Next - Leaders Induction 2026/Notes/Activity Completion Report ACR-SSLG-2026-006 - Onto the Next- Leaders Induction Ceremony.md",
      "record_type": "completion-report",
      "record_id": "ACR_SSLG_2026_006",
      "date": null,
      "event_date": "2026-07-22",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "leaders-induction-2026",
      "collection": "activities",
      "summary": "Completion report for the Onto the Next: Leaders Induction Ceremony held 22 July 2026 at the Multi-Purpose Hall.",
      "key_details": [
        "Newly elected student leaders were formally inducted.",
        "Programme opened with an invocation, the Philippine National Anthem and the School Principal's opening remarks.",
        "Collaboration among student organizations and the LGCC was reported."
      ],
      "source_keys": [
        "acr_sslg_2026_006.docx"
      ],
      "related": [
        "ap-sslg-2026-001"
      ],
      "review_reasons": []
    },
    {
      "key": "ap-sslg-2026-001",
      "title": "Activity Proposal AP-SSLG-2026-001 - Onto the Next: Leaders 2026-2027 Induction Ceremony",
      "note_path": "02 Activities/Onto the Next - Leaders Induction 2026/Notes/Activity Proposal AP-SSLG-2026-001 - Onto the Next- Leaders 2026-2027 Induction Ceremony.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_001",
      "date": null,
      "event_date": "2026-07-22",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "leaders-induction-2026",
      "collection": "activities",
      "summary": "Proposal for the 22 July 2026 induction ceremony, 8:00 A.M. to 12:00 N.N., at the Multi-Purpose Hall.",
      "key_details": [
        "Objectives cover formal induction of newly elected officers, accountability, unity and servant leadership.",
        "Rationale frames the ceremony as the start of the leadership journey of newly elected officers."
      ],
      "source_keys": [
        "ap_sslg_2026_001.docx"
      ],
      "related": [
        "acr-sslg-2026-006"
      ],
      "review_reasons": []
    },
    {
      "key": "ap-sslg-2026-002",
      "title": "Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD",
      "note_path": "02 Activities/Project ECOLEAD/Notes/Activity Proposal AP-SSLG-2026-002 - Project ECOLEAD.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_002",
      "date": null,
      "event_date": null,
      "school_year": "2026-2027",
      "status": "final",
      "activity": "project-ecolead-2026",
      "collection": "activities",
      "summary": "Proposal for Project ECOLEAD, the LGCC school clean-up and environmental stewardship programme for S.Y. 2026-2027.",
      "key_details": [
        "Clean-up activity conducted twice a month throughout the school year.",
        "Objectives cover cleanliness, learner responsibility, teamwork and consistent habits."
      ],
      "source_keys": [
        "ap_sslg_2026_002.docx"
      ],
      "related": [
        "om-sslg-2026-002-ecolead",
        "om-sslg-2026-003-ecolead"
      ],
      "review_reasons": []
    },
    {
      "key": "ap-sslg-2026-003",
      "title": "Activity Proposal AP-SSLG-2026-003 - Project TINIG",
      "note_path": "02 Activities/Project TINIG/Notes/Activity Proposal AP-SSLG-2026-003 - Project TINIG.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_003",
      "date": null,
      "event_date": null,
      "school_year": "2026-2027",
      "status": "final",
      "activity": "project-tinig-2026",
      "collection": "activities",
      "summary": "Proposal for Project TINIG: Transparent Information Network for Inclusive Governance, an SSLG information and documentation platform.",
      "key_details": [
        "Publishes official SSLG announcements, updates, reports and financial summaries.",
        "Gives recognized clubs and organizations a platform to present programmes and accomplishments."
      ],
      "source_keys": [
        "ap_sslg_2026_003.docx"
      ],
      "related": [],
      "review_reasons": []
    },
    {
      "key": "ap-sslg-2026-004",
      "title": "Activity Proposal AP-SSLG-2026-004 - Project LIWANAG",
      "note_path": "02 Activities/Project LIWANAG/Notes/Activity Proposal AP-SSLG-2026-004 - Project LIWANAG.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_004",
      "date": null,
      "event_date": null,
      "school_year": "2026-2027",
      "status": "final",
      "activity": "project-liwanag-2026",
      "collection": "activities",
      "summary": "Proposal for Project LIWANAG, a year-long documentation project producing a digital Legacy Journal of student leadership with quarterly features.",
      "key_details": [
        "Documents activities and accomplishments of student leaders for S.Y. 2026-2027.",
        "Recognizes student leader contributions through periodic features."
      ],
      "source_keys": [
        "ap_sslg_2026_004.docx"
      ],
      "related": [],
      "review_reasons": []
    },
    {
      "key": "ap-sslg-2026-005",
      "title": "Activity Proposal AP-SSLG-2026-005 - Foundation Day 2026",
      "note_path": "02 Activities/Foundation Day 2026/Notes/Activity Proposal AP-SSLG-2026-005 - Foundation Day 2026.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_005",
      "date": null,
      "event_date": null,
      "school_year": "2026-2027",
      "status": "needs-review",
      "activity": "foundation-day-2026",
      "collection": "activities",
      "summary": "Proposal for the school's 78th Foundation Day celebration with student-led booths managed by recognized clubs and organizations.",
      "key_details": [
        "Commemorates 78 years of service of the school.",
        "Student-led booths develop entrepreneurial and organizational skills."
      ],
      "source_keys": [
        "ap_sslg_2026_005-(2).docx"
      ],
      "related": [],
      "review_reasons": [
        "The single proposal copy states no activity date, so the Foundation Day schedule cannot be recorded from the source."
      ]
    },
    {
      "key": "ap-sslg-2026-006",
      "title": "Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration",
      "note_path": "02 Activities/World Teachers Day 2026/Notes/Activity Proposal AP-SSLG-2026-006 - 2026 World Teachers' Day Celebration.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_006",
      "date": null,
      "event_date": "2026-10-02",
      "school_year": "2026-2027",
      "status": "needs-review",
      "activity": "world-teachers-day-2026",
      "collection": "activities",
      "summary": "Proposal for the 2026 World Teachers' Day celebration from 6:30 A.M. to 10:30 A.M., honouring the contributions of teachers.",
      "key_details": [
        "Programme begins with assembly at 6:30 A.M.",
        "Objectives cover recognition and appreciation of teachers' dedication."
      ],
      "source_keys": [
        "ap_sslg_2026_006_revised.docx"
      ],
      "related": [],
      "review_reasons": [
        "The three 'revised' copies state 2 October 2026 while AP_SSLG_2026_006 (3).docx states 5 October 2026; neither copy is signed and no later authority resolves the conflict.",
        "Programme items also differ: the revised copies list an LGCC collaborative performance by named groups, the 5 October copy lists a generic LGCC performance."
      ]
    },
    {
      "key": "ap-sslg-2026-007",
      "title": "Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration",
      "note_path": "02 Activities/National Students Day 2026/Notes/Activity Proposal AP-SSLG-2026-007 - 2026 National Students' Day Celebration.md",
      "record_type": "proposal",
      "record_id": "AP_SSLG_2026_007",
      "date": null,
      "event_date": "2026-11-17",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "national-students-day-2026",
      "collection": "activities",
      "summary": "Proposal for the 2026 National Students' Day celebration on 17-18 November 2026 under the theme Beyond Limits, Beyond Ordinary: The Aquinian Spirit, with the Annex D division submission version.",
      "key_details": [
        "Anchored on Republic Act No. 11369, the National Students' Day Act.",
        "Annex D version adds a zumba segment from 3:00 P.M. to 5:00 P.M. with tickets and SPTA involvement.",
        "Proofread version cleans the title block and competition list."
      ],
      "source_keys": [
        "ap_sslg_2026_007_annexd.pdf",
        "ap_sslg_2026_007_annexd_proofread.docx"
      ],
      "related": [],
      "review_reasons": []
    },
    {
      "key": "el-sslg-2026-004",
      "title": "Excuse Letter EL-SSLG-2026-004 - SSLG Grade 7 Representative Miting de Avance",
      "note_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Excuse Letter EL-SSLG-2026-004 - SSLG Grade 7 Representative Miting de Avance.md",
      "record_type": "excuse-letter",
      "record_id": "EL_SSLG_2026_004",
      "date": "2026-06-23",
      "event_date": "2026-06-24",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "grade7-representative-election-2026",
      "collection": "activities",
      "summary": "Letter of 23 June 2026 requesting that SSLG officers be excused from classes on 24 June 2026 from 6:30 A.M. to 9:00 A.M. for the Grade 7 Representative Miting de Avance.",
      "key_details": [
        "Addressed to senior high school and junior high school teachers.",
        "Prepared by the SSLG Secretary, noted by the SSLG Adviser, recommending approval by the Head Teacher VI."
      ],
      "source_keys": [
        "el_sslg_2026_004.docx"
      ],
      "related": [
        "acr-sslg-2026-002",
        "el-sslg-2026-005-drill"
      ],
      "review_reasons": []
    },
    {
      "key": "el-sslg-2026-005-drill",
      "title": "Excuse Letter EL-SSLG-2026-005 - Earthquake Drill",
      "note_path": "02 Activities/Earthquake Drill 2026/Notes/Excuse Letter EL-SSLG-2026-005 - Earthquake Drill.md",
      "record_type": "excuse-letter",
      "record_id": "EL_SSLG_2026_005",
      "date": "2026-06-23",
      "event_date": "2026-06-24",
      "school_year": "2026-2027",
      "status": "signed",
      "activity": "earthquake-drill-2026",
      "collection": "activities",
      "summary": "Letter of 23 June 2026 excusing SSLG officers and Red Cross Youth members from classes on 24 June 2026 from 8:45 A.M. onwards for the earthquake drill.",
      "key_details": [
        "Approved by Amparo M. Munoz, EDD, Principal IV.",
        "The drill truncated the Miting de Avance programme recorded in ACR-SSLG-2026-002."
      ],
      "source_keys": [
        "el_sslg_2026_005.docx"
      ],
      "related": [
        "acr-sslg-2026-002",
        "el-sslg-2026-004"
      ],
      "review_reasons": []
    },
    {
      "key": "el-sslg-2026-005-elections",
      "title": "Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections",
      "note_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Excuse Letter EL-SSLG-2026-005 - SSLG Grade 7 Representative Elections.md",
      "record_type": "excuse-letter",
      "record_id": "EL_SSLG_2026_005",
      "date": "2026-06-23",
      "event_date": "2026-06-25",
      "school_year": "2026-2027",
      "status": "needs-review",
      "activity": "grade7-representative-election-2026",
      "collection": "activities",
      "summary": "Letter of 23 June 2026 excusing SSLG officers from classes on 25 June 2026 from 7:00 A.M. to 5:00 P.M. for the SSLG Grade 7 Representative Elections.",
      "key_details": [
        "Same routing as EL-SSLG-2026-004: prepared by the SSLG Secretary and noted by the SSLG Adviser."
      ],
      "source_keys": [
        "el_sslg_2026_005-(1).docx"
      ],
      "related": [
        "el-sslg-2026-005-drill",
        "acr-sslg-2026-002"
      ],
      "review_reasons": [
        "Two different letters dated 23 June 2026 both carry the number EL_SSLG_2026_005: one for the earthquake drill and one for the Grade 7 Representative Elections."
      ]
    },
    {
      "key": "el-sslg-2026-010",
      "title": "Excuse Letter EL-SSLG-2026-010 - Municipal Short Film Festival",
      "note_path": "02 Activities/Municipal Short Film Festival 2026/Notes/Excuse Letter EL-SSLG-2026-010 - Municipal Short Film Festival.md",
      "record_type": "excuse-letter",
      "record_id": "EL_SSLG_2026_010",
      "date": "2026-07-13",
      "event_date": "2026-07-13",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "short-film-festival-2026",
      "collection": "activities",
      "summary": "Letter of 13 July 2026 excusing SSLG officers from classes on 13 July 2026 from 1:00 P.M. to 5:00 P.M. for the Municipal Short Film Festival short-film shooting.",
      "key_details": [
        "Organised by the Concepcion Local Government Unit Social Welfare office.",
        "Participation enables the school to take part in the short film shooting."
      ],
      "source_keys": [
        "el_sslg_2026_010.docx"
      ],
      "related": [],
      "review_reasons": []
    },
    {
      "key": "nom-0516-sslg-nom",
      "title": "Notice of Meeting - Cluster IV Leadership Training Camp and Organizational Alignment (16 May 2026)",
      "note_path": "02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Notes/Notice of Meeting - Cluster IV Leadership Training Camp and Organizational Alignment (16 May 2026).md",
      "record_type": "meeting-notice",
      "record_id": null,
      "date": "2026-05-14",
      "event_date": "2026-05-16",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "cluster-iv-training-camp-2026",
      "collection": "activities",
      "summary": "Notice dated 14 May 2026 convening all SSLG officers on 16 May 2026, 8:30 A.M. at the SSLG Office for the same Cluster IV training camp and organizational alignment agenda.",
      "key_details": [
        "Agenda mirrors NOM-SSLG-2026-001 but for a 16 May session.",
        "Names the contact as Ms. Micaella Sabelle R. Monloy, Secretariat Committee Chairperson."
      ],
      "source_keys": [
        "05-16-26-sslg-notice-of-meeting.docx"
      ],
      "related": [
        "nom-sslg-2026-001"
      ],
      "review_reasons": []
    },
    {
      "key": "nom-sslg-2026-001",
      "title": "Notice of Meeting NOM-SSLG-2026-001 - Cluster IV Leadership Training Camp Preparation",
      "note_path": "02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Notes/Notice of Meeting NOM-SSLG-2026-001 - Cluster IV Leadership Training Camp Preparation.md",
      "record_type": "meeting-notice",
      "record_id": "NOM_SSLG_2026_001",
      "date": "2026-05-14",
      "event_date": "2026-05-15",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "cluster-iv-training-camp-2026",
      "collection": "activities",
      "summary": "Notice dated 14 May 2026 convening all SSLG officers on 15 May 2026, 8:30 A.M. at the SSLG Office for Cluster IV Federation Leadership Training Camp preparation and organizational alignment.",
      "key_details": [
        "Agenda: preparation for the Cluster IV SSLG Federation Leadership Training Camp; alignment on organizational expectations and officer conduct; other concerns.",
        "Attendance stated as strictly mandatory.",
        "Signed under Hon. Rhian Jade L. Castro, LGCC Chairperson and SSLG President."
      ],
      "source_keys": [
        "nom_sslg_2026_001.docx"
      ],
      "related": [
        "nom-0516-sslg-nom",
        "om-sslg-2026-001-may25"
      ],
      "review_reasons": []
    },
    {
      "key": "nom-sslg-2026-003-jun06",
      "title": "Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela Post-Evaluation and SSLG GPOA",
      "note_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela Post-Evaluation and SSLG GPOA.md",
      "record_type": "meeting-notice",
      "record_id": "NOM_SSLG_2026_003",
      "date": "2026-06-06",
      "event_date": "2026-06-07",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "gpoa-crafting-2026",
      "collection": "activities",
      "summary": "Notice dated 6 June 2026 convening an online meeting on 7 June 2026, 3:00 P.M. via Google Meet for the Brigada Eskwela 2026 post-evaluation and discussion of the SSLG GPOA.",
      "key_details": [
        "Agenda: Brigada Eskwela 2026 post-evaluation of tasks; discussion on crafting the SSLG GPOA; other concerns.",
        "Three text-identical re-saved copies accompany the notice."
      ],
      "source_keys": [
        "nom_sslg_2026_003.docx"
      ],
      "related": [
        "nom-sslg-2026-003-may29",
        "acr-sslg-2026-005",
        "nom-sslg-2026-004"
      ],
      "review_reasons": []
    },
    {
      "key": "nom-sslg-2026-003-may29",
      "title": "Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela 2026 and LGCC Standing Committees",
      "note_path": "02 Activities/Brigada Eskwela 2026/Notes/Notice of Meeting NOM-SSLG-2026-003 - Brigada Eskwela 2026 and LGCC Standing Committees.md",
      "record_type": "meeting-notice",
      "record_id": "NOM_SSLG_2026_003",
      "date": "2026-05-29",
      "event_date": "2026-05-31",
      "school_year": "2026-2027",
      "status": "final",
      "activity": "brigada-eskwela-2026",
      "collection": "activities",
      "summary": "Notice dated 29 May 2026 convening an online meeting on 31 May 2026, 4:00 P.M. via Google Meet for Brigada Eskwela 2026 kick-off preparation and the LGCC Standing Committees and composition.",
      "key_details": [
        "Agenda: preparation for the Brigada Eskwela 2026 kick-off; introduction and discussion of LGCC Standing Committees and composition; other concerns.",
        "Shares the number NOM_SSLG_2026_003 with the 6 June 2026 notice on a different subject."
      ],
      "source_keys": [
        "nom_sslg_2026_003-(1).docx"
      ],
      "related": [
        "acr-sslg-2026-001",
        "nom-sslg-2026-003-jun06",
        "om-sslg-2026-001-may25"
      ],
      "review_reasons": []
    },
    {
      "key": "nom-sslg-2026-004",
      "title": "Notice of Meeting NOM-SSLG-2026-004 - SSLG General Plan of Action Presentation",
      "note_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Notes/Notice of Meeting NOM-SSLG-2026-004 - SSLG General Plan of Action Presentation.md",
      "record_type": "meeting-notice",
      "record_id": "NOM_SSLG_2026_004",
      "date": "2026-07-02",
      "event_date": "2026-07-03",
      "school_year": "2026-2027",
      "status": "signed",
      "activity": "gpoa-crafting-2026",
      "collection": "activities",
      "summary": "Notice dated 2 July 2026 convening SSLG officers and advisers on 3 July 2026, 10:00 A.M. at the SSLG Office for the presentation of the SSLG GPOA for S.Y. 2026-2027.",
      "key_details": [
        "Attendance stated as strictly mandatory.",
        "A signed PDF export of the notice is present alongside the editable DOCX."
      ],
      "source_keys": [
        "nom_sslg_2026_004.docx",
        "nom_sslg_2026_004.pdf"
      ],
      "related": [
        "acr-sslg-2026-005",
        "nom-sslg-2026-003-jun06"
      ],
      "review_reasons": []
    },
    {
      "key": "om-cfsslg-2026-003",
      "title": "Cluster Federation Memorandum OM-CFSSLG-2026-003 - Nationwide Online Survey on Digital Device Use",
      "note_path": "04 External Memoranda/Cluster Federation Memorandum OM-CFSSLG-2026-003 - Nationwide Online Survey on Digital Device Use.md",
      "record_type": "memorandum",
      "record_id": "OM-CFSSLG-2026-003",
      "date": "2026-09-01",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "reference",
      "activity": "digital-device-survey-2026",
      "collection": "external",
      "summary": "Cluster IV Federation memorandum cascading the Nationwide Online Survey on Digital Device Use in Schools to school SSLG officers and board members, dated 1 September 2026.",
      "key_details": [
        "Addressed to the Vice President, Secretary, Treasurer, Auditor, Public Information Officer, Protocol Officer and all Cluster IV Federation board members.",
        "Follows the Division and National Federation issuances on the same survey."
      ],
      "source_keys": [
        "om-cfsslg-2026-003.docx"
      ],
      "related": [
        "om-dfsslg-2026-010",
        "om-nfsslg-2026-001",
        "om-sslg-2026-002-survey-aug28"
      ],
      "review_reasons": []
    },
    {
      "key": "om-dfsslg-2026-003",
      "title": "Division Memorandum OM-DFSSLG-2026-003 - LGCC Mobilization for Brigada Eskwela 2026",
      "note_path": "04 External Memoranda/Division Memorandum OM-DFSSLG-2026-003 - LGCC Mobilization for Brigada Eskwela 2026.md",
      "record_type": "memorandum",
      "record_id": "OM-DFSSLG-2026-003",
      "date": "2026-05-16",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "reference",
      "activity": "brigada-eskwela-2026",
      "collection": "external",
      "summary": "Division Federation memorandum from President Hon. Faith Naomi R. Manganaan mobilizing Learner Government Coordinating Councils to support the conduct of Brigada Eskwela 2026 under the 2026 Brigada Eskwela Implementing Guidelines.",
      "key_details": [
        "Enjoins learner government participation in cleaning and preparation of school environments.",
        "Covers literacy and reading development support, material support drives and stakeholder engagement.",
        "Includes improvement, repair and maintenance support prior to the opening of classes."
      ],
      "source_keys": [
        "om-dfsslg-2026-003-1.pdf"
      ],
      "related": [
        "acr-sslg-2026-001",
        "om-sslg-2026-001-may25"
      ],
      "review_reasons": []
    },
    {
      "key": "om-dfsslg-2026-007",
      "title": "Division Memorandum OM-DFSSLG-2026-007 - Campus Journalism and SSLG Partnership",
      "note_path": "04 External Memoranda/Division Memorandum OM-DFSSLG-2026-007 - Campus Journalism and SSLG Partnership.md",
      "record_type": "memorandum",
      "record_id": "OM-DFSSLG-2026-007",
      "date": "2026-06-05",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "reference",
      "activity": null,
      "collection": "external",
      "summary": "Division Federation memorandum institutionalizing the partnership between campus journalism and the Supreme Secondary Learner Government through student publication collaboration.",
      "key_details": [
        "Issued 5 June 2026 by Division SSLG Federation President Hon. Faith Naomi R. Manganaan.",
        "Frames the partnership around democratic governance, transparency and youth empowerment in schools."
      ],
      "source_keys": [
        "om-dfsslg-2026-007-1.pdf"
      ],
      "related": [
        "om-sslg-2026-001-may27"
      ],
      "review_reasons": []
    },
    {
      "key": "om-dfsslg-2026-010",
      "title": "Division Memorandum OM-DFSSLG-2026-010 - Nationwide Online Survey on Digital Device Use in Schools",
      "note_path": "04 External Memoranda/Division Memorandum OM-DFSSLG-2026-010 - Nationwide Online Survey on Digital Device Use in Schools.md",
      "record_type": "memorandum",
      "record_id": "OM-DFSSLG-2026-010",
      "date": null,
      "event_date": null,
      "school_year": "2026-2027",
      "status": "reference",
      "activity": "digital-device-survey-2026",
      "collection": "external",
      "summary": "Division Federation memorandum relaying the Nationwide Online Survey on Digital Device Use in Schools to DFSSLG officers, board members and public and private school SSLG presidents.",
      "key_details": [
        "Signed and issued by Hon. Rhian Jade L. Castro, Acting President and Vice President, DFSSLG S.Y. 2026-2027.",
        "The text layer of the export does not render the issuance date, so it is recorded as not stated.",
        "An 18-page export is present together with a byte-identical duplicate."
      ],
      "source_keys": [
        "om-dfsslg-2026-010.pdf"
      ],
      "related": [
        "om-nfsslg-2026-001",
        "om-cfsslg-2026-003",
        "om-sslg-2026-002-survey-aug28"
      ],
      "review_reasons": []
    },
    {
      "key": "om-nfsslg-2026-001",
      "title": "National Federation Memorandum OM-NFSSLG-2026-001 - Nationwide Online Survey on Digital Device Use in Schools",
      "note_path": "04 External Memoranda/National Federation Memorandum OM-NFSSLG-2026-001 - Nationwide Online Survey on Digital Device Use in Schools.md",
      "record_type": "memorandum",
      "record_id": "OM-NFSSLG-2026-001",
      "date": "2026-08-25",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "signed",
      "activity": "digital-device-survey-2026",
      "collection": "external",
      "summary": "Signed National Federation memorandum launching the Nationwide Online Survey on Digital Device Use in Schools, dated 25 August 2026 and cited by the Division, Cluster and school-level issuances.",
      "key_details": [
        "Signed copies are image-only PDFs with no extractable text layer.",
        "The 17-page signed export is retained as the primary source; an 18-page merged bundle and a 3-page compressed extract are kept as variants."
      ],
      "source_keys": [
        "memorandum-om-nfsslg-2026-001_signed-2.pdf"
      ],
      "related": [
        "om-dfsslg-2026-010",
        "om-cfsslg-2026-003",
        "om-sslg-2026-002-survey-aug27"
      ],
      "review_reasons": []
    },
    {
      "key": "om-sslg-2026-001-draft-vp",
      "title": "Draft Memorandum - Standing Committee Distribution (Number and Date Blank)",
      "note_path": "03 Governance/Draft Memorandum - Standing Committee Distribution (Number and Date Blank).md",
      "record_type": "memorandum",
      "record_id": "No. ____, s. 2026",
      "date": null,
      "event_date": null,
      "school_year": "2026-2027",
      "status": "draft",
      "activity": null,
      "collection": "governance",
      "summary": "Undated draft memorandum addressed to the Executive, Secretariat, Finance and Logistics, Publicity and Technical, and Learner Welfare and Policy Management committees, from Vice President Hon. Aaron Y. Hernandez.",
      "key_details": [
        "Committee block matches the structure established by Memorandum No. 001.",
        "Number and date fields remain as placeholders."
      ],
      "source_keys": [
        "om_sslg_2026_001-(5).docx"
      ],
      "related": [
        "om-sslg-2026-001-may27"
      ],
      "review_reasons": [
        "Document number and date are left blank and the memorandum issues from the Vice President rather than the President; no record establishes that it was released."
      ]
    },
    {
      "key": "om-sslg-2026-001-may25",
      "title": "Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (25 May 2026)",
      "note_path": "03 Governance/Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (25 May 2026).md",
      "record_type": "memorandum",
      "record_id": "OM SSLG No. 001, s. 2026",
      "date": "2026-05-25",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "final",
      "activity": null,
      "collection": "governance",
      "summary": "Memorandum mandating the establishment and implementation of Standing Committees in the school SSLG, issued pursuant to Division Memorandum OM-DFSSLG-2026-002.",
      "key_details": [
        "Directed to the Vice President, Secretary, Treasurer, Auditor, Public Information Officer, Protocol Officer and grade-level representatives.",
        "Signed by Hon. Rhian Jade L. Castro as LGCC Chairperson and SSLG President.",
        "Revised under the same number on 27 May 2026."
      ],
      "source_keys": [
        "om_sslg_2026_001.docx",
        "om_sslg_2026_001.pdf"
      ],
      "related": [
        "om-sslg-2026-001-may27",
        "nom-sslg-2026-003-may29",
        "om-dfsslg-2026-003"
      ],
      "review_reasons": []
    },
    {
      "key": "om-sslg-2026-001-may27",
      "title": "Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (27 May 2026)",
      "note_path": "03 Governance/Memorandum No. 001, s. 2026 - Establishment of LGCC Standing Committees (27 May 2026).md",
      "record_type": "memorandum",
      "record_id": "OM SSLG No. 001, s. 2026",
      "date": "2026-05-27",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "final",
      "activity": null,
      "collection": "governance",
      "summary": "Revised issuance of Memorandum No. 001, s. 2026 on the mandatory establishment of SSLG Standing Committees, adding named committee officers to the roster.",
      "key_details": [
        "Dated 27 May 2026 and carries the same number as the 25 May issuance.",
        "Adds named officers including Hon. Chloe Danielle L. David and Hon. Kean Albert J. Pineda.",
        "Exported as a 10-page PDF."
      ],
      "source_keys": [
        "om_sslg_2026_001-(8).docx",
        "om_sslg_2026_001.docx.pdf"
      ],
      "related": [
        "om-sslg-2026-001-may25",
        "om-sslg-ia-2026-001",
        "om-sslg-2026-001-draft-vp"
      ],
      "review_reasons": []
    },
    {
      "key": "om-sslg-2026-002-ecolead",
      "title": "Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD",
      "note_path": "02 Activities/Project ECOLEAD/Notes/Memorandum No. 002, s. 2026 - Implementation of Project ECOLEAD.md",
      "record_type": "memorandum",
      "record_id": "OM SSLG No. 002, s. 2026",
      "date": "2026-07-28",
      "event_date": "2026-07-31",
      "school_year": "2026-2027",
      "status": "needs-review",
      "activity": "project-ecolead-2026",
      "collection": "activities",
      "summary": "Memorandum directing the implementation of Project ECOLEAD, the LGCC school clean-up and environmental stewardship programme, to all club and organization presidents, advisers and SSLG officers.",
      "key_details": [
        "Original 28 July issuance sets implementation from 31 July 2026 with twice-monthly clean-ups.",
        "Assessment uses a prescribed rubric on attendance and participation, with monthly recognition for the highest-performing organization.",
        "September copies restate the schedule and rotation with new start dates."
      ],
      "source_keys": [
        "om_sslg_2026_002.docx"
      ],
      "related": [
        "ap-sslg-2026-002",
        "om-sslg-2026-003-ecolead"
      ],
      "review_reasons": [
        "Four copies all numbered No. 002, s. 2026 carry different issuance dates (28 July, 21 September, 23 September 2026) and different implementation start dates (31 July, 22 September, 30 September 2026); none is signed and no later document resolves which issuance is operative.",
        "Copies differ materially in content: the 28 July DOCX omits the area rotation schedule that later copies include."
      ]
    },
    {
      "key": "om-sslg-2026-002-survey-aug27",
      "title": "Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (27 August 2026)",
      "note_path": "02 Activities/Nationwide Online Survey on Digital Device Use/Notes/Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (27 August 2026).md",
      "record_type": "memorandum",
      "record_id": "OM SSLG No. 002, s. 2026",
      "date": "2026-08-27",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "needs-review",
      "activity": "digital-device-survey-2026",
      "collection": "activities",
      "summary": "School-level memorandum conveying the Nationwide Online Survey on Digital Device Use in Schools, issued by the Vice President under the authority of the SSLG President in line with OM-NFSSLG-2026-001 dated 25 August 2026.",
      "key_details": [
        "Directed to the Secretary, Treasurer, Auditor, Public Information Officer, Protocol Officer and grade-level representatives.",
        "Respondents below 18 years of age are advised to accomplish the Parental Consent Form.",
        "A 2-page PDF export of the 27 August text is present."
      ],
      "source_keys": [
        "om_sslg_2026_002-(3).docx",
        "om_sslg_2026_002.docx.pdf"
      ],
      "related": [
        "om-sslg-2026-002-survey-aug28",
        "om-nfsslg-2026-001",
        "om-sslg-2026-002-ecolead"
      ],
      "review_reasons": [
        "Memorandum No. 002, s. 2026 is used both for the Project ECOLEAD issuance of 28 July 2026 and for this survey issuance; the number alone cannot identify the record.",
        "Six DOCX copies of the 27 August survey differ: some include the annex list and parental-consent paragraph and some do not."
      ]
    },
    {
      "key": "om-sslg-2026-002-survey-aug28",
      "title": "Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (28 August 2026)",
      "note_path": "02 Activities/Nationwide Online Survey on Digital Device Use/Notes/Memorandum No. 002, s. 2026 - Nationwide Online Survey on Digital Device Use in Schools (28 August 2026).md",
      "record_type": "memorandum",
      "record_id": "OM SSLG No. 002, s. 2026",
      "date": "2026-08-28",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "signed",
      "activity": "digital-device-survey-2026",
      "collection": "activities",
      "summary": "Re-issued school memorandum for the Nationwide Online Survey on Digital Device Use in Schools dated 28 August 2026, with adviser review and signature, exported as a 19-page PDF.",
      "key_details": [
        "Reviewed and evaluated by Aaron Khristian T. Banag, SSLG Adviser.",
        "Signed/exported PDF copies are present in the collection.",
        "Condensed 3-page and 2-page PDF renders of the same text also exist."
      ],
      "source_keys": [
        "om_sslg_2026_002-(6).docx",
        "om_sslg_2026_002.pdf"
      ],
      "related": [
        "om-sslg-2026-002-survey-aug27",
        "om-dfsslg-2026-010",
        "om-nfsslg-2026-001"
      ],
      "review_reasons": []
    },
    {
      "key": "om-sslg-2026-003-ecolead",
      "title": "Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD",
      "note_path": "02 Activities/Project ECOLEAD/Notes/Memorandum No. 003, s. 2026 - Revised Implementation of Project ECOLEAD.md",
      "record_type": "memorandum",
      "record_id": "OM SSLG No. 003, s. 2026",
      "date": "2026-08-03",
      "event_date": "2026-08-07",
      "school_year": "2026-2027",
      "status": "needs-review",
      "activity": "project-ecolead-2026",
      "collection": "activities",
      "summary": "Revised memorandum implementing Project ECOLEAD from 7 August 2026, addressed to club and organization presidents, advisers and SSLG officers.",
      "key_details": [
        "Changes the implementation start from 31 July to 7 August 2026.",
        "Retains the rotation schedule and rubric-based assessment."
      ],
      "source_keys": [
        "om_sslg_2026_002-(7).docx"
      ],
      "related": [
        "om-sslg-2026-002-ecolead",
        "ap-sslg-2026-002"
      ],
      "review_reasons": [
        "Two copies dated 3 August 2026 with identical text carry conflicting numbers: OM_SSLG_2026_002 (7).docx reads No. 003 while OM_SSLG_2026_002 (8).docx reads No. 002; no silent winner was chosen.",
        "The file names also disagree with the numbers printed inside the documents."
      ]
    },
    {
      "key": "om-sslg-ia-2026-001",
      "title": "Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy",
      "note_path": "03 Governance/Memorandum OM-SSLG-IA-2026-001 - Governance Output Standardization, Digital Archiving and Monitoring Policy.md",
      "record_type": "governance-policy",
      "record_id": "OM-SSLG-IA-2026-001",
      "date": "2026-06-22",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "final",
      "activity": null,
      "collection": "governance",
      "summary": "Memorandum implementing the SSLG Governance Output Standardization, Digital Archiving and Monitoring Policy and establishing the related monitoring mechanism, issued 22 June 2026 by the SSLG President.",
      "key_details": [
        "Directed to all Standing Committee Chairpersons (Publicity, Finance, Learner Welfare, Secretariat) and executive officers.",
        "States its legal basis as SSLG Memorandum No. 1, Series of 2026 issued 25 May 2026."
      ],
      "source_keys": [
        "sslg_governance_memorandum_om-sslg-ia-2026-001.docx"
      ],
      "related": [
        "om-sslg-2026-001-may25",
        "om-sslg-2026-001-may27"
      ],
      "review_reasons": [
        "The template still carries the placeholder '[School Name]' in the letterhead, so the issuing school was never filled in on this copy."
      ]
    },
    {
      "key": "request-mph-jun25",
      "title": "Request for Use of the Multi-Purpose Hall - Grade 7 Representatives Vote Consolidation",
      "note_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Notes/Request for Use of the Multi-Purpose Hall - Grade 7 Representatives Vote Consolidation.md",
      "record_type": "request",
      "record_id": null,
      "date": "2026-06-25",
      "event_date": null,
      "school_year": "2026-2027",
      "status": "final",
      "activity": "grade7-representative-election-2026",
      "collection": "activities",
      "summary": "Request dated 25 June 2026 to Principal IV Amparo M. Munoz for the use of the Multi-Purpose Hall to facilitate canvassing and consolidation of votes for the Grade 7 Representatives Election.",
      "key_details": [
        "Commits to responsible use and cleanliness of the venue before, during and after the activity.",
        "No document number is stated in the source."
      ],
      "source_keys": [
        "request_for_mph.docx"
      ],
      "related": [
        "acr-sslg-2026-002",
        "el-sslg-2026-005-elections"
      ],
      "review_reasons": []
    }
  ],
  "files": [
    {
      "key": "05-16-26-sslg-notice-of-meeting-(1).docx",
      "original_path": "05-16-26-SSLG-Notice-of-Meeting (1).docx",
      "sha256": "64bfef0089fbdccfe883ab357674b43703279806aef80ee114b0966b8ec4716e",
      "role": "duplicate",
      "record_key": "nom-0516-sslg-nom",
      "archive_reason": "byte-identical duplicate of 05-16-26-SSLG-Notice-of-Meeting.docx",
      "current_path": "90 Archive/Duplicates/05-16-26-SSLG-Notice-of-Meeting (1).docx"
    },
    {
      "key": "05-16-26-sslg-notice-of-meeting.docx",
      "original_path": "05-16-26-SSLG-Notice-of-Meeting.docx",
      "sha256": "64bfef0089fbdccfe883ab357674b43703279806aef80ee114b0966b8ec4716e",
      "role": "primary",
      "record_key": "nom-0516-sslg-nom",
      "archive_reason": "",
      "current_path": "02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Sources/05-16-26-SSLG-Notice-of-Meeting.docx"
    },
    {
      "key": "05-16-26-sslg-notice-of-meeting_vp-(1).docx",
      "original_path": "05-16-26-SSLG-Notice-of-Meeting_VP (1).docx",
      "sha256": "0eccbbb246e06b69ccc12db6c21698063a4ddf9bda04458bcfba8c5de3761cb7",
      "role": "duplicate",
      "record_key": "nom-0516-sslg-nom",
      "archive_reason": "byte-identical duplicate of 05-16-26-SSLG-Notice-of-Meeting_VP.docx",
      "current_path": "90 Archive/Duplicates/05-16-26-SSLG-Notice-of-Meeting_VP (1).docx"
    },
    {
      "key": "05-16-26-sslg-notice-of-meeting_vp.docx",
      "original_path": "05-16-26-SSLG-Notice-of-Meeting_VP.docx",
      "sha256": "0eccbbb246e06b69ccc12db6c21698063a4ddf9bda04458bcfba8c5de3761cb7",
      "role": "revision",
      "record_key": "nom-0516-sslg-nom",
      "archive_reason": "re-saved copy with text identical to 05-16-26-SSLG-Notice-of-Meeting.docx",
      "current_path": "90 Archive/Revisions/05-16-26-SSLG-Notice-of-Meeting_VP.docx"
    },
    {
      "key": "acr_sslg_2026_001.docx",
      "original_path": "ACR_SSLG_2026_001.docx",
      "sha256": "c889f30c733832bfe9ab64a9c8fb202ae9bfc5360e3774ba91d95d335a89a515",
      "role": "primary",
      "record_key": "acr-sslg-2026-001",
      "archive_reason": "",
      "current_path": "02 Activities/Brigada Eskwela 2026/Sources/ACR_SSLG_2026_001.docx"
    },
    {
      "key": "acr_sslg_2026_002.docx",
      "original_path": "ACR_SSLG_2026_002.docx",
      "sha256": "66fdf704c05f1a80760e2189399c81f7a5b152053e40cae4b732ffb8b84dc85b",
      "role": "primary",
      "record_key": "acr-sslg-2026-002",
      "archive_reason": "",
      "current_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Sources/ACR_SSLG_2026_002.docx"
    },
    {
      "key": "acr_sslg_2026_003.docx",
      "original_path": "ACR_SSLG_2026_003.docx",
      "sha256": "d3379c32f4bcc4967875f4b3c40f9e649daaa8271709571778bf596fe67449cb",
      "role": "primary",
      "record_key": "acr-sslg-2026-003",
      "archive_reason": "",
      "current_path": "02 Activities/Club Fair 2026/Sources/ACR_SSLG_2026_003.docx"
    },
    {
      "key": "acr_sslg_2026_004.docx",
      "original_path": "ACR_SSLG_2026_004.docx",
      "sha256": "9006514b5f17e43cb756067be8d4c8e007361e604385d3480d19f3c321a444b5",
      "role": "primary",
      "record_key": "acr-sslg-2026-004",
      "archive_reason": "",
      "current_path": "02 Activities/Election of Registered School Clubs and Organizations 2026/Sources/ACR_SSLG_2026_004.docx"
    },
    {
      "key": "acr_sslg_2026_005.docx",
      "original_path": "ACR_SSLG_2026_005.docx",
      "sha256": "87bd134d6a3f191fb10069c0eb2fe5f030aa07a54aedd709de704da8ab2eddb1",
      "role": "primary",
      "record_key": "acr-sslg-2026-005",
      "archive_reason": "",
      "current_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Sources/ACR_SSLG_2026_005.docx"
    },
    {
      "key": "acr_sslg_2026_006.docx",
      "original_path": "ACR_SSLG_2026_006.docx",
      "sha256": "848895b88a9c4470ec4a146e928f1ac07d39350b44b19b96806d138a55232663",
      "role": "primary",
      "record_key": "acr-sslg-2026-006",
      "archive_reason": "",
      "current_path": "02 Activities/Onto the Next - Leaders Induction 2026/Sources/ACR_SSLG_2026_006.docx"
    },
    {
      "key": "ap_sslg_2026_001-(1).docx",
      "original_path": "AP_SSLG_2026_001 (1).docx",
      "sha256": "f202c20f39cfd13291627898c5d55ab4a4bdbbda5bb0bd49fe07924067fd9d4d",
      "role": "revision",
      "record_key": "ap-sslg-2026-001",
      "archive_reason": "variant draft that adds the ASSH Club to one committee assignment line",
      "current_path": "90 Archive/Revisions/AP_SSLG_2026_001 (1).docx"
    },
    {
      "key": "ap_sslg_2026_001.docx",
      "original_path": "AP_SSLG_2026_001.docx",
      "sha256": "eab63947f6b3df809d0bb9c003bebd640296472e1702fe4b5b43102cae0b3958",
      "role": "primary",
      "record_key": "ap-sslg-2026-001",
      "archive_reason": "",
      "current_path": "02 Activities/Onto the Next - Leaders Induction 2026/Sources/AP_SSLG_2026_001.docx"
    },
    {
      "key": "ap_sslg_2026_002.docx",
      "original_path": "AP_SSLG_2026_002.docx",
      "sha256": "7ff1b1e256de16d2a0c5a1bd7b4ed45e3df39535927418b480cb4ff32d154e09",
      "role": "primary",
      "record_key": "ap-sslg-2026-002",
      "archive_reason": "",
      "current_path": "02 Activities/Project ECOLEAD/Sources/AP_SSLG_2026_002.docx"
    },
    {
      "key": "ap_sslg_2026_003.docx",
      "original_path": "AP_SSLG_2026_003.docx",
      "sha256": "45920c44623ee6fc1adf80c689b616bfb6b1cfc42b4f4d78f9bd83c0e9a42fd2",
      "role": "primary",
      "record_key": "ap-sslg-2026-003",
      "archive_reason": "",
      "current_path": "02 Activities/Project TINIG/Sources/AP_SSLG_2026_003.docx"
    },
    {
      "key": "ap_sslg_2026_004.docx",
      "original_path": "AP_SSLG_2026_004.docx",
      "sha256": "93582a729dc11f3a60231370b4f740a62bb3162c70a7534c0734c8e046d9b4e6",
      "role": "primary",
      "record_key": "ap-sslg-2026-004",
      "archive_reason": "",
      "current_path": "02 Activities/Project LIWANAG/Sources/AP_SSLG_2026_004.docx"
    },
    {
      "key": "ap_sslg_2026_005-(2).docx",
      "original_path": "AP_SSLG_2026_005 (2).docx",
      "sha256": "19a3ff8b4840a139d9cf15260862a94a8d6ffab8eb5a3cd5aafe040d76bd4bfd",
      "role": "primary",
      "record_key": "ap-sslg-2026-005",
      "archive_reason": "",
      "current_path": "02 Activities/Foundation Day 2026/Sources/AP_SSLG_2026_005 (2).docx"
    },
    {
      "key": "ap_sslg_2026_006-(3).docx",
      "original_path": "AP_SSLG_2026_006 (3).docx",
      "sha256": "84919dc1f83194cec1ff4f81776e643d8fe3d6cd1f136299bdc695ed3238f8ec",
      "role": "revision",
      "record_key": "ap-sslg-2026-006",
      "archive_reason": "states a 5 October 2026 celebration date against 2 October 2026 in the revised copies",
      "current_path": "90 Archive/Revisions/AP_SSLG_2026_006 (3).docx"
    },
    {
      "key": "ap_sslg_2026_006_revised-(1).docx",
      "original_path": "AP_SSLG_2026_006_revised (1).docx",
      "sha256": "8eeb2fd8b0cb0c077da5ed14e95600ac142a577d92f0058d1f3c8175db61aabc",
      "role": "duplicate",
      "record_key": "ap-sslg-2026-006",
      "archive_reason": "byte-identical duplicate of AP_SSLG_2026_006_revised.docx",
      "current_path": "90 Archive/Duplicates/AP_SSLG_2026_006_revised (1).docx"
    },
    {
      "key": "ap_sslg_2026_006_revised-(2).docx",
      "original_path": "AP_SSLG_2026_006_revised (2).docx",
      "sha256": "8eeb2fd8b0cb0c077da5ed14e95600ac142a577d92f0058d1f3c8175db61aabc",
      "role": "duplicate",
      "record_key": "ap-sslg-2026-006",
      "archive_reason": "byte-identical duplicate of AP_SSLG_2026_006_revised.docx",
      "current_path": "90 Archive/Duplicates/AP_SSLG_2026_006_revised (2).docx"
    },
    {
      "key": "ap_sslg_2026_006_revised.docx",
      "original_path": "AP_SSLG_2026_006_revised.docx",
      "sha256": "8eeb2fd8b0cb0c077da5ed14e95600ac142a577d92f0058d1f3c8175db61aabc",
      "role": "primary",
      "record_key": "ap-sslg-2026-006",
      "archive_reason": "",
      "current_path": "02 Activities/World Teachers Day 2026/Sources/AP_SSLG_2026_006_revised.docx"
    },
    {
      "key": "ap_sslg_2026_007-(1).docx",
      "original_path": "AP_SSLG_2026_007 (1).docx",
      "sha256": "53c8add2ae9442fdf1fc860322b0a413ec530b8344a2023234747ab8d624d55f",
      "role": "duplicate",
      "record_key": "ap-sslg-2026-007",
      "archive_reason": "byte-identical duplicate of AP_SSLG_2026_007.docx",
      "current_path": "90 Archive/Duplicates/AP_SSLG_2026_007 (1).docx"
    },
    {
      "key": "ap_sslg_2026_007-(2).docx",
      "original_path": "AP_SSLG_2026_007 (2).docx",
      "sha256": "53c8add2ae9442fdf1fc860322b0a413ec530b8344a2023234747ab8d624d55f",
      "role": "duplicate",
      "record_key": "ap-sslg-2026-007",
      "archive_reason": "byte-identical duplicate of AP_SSLG_2026_007.docx",
      "current_path": "90 Archive/Duplicates/AP_SSLG_2026_007 (2).docx"
    },
    {
      "key": "ap_sslg_2026_007.docx",
      "original_path": "AP_SSLG_2026_007.docx",
      "sha256": "53c8add2ae9442fdf1fc860322b0a413ec530b8344a2023234747ab8d624d55f",
      "role": "revision",
      "record_key": "ap-sslg-2026-007",
      "archive_reason": "base proposal text without the Annex D programme additions",
      "current_path": "90 Archive/Revisions/AP_SSLG_2026_007.docx"
    },
    {
      "key": "ap_sslg_2026_007_annexd.docx",
      "original_path": "AP_SSLG_2026_007_AnnexD.docx",
      "sha256": "14fad84c847e8f8b0cddb01da1cd9a974fbadd876c5e2107c437b935059adf47",
      "role": "revision",
      "record_key": "ap-sslg-2026-007",
      "archive_reason": "Annex D division submission version superseded by AP_SSLG_2026_007_AnnexD_proofread.docx",
      "current_path": "90 Archive/Revisions/AP_SSLG_2026_007_AnnexD.docx"
    },
    {
      "key": "ap_sslg_2026_007_annexd.pdf",
      "original_path": "AP_SSLG_2026_007_AnnexD.pdf",
      "sha256": "dcfc5bc611ef848517d6e6c68b0d321cfe02d0b57d4e722557bfee8c0169ff04",
      "role": "alternative-format",
      "record_key": "ap-sslg-2026-007",
      "archive_reason": "",
      "current_path": "02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD.pdf"
    },
    {
      "key": "ap_sslg_2026_007_annexd_proofread.docx",
      "original_path": "AP_SSLG_2026_007_AnnexD_proofread.docx",
      "sha256": "91da5eb08088b5e8c01cb47576dcd3d2d4c506e7c30d1178189352d7f313d6d8",
      "role": "primary",
      "record_key": "ap-sslg-2026-007",
      "archive_reason": "",
      "current_path": "02 Activities/National Students Day 2026/Sources/AP_SSLG_2026_007_AnnexD_proofread.docx"
    },
    {
      "key": "el_sslg_2026_004.docx",
      "original_path": "EL_SSLG_2026_004.docx",
      "sha256": "48b1e0c690c83b6eec9cb32cf52f16637755682cc084c672555369d34bdc3573",
      "role": "primary",
      "record_key": "el-sslg-2026-004",
      "archive_reason": "",
      "current_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Sources/EL_SSLG_2026_004.docx"
    },
    {
      "key": "el_sslg_2026_0041.docx",
      "original_path": "EL_SSLG_2026_0041.docx",
      "sha256": "d117344fc902f3b482fe77958c0beff6fc061da545de98d134e5bb3405ae5f13",
      "role": "revision",
      "record_key": "el-sslg-2026-004",
      "archive_reason": "filename variant EL_SSLG_2026_0041 with text identical to EL_SSLG_2026_004.docx",
      "current_path": "90 Archive/Revisions/EL_SSLG_2026_0041.docx"
    },
    {
      "key": "el_sslg_2026_005-(1).docx",
      "original_path": "EL_SSLG_2026_005 (1).docx",
      "sha256": "205ef8f3e323c4af611086d31dd6db71c73a30d6cfb0e043dd1ac9885d588a7b",
      "role": "primary",
      "record_key": "el-sslg-2026-005-elections",
      "archive_reason": "",
      "current_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Sources/EL_SSLG_2026_005 (1).docx"
    },
    {
      "key": "el_sslg_2026_005.docx",
      "original_path": "EL_SSLG_2026_005.docx",
      "sha256": "3ab22b390604212dd08532751b09c39642f02ba0c9e926432f38d660484799cd",
      "role": "primary",
      "record_key": "el-sslg-2026-005-drill",
      "archive_reason": "",
      "current_path": "02 Activities/Earthquake Drill 2026/Sources/EL_SSLG_2026_005.docx"
    },
    {
      "key": "el_sslg_2026_010-(1).docx",
      "original_path": "EL_SSLG_2026_010 (1).docx",
      "sha256": "e87ebf1a362f758968d210e0e6664004be5366fc9e14d7747b17b663c00b365a",
      "role": "duplicate",
      "record_key": "el-sslg-2026-010",
      "archive_reason": "byte-identical duplicate of EL_SSLG_2026_010.docx",
      "current_path": "90 Archive/Duplicates/EL_SSLG_2026_010 (1).docx"
    },
    {
      "key": "el_sslg_2026_010.docx",
      "original_path": "EL_SSLG_2026_010.docx",
      "sha256": "e87ebf1a362f758968d210e0e6664004be5366fc9e14d7747b17b663c00b365a",
      "role": "primary",
      "record_key": "el-sslg-2026-010",
      "archive_reason": "",
      "current_path": "02 Activities/Municipal Short Film Festival 2026/Sources/EL_SSLG_2026_010.docx"
    },
    {
      "key": "memorandum-om-nfsslg-2026-001_signed-2-merged.pdf",
      "original_path": "Memorandum-OM-NFSSLG-2026-001_signed-2-merged.pdf",
      "sha256": "377ae136590eb8242d1a2b5e335029ab7d7c14246a16cac96f007e3ac6b6c8b3",
      "role": "revision",
      "record_key": "om-nfsslg-2026-001",
      "archive_reason": "18-page bundle that appends the school-level survey memorandum to the signed national memorandum",
      "current_path": "90 Archive/Revisions/Memorandum-OM-NFSSLG-2026-001_signed-2-merged.pdf"
    },
    {
      "key": "memorandum-om-nfsslg-2026-001_signed-2-pages-deleted-compressed.pdf",
      "original_path": "Memorandum-OM-NFSSLG-2026-001_signed-2-pages-deleted-compressed.pdf",
      "sha256": "28cfc427e5c0c24dcd5badcfba33d38b7b21c6ea65d3ca9cb1f008d4cc82d0d1",
      "role": "revision",
      "record_key": "om-nfsslg-2026-001",
      "archive_reason": "3-page compressed extract of the signed memorandum, not the complete document",
      "current_path": "90 Archive/Revisions/Memorandum-OM-NFSSLG-2026-001_signed-2-pages-deleted-compressed.pdf"
    },
    {
      "key": "memorandum-om-nfsslg-2026-001_signed-2.pdf",
      "original_path": "Memorandum-OM-NFSSLG-2026-001_signed-2.pdf",
      "sha256": "2d5c2020ba7f643a57dcb7b7b90326d83d0e418fa413255123db98c5feba40e7",
      "role": "primary",
      "record_key": "om-nfsslg-2026-001",
      "archive_reason": "",
      "current_path": "04 External Memoranda/Sources/Memorandum-OM-NFSSLG-2026-001_signed-2.pdf"
    },
    {
      "key": "nom_sslg_2026_001.docx",
      "original_path": "NOM_SSLG_2026_001.docx",
      "sha256": "89f389ba032c51516e81cc595e2f3efc7cc4e5141e2ee5a0b0150cb2b9c1f9f0",
      "role": "primary",
      "record_key": "nom-sslg-2026-001",
      "archive_reason": "",
      "current_path": "02 Activities/Cluster IV SSLG Federation Leadership Training Camp/Sources/NOM_SSLG_2026_001.docx"
    },
    {
      "key": "nom_sslg_2026_003-(1).docx",
      "original_path": "NOM_SSLG_2026_003 (1).docx",
      "sha256": "e287b200e74e8d803d4e28c8e6154d09d773c107ecf530cc7379c979cc42a6aa",
      "role": "primary",
      "record_key": "nom-sslg-2026-003-may29",
      "archive_reason": "",
      "current_path": "02 Activities/Brigada Eskwela 2026/Sources/NOM_SSLG_2026_003 (1).docx"
    },
    {
      "key": "nom_sslg_2026_003-(2).docx",
      "original_path": "NOM_SSLG_2026_003 (2).docx",
      "sha256": "f7c8bca3fc9be7d292f42d4808273c0ff2efb0b18ecd5c291a15453fd42af1bb",
      "role": "revision",
      "record_key": "nom-sslg-2026-003-jun06",
      "archive_reason": "re-saved copy with text identical to NOM_SSLG_2026_003.docx",
      "current_path": "90 Archive/Revisions/NOM_SSLG_2026_003 (2).docx"
    },
    {
      "key": "nom_sslg_2026_003-(3).docx",
      "original_path": "NOM_SSLG_2026_003 (3).docx",
      "sha256": "76c9af4e3f14ffd334d15eb291d350634ed078250e229160f42cc34efdb5021b",
      "role": "duplicate",
      "record_key": "nom-sslg-2026-003-jun06",
      "archive_reason": "byte-identical duplicate of NOM_SSLG_2026_003.docx",
      "current_path": "90 Archive/Duplicates/NOM_SSLG_2026_003 (3).docx"
    },
    {
      "key": "nom_sslg_2026_003-(4).docx",
      "original_path": "NOM_SSLG_2026_003 (4).docx",
      "sha256": "7f69e2e854857dc04f0ac8d55a24e19b3e469ef2197be513b6e366cacd07ea7a",
      "role": "revision",
      "record_key": "nom-sslg-2026-003-jun06",
      "archive_reason": "re-saved copy with text identical to NOM_SSLG_2026_003.docx",
      "current_path": "90 Archive/Revisions/NOM_SSLG_2026_003 (4).docx"
    },
    {
      "key": "nom_sslg_2026_003.docx",
      "original_path": "NOM_SSLG_2026_003.docx",
      "sha256": "76c9af4e3f14ffd334d15eb291d350634ed078250e229160f42cc34efdb5021b",
      "role": "primary",
      "record_key": "nom-sslg-2026-003-jun06",
      "archive_reason": "",
      "current_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Sources/NOM_SSLG_2026_003.docx"
    },
    {
      "key": "nom_sslg_2026_004.docx",
      "original_path": "NOM_SSLG_2026_004.docx",
      "sha256": "63b8f046226b990aedea4964cacfa8600eee241e36814aaea88c976eee36baf2",
      "role": "primary",
      "record_key": "nom-sslg-2026-004",
      "archive_reason": "",
      "current_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Sources/NOM_SSLG_2026_004.docx"
    },
    {
      "key": "nom_sslg_2026_004.pdf",
      "original_path": "NOM_SSLG_2026_004.pdf",
      "sha256": "3ed1e8545239407648870e4eb2e83964a2d282e06ca43f10d2571866398338b1",
      "role": "alternative-format",
      "record_key": "nom-sslg-2026-004",
      "archive_reason": "",
      "current_path": "02 Activities/Crafting of the SSLG General Plan of Action 2026/Sources/NOM_SSLG_2026_004.pdf"
    },
    {
      "key": "om-cfsslg-2026-003.docx",
      "original_path": "OM-CFSSLG-2026-003.docx",
      "sha256": "9d84777ab2ce5c48aba6da97c17df2973daff47f7609cf13db17ec242f8b7a88",
      "role": "primary",
      "record_key": "om-cfsslg-2026-003",
      "archive_reason": "",
      "current_path": "04 External Memoranda/Sources/OM-CFSSLG-2026-003.docx"
    },
    {
      "key": "om-dfsslg-2026-003-1.pdf",
      "original_path": "OM-DFSSLG-2026-003-1.pdf",
      "sha256": "a0988be92503b4009941650d46a514f600b197a1e851366e83896f7075f3eb74",
      "role": "primary",
      "record_key": "om-dfsslg-2026-003",
      "archive_reason": "",
      "current_path": "04 External Memoranda/Sources/OM-DFSSLG-2026-003-1.pdf"
    },
    {
      "key": "om-dfsslg-2026-007-1.pdf",
      "original_path": "OM-DFSSLG-2026-007-1.pdf",
      "sha256": "3d4fb9cce15069bf6cc4c06ce81bb1e6ebf25378dc02814ac3acbdbd01c37234",
      "role": "primary",
      "record_key": "om-dfsslg-2026-007",
      "archive_reason": "",
      "current_path": "04 External Memoranda/Sources/OM-DFSSLG-2026-007-1.pdf"
    },
    {
      "key": "om-dfsslg-2026-010-(1).pdf",
      "original_path": "OM-DFSSLG-2026-010 (1).pdf",
      "sha256": "d3513e1351cb0091f52da9faa77263ce0638356428b811248383b83bead86af7",
      "role": "duplicate",
      "record_key": "om-dfsslg-2026-010",
      "archive_reason": "byte-identical duplicate of OM-DFSSLG-2026-010.pdf",
      "current_path": "90 Archive/Duplicates/OM-DFSSLG-2026-010 (1).pdf"
    },
    {
      "key": "om-dfsslg-2026-010.pdf",
      "original_path": "OM-DFSSLG-2026-010.pdf",
      "sha256": "d3513e1351cb0091f52da9faa77263ce0638356428b811248383b83bead86af7",
      "role": "primary",
      "record_key": "om-dfsslg-2026-010",
      "archive_reason": "",
      "current_path": "04 External Memoranda/Sources/OM-DFSSLG-2026-010.pdf"
    },
    {
      "key": "request_for_mph.docx",
      "original_path": "REQUEST_FOR_MPH.docx",
      "sha256": "64aecb44401b36b7a1210a7eb1c3d2627d48ea6d9bdcc7e673bead78064bda8c",
      "role": "primary",
      "record_key": "request-mph-jun25",
      "archive_reason": "",
      "current_path": "02 Activities/SSLG Grade 7 Representative Elections 2026/Sources/REQUEST_FOR_MPH.docx"
    },
    {
      "key": "sslg_governance_memorandum_om-sslg-ia-2026-001.docx",
      "original_path": "SSLG_Governance_Memorandum_OM-SSLG-IA-2026-001.docx",
      "sha256": "c0a3e0cf857bdf7d2f3772284a2781079e05bdc7246b7da68b37fe91d9f52a04",
      "role": "primary",
      "record_key": "om-sslg-ia-2026-001",
      "archive_reason": "",
      "current_path": "03 Governance/Sources/SSLG_Governance_Memorandum_OM-SSLG-IA-2026-001.docx"
    },
    {
      "key": "om_sslg_2026_001-(1).docx",
      "original_path": "OM_SSLG_2026_001 (1).docx",
      "sha256": "c276dafc7ffdf22d65456a8a2b9b55d6b66a60e8ad0bc488cf6f1a4a6aa5bb14",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "25 May text with the LGCC and SSLG role lines compressed into one paragraph",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (1).docx"
    },
    {
      "key": "om_sslg_2026_001-(2).docx",
      "original_path": "OM_SSLG_2026_001 (2).docx",
      "sha256": "9b33bc0badecda4be292625a2b1f0cc19cc048dc81905947182f0fe90f860a85",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "25 May issuance retained as a re-saved copy alongside the canonically named file",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (2).docx"
    },
    {
      "key": "om_sslg_2026_001-(3).docx",
      "original_path": "OM_SSLG_2026_001 (3).docx",
      "sha256": "e4f8e1db01c429da7b1a16a3f6f9e0969451e683569a01c101dc4e8d0a6fcaba",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (10).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (3).docx"
    },
    {
      "key": "om_sslg_2026_001-(4).docx",
      "original_path": "OM_SSLG_2026_001 (4).docx",
      "sha256": "0c68b93147d48104d1dcae16dc86c84a0bd2641dbacd5b3c6279689e4d6a200c",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "25 May text with the signature block line-wrapped differently",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (4).docx"
    },
    {
      "key": "om_sslg_2026_001-(5).docx",
      "original_path": "OM_SSLG_2026_001 (5).docx",
      "sha256": "f38903879d3755e6609045987bb441e7c19790a7e11d0e754a6306c32c3c2ae2",
      "role": "primary",
      "record_key": "om-sslg-2026-001-draft-vp",
      "archive_reason": "",
      "current_path": "03 Governance/Sources/OM_SSLG_2026_001 (5).docx"
    },
    {
      "key": "om_sslg_2026_001-(6).docx",
      "original_path": "OM_SSLG_2026_001 (6).docx",
      "sha256": "c276dafc7ffdf22d65456a8a2b9b55d6b66a60e8ad0bc488cf6f1a4a6aa5bb14",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (1).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (6).docx"
    },
    {
      "key": "om_sslg_2026_001-(7).docx",
      "original_path": "OM_SSLG_2026_001 (7).docx",
      "sha256": "0c68b93147d48104d1dcae16dc86c84a0bd2641dbacd5b3c6279689e4d6a200c",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (4).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (7).docx"
    },
    {
      "key": "om_sslg_2026_001-(8).docx",
      "original_path": "OM_SSLG_2026_001 (8).docx",
      "sha256": "b34d4d428c2450122c82337aae27511d172cacc4b665d711d832536f8f4810c6",
      "role": "primary",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "",
      "current_path": "03 Governance/Sources/OM_SSLG_2026_001 (8).docx"
    },
    {
      "key": "om_sslg_2026_001-(9).docx",
      "original_path": "OM_SSLG_2026_001 (9).docx",
      "sha256": "b34d4d428c2450122c82337aae27511d172cacc4b665d711d832536f8f4810c6",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (8).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (9).docx"
    },
    {
      "key": "om_sslg_2026_001-(10).docx",
      "original_path": "OM_SSLG_2026_001 (10).docx",
      "sha256": "e4f8e1db01c429da7b1a16a3f6f9e0969451e683569a01c101dc4e8d0a6fcaba",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (3).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (10).docx"
    },
    {
      "key": "om_sslg_2026_001-(11).docx",
      "original_path": "OM_SSLG_2026_001 (11).docx",
      "sha256": "02ad2975c4fdee96c6664e7b6a81e7d041dfa430e8464df5f2d24ae1025e742a",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "27 May issuance with the named officer roster removed",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (11).docx"
    },
    {
      "key": "om_sslg_2026_001-(12).docx",
      "original_path": "OM_SSLG_2026_001 (12).docx",
      "sha256": "b34d4d428c2450122c82337aae27511d172cacc4b665d711d832536f8f4810c6",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (8).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (12).docx"
    },
    {
      "key": "om_sslg_2026_001-(13).docx",
      "original_path": "OM_SSLG_2026_001 (13).docx",
      "sha256": "e4f8e1db01c429da7b1a16a3f6f9e0969451e683569a01c101dc4e8d0a6fcaba",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (3).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (13).docx"
    },
    {
      "key": "om_sslg_2026_001-(14).docx",
      "original_path": "OM_SSLG_2026_001 (14).docx",
      "sha256": "b34d4d428c2450122c82337aae27511d172cacc4b665d711d832536f8f4810c6",
      "role": "duplicate",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_001 (8).docx",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_001 (14).docx"
    },
    {
      "key": "om_sslg_2026_001-(14)-(1).docx",
      "original_path": "OM_SSLG_2026_001 (14) (1).docx",
      "sha256": "ff35d717f83cfdb460e22427dcffecef3a9be70eff9276465c129d03348b291c",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "re-saved copy with text identical to OM_SSLG_2026_001 (8).docx",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (14) (1).docx"
    },
    {
      "key": "om_sslg_2026_001-(14)-(2).docx",
      "original_path": "OM_SSLG_2026_001 (14) (2).docx",
      "sha256": "92ffb1001c9595bb3b23cc140e0f63a21e6eca3bcb75db97933ab3f422f8b2ab",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "file named OM_SSLG_2026_001 but containing the 27 August survey memorandum numbered No. 002",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (14) (2).docx"
    },
    {
      "key": "om_sslg_2026_001-(15).docx",
      "original_path": "OM_SSLG_2026_001 (15).docx",
      "sha256": "ecec8e751ae3e4c04e2ced7081cf888e332f2eae51f6bcf5aa00bfe14e4088f7",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "re-saved copy with text identical to OM_SSLG_2026_001 (8).docx",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (15).docx"
    },
    {
      "key": "om_sslg_2026_001.docx",
      "original_path": "OM_SSLG_2026_001.docx",
      "sha256": "ee453a9cd9ea0399caab4aeb365183c87f2095a636447d564d7cf7bc20b359af",
      "role": "primary",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "",
      "current_path": "03 Governance/Sources/OM_SSLG_2026_001.docx"
    },
    {
      "key": "om_sslg_2026_001_vp.docx",
      "original_path": "OM_SSLG_2026_001_VP.docx",
      "sha256": "c55fc017146b0bc845621bb6db682d2561ea282d82e995703072ba52c4483f41",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "25 May issuance re-set with school-year-labelled officer titles",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001_VP.docx"
    },
    {
      "key": "om_sslg_2026_002-(1).docx",
      "original_path": "OM_SSLG_2026_002 (1).docx",
      "sha256": "28672b0ce8035603ea6e0c986a6073e4eb07637d1284893a9ed2be8231793342",
      "role": "revision",
      "record_key": "om-sslg-2026-002-ecolead",
      "archive_reason": "28 July No. 002 draft that adds the area rotation schedule absent from the canonically named file",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002 (1).docx"
    },
    {
      "key": "om_sslg_2026_002-(2).docx",
      "original_path": "OM_SSLG_2026_002 (2).docx",
      "sha256": "b3b1ab635e2fed7d023f5036d9a5b46b20fef867a21935f13f889b6d0a5daf71",
      "role": "revision",
      "record_key": "om-sslg-2026-002-ecolead",
      "archive_reason": "28 July No. 002 draft adding the club-by-month implementation matrix",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002 (2).docx"
    },
    {
      "key": "om_sslg_2026_002-(3).docx",
      "original_path": "OM_SSLG_2026_002 (3).docx",
      "sha256": "88e09400efac4a51399aca130a8498e7f19731bd315311e6603bf73739409ab6",
      "role": "primary",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "",
      "current_path": "02 Activities/Nationwide Online Survey on Digital Device Use/Sources/OM_SSLG_2026_002 (3).docx"
    },
    {
      "key": "om_sslg_2026_002-(4).docx",
      "original_path": "OM_SSLG_2026_002 (4).docx",
      "sha256": "8e978adb0a7a06b4a7196093aa04e924e75d165e9d73a625a8812e7887ee1b8d",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "27 August survey text without the annex list and parental-consent paragraph",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002 (4).docx"
    },
    {
      "key": "om_sslg_2026_002-(5).docx",
      "original_path": "OM_SSLG_2026_002 (5).docx",
      "sha256": "a5ebd2f684f2666cb8a74e88d007e8ec19bffe0cc044e87c809e4ef490201e28",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "27 August survey text without the annex list and parental-consent paragraph",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002 (5).docx"
    },
    {
      "key": "om_sslg_2026_002-(6).docx",
      "original_path": "OM_SSLG_2026_002 (6).docx",
      "sha256": "fcad570e283bf8b2ddcb61d9d56f4619127d07c40aac4155b9ee4cece0f0ae9e",
      "role": "primary",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "",
      "current_path": "02 Activities/Nationwide Online Survey on Digital Device Use/Sources/OM_SSLG_2026_002 (6).docx"
    },
    {
      "key": "om_sslg_2026_002-(7).docx",
      "original_path": "OM_SSLG_2026_002 (7).docx",
      "sha256": "d2efc929b7ac157c583f07509bd7cefe6aefc6d380e1bd2bf6f4ecbb0f5fb85d",
      "role": "primary",
      "record_key": "om-sslg-2026-003-ecolead",
      "archive_reason": "",
      "current_path": "02 Activities/Project ECOLEAD/Sources/OM_SSLG_2026_002 (7).docx"
    },
    {
      "key": "om_sslg_2026_002-(8).docx",
      "original_path": "OM_SSLG_2026_002 (8).docx",
      "sha256": "a5a010ec16de7bcc21e40258f81ccb6c18abd27af17bcba9d810b672f10a7b45",
      "role": "revision",
      "record_key": "om-sslg-2026-003-ecolead",
      "archive_reason": "3 August 2026 ECOLEAD copy numbered No. 002 against No. 003 in OM_SSLG_2026_002 (7).docx",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002 (8).docx"
    },
    {
      "key": "om_sslg_2026_002.-(3).docx",
      "original_path": "OM_SSLG_2026_002. (3).docx",
      "sha256": "982697ace613e9b0798d7b72d8b217eb5aec15a640fa4087f9ebf0d62311e9d0",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "re-saved copy with text identical to OM_SSLG_2026_002 (6).docx",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002. (3).docx"
    },
    {
      "key": "om_sslg_2026_002.-(4).docx",
      "original_path": "OM_SSLG_2026_002. (4).docx",
      "sha256": "067be36f01848b17ee457919cd6d086ce92f7960f2083cba8e9313edeb65d0e1",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "27 August survey text without the annex list and parental-consent paragraph",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002. (4).docx"
    },
    {
      "key": "om_sslg_2026_002..docx",
      "original_path": "OM_SSLG_2026_002..docx",
      "sha256": "1de8b97ba990e3562fcccf0ad6062a8f2025f9263dba557ecd97c8a959ca1ad5",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "27 August survey text without the annex list and parental-consent paragraph",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002..docx"
    },
    {
      "key": "om_sslg_2026_002.docx",
      "original_path": "OM_SSLG_2026_002.docx",
      "sha256": "93de7baeb3e6d0ea05cb3efcd1ca44341ed0d293de05ee525f2a26f5aced0a16",
      "role": "primary",
      "record_key": "om-sslg-2026-002-ecolead",
      "archive_reason": "",
      "current_path": "02 Activities/Project ECOLEAD/Sources/OM_SSLG_2026_002.docx"
    },
    {
      "key": "om_sslg_2026_003-(3).docx",
      "original_path": "OM_SSLG_2026_003 (3).docx",
      "sha256": "d53f1fbfeaa7e67ac4c7d5d1e902a2f1465e64426a255cdfc520f4fd731993a1",
      "role": "revision",
      "record_key": "om-sslg-2026-002-ecolead",
      "archive_reason": "No. 002 ECOLEAD text re-issued 23 September 2026 with a 30 September start",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_003 (3).docx"
    },
    {
      "key": "om_sslg_2026_003.docx",
      "original_path": "OM_SSLG_2026_003.docx",
      "sha256": "49a7076fc9e6dbffede6ba7807c8c56ddea0613f3fc127323c9f5fdcdb06a598",
      "role": "revision",
      "record_key": "om-sslg-2026-002-ecolead",
      "archive_reason": "No. 002 ECOLEAD text re-issued 21 September 2026 in a file named OM_SSLG_2026_003",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_003.docx"
    },
    {
      "key": "om_sslg_2026_001-(14).docx.pdf",
      "original_path": "OM_SSLG_2026_001 (14).docx.pdf",
      "sha256": "be93a52dca1919750a8f2c42df5efdf346e741262efe8f70f8b7a7aa7ddc0e8b",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "second 10-page PDF render of the 27 May issuance with identical text to OM_SSLG_2026_001.docx.pdf",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001 (14).docx.pdf"
    },
    {
      "key": "om_sslg_2026_001.docx-(1).pdf",
      "original_path": "OM_SSLG_2026_001.docx (1).pdf",
      "sha256": "8d2bccd2230d7971222a99c89b8ef7479700a32f3bb578a8f45f1023cb490f2b",
      "role": "revision",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "third 10-page PDF render of the 27 May issuance with identical text to OM_SSLG_2026_001.docx.pdf",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_001.docx (1).pdf"
    },
    {
      "key": "om_sslg_2026_001.docx.pdf",
      "original_path": "OM_SSLG_2026_001.docx.pdf",
      "sha256": "5cd2c14c4cdf59817b94f0a2c97ff56935a553c853139551044efa92b672631e",
      "role": "alternative-format",
      "record_key": "om-sslg-2026-001-may27",
      "archive_reason": "",
      "current_path": "03 Governance/Sources/OM_SSLG_2026_001.docx.pdf"
    },
    {
      "key": "om_sslg_2026_001.pdf",
      "original_path": "OM_SSLG_2026_001.pdf",
      "sha256": "2e127ed0f27c22d09f3c6b31a2fdb3d40890f45c5a36b22a968f6db52d458792",
      "role": "alternative-format",
      "record_key": "om-sslg-2026-001-may25",
      "archive_reason": "",
      "current_path": "03 Governance/Sources/OM_SSLG_2026_001.pdf"
    },
    {
      "key": "om_sslg_2026_002-(1).pdf",
      "original_path": "OM_SSLG_2026_002 (1).pdf",
      "sha256": "1c390d3a5d13587ecabe173434078b21bb58cd551801e1d69a27e7462f13a8b1",
      "role": "duplicate",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "byte-identical duplicate of OM_SSLG_2026_002.pdf",
      "current_path": "90 Archive/Duplicates/OM_SSLG_2026_002 (1).pdf"
    },
    {
      "key": "om_sslg_2026_002..docx.pdf",
      "original_path": "OM_SSLG_2026_002..docx.pdf",
      "sha256": "5ece23b199cb1a8681139f8947fed5310605056ffb7457404cfa95d474f843da",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "3-page condensed render of the 28 August survey text",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002..docx.pdf"
    },
    {
      "key": "om_sslg_2026_002.post.docx-merged.pdf",
      "original_path": "OM_SSLG_2026_002.POST.docx-merged.pdf",
      "sha256": "e40e36ffb9a9877af547217340b901bf2140389eee33bea37cd44ffecdd1a513",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "18-page bundle that appends annex material to the 28 August survey text",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002.POST.docx-merged.pdf"
    },
    {
      "key": "om_sslg_2026_002.post.docx.pdf",
      "original_path": "OM_SSLG_2026_002.POST.docx.pdf",
      "sha256": "1190c1acbb714ef25f99c99b4dfcfd091ad9485ca83b7819d42f79aff7030b2f",
      "role": "revision",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "2-page export of the 28 August survey text",
      "current_path": "90 Archive/Revisions/OM_SSLG_2026_002.POST.docx.pdf"
    },
    {
      "key": "om_sslg_2026_002.docx.pdf",
      "original_path": "OM_SSLG_2026_002.docx.pdf",
      "sha256": "d6b81707b25f231c8be2a34675530b37b4a2bfe24fdd1ba573c05cbc91ba602d",
      "role": "alternative-format",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "file name suggests the ECOLEAD memorandum but the content is the 27 August survey memorandum",
      "current_path": "02 Activities/Nationwide Online Survey on Digital Device Use/Sources/OM_SSLG_2026_002.docx.pdf"
    },
    {
      "key": "om_sslg_2026_002.pdf",
      "original_path": "OM_SSLG_2026_002.pdf",
      "sha256": "1c390d3a5d13587ecabe173434078b21bb58cd551801e1d69a27e7462f13a8b1",
      "role": "alternative-format",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "",
      "current_path": "02 Activities/Nationwide Online Survey on Digital Device Use/Sources/OM_SSLG_2026_002.pdf"
    },
    {
      "key": "om-dfsslg-2026-003-1.pdf-staging",
      "original_path": "_DUPLICATES_TO_DELETE/OM-DFSSLG-2026-003-1.pdf",
      "sha256": "a0988be92503b4009941650d46a514f600b197a1e851366e83896f7075f3eb74",
      "role": "staged",
      "record_key": "om-dfsslg-2026-003",
      "archive_reason": "pre-existing staging folder copy, byte-identical to OM-DFSSLG-2026-003-1.pdf",
      "current_path": "90 Archive/Staging/OM-DFSSLG-2026-003-1.pdf"
    },
    {
      "key": "om_sslg_2026_002..docx-staging",
      "original_path": "_DUPLICATES_TO_DELETE/OM_SSLG_2026_002..docx",
      "sha256": "1de8b97ba990e3562fcccf0ad6062a8f2025f9263dba557ecd97c8a959ca1ad5",
      "role": "staged",
      "record_key": "om-sslg-2026-002-survey-aug27",
      "archive_reason": "pre-existing staging folder copy, byte-identical to OM_SSLG_2026_002..docx",
      "current_path": "90 Archive/Staging/OM_SSLG_2026_002..docx"
    },
    {
      "key": "om_sslg_2026_002.-(1).docx",
      "original_path": "_DUPLICATES_TO_DELETE/OM_SSLG_2026_002. (1).docx",
      "sha256": "94b8d65d4a8f681f8c1ed1b3151f093bd30db5b37993804047e915ad41f384a0",
      "role": "staged",
      "record_key": "om-sslg-2026-002-survey-aug28",
      "archive_reason": "pre-existing staging folder copy differing from OM_SSLG_2026_002 (6).docx only in signature-block line breaks",
      "current_path": "90 Archive/Staging/OM_SSLG_2026_002. (1).docx"
    },
    {
      "key": "om_sslg_2026_001-1.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-1.png",
      "sha256": "70582943f07cdd64d0107c2b089bde3eba08d8de73df2eebddd8df0ce5c88ae5",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-1.png"
    },
    {
      "key": "om_sslg_2026_001-2.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-2.png",
      "sha256": "7ed6156f0ad07c2436ade6bea2425427dbd9a845ff3f7090314b02c1778474e7",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-2.png"
    },
    {
      "key": "om_sslg_2026_001-3.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-3.png",
      "sha256": "6373a5f4019dd00122e07cb9e2d1bea8dc9626ce673a6c4d3cc133d257f70bb1",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-3.png"
    },
    {
      "key": "om_sslg_2026_001-4.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-4.png",
      "sha256": "139cf65a50c43d766eb8b2e3d8d0f5a51cd37f26aa98d5b88d6fda5791a43eb7",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-4.png"
    },
    {
      "key": "om_sslg_2026_001-5.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-5.png",
      "sha256": "5a3439dbadd05d11e236babec5f76198b9cb78b2c1bf0dcd242caf8285adc784",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-5.png"
    },
    {
      "key": "om_sslg_2026_001-6.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-6.png",
      "sha256": "43eeb29e107dc9dd28857cda1b279db5f6cbbe78b24b3a42df15dce0e1f5ff88",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-6.png"
    },
    {
      "key": "om_sslg_2026_001-7.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-7.png",
      "sha256": "a105dacfa6408db0fda90f987cccb36365809ed3ef24bb19a662025d69df159d",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-7.png"
    },
    {
      "key": "om_sslg_2026_001-8.png",
      "original_path": "OM_SSLG_2026_001/OM_SSLG_2026_001-8.png",
      "sha256": "295d2666ab217acddb76a314b7d3a5f0ad3dbed7d5f7252d482fab907b5c93af",
      "role": "asset",
      "record_key": null,
      "archive_reason": "",
      "current_path": "80 Assets/OM_SSLG_2026_001-8.png"
    }
  ],
  "protected_files": [
    {
      "path": "Scheduler_v1-main/.gitignore",
      "sha256": "83b9485b1a1834a614064cf5af82070e15d1cae23be6ae1fceae5ee6384b8d8d"
    },
    {
      "path": "Scheduler_v1-main/ASCS_Scheduler.spec",
      "sha256": "24a372aa5bb1614e5fa46e8aef24248d170969474d766115dab88a94bfbef6e4"
    },
    {
      "path": "Scheduler_v1-main/build_exe.py",
      "sha256": "a6216fe38182ae55e18e133a56b5f91b1ade7b84dfb30bef65d770a340708fac"
    },
    {
      "path": "Scheduler_v1-main/create_test_user.py",
      "sha256": "8fc252fe493402798d72b34fa3e7c28d84943aa69451459878d869444aa7220a"
    },
    {
      "path": "Scheduler_v1-main/docker-compose.yml",
      "sha256": "46564e7a82dd226ab563b02ef2cf76953dac99c7d1dfe6b840e5eb0e3c436aef"
    },
    {
      "path": "Scheduler_v1-main/docs/architecture/data_model.md",
      "sha256": "c35d4e599eeeab8eeef133ec581dc5a242dd1c3604a39db3dbe8025c2f7f22a4"
    },
    {
      "path": "Scheduler_v1-main/docs/architecture/module_boundaries.md",
      "sha256": "d2ed602408dfd4930aaba124d3dfcc366c2d06848541c3ee4b81e8832e416bad"
    },
    {
      "path": "Scheduler_v1-main/docs/QUICKSTART.md",
      "sha256": "4acd0dce543724c73c964dc31bf7829f61e45b8c3d55425f7428d386c7a3c496"
    },
    {
      "path": "Scheduler_v1-main/requirements.txt",
      "sha256": "9b291e62fc7521a62972d55e0457fdcc960486e1ff0a8346cad17c9e3b77b816"
    },
    {
      "path": "Scheduler_v1-main/run_app.py",
      "sha256": "4118bedb804dcc62e63eced85f4c4727a5b605533af4ecf572c53f88db74042e"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/alembic.ini",
      "sha256": "143647a5c3505fcdcf2d6709a8d50596af854604e3040581adee1dabd9d7ff33"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/__init__.py",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/__init__.py",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_ai.py",
      "sha256": "8406393e6575a23f304bdd6dca5f42a6bd1e14ec5a89d0a6104f7b870edebafb"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_auth.py",
      "sha256": "73e16de7cd5e7b01dc6cbb74d89cd6855544567a65b0f111069722dca7eeeca2"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_build_jobs.py",
      "sha256": "c1130eca7a066c7db825bce42b4bb2df2cead27d82457ca10a10fc1565d8466f"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_conflict_logs.py",
      "sha256": "37e8b5a1e9b6bf472ac98e3bc776932a902d07df9355daf88b5186282105b6d4"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_conflicts.py",
      "sha256": "15f139701efcc1cf89c951274a2d307a763d91e7e324ed9c6a63e0b480ff0754"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_faculty.py",
      "sha256": "73821d21ef0605e4394cb3ec467a89172ad016df579f46378649983aa4f213c8"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_imports.py",
      "sha256": "3c242f9c8f40a03fa490a87cf76eec5fe949b36587584b99409ab707222ac4a3"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_rooms.py",
      "sha256": "5df115ab9bf2a5fa510d216893e6c893b934566f6564ac30bab44ff034d47574"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_schedule_entries.py",
      "sha256": "98400ba5cdc5e14e70edaabb8dbfa53dde322a095332d6f035777c70f50018a3"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/api/routes_subjects.py",
      "sha256": "9257b6e2c681c9018a94c76be3b3db1cc7677956194894e2af5a941ad21de178"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/core/__init__.py",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/core/auth.py",
      "sha256": "b79052d5a755e99132299c79de28dd27748a0670e4e0866308bad96d20adb495"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/core/security.py",
      "sha256": "b9608f1f5a4b4429f742bc256bc4c8feb9ad00717d7d334a63fe073ecb2f3e43"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/db/__init__.py",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/db/database.py",
      "sha256": "bfcf845c36a968cda410c3c197ab59454d1293a8f5fac8c043b397aa1e7fe7c7"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/db/schema.sql",
      "sha256": "3ddcd71a9303857b4115f4bb753a0f5da3dd2366212f7a008f42af5d84e1f30d"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/main.py",
      "sha256": "4575277b1fc05646c835c0e680640b7b0d186864cdbf89e2f42189b9eaf3e6cc"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/models/__init__.py",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/models/entities.py",
      "sha256": "088c01a68ea7e0ed852022487b160af6d84fc521bc956eacc5a59c0bb96bc8c1"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/__init__.py",
      "sha256": "062dba14701b14f3b3f15b2de67aee74001748784d8aad10d3aec9b33f14af38"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/auth.py",
      "sha256": "4c25a882c8d5af8918af725f4402c8e8a4cde84b12c559ceef03fdbb7b96e409"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/build_jobs.py",
      "sha256": "1107d6257f3da18c68b08ab681100c6107249a3caee6baec0411fa38861a31bf"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/conflict_logs.py",
      "sha256": "9f1ef2739690e74a92fb3b314d048e2d59e5771ab9eb1806ad91e1ab7908e4f8"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/conflicts.py",
      "sha256": "14b0b86434e91e15d59fa9b6fd7c580566299d5cb9ddcda4acc69e434676d8d1"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/faculty.py",
      "sha256": "9ad27af1e00db1cbaf3a4946eac70db609f268a61fd4def63b05cbb4a55f7e59"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/imports.py",
      "sha256": "c86a253b1f2568c5b327197c97fac8b67275925839f2eb09e25061954b9caaab"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/rooms.py",
      "sha256": "02f2d7a58bfa285528b9105156f0f310ff30e18af13efcdaea841a31dc75c479"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/schedule_entries.py",
      "sha256": "eee6fcfc63fc29b3243522aa0553fabb37c8411e534bb1bdb9784e869d846af0"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/schemas/subjects.py",
      "sha256": "fa8f793cf0552a92693f8728e131c6a995db450bebd668174d79b574ceb8adf7"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/services/__init__.py",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/services/build_jobs.py",
      "sha256": "d441faabbf9465beae3af69beabd677d03bb4c47148c4afee5d3de3e9dc52c31"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/services/email_service.py",
      "sha256": "a10e54305badfd3f27120a9ef577f931ac83bafc8c09ebf1d050f053e008b34b"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/app/services/scheduler_core.py",
      "sha256": "76d573370ef57450bf904f6bad15cf1a1fdf64dbd2aa56dea4d612937bee93ca"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/Dockerfile",
      "sha256": "98d645473fc4024db32ba4dcd8bf927b6ca9edc95b2f60961fc2df762f340f0d"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/migrations/env.py",
      "sha256": "819899f17b88981f7d5fc3d2eedb6408211ee713631c5fc14122bdd0ae6e8609"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/migrations/script.py.mako",
      "sha256": "a09e093c12cde90c77be71d3268be31f7b1c32d15c1a4a4e468ffc255a62b0da"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/migrations/versions/0001_initial_schema.py",
      "sha256": "f1ca6d33db6ad8a656311565a667003b6bbd29edc019007daef6cd46d084d290"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/migrations/versions/0002_scheduling_domain.py",
      "sha256": "072df41cea4fe5e4506fef5b50fd0893900635b4399e56ead0bc0373149b75b6"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/README.md",
      "sha256": "d4034e804feeb82648d7bf3b134c45b73d1c26d8f71a529d8b93357d3edeaf11"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/requirements.txt",
      "sha256": "f5f2d38634dfc53c9f0121d0a96c729efbfc375b9d89da52e066d5b96a811b88"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/tests/conftest.py",
      "sha256": "d2a13c3fa3b5e4a177d1b37d98af47da4d24f23862a1c34485cda7a613ed0d09"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/tests/test_auth.py",
      "sha256": "82c7a26a79af2763af256b87cdd3438619f92fc7fd21c23152da73e8ec953ba2"
    },
    {
      "path": "Scheduler_v1-main/saas_backend/tests/test_faculty.py",
      "sha256": "b67daa0c70c06456601c251d1ad05d47d0d0e71e8b377728eb84966f6039c52e"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/design_tokens.json",
      "sha256": "d927d87f471bcad801240437345738d21b33f13272e30131bc8a3ee835451716"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/Dockerfile",
      "sha256": "4ad4edd3b4e721b62f0c25982f310c904732a2a07cf414356da7d19d93c4c4e5"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/components/AppShell.tsx",
      "sha256": "82435a288b8823fcb98b52b0ae6520ab92e6571ed776261cd7516c7b30c3d847"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/components/BuildKpiCards.tsx",
      "sha256": "8391d3243304ef5a3614c93f469020600e8b5ee989e5483703c83d942e5d6aa8"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/components/BuildStatusTimeline.tsx",
      "sha256": "5ec1298fabf1548f62038861c36f505b209ae7307b1bb1dd175b7258dae64105"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/components/ConflictTable.tsx",
      "sha256": "493158f19a3a18a9402c16f2aba718b7126caab772848fd781ffc1cfee07df16"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/components/ThemeProvider.tsx",
      "sha256": "36d2512c42d4293ff33a33f54bb2b5a9d5687eb5018816365c2d5422c0c5e4de"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/components/TimetableGrid.tsx",
      "sha256": "bc3e0b1037e4935d49cbfe7830c3704630fcd430bfb28b45762ad9fd542e82bc"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/useLocalStorage.ts",
      "sha256": "cd4e44cf57c858ad2c502b465f70b7db03d50bb307a6b2f8f04b3d311f49188d"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/hooks/useMediaQuery.ts",
      "sha256": "c22e67c725659399ad8c21eda5266c607b42bbd1beb3f670138b3fd518bcb773"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/lib/api.ts",
      "sha256": "a4b7455abb5c6a54cd05ccd29b53527d516897383b9929695e73135dc725cfce"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/next-env.d.ts",
      "sha256": "6270cb0e77bf8b6add74edb5e90994381850fabaf82f3480e6dd0721eacbd40b"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/package-lock.json",
      "sha256": "3e28c4812d81bbe3bb704dec221a5b1fb058514b10128c52cd940a9e21a156bd"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/package.json",
      "sha256": "db0acae2065effac5a5459439a19b79947c922cb19e466e36bdd8c15e090a552"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/_app.tsx",
      "sha256": "f9780cdd3eb501fffa7bf185c1191b8b3ebf8afa31d28f8b4bb502606fa066b0"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/build.tsx",
      "sha256": "10d8b91bc5ed52f282a2789fe30a0b84c0c0809dc3a47573062093e520e3b318"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/conflicts.tsx",
      "sha256": "cead0958daafbfd6722bd8e57f04fc0fb743f27dddc87d106ffab0288a354f56"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/index.tsx",
      "sha256": "15ce34239551b697a049f080b831286480259ee09ab72deef2e08829333d0298"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/login.tsx",
      "sha256": "fa1746c2767b5d0be513ca7682a0ff1469955955e6966006af75fcc8e8754536"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/manage/faculty.tsx",
      "sha256": "39bf49f66a30554a95a6f0af2317445fd64d0f97e16ec478bbd2b191f1001c29"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/manage/rooms.tsx",
      "sha256": "365a076ead5375d032084367568cb2f34f734b66afc58a5fbd9d4f96f8cc18ab"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/pages/manage/subjects.tsx",
      "sha256": "cef226a8bf1157d4913f8f125d4d9af47763f4fccef00e2f427ac4317688230f"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/SKILL.md",
      "sha256": "e62da806e5c3e3506592781c57b39086701a82f346e6c6c7c3f0ebd8fbeca84a"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/styles/globals.css",
      "sha256": "1a8843fd384d852e6b2e47815efb570a5aad0f3fd4dfc9e4dbe996ea2c0bae04"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/tsconfig.json",
      "sha256": "564aa154c971f75b8f684df850ab2f24336d511baec53cbb4173267561b5d203"
    },
    {
      "path": "Scheduler_v1-main/saas_frontend/ui_sitemap.md",
      "sha256": "c9f51f6e589a42c6c86b02c5b4c91770d84b7838ec68031ab834fb4821cc9b15"
    },
    {
      "path": "Scheduler_v1-main/scratch/apply_jhs_shs.py",
      "sha256": "3a27f5fc117985e26699b3ead3906d60d5e68b277a053f6d4a5d343c97f33be5"
    },
    {
      "path": "Scheduler_v1-main/scratch/apply_phase2.py",
      "sha256": "33c601af05b8bab4480eeeb522d76bd83557bbac41487ed189c84304f4038271"
    },
    {
      "path": "Scheduler_v1-main/scratch/rewrite_app.py",
      "sha256": "4dfd62f83e9c22921883ac1ff6c59611628679bb4da63e405ee2272a30e2e6de"
    },
    {
      "path": "Scheduler_v1-main/Streamlit/.streamlit/config.toml",
      "sha256": "38c362f56eaf8839eafb2329a3e0ff14f6d9cd01bc8f9c4a0c81f178e221d721"
    },
    {
      "path": "Scheduler_v1-main/Streamlit/App.py",
      "sha256": "0c203d5676b0000641c4c6d10906c348c4664208c7175c6b154b4a0089d35808"
    }
  ]
}
