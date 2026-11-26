
## Navigation consistency check — 2026-11-04 (read-only, post-rebuild)

Method: parsed YAML frontmatter with python -X utf8 across `02 Activities/**/Notes`, `03 Governance`,
`04 External Memoranda` (record notes) and `02 Activities/<hub>/<hub>.md` (hubs); excluded `99 Templates`,
`Scheduler_v1-main`, `tools`, `docs`, `_DUPLICATES_TO_DELETE`, `90 Archive`. Compared against
`tools/sslg_content.json` (36 records, 16 activities). No files modified.

### 1. needs_review: "yes" counts
- Vault record notes flagged: 10. Vault activity hubs flagged: 13. Total 23.
- Manifest records with non-empty review_reasons or status==needs-review: 10 (ap-sslg-2026-005,
  ap-sslg-2026-006, el-sslg-2026-005-elections, om-nfsslg-2026-001, om-sslg-2026-001-draft-vp,
  om-sslg-2026-002-ecolead, om-sslg-2026-002-survey-aug27, om-sslg-2026-002-survey-aug28,
  om-sslg-2026-003-ecolead, om-sslg-ia-2026-001). Exact path-set equality with vault: yes (0 missing, 0 extra).
- Manifest activities flagged: 13; exact hub-path equality with vault: yes (0 missing, 0 extra).
  Unflagged hubs (3): onto-the-next-2026, gpoa-2026-crafting, sslg-grade-7-representatives-2026.
- Records with status==needs-review: 6; all 6 carry >=1 review_reason (0 without). Pass.
- 99 Templates (2 files): needs_review: "no" on both, correctly excluded.

### 2. 01 Dashboards/Review Queue.md
- Links 23 unique notes: 10 under "Records needing review", 13 under "Activities needing review".
- Linked set == flagged set from (1): yes. Missing: none. Extra: none. Header text "Needs review:
  10 records, 13 activities." matches. aug28 survey entry shown with Status: final plus 2 open questions;
  om-sslg-ia-2026-001 shown Status: final plus placeholder reason; nom-sslg-2026-004 absent.

### 3. 01 Dashboards/SSLG Records.base
- Global filters: file.folder != "Scheduler_v1-main"; file.folder != "99 Templates". Present as intended.
- Views: All records (type=="record"); Proposals (type=="record" + record_type=="proposal");
  Completion reports (record_type=="completion-report"); Memoranda (record_type=="memorandum");
  Needs review (type=="record" + needs_review=="yes"); Activities needing review (type=="activity" +
  needs_review=="yes"). Both review views confirmed to filter on needs_review == "yes".
- Caveat: exact Obsidian Bases semantics (quote/keyword comparison, and whether file.folder excludes only
  the top folder vs nested subfolders of Scheduler_v1-main) could not be verified without opening Obsidian.
  Notes do carry type: record / type: activity and needs_review fields, so the filters bind to real data.

### 4. Dashboards + START HERE link integrity
- Activity Dashboard.md: 19 wikilinks, all 16 activities present, 0 links into Scheduler_v1-main/tools/docs,
  0 unresolved.
- Timeline.md: 92 links (52 unique), all 16 activities present, 0 forbidden, 0 unresolved.
- Document Library.md: by design shows records/hubs via embedded Bases views, not per-activity links;
  0/16 activities named (intended). Its single link ![[01 Dashboards/SSLG Records.base]] resolves to the
  existing .base file. Mentions Scheduler_v1-main only in prose explaining it is a separate application
  excluded from every view.
- START HERE.md: 33 wikilinks, all 16 activities present, 0 unresolved (90 Archive/Archive Index.md and
  90 Archive/File Manifest.json exist). tools/ and docs/ mentioned only in prose stating neither contains
  SSLG records.
- Review Queue.md: 23 links, 0 unresolved, 0 forbidden.
- Total unresolved links across the five files: 0.

### 5. Status-changed records
- nom-sslg-2026-004 (Notice of Meeting, GPOA Presentation): note frontmatter status: final,
  needs_review: "no"; Timeline rows (2026-07-03, 2026-07-02) show final; absent from Review Queue. Correct.
- om-sslg-2026-002-survey-aug28 (Memorandum No. 002, 28 Aug survey): note frontmatter status: final,
  needs_review: "yes"; Timeline row 2026-08-28 shows final; present in Review Queue with 2 open questions.
  Correct (flagged via review_reasons despite final status).
- Manifest statuses agree for both records.

Conclusion: navigation layer is fully consistent with the rebuilt manifest; no mismatches found.
