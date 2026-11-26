# Final Whole-App Fix Wave

This is the single final fix dispatch after broad review. Implement only the concrete findings below. Preserve all approved product decisions and do not add features.

Workspace: `C:/Users/Ma Christine/Downloads/SSLG MEMOS`
App: `SSLG Attendance App/`
Baseline snapshot: `.superpowers/sdd/2026-11-24-sslg-qr-attendance/before-final-fix/`

## 1. Important — formula injection in Sheets and CSV

Required behavior:
- Reject new or returning names whose normalized value begins with `=`, `+`, `-`, or `@` with error code `NAME_INVALID`. Rejection must occur before any People or Attendance write.
- Keep ordinary names, punctuation inside names, and existing normalization/length rules working.
- Harden CSV export for every field, including manually edited legacy rows: if a field begins with `=`, `+`, `-`, `@`, tab, CR, or LF, or has leading spaces followed by one of those formula triggers, prefix the exported value with an apostrophe before normal CSV quoting. Do not change stored values during export.
- Add a readable `NAME_INVALID` client error message.
- Add focused tests for all formula-leading characters, leading whitespace/control cases, no-write behavior, and legacy CSV neutralization.

Files: `Core.gs`, `Client.html`, relevant tests, preview only if needed for parity (it already loads Core).

TDD: write/modify tests first, run them and capture expected RED, then implement the minimal fix and capture GREEN.

## 2. Minor — student result accessibility

Required behavior:
- Submission error box is an assertive live alert (`role="alert"`, `aria-live="assertive"`, `aria-atomic="true"`).
- After successful scan, move focus to the success heading (e.g. `tabindex="-1"` plus `.focus()`), rather than relying only on a newly inserted polite live region.
- Add static regression assertions for these behaviors. If practical, verify actual focus/alert attributes in the local browser smoke test.

Files: `Client.html`, `tests/client-static.test.cjs`.

## 3. Minor — configuration guidance

Update `SPREADSHEET_NOT_CONFIGURED` message to tell the office to set `SPREADSHEET_ID` in Apps Script Project Settings → Script Properties. Add a static assertion.

Files: `Client.html`, `tests/client-static.test.cjs`.

## 4. Minor — exact preview/backend status parity

Backend `scan.status` requires a nonempty token but does not impose the 100-character record limit. Preview must match:
- Status accepts a 101-character token and returns the normal validated status.
- Record still rejects tokens over 100 characters with `DEVICE_TOKEN_REQUIRED` and writes nothing.

Modify the existing preview regression test first, capture RED, then make the minimal preview change and capture GREEN.

Files: `tests/preview.test.cjs`, `preview/server.cjs`.

## 5. Minor — setup smoke checklist

Expand `SETUP.md` Test section so a real deployment is not considered verified until the owner has also:
- regenerated codes and confirmed earlier codes are rejected without writes;
- confirmed the real office list and CSV show the records;
- inspected the real `Daily Codes`, `People`, and `Attendance` tabs and documented columns.

Add `NAME_INVALID` troubleshooting. Keep the public-admin warning and the exact pending-deployment statement.

Files: `SETUP.md`.

## 6. High-value deferred test gaps

Add focused backend regressions without changing production behavior:
- unmatched OUT as the first scan creates one OUT row;
- direct admin HTTP actions (`admin.generate`, `admin.list`, `admin.export`), public wrappers, and `doGet` return the expected shapes/HTML;
- freeze the backend test clock to a fixed Manila date to eliminate midnight flakiness;
- if the lock mock is made configurable, add a `SHEET_BUSY` no-write regression.

Files: `tests/backend.test.cjs` and test helpers only.

## 7. Verification record and report

After code/tests are green:
- Run `npm test` and record exact final counts.
- Start the local preview and use Playwright MCP for a focused final browser smoke: valid registration/success focus, formula-like name rejection with no success/no row, and returning recognition. Do not claim a full rerun of earlier checks unless actually performed.
- Update `VERIFICATION.md` with the final security/accessibility/parity fixes, fresh test counts, focused browser evidence, and unchanged `Pending owner deployment` status. Preserve prior local evidence but distinguish it from final-fix evidence.
- Append a final-fix section to `task-7-report.md` or create `.superpowers/sdd/2026-11-24-sslg-qr-attendance/final-fix-report.md` with RED/GREEN evidence and files changed. Prefer the dedicated final-fix report.
- Stop only the preview process you start. Remove any scratch artifacts you create.

## Constraints

- No Git commands or commits.
- No credentials, real Spreadsheet ID, live deployment, production URL, phone number, login, private admin auth, or attendance-semantics changes.
- Do not dispatch subagents/reviewers.
- Do not alter tests merely to pass; prove new security/parity tests fail before fixes.
- Final report path: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/final-fix-report.md`

Return Status, no commits, one-line test summary, focused browser summary, concerns, and report path.
