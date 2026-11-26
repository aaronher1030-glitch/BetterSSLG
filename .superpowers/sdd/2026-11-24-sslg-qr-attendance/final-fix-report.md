# Final Whole-App Fix Wave Report

> **Historical scope note (2026-11-25):** This report records the earlier security/accessibility fix wave. The user subsequently approved one permanent date-free QR pair with no regeneration; that later change supersedes this report's daily-code lifecycle. See `permanent-pair-report.md` and the final amendment in `SSLG Attendance App/VERIFICATION.md`.

**Date:** 2026-11-24  
**Status:** Complete for local implementation and verification after the subsequent security correction below; real Google deployment remains pending.  
**Baseline:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/before-final-fix/`  
**App:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`  
**Commits:** None. No Git commands or commits were run.

## Scope completed

1. Rejected normalized formula-leading names with `NAME_INVALID` before person-record upsert or Attendance append.
2. Neutralized formula/control-leading CSV fields before normal CSV quoting without changing stored values.
3. Added readable `NAME_INVALID` and explicit `SPREADSHEET_ID` configuration guidance.
4. Made the student submission error an assertive atomic live alert and moved success focus to the success heading.
5. Matched preview/backend device-token status parity while retaining the record limit.
6. Expanded the real-deployment setup smoke checklist and added `NAME_INVALID` troubleshooting.
7. Added the deferred backend regressions without changing production attendance behavior.
8. Ran focused Playwright MCP smoke checks and updated `VERIFICATION.md` with fresh final-fix evidence.

## Initial fix-wave files changed

Absolute paths:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Core.gs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Client.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/preview/server.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/SETUP.md`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/VERIFICATION.md`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/core.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/backend.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/client-static.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/preview.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/final-fix-report.md` (this report)

A recursive comparison against `before-final-fix`, excluding `node_modules`, found only the nine app files listed above changed before this report was written. `Code.gs`, `Styles.html`, manifests, dependencies, and attendance semantics were not changed.

## TDD evidence

All behavior-changing tests were written or modified before production changes. The accepted RED runs were:

| Command | RED result | Expected missing behavior |
| --- | --- | --- |
| `node --test tests/core.test.cjs` | 9 tests, 7 pass, 2 fail | Formula-leading names were accepted; dangerous CSV fields were not neutralized. |
| `node --test tests/client-static.test.cjs` | 7 tests, 4 pass, 3 fail | Alert attributes, success focus, and new guidance were absent. |
| `node --test tests/preview.test.cjs` | 9 tests, 7 pass, 2 fail | Status rejected a 101-character token; formula-like names were recorded. |
| `node --test tests/backend.test.cjs` | 13 tests, 10 pass, 3 fail | New/returning formula names were written; legacy CSV fields were not neutralized. |

Representative actual RED failures:

```text
core: Missing expected exception; expected /NAME_INVALID/
core CSV: actual '"=1+1"', expected '"\'=1+1"'
preview status: actual { ok: false, error: 'DEVICE_TOKEN_REQUIRED' }, expected validated status
preview record: actual { ok: true, event: { name: '=SUM(A1)', ... } }, expected NAME_INVALID
backend new name: actual { ok: true, event: { name: '=SUM(A1)', ... } }, expected NAME_INVALID
backend returning name: actual { ok: true, event: { name: '=legacy', ... } }, expected NAME_INVALID
backend CSV: actual '"=event",...', expected '"\'=event",...'
```

The first backend RED run also exposed two test-harness mistakes: a lexical `const` was incorrectly accessed as a VM context property, and cross-VM objects were compared without normalizing prototypes. Only the tests were corrected; the backend was rerun and produced the accepted 10-pass/3-fail RED above before any production fix.

After the minimal implementation, the same focused files were GREEN:

| Command | GREEN result |
| --- | --- |
| `node --test tests/core.test.cjs` | 9 tests, 9 pass, 0 fail |
| `node --test tests/client-static.test.cjs` | 7 tests, 7 pass, 0 fail |
| `node --test tests/preview.test.cjs` | 9 tests, 9 pass, 0 fail |
| `node --test tests/backend.test.cjs` | 13 tests, 13 pass, 0 fail |

## Implementation details

### Name validation and no-record-write behavior

- `normalizeName_` retains trimming, internal-whitespace collapse, blank rejection, and the 80-character limit.
- After normalization, a leading `=`, `+`, `-`, or `@` throws `NAME_INVALID`.
- `recordScan_` already normalizes the stored returning name or submitted new name before `upsertPerson_` and Attendance append, so rejected names create no People record update/insert and no Attendance row.
- Tests cover all four leading characters for new names, leading whitespace/control variants in core normalization, returning legacy formula names, unchanged People rows, and unchanged Attendance row counts.
- Ordinary names such as `Ana O'Neil-Cruz, Jr.`, internal punctuation, tab/newline whitespace normalization, and the 80/81-character boundary remain covered.

### CSV hardening

- Every value passed through `csvEscape_` is checked before quote escaping.
- Values beginning with `=`, `+`, `-`, `@`, tab, CR, or LF are prefixed with an apostrophe.
- The same protection applies when leading spaces precede one of those triggers.
- Normal quoting, including doubled quotes, is applied after neutralization.
- Tests cover each trigger directly and after leading spaces, safe leading-space names, internal hyphens, and a manually edited legacy Attendance row with dangerous values in multiple columns.
- The legacy row is asserted unchanged after export.

### Client accessibility and guidance

- Submission error markup now has `role="alert"`, `aria-live="assertive"`, and `aria-atomic="true"`.
- The success heading has `id="scan-success"` and `tabindex="-1"`; `submitScan_` calls `.focus()` after rendering success.
- `NAME_INVALID` displays: `Please enter a name that does not start with =, +, -, or @.`
- `SPREADSHEET_NOT_CONFIGURED` directs the office to set `SPREADSHEET_ID` in Apps Script `Project Settings → Script Properties`.
- Static regression assertions cover all of these behaviors.

### Preview/backend parity

- Preview `scan.status` now requires only a nonempty token and accepts a 101-character token, matching backend `getScanStatus_`.
- Preview `scan.record` still rejects tokens over 100 characters with `DEVICE_TOKEN_REQUIRED`.
- The parity regression verifies validated status fields, record rejection, and zero resulting scans/people.

## Deferred backend regressions

Added without production behavior changes:

- Unmatched OUT as the first scan creates exactly one People row and one OUT Attendance row.
- Direct `admin.generate`, `admin.list`, and `admin.export` HTTP actions return expected result shapes.
- Public `adminGenerate`, `adminList`, `adminExport`, `scanStatus`, and `scanRecord` wrappers return expected shapes.
- `doGet` evaluates `Index` HTML for missing events, landing, scan, and admin requests.
- The backend test clock is fixed at `2026-11-24T12:00:00.000Z`, which is `2026-11-24T20:00:00+08:00` in Manila, eliminating real-midnight dependence.
- The test-only lock mock is configurable; the `SHEET_BUSY` regression confirms no People/Attendance write and no Daily Codes replacement while locked out.

## Final automated verification

Working directory: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`.

```text
$ npm test
> sslg-office-attendance@1.0.0 test
> node --test
ℹ tests 47
ℹ suites 0
ℹ pass 47
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1765.5935
```

Exit code: `0`. Baseline was 32/32; the final suite is 47/47.

## Focused final browser smoke

A fresh local preview was started as background task `b6a5uuj5a` at `http://127.0.0.1:4173`. Playwright MCP/Chromium was used for the following focused checks only; the earlier full Task 7 browser checklist was not rerun.

1. **Code generation:** Generated a preview pair for Manila date `2026-11-24`; creation time was `2026-11-24T23:06:37+08:00`.
2. **Valid registration and focus:** With fresh browser storage, submitted `Final Fix Ana` through the IN form. The screen showed `Checked in` and `Final Fix Ana`. Measured `document.activeElement.id` was `scan-success`; the heading had `tabindex="-1"`. The list showed exactly 1 scan, 1 person, 1 IN, and 0 OUT.
3. **Formula-like rejection and no row:** Cleared only the device token, reopened IN, and submitted `  =SUM(A1)  `. The visible message was `Please enter a name that does not start with =, +, -, or @.` Measured error attributes were `role="alert"`, `aria-live="assertive"`, and `aria-atomic="true"`. There were zero success headings. The list remained at 1 scan and 1 person, with only the valid `Final Fix Ana` row.
4. **Returning recognition:** Restored the original browser token and opened OUT. The page showed `Continuing as`, `Final Fix Ana`, and `Confirm check out`, with no registration form. Confirmation showed `Checked out`; focus again moved to `scan-success`.
5. **Final list:** Totals were 2 scans, 1 person, 1 IN, and 1 OUT. Both rows were `Final Fix Ana`; no formula-like row existed.
6. **Console:** Playwright reported `Total messages: 0 (Errors: 0, Warnings: 0)`.

Local QR tokens and device tokens are intentionally omitted from this report. They were ephemeral preview values, not credentials.

## Setup and verification documentation

- `SETUP.md` Test section now requires regeneration and confirmation that earlier codes are rejected without writes, real office-list/CSV confirmation, and inspection/documentation of real `Daily Codes`, `People`, and `Attendance` columns.
- `NAME_INVALID` troubleshooting was added.
- The public-admin warning and the exact statement `A live deployment is not verified until the owner completes the scan test in this guide.` were preserved.
- `VERIFICATION.md` retains prior Task 7 evidence and adds a clearly separated final-fix section with RED/GREEN results, 47/47 counts, focused browser evidence, and unchanged pending-deployment status.

## Cleanup and constraints

- Closed the Playwright page.
- Stopped only preview task `b6a5uuj5a`, which was started for this smoke.
- Confirmed no listener remained on port 4173; only transient `TIME_WAIT` entries were present immediately afterward.
- Removed the oversized temporary browser-evaluation output created by the MCP tool. No scratch files were added to the app or baseline.
- No subagents or reviewers were dispatched.
- No Git commands or commits were run.
- No credentials, real Spreadsheet ID, production URL, phone number, login, private admin authentication, or attendance-semantics change was introduced.

## Concerns / remaining verification

- **Pending owner deployment:** No real Google Apps Script/Sheets environment was available. Local preview and mocked backend evidence do not verify owner permissions, script properties, deployment access, real QR invalidation, real office-list/CSV output, or real tab schemas.
- The owner must complete the expanded `SETUP.md` deployment checklist before treating the live app as verified.

## Subsequent security correction (2026-11-25)

The scoped re-review left two findings open, so an additional tightly scoped corrective dispatch followed. Full RED/GREEN evidence is in `final-security-fix-report.md`; the exact snapshot diff is `final-security-fix.diff`.

- Fixed `today_(backend)` to use the VM's fixed `Date`; a host-clock-advance regression failed before the correction and passed afterward.
- Added shared `deviceTokenError_` validation in `Core.gs`, called by backend and preview before person/attendance mutations. Formula/control-leading tokens now return `DEVICE_TOKEN_INVALID`; safe-token recognition and 100/101-character boundaries remain intact.
- Added readable client guidance and matching `SETUP.md` troubleshooting.
- Additional changed app files: `Core.gs`, `Code.gs`, `Client.html`, `preview/server.cjs`, `tests/backend.test.cjs`, and `tests/client-static.test.cjs`. Controller documentation updates: `SETUP.md` and `VERIFICATION.md`.
- Controller independently ran `npm test`: **51 tests, 51 pass, 0 fail**.
- Focused Playwright smoke showed invalid-token guidance, zero rejected-scan records, then a successful valid-token registration with success focus and exactly one IN row; console had zero errors/warnings.
- Fresh scoped reviewer verdict: both findings **ADDRESSED**, no new Critical/Important breakage. Local implementation and review are complete; real deployment remains pending.
