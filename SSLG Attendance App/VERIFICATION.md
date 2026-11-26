# SSLG QR Attendance Verification

**Initial verification date:** 2026-11-24  
**Final security correction:** 2026-11-25  
**Local verification status:** PASS  
**Real Google Apps Script/Sheets smoke test:** **Pending owner deployment**

> **Current QR lifecycle (amended 2026-11-25):** one permanent, date-free IN/OUT pair is reused every day with no regeneration/reset. Evidence before the final permanent-pair amendment is retained as historical record; its daily-generation, expiry, regeneration, and `Daily Codes` claims are superseded by the final section below.

## Environment and method

- Workspace: `C:/Users/Ma Christine/Downloads/SSLG MEMOS`
- App: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`
- OS: Windows 10.0.26200, x64; shell: Git Bash
- Observed runtime: Node.js `v26.13.1`, npm `11.20.0` (the environment notice listed Node `v24.22.1`; the commands actually ran under `v26.13.1`, which satisfies `node >=20`)
- Browser: installed Playwright MCP, Chromium `Chrome/157.0.0.0`, `en-US`, Win32
- Desktop viewport: `1440×1000`
- Mobile viewport: fresh isolated browser context, `390×844`; mobile media query matched and document width equalled client width (`375px`, with no horizontal overflow)
- Attendance date: Manila date `2026-11-24`
- Backend: local preview with in-memory mocked Apps Script/Sheets behavior; no Google credentials, Spreadsheet ID, or external deployment was used

## Automated commands and results

Working directory: `SSLG Attendance App/`.

```text
$ npm install
up to date, audited 4 packages in 27s
found 0 vulnerabilities
```

```text
$ npm test
> sslg-office-attendance@1.0.0 test
> node --test
ℹ tests 32
ℹ suites 0
ℹ pass 32
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
```

The original Task 7 run recorded durations of `2580.9216ms` and `1746.7284ms`; both runs reported `32` tests, `32` pass, `0` fail, `0` cancelled, `0` skipped, and `0` todo. The print-layout PASS below applies to the corrected `Styles.html`, not to the baseline print behavior. Fix round 1 reran `npm test` after the documentation corrections and scratch-PDF cleanup; its fresh result is recorded after the defect evidence below.

The suite covered core/backend rules, client static and admin race behavior, QR decode round-trips, preview API behavior, and packaging.

## Preview process

```text
$ npm run preview
> sslg-office-attendance@1.0.0 preview
> node preview/server.cjs
SSLG attendance preview: http://127.0.0.1:4173
```

The preview was started as background task `b15je8567`. Both browser contexts were closed, that task alone was stopped, and `netstat -ano | findstr ':4173' || true` returned no output afterward.

## URLs tested

All URLs below are local-preview URLs. QR tokens were copied from actual `admin.generate` response bodies, not invented.

### Desktop office URL

- `http://127.0.0.1:4173/?page=admin`

### Pair A — generated at `2026-11-24T21:00:50+08:00`

- IN, opened in the fresh mobile context and reopened for the repeated scan:  
  `http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=IN&code=2a57530d-6f2d-46ca-bfe3-50e98f9ce2f6`
- OUT, opened in the same mobile context:  
  `http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=OUT&code=5dbdc492-622a-4ad8-ac90-a1b1ff80194c`

### Pair B — regeneration at `2026-11-24T21:24:59+08:00`

- Previous Pair A IN URL: reopened and correctly rejected.
- New IN, opened in the same mobile context for offline failure and retry:  
  `http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=IN&code=24933dd4-1cd7-4a46-bc83-eb051933d762`
- Generated OUT URL, not opened during this run:  
  `http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=OUT&code=83f09141-6a24-455a-9a82-e91ac0072917`

### Pair C — generated for print verification at `2026-11-24T21:30:15+08:00`

- Generated IN URL, printed as a QR card but not opened:  
  `http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=IN&code=228d26aa-e77a-40de-bcf5-43aec441efcb`
- Generated OUT URL, printed as a QR card but not opened:  
  `http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=OUT&code=0d5fd135-6286-46d6-90b1-1d5d567e3fa5`

## Browser checklist

| Step | Result | Observed evidence |
| --- | --- | --- |
| 3. Office golden path | PASS | Desktop admin date was `2026-11-24`. Generate confirmation read `Generate new IN and OUT codes? The previous pair for this date will stop working.` Two images rendered with `Check in` / `Check out`, date `2026-11-24`, and `Created 2026-11-24T21:00:50+08:00`. Empty list read `No scans recorded for this date.` Totals were `0 Scans`, `0 People`, `0 IN`, `0 OUT`. Search `No such attendee` caused no console error. Export offered `SSLG-attendance-2026-11-24.csv`, failure `null`. |
| 4. New-user mobile registration | PASS | Fresh mobile context showed `Record your arrival`, `Your name`, and `Register and check in`; no admin link. Submitting `Ana Cruz` showed `Recorded`, `Checked in`, `Ana Cruz`, `2026-11-24T21:14:21+08:00 · Philippines time`, and `You may close this page.` Office then showed one IN row and totals `1 Scans`, `1 People`, `1 IN`, `0 OUT`. |
| 5. Returning recognition and repeated scans | PASS | OUT page showed `Continuing as` / `Ana Cruz` and `Confirm check out`, with no name form or login. Success read `Checked out`, `Ana Cruz`, `2026-11-24T21:16:09+08:00 · Philippines time`; office totals became `2 Scans`, `1 People`, `1 IN`, `1 OUT`. Reopening IN showed `Continuing as` / `Ana Cruz` and `Confirm check in`; success timestamp was `2026-11-24T21:23:10+08:00`. Office showed three separate rows and totals `3 Scans`, `1 People`, `2 IN`, `1 OUT`; no duplicate-open-session message appeared. |
| 6. Invalidation and failed request | PASS | Regeneration produced Pair B. Previous IN returned HTTP 200 with `{"ok":false,"error":"INVALID_CODE"}` and displayed `This QR code is no longer valid. A newer code may have been generated.` No row was added. With Pair B IN loaded, browser context offline state set `navigator.onLine=false` before confirmation. UI showed `The scan was not recorded. Check your connection and try again.`, no success heading, remembered `Ana Cruz`, and an enabled retry button. After reconnecting, retry showed `Checked in` at `2026-11-24T21:27:36+08:00`. Office then showed exactly four rows: the prior three plus one retry row, with the new row using `qr_created_at=2026-11-24T21:24:59+08:00`. |
| 7. Print layout | PASS after fix | Generated Pair C, emulated `media=print`, and inspected computed print state after correcting `Styles.html`. Exactly 11 rendered visible elements existed, all `#qr-pair` or its two card descendants. Both QR images had natural size `336×336` and rendered print size `272.13×272.13px`; cards were `464.88×405.13px` and `464.89×405.13px`. Header/footer had `display:none`; buttons, filters, totals, and attendance table were hidden with zero bounds; the attendance card had `display:none`. Post-fix Chromium PDF `.task7-print-fixed.pdf` had one page; baseline `.task7-print.pdf` had two pages, with the second blank. |

## Search, totals, date filter, and CSV evidence

- Search `ana`: three visible rows, while totals remained `3 Scans`, `1 People`, `2 IN`, `1 OUT` before regeneration.
- Search `nobody`: zero visible rows and `No scans recorded for this date.`, while totals remained based on the full date.
- Export after three scans offered `SSLG-attendance-2026-11-24.csv`, failure `null`; its header was `"event_id","date","scanned_at","mode","name","device_token","qr_created_at"` and it contained three data rows. Device-token values are intentionally omitted from this report.
- Date `2026-11-23`: `admin.list` returned totals `{scans:0,people:0,in:0,out:0}` and zero rows; export offered `SSLG-attendance-2026-11-23.csv`.
- Date restored to `2026-11-24`: four rows and totals `{scans:4,people:1,in:3,out:1}`.

## Exact critical UI text

### Registration success

```text
OK
RECORDED
Checked in
Ana Cruz
2026-11-24T21:14:21+08:00 · Philippines time
You may close this page.
```

### Returning recognition before OUT confirmation

```text
Check out
Record your departure
2026-11-24 · SSLG Office
Continuing as
Ana Cruz
Confirm check out
```

### Invalid regenerated code

```text
This QR code is no longer valid. A newer code may have been generated.
```

### Offline failure before retry

```text
CHECK IN
Record your arrival
2026-11-24 · SSLG Office
Continuing as
Ana Cruz
Confirm check in
The scan was not recorded. Check your connection and try again.
```

### Successful retry

```text
OK
RECORDED
Checked in
Ana Cruz
2026-11-24T21:27:36+08:00 · Philippines time
You may close this page.
```

### Post-fix print-media visible card text

```text
CHECK IN
2026-11-24
Created 2026-11-24T21:30:15+08:00

CHECK OUT
2026-11-24
Created 2026-11-24T21:30:15+08:00
```

## Console and network review

- Desktop: Playwright console inspection reported `Total messages: 0 (Errors: 0, Warnings: 0)`. All observed admin API requests returned HTTP 200.
- Mobile: all normal `scan.status` and `scan.record` requests returned HTTP 200. The deliberate offline request was recorded as `[FAILED] net::ERR_INTERNET_DISCONNECTED`; the retry returned HTTP 200.
- Mobile console contained exactly one expected resource error: `Failed to load resource: net::ERR_INTERNET_DISCONNECTED @ http://127.0.0.1:4173/api/scan.record:0`.
- The offline interaction had zero uncaught `pageerror` events. No uncaught application errors were observed. Invalid-code responses were HTTP 200 with `ok:false`, not transport failures.
- No device token or QR token was logged by application console code. Tokens shown in this report are local QR URLs obtained from the preview API; device-token values are redacted.

## Defects and fixes

### Print-layout defect found and fixed

- **Defect:** Printing the office page did not reliably produce only the two QR cards on one page.
- **Root cause:** The baseline `@media print` rules hid most content with `visibility:hidden`, which retains layout space, while `#qr-pair` was absolutely positioned with `top:0; left:0`. The hidden page structure could still contribute to pagination, and the absolutely positioned QR pair was outside normal flow.
- **RED / before:** Against baseline `Styles.html`, Chromium print output `.task7-print.pdf` contained **2 pages**, and the **second page was blank**.
- **Minimal fix:** In `Styles.html` only, the print block adds explicit `display:none` rules for non-app body children, non-first app cards, and first-card children other than `#qr-pair`; resets the first card's print spacing/border; and changes `#qr-pair` from absolute positioning to `position:static`. Screen layout and attendance behavior were not changed.
- **GREEN / after:** With that fix, Chromium print output `.task7-print-fixed.pdf` contained **1 page**. The post-fix computed-state evidence in Step 7 showed only `#qr-pair` and its two card descendants rendered visibly, with both QR images legible and controls, header, footer, totals, and attendance content absent.
- **Print verdict:** **PASS after the fix.** This verdict does not describe the baseline's failing two-page output.
- **Cleanup:** `.task7-print.pdf`, `.task7-print-hypothesis.pdf`, and `.task7-print-fixed.pdf` were session-created scratch artifacts, absent from the `before-task-7` snapshot. They were removed after their evidence was recorded; they are not app deliverables.

No tests, package files, configuration, dependencies, or product features were changed. The existing automated suite was rerun after the documentation corrections and cleanup.

### Fix round 1 fresh test result

Working directory: `SSLG Attendance App/`.

```text
$ npm test
> sslg-office-attendance@1.0.0 test
> node --test
ℹ tests 32
ℹ suites 0
ℹ pass 32
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1635.67
```

Exit code: `0`.

## Ten-criterion acceptance audit

| # | Acceptance criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | A new phone can scan a valid IN code, enter a name once, and create exactly one Attendance row. | PASS | Fresh mobile context registered `Ana Cruz`; office list had exactly one IN row and totals `1/1/1/0`. Automated registration tests also passed. |
| 2 | The same phone recognizes the saved name on a later scan without asking for a login or name again. | PASS | Same isolated mobile context showed `Continuing as Ana Cruz` for OUT and later IN, with confirmation buttons and no name form/login. |
| 3 | A valid OUT scan creates an Attendance row with mode `OUT` and the server timestamp. | PASS | OUT success at `2026-11-24T21:16:09+08:00`; office row had mode `OUT`, matching Manila timestamp, and Pair A creation time. |
| 4 | Multiple valid scans create multiple rows; no in/out pairing rule blocks them. | PASS | IN → OUT → IN produced three distinct rows; no duplicate-open-session message. Totals `3 Scans`, `1 People`, `2 IN`, `1 OUT`. |
| 5 | One date-free IN/OUT pair is reused every day; each scan receives the current Asia/Manila server date and no regeneration/reset exists. | PASS | Permanent-pair core/backend/preview tests accept the same record on different Manila dates, ignore caller dates, use one server instant per scan, and expose no reset action. Final browser smoke confirmed identical date-free URLs/images on repeated display. |
| 6 | Invalid codes and failed requests create no Attendance row and never show false success. | PASS | Invalid code added no row. Offline confirmation showed the not-recorded message and zero success headings; after one successful retry the total rose only from three to four. Automated rejection tests passed. |
| 7 | The office can create/show the same permanent QR pair, see its original creation time, filter daily records, and export CSV. | PASS | Idempotent backend/preview tests and final browser smoke showed the same pair, original creation timestamp, date-independent cards, daily filtering, and CSV behavior. |
| 8 | The Spreadsheet contains the documented `QR Codes`, `People`, and `Attendance` tabs and columns, with exactly one permanent-pair row. | PENDING | Mock-backed schema/idempotency tests passed, but no owner Spreadsheet was available. **Pending owner deployment** real Sheets inspection. |
| 9 | The student flow contains no admin link or attendance list. | PASS | Mobile snapshots and DOM checks found zero admin links and zero attendance tables; static navigation tests passed. |
| 10 | Automated tests and local browser checks pass; deployment-specific checks remain explicitly pending until run on the owner's account. | PASS | The final permanent-pair suite passed `64/64`; backend/preview tests cover cross-date reuse and daily rows, and the final browser smoke confirmed permanent cards, date-free links, registration, server dating, and zero console errors/warnings. Real Apps Script/Sheets checks are explicitly **Pending owner deployment**. |

## Pending owner deployment checks

**Status: Pending owner deployment.** The local preview is not evidence about the owner's Google Spreadsheet or Apps Script execution.

The owner still needs to:

1. Configure the Spreadsheet ID and `Asia/Manila` timezone in the owner's Apps Script project.
2. Deploy with the intended anyone-with-link access.
3. Show the permanent pair once; repeat and confirm identical codes and creation time.
4. Scan IN on a phone, register a name, and confirm exactly one real `Attendance` row.
5. Scan OUT on the same phone and confirm recognition plus a second real row.
6. Confirm unknown and wrong-mode codes create no rows.
7. Confirm the real office list and CSV show the real records.
8. Inspect the real `QR Codes`, `People`, and `Attendance` tabs and documented columns; confirm exactly one `QR Codes` row.
9. On a later day, reuse the exact same links and confirm new rows carry that later Manila date.

## Scope and self-review

- Re-read Task 7 Steps 1–10 and the ten acceptance criteria before recording results.
- Used actual Playwright browser interactions at both required widths; static inspection was not substituted for browser checks.
- Offline mode was genuinely exercised with Playwright browser-context offline control, not inferred from source.
- No subagents or reviewers were dispatched; no Git commands or commits were run.
- No phone number, login, private admin authentication, attendance-semantics change, credential, Spreadsheet ID, or external URL was introduced.
- Task 7 changed `SSLG Attendance App/Styles.html` for the minimal print fix, added `SSLG Attendance App/VERIFICATION.md`, and removed its own three temporary scratch PDFs. It also created the approved SDD report outside the app at `.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-7-report.md`.
- The final app-source comparison against `before-task-7` (excluding `node_modules`) contains only modified `Styles.html` and added `VERIFICATION.md`. The three scratch PDFs were absent from that baseline and are absent after cleanup. No unsupported vault-wide file counts or whole-vault hash claims are made.
- Print RED/GREEN evidence is Chromium print-media emulation, computed layout, and generated PDF page counts, not a physical-printer test. Mobile evidence is an isolated Chromium context at `390×844`, not a physical phone or native-camera scan.

## Final fix wave — fresh evidence (2026-11-24)

This section records the final whole-app fix wave. It is distinct from the preserved Task 7 evidence above; the earlier browser checklist was not rerun in full.

### Security, accessibility, configuration, and parity

- `Core.gs` rejects normalized names beginning with `=`, `+`, `-`, or `@` as `NAME_INVALID` before person upsert or Attendance append. Existing blank-name, 80-character, whitespace, and punctuation rules remain covered.
- CSV escaping prefixes an apostrophe before normal quoting for formula-leading fields, leading tab/CR/LF fields, and leading-space variants. Export does not mutate stored rows; a manually edited legacy Attendance row is covered.
- The student submission error is `role="alert"`, `aria-live="assertive"`, and `aria-atomic="true"`. Successful IN and OUT screens move focus to `#scan-success` with `tabindex="-1"`.
- `SPREADSHEET_NOT_CONFIGURED` now directs the office to set `SPREADSHEET_ID` in Apps Script `Project Settings → Script Properties`.
- Preview status now accepts a 101-character device token like the backend; preview record still rejects it with `DEVICE_TOKEN_REQUIRED` and writes nothing.
- Backend regressions also cover first-scan unmatched OUT, direct admin HTTP actions, public wrappers, `doGet` HTML, a fixed Manila test clock (`2026-11-24T20:00:00+08:00`), and `SHEET_BUSY` no-write behavior.

### RED / GREEN evidence

Tests were written or modified before production changes. Focused RED runs failed for the intended missing behavior:

```text
core:       9 tests, 7 pass, 2 fail
client:     7 tests, 4 pass, 3 fail
preview:    9 tests, 7 pass, 2 fail
backend:   13 tests, 10 pass, 3 fail
```

The failures included missing `NAME_INVALID`, unneutralized CSV values, missing alert/focus markup, preview status rejecting a 101-character token, and formula-like preview names being recorded. After the minimal fixes, the same focused files were GREEN: core `9/9`, client static `7/7`, preview `9/9`, backend `13/13`.

### Final automated result

Working directory: `SSLG Attendance App/`.

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

Exit code: `0`.

### Focused final Playwright smoke

A fresh local preview was started as task `b6a5uuj5a` on `127.0.0.1:4173`. Playwright MCP/Chromium performed only the focused checks below:

1. Generated a real preview code pair for Manila date `2026-11-24` at `2026-11-24T23:06:37+08:00`.
2. With fresh browser storage, registered `Final Fix Ana` through the IN form. Success read `Checked in`; `document.activeElement.id` was `scan-success`, and the heading had `tabindex="-1"`. The preview list showed exactly `1` scan and `1` person.
3. Cleared only the device token, reopened IN, and submitted `  =SUM(A1)  `. The visible error read `Please enter a name that does not start with =, +, -, or @.` Its measured attributes were `role="alert"`, `aria-live="assertive"`, and `aria-atomic="true"`. There were zero success headings, and the list remained at `1` scan / `1` person with no formula-like row.
4. Restored the original browser device token and opened OUT. The page showed `Continuing as` / `Final Fix Ana`, no registration form, and `Confirm check out`. Confirmation showed `Checked out`, again with focus on `scan-success`. Final totals were `2` scans, `1` person, `1` IN, and `1` OUT; both rows belonged to `Final Fix Ana`.
5. Playwright console inspection reported `Total messages: 0 (Errors: 0, Warnings: 0)`.

The browser tab was closed and only the preview task started for this smoke was stopped. Port `4173` had no remaining listener; only transient `TIME_WAIT` entries were observed. No credentials, real Spreadsheet ID, external deployment, or production URL was used.

### Setup and deployment status

`SETUP.md` now requires code regeneration with old-code rejection and no writes, real office-list/CSV confirmation, and inspection/documentation of the real `Daily Codes`, `People`, and `Attendance` columns. It includes `NAME_INVALID` troubleshooting while preserving the public-admin warning and the exact pending-deployment statement.

**Real Google Apps Script/Sheets smoke test: Pending owner deployment.** Local preview evidence does not verify the owner's Spreadsheet or Apps Script execution.

## Final security correction and re-review (2026-11-25)

A scoped re-review of the first fix wave left two findings open: the backend test helper still constructed a host-runtime date, and caller-controlled formula/control-leading device tokens could reach Sheets. Both were corrected without changing valid attendance behavior.

### Corrections

- `tests/backend.test.cjs` now constructs its fixture date from the VM's `FixedDate`. A regression advances the host clock to Manila date `2026-11-26` while proving backend request, status, event, and timestamp values remain on `2026-11-24`.
- `Core.gs` adds one shared device-token validator. `Code.gs` and `preview/server.cjs` call it before person lookup/upsert or Attendance writes. It rejects `=`, `+`, `-`, `@`, tab, CR, and LF leaders, including after leading whitespace, with `DEVICE_TOKEN_INVALID`.
- Empty tokens and write tokens over 100 characters retain `DEVICE_TOKEN_REQUIRED`. Safe tokens are not trimmed or transformed; safe 100-character write tokens and safe 101-character status tokens retain their existing behavior.
- `Client.html` and `SETUP.md` explain how to recover from `DEVICE_TOKEN_INVALID` by clearing site storage and reopening the QR link.

### TDD and automated evidence

The clock regression failed before its helper correction (`actual 2026-11-26`, `expected 2026-11-24`). The dangerous-token and client-guidance regressions failed before implementation because `=device` was accepted and the client showed the generic connection error. Focused corrected tests then passed `4/4`.

The controller independently ran the full suite from `SSLG Attendance App` after implementation:

```text
$ npm test
ℹ tests 51
ℹ suites 0
ℹ pass 51
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3711.0299
```

Exit code: `0`. Tests cover all seven dangerous leaders and leading-space variants for both actions, backend/preview parity, unchanged backend People/Attendance rows and write counts, zero preview records, valid-token recognition, and the existing length boundaries.

### Focused Playwright correction smoke

A fresh preview ran as task `bbn9yk2el` on `127.0.0.1:4173`. A real preview pair was generated for Manila date `2026-11-25` at `2026-11-25T07:21:41+08:00`.

1. Set the saved device token to a formula-leading value and opened the generated IN URL. The page displayed `This browser’s saved device token is invalid. Clear site storage and try again.`
2. The office list remained exactly `0 Scans`, `0 People`, `0 IN`, `0 OUT`.
3. Replaced the invalid saved token with a valid test token, reopened IN, registered `Security Fix Ana`, and confirmed. The page showed `Checked in`, focus remained on `scan-success`, and the list showed exactly one IN row, one person, and one scan.
4. Playwright console inspection reported `Total messages: 0 (Errors: 0, Warnings: 0)`.

The browser page was closed and only the preview task started for this smoke was stopped. No credential, real Spreadsheet ID, production URL, or real Sheet write was used.

### Independent scoped re-review

The exact correction diff and report were reviewed independently. Both findings were verdicted **ADDRESSED**, with no new Critical/Important breakage identified. The final whole-app review is therefore clean for local implementation. Acceptance criterion 8 and the real Apps Script/Sheets smoke test remain **Pending owner deployment**.

## Permanent reusable QR pair amendment (2026-11-25)

The user explicitly changed the QR lifecycle: the same IN/OUT pair must be reused every day, with no replacement option. This amendment supersedes the historical daily-generation evidence above.

### Implemented behavior

- `QR Codes` replaces `Daily Codes` and stores exactly one row with `in_code`, `out_code`, `created_at`, and `created_by`.
- The first `admin.generate`/`adminGenerate` request creates the pair under the script lock. Later requests return identical codes, URLs, and creation time without another Sheet write or UUID consumption.
- QR URLs contain `page=scan`, `mode`, and `code` only. Caller-supplied dates are ignored.
- `recordScan_` uses one server instant for validation, the Manila attendance date, person timestamps, and exact scan timestamp. A midnight-boundary regression covers date/timestamp consistency.
- The admin page says `Permanent QR codes`, uses `Show permanent QR pair`, removes the regeneration confirmation, and labels cards `Reusable every day`. Changing the attendance-date filter affects records only.
- The preview mirrors the permanent record and date logic. Repeated IN, unmatched OUT, returning recognition, formula/name/token/CSV defenses, public admin, and daily list/export behavior remain intact.

### TDD and independent automated result

The focused pre-production RED run reported **63 tests: 27 pass, 36 fail** for the expected missing permanent-record, idempotency, date-free, schema, UI, and preview behavior. A separate midnight regression also failed before the single-instant correction. After implementation and test-harness corrections, the focused suite passed **64/64**.

The controller independently ran the full suite from `SSLG Attendance App`:

```text
$ npm test
ℹ tests 64
ℹ suites 0
ℹ pass 64
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 22830.0157
```

Exit code: `0`. Coverage includes permanent-pair idempotency and no UUID consumption, cross-Manila-date reuse in backend and preview, caller-date independence, one-instant midnight consistency, no reset action, schema headers, daily totals, and all previous security/attendance regressions.

### Independent browser smoke

A fresh preview ran as task `b990s2jmd` on `127.0.0.1:4173`. The permanent pair was created at `2026-11-25T08:22:35+08:00`.

1. The office page showed `Permanent QR codes`, `Show permanent QR pair`, and two cards labeled `Reusable every day`.
2. Changing the attendance date to `2026-11-26` preserved the exact two image data URLs. Clicking `Show permanent QR pair` again preserved them again.
3. Two direct generation requests returned identical IN/OUT records and creation time. Both URLs were date-free.
4. With fresh site storage, opening the exact generated IN URL showed server date `2026-11-25`; registering `Permanent Pair Ana` produced `Checked in` at `2026-11-25T08:32:25+08:00`, focus on `scan-success`, and totals `1 Scan`, `1 Person`, `1 IN`, `0 OUT`.
5. Playwright console inspection reported `Total messages: 0 (Errors: 0, Warnings: 0)`.

The browser and preview task were closed/stopped. No credential, real Spreadsheet ID, production URL, or real Sheet write was used.

### Review disposition

Independent review found spec compliance with two Low observations and no High/Medium defects:

- Retained `WRONG_DATE`/`CODE_EXPIRED` client assertions are negative coverage proving removed lifecycle errors receive no special permanent-code wording; they do not support obsolete behavior.
- A rejected scan on a pristine Sheet may initialize schema headers through the existing `ensureSchema_` path, but creates no People or Attendance data row. This preserves the established initializer contract and matches the user-visible no-attendance-write requirement.

Real concurrent first creation, physical phone/camera use, real QR decoding from the deployed URL, one-row Sheet inspection, and later-day live reuse remain owner-deployment checks. **Acceptance criterion 8 and the real Apps Script/Sheets smoke test remain Pending owner deployment.**

## Single-file deployment bundle (2026-11-25)

`deploy/SSLG Attendance.gs` combines the unchanged core, backend, styles, QR library, and client into one pasteable Apps Script file. Its `doGet` returns the exact HTML produced by the split `Index.html` includes, without Apps Script HTML-file dependencies. The bundle is 94,197 characters and contains no spreadsheet ID or secret assignment.

A pre-production packaging RED run failed the two new deployment tests because the bundle and checklist did not exist. After adding `scripts/build-deployment.cjs`, the focused packaging suite passed 6/6 and the final full controller suite passed **66/66** with exit code 0. The standalone zip contains only `SSLG Attendance.gs`, the matching `appsscript.json`, and `START HERE.txt`.

This reduces owner setup to creating the Sheet, pasting one script file, setting `SPREADSHEET_ID`, and publishing from their own Google account. It does not authorize or perform a real deployment; the owner-deployment checks above remain pending.
