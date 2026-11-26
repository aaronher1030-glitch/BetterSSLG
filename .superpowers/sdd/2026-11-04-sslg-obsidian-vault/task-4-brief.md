### Task 4: Homepage, Dashboards, Review Queue, and Templates

**Files:**
- Create: `tools/sslg_navigation.py`
- Create: `tools/tests/test_sslg_navigation.py`
- Create through the renderer: `START HERE.md`, `01 Dashboards/*`, `99 Templates/*`, `.obsidian/templates.json`

**Interfaces:**
- Consumes: Task 2 content data and Task 3 note paths.
- Produces: `render_home(data: dict) -> str`, `render_activity_dashboard(data: dict) -> str`, `render_timeline(data: dict) -> str`, `render_review_queue(data: dict) -> str`, `render_document_library() -> str`, `render_record_template() -> str`, `render_activity_template() -> str`, and `generate_navigation(root: Path, data: dict) -> list[Path]`.

- [ ] **Step 1: Write failing navigation tests**

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

- [ ] **Step 2: Run tests and verify the import failure**

Run: `python -m unittest tools.tests.test_sslg_navigation -v`  
Expected: FAIL because `tools.sslg_navigation` does not exist.

- [ ] **Step 3: Implement native Bases and navigation pages**

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

- [ ] **Step 4: Implement reusable templates and no-overwrite output**

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

- [ ] **Step 5: Run tests, generate navigation, and record Checkpoint 4**

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
