# Task 7 Report: End-to-End Browser Verification and Acceptance Audit

**Date:** 2026-11-24  
**Task status:** Complete for local verification  
**Real Google Apps Script/Sheets smoke test:** **Pending owner deployment**  
**Commits:** None; the workspace is not a Git repository and no Git commands were run.

## 1. Scope and honesty controls

Task 7 was treated as final verification, not feature expansion. Tasks 1–6 were not reimplemented. Browser print verification did find a defect: the baseline produced a two-page PDF with a blank second page. The only app-source fix was the minimal print CSS correction in `SSLG Attendance App/Styles.html`; `SSLG Attendance App/VERIFICATION.md` was added as the verification record. Task 7's three temporary scratch PDFs were removed after their evidence was recorded. No Google credentials, real Spreadsheet ID, external deployment, phone number, login, private admin authentication, or attendance-semantics change was introduced. No subagents or reviewers were dispatched.

Evidence is split explicitly between:

- **Automated/local-preview evidence:** Node tests, the in-memory preview API, and Playwright Chromium interactions.
- **Owner-environment evidence:** not available; all real Apps Script/Sheets checks remain **Pending owner deployment**.

## 2. Environment

| Item | Observed value |
| --- | --- |
| Workspace | `C:/Users/Ma Christine/Downloads/SSLG MEMOS` |
| Project root | `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App` |
| OS | Windows 10.0.26200, x64 |
| Shell | Git Bash |
| Runtime actually used | Node.js `v26.13.1`; npm `11.20.0` |
| Runtime notice discrepancy | Environment notice listed Node `v24.22.1`; shell commands reported `v26.13.1`. Both satisfy the project's `node >=20` engine requirement. |
| Browser tool | Installed Playwright MCP |
| Browser | Chromium `Chrome/157.0.0.0`, Win32, `en-US` |
| Desktop viewport | `1440×1000` |
| Mobile viewport | Fresh isolated context at `390×844` |
| Manila attendance date | `2026-11-24` |
| Preview bind address | `http://127.0.0.1:4173` |

The mobile context used the required `390×844` viewport and matched `(max-width: 620px)`. `innerWidth` was `390`; document `clientWidth` and `scrollWidth` were both `375`, so there was no horizontal overflow. It was an isolated Chromium context, not a physical handset or native-camera scan.

## 3. Exact commands and automated results

Working directory for npm commands:

```text
C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App
```

### 3.1 Dependency installation

```text
$ npm install
up to date, audited 4 packages in 27s
found 0 vulnerabilities
```

Exit code: `0`.

### 3.2 Initial full suite

```text
$ npm test
> sslg-office-attendance@1.0.0 test
> node --test

✔ creates the documented Sheet tabs and headers (19.5718ms)
✔ generates daily codes and invalidates the previous pair (205.3734ms)
✔ registers a device once and records every valid scan (19.3655ms)
✔ rejects invalid codes without writing attendance (6.6327ms)
✔ filters attendance and exports CSV (14.9583ms)
✔ a late generation response cannot redisplay QR cards for a previous date (172.8897ms)
✔ an older attendance response cannot overwrite a newer search result (12.5746ms)
✔ an older attendance failure cannot resurface an error after a newer search succeeds (12.6986ms)
✔ starting list and export requests hides a recovered office error (8.4376ms)
✔ client script parses as JavaScript (7.5243ms)
✔ landing and student navigation contain no admin link (1.1787ms)
✔ index includes every client asset exactly once (1.1984ms)
✔ Apps Script adapter maps every API action to a public server function (1.1166ms)
✔ normalizes a registered name and rejects blank names (5.9942ms)
✔ uses the Manila calendar date across UTC midnight (126.0595ms)
✔ rejects impossible calendar dates (1.3771ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (2.9927ms)
✔ validates matching code, mode, and current Manila date (6.4488ms)
✔ escapes CSV commas, quotes, and newlines (4.8393ms)
✔ manifest uses Manila time and anonymous access (4.9872ms)
✔ required Apps Script files exist (5.6919ms)
✔ project contains no hard-coded spreadsheet ID or secret assignment (6.0432ms)
✔ renders all include files without scriptlet placeholders (217.2665ms)
✔ preview supports registration, recognition, and repeated scans (195.5555ms)
✔ preview exports recorded attendance as CSV (121.1001ms)
✔ preview returns a JSON error for malformed request bodies (81.0443ms)
✔ preview scan handlers reject missing device tokens without writing attendance (54.1493ms)
✔ preview scan handlers reject 101-character device tokens without writing attendance (65.1084ms)
✔ preview accepts 100-character device tokens and returns validated scan status fields (71.7024ms)
✔ preview search trims and stringifies queries like the backend (58.0407ms)
✔ IN QR payload decodes exactly (432.2655ms)
✔ OUT QR payload decodes exactly (188.7891ms)
ℹ tests 32
ℹ suites 0
ℹ pass 32
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2580.9216
```

Exit code: `0`.

### 3.3 Earlier final full suite

Recorded during the original Task 7 run after browser verification:

```text
$ npm test
> sslg-office-attendance@1.0.0 test
> node --test

✔ creates the documented Sheet tabs and headers (14.343ms)
✔ generates daily codes and invalidates the previous pair (58.0691ms)
✔ registers a device once and records every valid scan (15.4371ms)
✔ rejects invalid codes without writing attendance (4.6963ms)
✔ filters attendance and exports CSV (9.8896ms)
✔ a late generation response cannot redisplay QR cards for a previous date (69.6341ms)
✔ an older attendance response cannot overwrite a newer search result (5.1352ms)
✔ an older attendance failure cannot resurface an error after a newer search succeeds (3.7474ms)
✔ starting list and export requests hides a recovered office error (5.1281ms)
✔ client script parses as JavaScript (2.7615ms)
✔ landing and student navigation contain no admin link (0.8927ms)
✔ index includes every client asset exactly once (0.437ms)
✔ Apps Script adapter maps every API action to a public server function (1.3116ms)
✔ normalizes a registered name and rejects blank names (5.7612ms)
✔ uses the Manila calendar date across UTC midnight (58.0808ms)
✔ rejects impossible calendar dates (1.3761ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (2.3423ms)
✔ validates matching code, mode, and current Manila date (2.2267ms)
✔ escapes CSV commas, quotes, and newlines (0.5116ms)
✔ manifest uses Manila time and anonymous access (2.776ms)
✔ required Apps Script files exist (5.7612ms)
✔ project contains no hard-coded spreadsheet ID or secret assignment (11.9144ms)
✔ renders all include files without scriptlet placeholders (140.9811ms)
✔ preview supports registration, recognition, and repeated scans (122.9536ms)
✔ preview exports recorded attendance as CSV (44.7691ms)
✔ preview returns a JSON error for malformed request bodies (23.4063ms)
✔ preview scan handlers reject missing device tokens without writing attendance (41.3901ms)
✔ preview scan handlers reject 101-character device tokens without writing attendance (45.5591ms)
✔ preview accepts 100-character device tokens and returns validated scan status fields (22.4063ms)
✔ preview search trims and stringifies queries like the backend (3.7474ms)
✔ IN QR payload decodes exactly (306.018ms)
✔ OUT QR payload decodes exactly (150.9848ms)
ℹ tests 32
ℹ suites 0
ℹ pass 32
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1746.7284
```

Exit code: `0`.

## 4. Preview lifecycle

```text
$ npm run preview
> sslg-office-attendance@1.0.0 preview
> node preview/server.cjs
SSLG attendance preview: http://127.0.0.1:4173
```

The process was started with Bash background execution as task `b15je8567`. The port was not listening before startup. After browser work:

1. Closed the isolated mobile page and desktop page through Playwright MCP.
2. Stopped only background task `b15je8567` (`npm run preview`).
3. Ran `netstat -ano | findstr ':4173' || true`; output was empty, confirming no listener remained on port `4173`.

No unrelated Node or browser process was killed.

## 5. Actual generated QR URLs

The QR URLs were read from `admin.generate` HTTP 200 response bodies through the Playwright network panel. No token was invented.

### Pair A

Generated for `2026-11-24` at `2026-11-24T21:00:50+08:00`.

```text
IN:  http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=IN&code=2a57530d-6f2d-46ca-bfe3-50e98f9ce2f6
OUT: http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=OUT&code=5dbdc492-622a-4ad8-ac90-a1b1ff80194c
```

Both were opened in the mobile context. IN was opened for registration, then reopened after OUT for a repeated IN scan.

### Pair B

Generated for the same date at `2026-11-24T21:24:59+08:00`, invalidating Pair A.

```text
IN:  http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=IN&code=24933dd4-1cd7-4a46-bc83-eb051933d762
OUT: http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=OUT&code=83f09141-6a24-455a-9a82-e91ac0072917
```

Pair A IN was reopened and rejected. Pair B IN was opened for the offline-failure and retry check. Pair B OUT was generated but not opened.

### Pair C

Generated for print verification at `2026-11-24T21:30:15+08:00`.

```text
IN:  http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=IN&code=228d26aa-e77a-40de-bcf5-43aec441efcb
OUT: http://127.0.0.1:4173/?page=scan&date=2026-11-24&mode=OUT&code=0d5fd135-6286-46d6-90b1-1d5d567e3fa5
```

Both URLs were encoded into the printed QR cards. Neither scan URL was opened during this run.

Desktop office URL used throughout:

```text
http://127.0.0.1:4173/?page=admin
```

## 6. Step 3 — desktop office golden path

Viewport: `1440×1000`.

1. Navigated to `http://127.0.0.1:4173/?page=admin`.
2. Attendance date was `2026-11-24`, the current Manila date.
3. Clicked `Generate QR pair`. Confirmation text was exactly:

   ```text
   Generate new IN and OUT codes? The previous pair for this date will stop working.
   ```

4. Accepted the confirmation. `admin.generate` returned HTTP 200 and Pair A.
5. Snapshot showed two QR images:
   - `Check in`, image `Check-in QR code`, `2026-11-24`, `Created 2026-11-24T21:00:50+08:00`
   - `Check out`, image `Check-out QR code`, `2026-11-24`, `Created 2026-11-24T21:00:50+08:00`
6. Empty attendance state:

   ```text
   No scans recorded for this date.
   0 Scans
   0 People
   0 IN
   0 OUT
   ```

7. Typed `No such attendee` in `Search name`. The empty state remained and console inspection reported zero messages/errors/warnings.
8. Clicked `Export CSV` while capturing the browser download event. Offered filename: `SSLG-attendance-2026-11-24.csv`; download failure: `null`.

**Result: PASS.**

## 7. Step 4 — new-user registration at mobile width

Created a fresh isolated Playwright context named `sslg-task7-mobile`, opened Pair A IN, and set viewport to `390×844`.

Initial snapshot showed:

```text
Check in
Record your arrival
2026-11-24 · SSLG Office
Your name
[Enter your full name]
Register and check in
You only need to enter your name once on this phone.
```

There was no admin link. Entered `Ana Cruz` and clicked `Register and check in`.

Success snapshot:

```text
OK
RECORDED
Checked in
Ana Cruz
2026-11-24T21:14:21+08:00 · Philippines time
You may close this page.
```

Network showed `scan.status` and `scan.record` both HTTP 200. Office `admin.list` then returned one row:

```text
2026-11-24T21:14:21+08:00 | Ana Cruz | IN
qr_created_at: 2026-11-24T21:00:50+08:00
```

Office totals:

```text
1 Scans
1 People
1 IN
0 OUT
```

**Result: PASS.**

## 8. Step 5 — returning recognition and repeated scans

### OUT recognition and confirmation

In the same mobile context, opened Pair A OUT. Snapshot:

```text
Check out
Record your departure
2026-11-24 · SSLG Office
Continuing as
Ana Cruz
Confirm check out
```

No name textbox, login, or admin link appeared. Clicked `Confirm check out`.

Success text:

```text
OK
RECORDED
Checked out
Ana Cruz
2026-11-24T21:16:09+08:00 · Philippines time
You may close this page.
```

Office list then had two rows, newest first:

```text
2026-11-24T21:16:09+08:00 | Ana Cruz | OUT
2026-11-24T21:14:21+08:00 | Ana Cruz | IN
```

Totals: `2 Scans`, `1 People`, `1 IN`, `1 OUT`.

### Repeated IN

Reopened Pair A IN in the same mobile context. Snapshot:

```text
Check in
Record your arrival
2026-11-24 · SSLG Office
Continuing as
Ana Cruz
Confirm check in
```

Clicked `Confirm check in`. Success text included:

```text
Checked in
Ana Cruz
2026-11-24T21:23:10+08:00 · Philippines time
```

Office list then had three distinct rows:

```text
2026-11-24T21:23:10+08:00 | Ana Cruz | IN
2026-11-24T21:16:09+08:00 | Ana Cruz | OUT
2026-11-24T21:14:21+08:00 | Ana Cruz | IN
```

Totals: `3 Scans`, `1 People`, `2 IN`, `1 OUT`. A case-insensitive body-text check for an already-open/duplicate-open-session message returned `false`.

**Result: PASS.**

## 9. Step 6 — regeneration invalidation, offline failure, and retry

### Regeneration and previous-code rejection

On the desktop office page, regenerated the pair for `2026-11-24`. Pair B was created at `2026-11-24T21:24:59+08:00`.

Reopened the previous Pair A IN URL in the same mobile context. `scan.status` returned HTTP 200 with:

```json
{"ok":false,"error":"INVALID_CODE"}
```

The mobile page displayed exactly:

```text
This QR code is no longer valid. A newer code may have been generated.
```

No name form or confirmation button appeared. No attendance row was added.

### Genuine browser offline failure

Opened Pair B IN. The same mobile device was recognized:

```text
Continuing as
Ana Cruz
Confirm check in
```

Using Playwright browser-context offline control, set the context offline before clicking confirmation. Observed `navigator.onLine=false`.

Clicked `Confirm check in`. The failed request was:

```text
POST http://127.0.0.1:4173/api/scan.record
[FAILED] net::ERR_INTERNET_DISCONNECTED
```

UI text:

```text
CHECK IN
Record your arrival
2026-11-24 · SSLG Office
Continuing as
Ana Cruz
Confirm check in
The scan was not recorded. Check your connection and try again.
```

Additional checks at failure:

- `Checked in` success heading count: `0`
- Remembered name: `Ana Cruz`
- Retry button enabled: `true`
- Uncaught `pageerror` events: `0`

The console recorded the expected browser resource error:

```text
Failed to load resource: net::ERR_INTERNET_DISCONNECTED
```

This was an intentionally induced network failure, not an uncaught application exception.

### Reconnect and retry

Set the context online; `navigator.onLine=true`. Clicked `Confirm check in` again. Retry request returned HTTP 200.

Success text:

```text
OK
RECORDED
Checked in
Ana Cruz
2026-11-24T21:27:36+08:00 · Philippines time
You may close this page.
```

Office then had exactly four rows:

```text
2026-11-24T21:27:36+08:00 | Ana Cruz | IN | qr_created_at 2026-11-24T21:24:59+08:00
2026-11-24T21:23:10+08:00 | Ana Cruz | IN | qr_created_at 2026-11-24T21:00:50+08:00
2026-11-24T21:16:09+08:00 | Ana Cruz | OUT | qr_created_at 2026-11-24T21:00:50+08:00
2026-11-24T21:14:21+08:00 | Ana Cruz | IN | qr_created_at 2026-11-24T21:00:50+08:00
```

Totals: `4 Scans`, `1 People`, `3 IN`, `1 OUT`.

The invalid-code attempt and failed offline attempt added no rows; the successful retry added exactly one.

**Result: PASS.**

## 10. Search, totals, date filter, and CSV

### Search and totals

- `ana`: three visible rows; totals remained `3 Scans`, `1 People`, `2 IN`, `1 OUT`.
- `nobody`: zero visible rows; empty text `No scans recorded for this date.`; totals remained based on the complete date.
- Cleared search before export.

### CSV after three scans

Download event filename: `SSLG-attendance-2026-11-24.csv`; failure: `null`.

Observed header:

```text
"event_id","date","scanned_at","mode","name","device_token","qr_created_at"
```

The file had three data rows in chronological order: IN at `21:14:21`, OUT at `21:16:09`, IN at `21:23:10`, all for `Ana Cruz` and `2026-11-24`. Device-token values are intentionally redacted from this report.

### Date filter

Changed the office date to `2026-11-23`. `admin.list` returned:

```json
{"scans":0,"people":0,"in":0,"out":0}
```

and zero rows. Export offered `SSLG-attendance-2026-11-23.csv`.

Restored `2026-11-24`; list returned four rows and totals:

```json
{"scans":4,"people":1,"in":3,"out":1}
```

**Result: PASS.**

## 11. Step 7 — print-media verification

After the date-filter check, generated Pair C on the office page for `2026-11-24`. Both cards showed `Created 2026-11-24T21:30:15+08:00`.

Invoked Playwright media emulation with `media=print`; `matchMedia('print').matches` was `true`. The computed-state observations below and the print PASS are **post-fix** evidence for the corrected `Styles.html`; the baseline RED evidence is documented in Section 13.

Post-fix computed print-state evidence:

- Rendered visible element count: `11`.
- Every rendered visible element was `#qr-pair` or one of its two card descendants.
- `#qr-pair`: `display:grid`, `visibility:visible`, `960×405.13px`.
- IN card: `464.88×405.13px`; OUT card: `464.89×405.13px`.
- IN image: natural `336×336`, rendered `272.13×272.13px`, visible.
- OUT image: natural `336×336`, rendered `272.13×272.13px`, visible.
- Header: `display:none`, `visibility:hidden`, `0×0`.
- Footer: `display:none`, `visibility:hidden`, `0×0`.
- Generate and Export buttons: hidden with `0×0` bounds.
- Date/search inputs: hidden with `0×0` bounds.
- Totals and attendance table: hidden with `0×0` bounds.
- Attendance records card: `display:none`, `visibility:hidden`, `0×0`.

Visible card text was limited to:

```text
CHECK IN
2026-11-24
Created 2026-11-24T21:30:15+08:00

CHECK OUT
2026-11-24
Created 2026-11-24T21:30:15+08:00
```

This satisfies the brief's accepted alternative of precise observed text plus computed print-state evidence. Post-fix Chromium PDF `.task7-print-fixed.pdf` contained one page. By contrast, the baseline `.task7-print.pdf` contained two pages with a blank second page. This is not a physical-printer test.

**Result: PASS after the print-layout fix; baseline print output failed the one-page check.**

## 12. Console and network audit

### Desktop

Playwright `browser_console_messages` with `level=info`, `all=true`:

```text
Total messages: 0 (Errors: 0, Warnings: 0)
```

The observed desktop `admin.list`, `admin.generate`, and `admin.export` requests all returned HTTP 200. No failed desktop request appeared.

### Mobile

Normal `scan.status` and `scan.record` calls returned HTTP 200. The deliberate offline `scan.record` was the only failed request:

```text
[FAILED] net::ERR_INTERNET_DISCONNECTED
```

The subsequent retry returned HTTP 200. Mobile console total was one error, exactly the expected offline resource error. The scripted offline/retry interaction recorded zero uncaught `pageerror` events.

No application console logging of device tokens or QR tokens was observed. Device-token values were not copied into either report.

## 13. Defects and fixes

**One print-layout defect was found and fixed.**

### Defect and root cause

Baseline `Styles.html` used `body * { visibility:hidden !important; }` with visible exceptions only for `#qr-pair` and its descendants. `visibility:hidden` preserves layout space, so hidden header, controls, cards, totals, and records could still affect pagination. `#qr-pair` was also `position:absolute; top:0; left:0`, taking the QR cards out of normal document flow rather than allowing the reduced print content to paginate normally.

### RED / before evidence

Chromium print of the baseline office page produced `.task7-print.pdf` with **2 pages**; the **second page was blank**. This failed the requirement that only the two QR cards print cleanly on one page.

### Minimal fix

Only the `@media print` block in `SSLG Attendance App/Styles.html` changed:

1. Added explicit `display:none !important` rules for body children other than `#app`, app cards other than the first card, and first-card children other than `#qr-pair`.
2. Reset the first card's print margin, padding, border, and box shadow.
3. Changed `#qr-pair` from `position:absolute` with `top/left` offsets to `position:static`.

No screen styles, application logic, tests, package files, configuration, dependencies, or product behavior outside printing were changed. The existing suite and browser-generated PDF evidence provided regression verification; no new automated test or feature was added.

### GREEN / after evidence

With the corrected stylesheet, Chromium print produced `.task7-print-fixed.pdf` with **1 page**. Post-fix computed print-state evidence in Section 11 showed only `#qr-pair` and its two card descendants visibly rendered, both QR images visible at `272.13×272.13px`, and header, footer, controls, filters, totals, and attendance content absent.

**Print result: PASS after the fix.** The PASS does not apply to the baseline's two-page/blank-second-page output.

### Scratch-artifact cleanup

`.task7-print.pdf`, `.task7-print-hypothesis.pdf`, and `.task7-print-fixed.pdf` were created and overwritten during Task 7's print experimentation. They were absent from the `before-task-7` snapshot and were removed after recording the evidence above. No baseline/snapshot file or unrelated user file was deleted.

## 14. Ten-row acceptance audit

| # | Acceptance criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | A new phone can scan a valid IN code, enter a name once, and create exactly one Attendance row. | PASS | Fresh `390×844` context registered `Ana Cruz`; office had one IN row and `1/1/1/0` totals. Automated registration tests passed. |
| 2 | The same phone recognizes the saved name on a later scan without asking for a login or name again. | PASS | Same context showed `Continuing as Ana Cruz` for OUT and later IN, with no name form or login. |
| 3 | A valid OUT scan creates an Attendance row with mode `OUT` and the server timestamp. | PASS | OUT success `2026-11-24T21:16:09+08:00`; office row had mode `OUT` and matching timestamp. |
| 4 | Multiple valid scans create multiple rows; no in/out pairing rule blocks them. | PASS | IN → OUT → IN yielded three distinct rows and `3 Scans / 1 People / 2 IN / 1 OUT`; no duplicate-open-session message. |
| 5 | Codes are date-bound in Asia/Manila time and become invalid when regenerated. | PASS | Manila boundary tests passed; browser regeneration invalidated Pair A IN; Pair B row carried Pair B creation time. |
| 6 | Invalid codes and failed requests create no Attendance row and never show false success. | PASS | Invalid code and offline attempt added no rows; offline UI had no success heading; one retry raised total only from three to four. |
| 7 | The office can generate both QR codes, see their creation times, filter records, and export CSV. | PASS | Three pairs generated; creation timestamps visible; search/date filters, totals, and correctly named CSV downloads observed. |
| 8 | The Spreadsheet contains the documented `Daily Codes`, `People`, and `Attendance` tabs and columns. | PENDING | Mock schema tests passed, but the owner's real Spreadsheet was unavailable. **Pending owner deployment.** |
| 9 | The student flow contains no admin link or attendance list. | PASS | Mobile snapshots and DOM checks found zero admin links and zero attendance tables; static tests passed. |
| 10 | Automated tests and local browser checks pass; deployment-specific checks remain explicitly pending until run on the owner's account. | PASS | Initial, earlier final, and fix-round fresh test runs each passed `32/32`; all required local browser checks passed, with print PASS post-fix; owner-environment checks explicitly pending. |

Acceptance summary: **9 PASS, 1 PENDING, 0 FAIL.** Criterion 8 is deliberately not marked PASS because real Sheets evidence is unavailable.

## 15. Pending owner deployment checks

**Status: Pending owner deployment.**

The owner must still perform the real Apps Script/Sheets smoke test:

1. Configure the Spreadsheet ID and `Asia/Manila` timezone in the owner's Apps Script project.
2. Deploy with the intended anyone-with-link access.
3. Generate today's real IN/OUT pair.
4. Scan IN on a phone, register a name, and confirm exactly one real `Attendance` row.
5. Scan OUT on the same phone and confirm remembered name plus a second row.
6. Regenerate and confirm earlier codes are rejected without writes.
7. Confirm the real office list and CSV show the real records.
8. Inspect the real `Daily Codes`, `People`, and `Attendance` tabs and columns.

No claim is made about the owner's Google environment.

## 16. Scope integrity and self-review

### Checklist review

- [x] Step 1: `npm install` and full `npm test`; exact `32/32/0` result captured.
- [x] Step 2: preview started, exact URL observed, and only that process stopped.
- [x] Step 3: desktop golden path, empty totals, search, and CSV download.
- [x] Step 4: fresh mobile registration, Philippines timestamp, and one-row office result.
- [x] Step 5: returning recognition, OUT, repeated IN, and three-row result.
- [x] Step 6: regeneration invalidation, genuine offline failure, retry, console/network review.
- [x] Step 7: baseline print defect reproduced, minimal print CSS fix applied, post-fix computed-state and one-page PDF evidence recorded.
- [x] Step 8: `SSLG Attendance App/VERIFICATION.md` created with date, environment, counts, URLs, checklist, exact text, post-fix print evidence, RED/GREEN defect evidence, pending status, and scope corrections.
- [x] Step 9: all ten acceptance criteria audited with PASS/PENDING/FAIL and evidence.
- [x] Step 10: fresh full `npm test` after documentation corrections and scratch cleanup; app comparison against `before-task-7`; preview cleanup; pending owner checks disclosed.

### File-integrity review

Task 7's app-scope changes are:

- **Modified:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Styles.html` — minimal print-layout fix only.
- **Added:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/VERIFICATION.md` — verification record.
- **Removed after use:** the three session-created app-root scratch PDFs `.task7-print.pdf`, `.task7-print-hypothesis.pdf`, and `.task7-print-fixed.pdf`.
- **Added outside the app:** approved SDD artifact `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-7-report.md`.

The final recursive app-source comparison against `.superpowers/sdd/2026-11-24-sslg-qr-attendance/before-task-7`, excluding `node_modules`, contains only modified `Styles.html` and added `VERIFICATION.md`. The three scratch PDFs were not present in the baseline and no longer exist in the app root. The earlier exact whole-vault file counts and SHA-256 claims were unsupported and are not relied upon; no vault-wide unchanged claim is made.

### Limitations and concerns

- The local preview is in-memory and is not the owner's Apps Script/Sheets environment.
- Mobile verification used Chromium at the required viewport, not a physical phone or native camera.
- Print verification used Chromium print-media emulation, computed styles, and generated PDF page counts, not a physical printer. The print PASS applies only after the stylesheet fix; the baseline remains documented as RED.
- One expected console resource error occurred during the deliberate offline test; it was accompanied by the correct not-recorded UI and zero uncaught page errors.
- The environment notice and shell reported different Node versions; the actual shell version is recorded above and satisfies the engine requirement.
- Real Apps Script/Sheets deployment behavior remains untested and **Pending owner deployment**.

## 17. Final result

- Automated tests: **32 passed, 0 failed** on the initial, earlier final, and fix-round fresh runs.
- Local browser verification: **PASS** at `1440×1000` and `390×844`, including genuine offline failure/retry and post-fix print-media checks.
- Defects/fixes: **one print-layout defect fixed in `Styles.html`; baseline RED was two pages with a blank second page, post-fix GREEN was one page**.
- Real Apps Script/Sheets smoke test: **Pending owner deployment**.
- Commits: **none**.

## 18. Fix round 1

### Finding 1 — print defect and scope were misreported

**Resolved.** Section 1, Section 11, Section 13, Section 16, Section 17, and `VERIFICATION.md` now state that Task 7 found and fixed a print-layout defect in `Styles.html`. The records identify the baseline's visibility-only hiding and absolute `#qr-pair` positioning as the root cause, describe the minimal `display:none`/`position:static` correction, and distinguish **RED / before** (`.task7-print.pdf`: 2 pages, blank second page) from **GREEN / after** (`.task7-print-fixed.pdf`: 1 page). Print PASS is explicitly post-fix. The corrected CSV header remains unchanged.

### Finding 2 — scratch PDFs and unsupported integrity claims

**Resolved.** The three session-created scratch PDFs were confirmed absent from the baseline and present only in the app root; their recorded page-count evidence was retained in the documentation, and only these exact files were removed:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/.task7-print.pdf`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/.task7-print-hypothesis.pdf`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/.task7-print-fixed.pdf`

Each is absent from both the app root and the `before-task-7` snapshot after cleanup. No baseline/snapshot file or unrelated user file was removed. The unsupported exact vault-wide counts and whole-vault unchanged/hash claims were removed from both records. The final app comparison against `before-task-7`, excluding `node_modules`, reports only modified `Styles.html` and added `VERIFICATION.md`.

### Exact fix-round file changes

- **Changed:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/VERIFICATION.md` — corrected defects, post-fix print evidence, fresh test result, and scope/self-review statements.
- **Changed:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-7-report.md` — corrected contradictory sections and appended this fix-round record.
- **Removed:** the three scratch PDFs listed above.
- **Inspected but unchanged in fix round 1:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Styles.html`; the prior minimal print fix remains intact.
- **Overall Task 7 app diff:** only `Styles.html` and `VERIFICATION.md` relative to `before-task-7`.

### Fresh test output

Run from `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App` after the documentation corrections and scratch cleanup:

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

Exit code: `0`. Result: **32 passed, 0 failed, 0 cancelled, 0 skipped, 0 todo**.

### Remaining limitations

- Fix round 1 did not rerun browser interactions or regenerate PDFs; it retained the earlier Chromium RED/GREEN evidence and left the verified stylesheet fix unchanged.
- Print evidence is local Chromium print emulation and PDF pagination, not a physical-printer test. The scratch PDF binaries were intentionally removed after their evidence was documented.
- Mobile evidence remains an isolated Chromium context at `390×844`, not a physical phone or native-camera scan.
- Real Google Apps Script/Sheets behavior remains untested and **Pending owner deployment**.
- No Git commands, commits, credentials, dependencies, features, or subagents were used in this fix round.
