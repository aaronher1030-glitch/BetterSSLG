# SDD ledger — plan: C:/Users/Ma Christine/Downloads/SSLG MEMOS/docs/superpowers/plans/2026-11-24-sslg-qr-attendance.md

## Environment

- Workspace: `C:/Users/Ma Christine/Downloads/SSLG MEMOS`
- Git repository: none (`git rev-parse` returned no output)
- Implementation isolation: new `SSLG Attendance App/` directory; existing vault files remain untouched
- Agent model selection: the Agent tool exposes no model parameter, so every implementer/reviewer inherits the session model
- Review packages: per-task source snapshots plus `diff -ruN -x node_modules`; no commit SHAs exist

## Rulings

- Ruling: Use local file snapshots instead of Git commits/worktrees — the workspace is not a Git repository — cost if wrong: less granular history, but existing files remain untouched and every task still gets an independent diff review.
- Ruling: Keep the SDD ledger and verification artifacts after completion — there is no Git history to preserve the execution record — cost if wrong: one ignored scratch directory remains under `.superpowers/sdd/`.
- Ruling: Use a “modern civic ledger” visual direction with warm paper, navy ink, teal stamps, serif display headings, and sans-serif body text; remove the plan's initial Inter font stack — frontend-design explicitly rejects generic Inter-led aesthetics — cost if wrong: visual refinement may need adjustment after browser review.
- Ruling: Subagents inherit the session model because the Agent schema has no model selector — the SDD model-selection parameter cannot be supplied — cost if wrong: review cost may be higher than a cheaper selectable tier.
- Ruling: Correct Task 1's Manila fixture to `2026-11-23T16:30:00.000Z` → `2026-11-24T00:30:00+08:00` and expect quoted CSV headers — the original fixture did not cross midnight and quoted headers are valid CSV consistent with `toCsv_` — cost if wrong: none; production behavior is unchanged and the tests now match the specified implementation.

## Pre-flight conflict scan

| Tasks | Shared file or interface | What one produces / the other consumes | Finding and ruling |
| --- | --- | --- | --- |
| 1 → 2 | `Core.gs` | Task 1 produces date/name/code/CSV helpers and headers; Task 2 consumes them | Consistent; no ruling needed. |
| 1 → 5 | `Core.gs` | Task 5 preview consumes the same validation and CSV helpers | Consistent; preview must load the real file, not duplicate logic. |
| 2 → 3 | `scan.status`, `scan.record` | Task 2 produces HTTP actions and public Apps Script wrappers; Task 3 consumes both through an adapter | Consistent after adding `SERVER_ACTIONS` mapping; no dotted function names are passed to `google.script.run`. |
| 2 → 4 | `admin.generate`, `admin.list`, `admin.export` | Task 2 produces actions/wrappers; Task 4 consumes them | Consistent. |
| 2 ↔ 5 | API action contract | Task 5 must mirror Task 2 request/response shapes | Consistent; preview integration tests cover parity. |
| 3 ↔ 4 | `Client.html`, `Styles.html` | Task 3 creates shell/student UI; Task 4 extends the same files for office UI | Consistent; no duplicate `<script>` or `<style>` blocks. |
| 3 + 4 → 5 | `Index.html` includes | Task 5 replaces `Styles`, `QRCodeLib`, and `Client` include tokens | Consistent; include names occur exactly once. |
| 1–6 → 7 | Full project | Task 7 runs all tests and browser checks | Consistent; live Google deployment remains pending owner authorization. |
| Task 1 | Own text | Tests reference `Core.gs` before it exists; package test command is cross-platform | Consistent; expected RED is missing module/file, then GREEN after implementation. |
| Task 2 | Own text | Backend tests use an in-memory Sheet mock and dynamic current Manila date | Consistent; mock now provides `getLastColumn`. |
| Task 3 | Own text | Bootstrap references `renderAdminPage_`, which Task 4 defines later | Acceptable staged dependency: Task 3 tests student/static behavior; full admin runtime begins after Task 4. |
| Task 4 | Own text | QR library is vendored from npm and round-trip decoded | Consistent; no runtime CDN. |
| Task 5 | Own text | Preview tests use ephemeral ports and current Manila date | Consistent; generated QR URLs use the fixed preview port but tests submit tokens directly. |
| Task 6 | Own text | Manifest and setup guide are configuration/docs, not behavior | TDD exception applies to configuration; packaging tests verify structure and secret absence. |
| Task 7 | Own text | Browser checks depend on the preview server and Playwright MCP | Consistent; Playwright is available again in the current MCP catalog. |

## Task status

- Task 1: fix round 1/5 (2 plan-fixture issues addressed, 0 open; no commits)
- Task 1: minor (deferred): core tests do not cover every helper branch; carry to final review.
- Task 1: minor (deferred): preview script targets the later Task 5 file; expected staged dependency.
- Task 1: complete (before-task-1..current source snapshot, review clean; TDD chronology confirmed from report RED/GREEN evidence)
- Task 2: complete (before-task-2..current source snapshot, review clean; TDD report accepted, live deployment pending)
- Task 2: minor (deferred): add unmatched-OUT-first regression coverage.
- Task 2: minor (deferred): add direct tests for admin HTTP actions, public wrappers, and doGet.
- Task 2: minor (deferred): freeze the backend test clock to avoid a Manila-midnight flake.
- Task 3: complete (before-task-3..current source snapshot, review clean; TDD report accepted, browser verification pending)
- Task 3: minor (deferred): reconcile `submitScan_` declared interface with its actual scoped arguments.
- Task 3: minor (deferred): add assertive announcement/focus for student submission and status errors.
- Task 4: fix round 1/5 (2 addressed, 0 open; before-task-4-fix-1..current source snapshot)
- Task 4: complete (before-task-4..current source snapshot, review clean after scoped re-review; physical print/camera checks pending Task 7)
- Task 4: minor (deferred): regression tests do not separately cover overlapping date-change list requests or generate-start error clearing; implementation guards both by inspection.
- Task 5: Ruling: The preview must match `Code.gs` token validation, normalized status fields, query normalization, and malformed-JSON error responses even though the plan's preview snippet omitted them — the spec makes API parity binding — cost if wrong: the preview becomes slightly stricter, but it will no longer give false confidence relative to the deployed backend.
- Task 5: fix round 1/5 (3 addressed, 0 Critical/Important open; before-task-5-fix-1..current source snapshot)
- Task 5: minor (deferred): preview `scan.status` also caps tokens at 100 characters while backend status checks presence only; no write side effects.
- Task 5: complete (before-task-5..current source snapshot, review clean after scoped re-review; live browser re-verification remains Task 7)
- Task 6: complete (before-task-6..current source snapshot; independent `npm test` 32/32 PASS; fresh reviewer approved with no findings; no live deployment)
- Task 7: fix round 1/5 (2 review findings addressed, 0 open; print-layout RED/GREEN documented; three session-created scratch PDFs removed)
- Task 7: complete (before-task-7..current source snapshot; local browser verification PASS; independent `npm test` 32/32 PASS; scoped re-review clean; real Apps Script/Sheets smoke test pending owner deployment)
- Task 2: deferred minors resolved by later evidence: unmatched-OUT-first, direct admin HTTP/public-wrapper/doGet regressions, and a fully fixed backend VM clock are now covered.
- Task 5: deferred status-length parity resolved in the final fix wave; status accepts safe 101-character tokens while record rejects them without writes.
- Final whole-app review: completed (whole-app findings addressed; scoped final-fix re-review initially left clock and device-token findings open).
- Final security correction: fix round 1/1 (2 addressed, 0 open; `before-final-security-fix`..current source snapshot; no commits).
- Final security correction: independent `npm test` 51/51 PASS; focused Playwright invalid-token/zero-write/valid-registration smoke PASS; scoped re-review clean with no new Critical/Important breakage.
- Final whole-app review: complete for local implementation; acceptance criterion 8 and real Apps Script/Sheets deployment remain pending owner action. SDD ledger retained because this workspace has no Git history.
- Permanent-pair amendment: Ruling: replace daily regeneration with one immutable date-free IN/OUT pair and no reset option — explicit user approval on 2026-11-25 — cost if wrong: a lost pair requires maintainer intervention, but the requested same-code daily workflow is satisfied.
- Permanent-pair amendment: baseline `before-permanent-pair`; focused RED 63 tests/27 pass/36 fail plus midnight RED; implementation complete; independent `npm test` 64/64 PASS; no commits.
- Permanent-pair amendment: independent review found no High/Medium defects. Low observations ruled non-blocking: removed-error assertions are negative coverage; pristine-Sheet schema initialization writes headers but no attendance/person data.
- Permanent-pair amendment: controller Playwright smoke confirmed identical cards/images across date changes and repeated display, date-free URLs, server-dated registration, success focus, and zero console errors/warnings.
- Permanent-pair amendment: final post-documentation controller `npm test` PASS, 64/64, exit 0; port 4173 has no listener. Operational-doc scan found only intentional permanent-code/historical-verification references.
- Permanent-pair amendment: complete for local implementation; `QR Codes` real-schema inspection, physical phone/camera checks, concurrent live first creation, and later-day live reuse remain pending owner deployment.
- Task 52: complete (specification and verification records propagated; permanent-pair evidence recorded and freshly verified; real deployment remains owner-dependent).
