# SSLG QR Office Attendance Design

**Date:** 2026-11-24  
**Amended:** 2026-11-25 — permanent reusable QR pair approved in chat  
**Status:** Approved; permanent-pair amendment implemented and locally verified  
**Workspace:** SSLG MEMOS

## Purpose

Build a phone-friendly SSLG office attendance web app connected to a Google Spreadsheet. The office creates one permanent IN QR code and one permanent OUT QR code, then reuses the same codes every day. Each scan records the server's current Asia/Manila date and timestamp in the shared Sheet. A person registers with a name once on a phone; later scans on that same phone/browser recognize the saved name without a login.

## Current State

- The workspace contains an unrelated school scheduler application, but no reusable QR attendance flow.
- The SSLG vault and its document tooling remain separate and unchanged.
- The new app will live in its own project directory.

## Requirements

1. Daily office attendance is the first release scope; named event sessions are out of scope.
2. The office can show a printable permanent IN code and OUT code. The first request creates them; later requests return the identical pair.
3. The same codes are valid every day and do not expire. Each accepted scan is dated by the server's current Asia/Manila calendar date.
4. The app provides no regeneration, rotation, reset, or replacement option.
5. Every valid scan is recorded as a separate row. Repeated IN scans and OUT scans without a matching IN are allowed.
6. First-time registration asks only for a name.
7. A random, unguessable device token stored in the browser recognizes a returning user on the same phone/browser.
8. The app does not collect or infer a phone number.
9. The office page is not password-protected and is not linked from the student flow. Anyone with its direct URL can access it.
10. The Google Spreadsheet is the source of truth.
11. No student login, SMS verification, camera permission inside the app, event sessions, or attendance corrections interface is included in this release.

## Architecture

Use a single Google Apps Script web application:

- **Apps Script backend:** validates requests and codes, creates device profiles, records scans, reads attendance, exports CSV, and serves HTML.
- **Google Spreadsheet:** stores one permanent QR pair, recognized devices, and daily attendance events.
- **Browser client:** renders the student registration/confirmation flow and the office dashboard.
- **QR generator:** a locally bundled JavaScript library renders QR codes in the office page. Scanning uses the phone's native camera, which opens the deployed web-app URL.
- **LockService:** serializes Sheet writes to reduce lost updates during simultaneous scans.

The app requires one Apps Script deployment and one Spreadsheet. There is no separate backend host, database server, API key, or paid service.

## Spreadsheet Schema

### `QR Codes`

| Column | Meaning |
| --- | --- |
| `in_code` | Permanent unguessable IN token |
| `out_code` | Permanent unguessable OUT token |
| `created_at` | Server timestamp when the permanent pair was first created |
| `created_by` | Fixed label `SSLG Office`; no personal identity is collected |

Exactly one row exists. Showing the pair again never changes its codes or creation timestamp.

### `People`

| Column | Meaning |
| --- | --- |
| `device_token` | Unguessable browser token; primary recognition key |
| `name` | Registered display name |
| `first_seen_at` | Server timestamp of first registration |
| `last_seen_at` | Server timestamp of most recent recognized visit |

No phone number, email, grade, section, or device fingerprint is stored.

### `Attendance`

| Column | Meaning |
| --- | --- |
| `event_id` | Unique event identifier |
| `date` | Local date of the scan |
| `scanned_at` | Server timestamp of the scan |
| `mode` | `IN` or `OUT` |
| `name` | Name snapshot at scan time |
| `device_token` | Token linking the scan to the recognized phone |
| `qr_created_at` | Creation timestamp of the code used for the scan |

Every accepted request appends exactly one row. The Sheet may be edited manually outside the app, but the app provides no editing interface.

## Student Flow

1. A student scans an office QR code with the native phone camera.
2. The browser opens the deployed app with `page=scan`, mode, and code parameters. The QR URL contains no date.
3. The backend checks that the permanent code exists and matches the mode. A caller-supplied date is ignored; the server clock determines the attendance date.
4. The browser reads its device token from local storage and asks the backend for a matching profile.
5. If no profile exists, the browser shows a name-only registration form.
6. If a profile exists, the browser shows the remembered name and a confirmation button labeled for the scanned mode.
7. On confirmation, the browser sends the device token, name when registering, and QR parameters to the backend.
8. The backend validates again, records the scan with a server timestamp, and returns a success screen with the exact local time.
9. A success screen tells the student the record was saved. It does not imply that an attendance correction or approval occurred.

A returning user does not log in, but still confirms the scan to avoid recording an accidental page open.

## Office Flow

The office opens the direct admin URL (`?page=admin`), which is omitted from student navigation and QR payloads.

The office page provides:

- date selection for attendance records only;
- one-time creation and repeated display of the same permanent IN and OUT codes;
- visible original code creation time;
- printable QR cards;
- scan totals for the selected date;
- a searchable attendance list with date, time, name, and mode;
- CSV export for the selected date.

Showing the permanent pair is idempotent. Changing the attendance-date filter does not clear, hide, regenerate, or date-bind the QR cards. There is no replacement confirmation or reset control.

## Time and QR Rules

- Script timezone is set to `Asia/Manila`.
- Each scan's attendance date and exact timestamp come from one server instant in Asia/Manila time, not the phone's clock.
- The QR payload contains the deployed app URL plus a mode and permanent random code, with no date.
- The code is an attendance identifier, not an authentication secret for the public admin page.
- The same code is accepted on every Manila calendar date.
- A malformed, unknown, or wrong-mode code is rejected without a People or Attendance data write.

## Error Handling

- **Invalid or wrong-mode code:** show a clear explanation and direct the student to the posted permanent codes; do not offer registration.
- **Blank name:** keep the user on the form and show an inline validation message.
- **Network failure:** show that the scan was not recorded and allow retry.
- **Sheet write failure:** do not show success; preserve the entered name and allow retry.
- **Concurrent submissions:** use LockService around read/validate/write operations.
- **Repeated taps:** disable the active submit button while a request is in flight; subsequent intentional scans remain allowed.
- **Missing Spreadsheet configuration:** admin setup screen explains which Script Property must be set.

## Privacy and Security

- Only a name, random device token, and attendance timestamps are stored.
- Device tokens and QR codes are generated with cryptographically strong random values available in Apps Script.
- The app must not log device tokens or QR codes to the console.
- The public admin page is an explicit user-selected limitation. Its direct URL is not a security boundary. The student interface does not display the attendance list or admin link.
- Deployment access is set to anyone with the web-app URL because students scan from personal phones.
- No secrets are committed to the project. The Spreadsheet ID is stored in Apps Script Script Properties.

## Testing

### Automated

- Unit-test permanent-pair creation, idempotency, date-free validation across Manila dates, one-instant scan timestamps, and malformed/unknown/wrong-mode parameters.
- Unit-test first registration, returning-device recognition, and one-row-per-valid-scan behavior using a Sheet mock.
- Verify required Sheet headers and schema creation.
- Generate an IN and OUT QR image and decode them in a test to confirm the payload is readable and correct.
- Check that CSV output escapes names correctly.

### Browser

Use a local preview with a mocked Apps Script API to verify:

- new-user registration and success;
- returning-user confirmation;
- repeated scans;
- invalid/wrong-mode code messages;
- permanent-pair display, repeated-show identity, date-filter independence, and print layout;
- date filter, search, totals, and CSV download;
- mobile and desktop layouts with no console errors.

### Deployment Smoke Test

After the owner deploys the script, verify against the real web-app URL:

1. Configure the Spreadsheet ID and timezone.
2. Deploy as the owner with access set to anyone with the link.
3. Show the permanent pair once and confirm repeated display returns the same codes and creation timestamp.
4. Scan IN on one phone, register a name, and confirm one Attendance row.
5. Scan OUT on the same phone and confirm the remembered name plus a second row.
6. Confirm unknown and wrong-mode codes create no rows.
7. Confirm the office list and CSV show both real records.
8. Inspect the single `QR Codes` row and its four columns.
9. On a later day, reuse the exact same links and confirm new rows carry that later Manila date.

A live deployment cannot be claimed until this smoke test passes.

## Deployment Deliverables

The implementation will provide:

- an isolated project directory;
- `appsscript.json`, backend source, HTML/CSS/JavaScript client, and bundled QR library;
- a local preview/test harness;
- setup and deployment instructions;
- a blank-Sheet schema initializer.

The user must create or select the Google Spreadsheet and authorize the Apps Script deployment. The project will not embed credentials or require a paid service.

## Acceptance Criteria

1. A new phone can scan a valid IN code, enter a name once, and create exactly one Attendance row.
2. The same phone recognizes the saved name on a later scan without asking for a login or name again.
3. A valid OUT scan creates an Attendance row with mode `OUT` and the server timestamp.
4. Multiple valid scans create multiple rows; no in/out pairing rule blocks them.
5. One date-free IN/OUT pair is reused every day; each scan receives the current Asia/Manila server date and no regeneration/reset exists.
6. Invalid codes and failed requests create no Attendance row and never show false success.
7. The office can create/show the same permanent QR pair, see its original creation time, filter daily records, and export CSV.
8. The Spreadsheet contains the documented `QR Codes`, `People`, and `Attendance` tabs and columns, with exactly one permanent-pair row.
9. The student flow contains no admin link or attendance list.
10. Automated tests and local browser checks pass; deployment-specific checks remain explicitly pending until run on the owner's account.

## Out of Scope

- Event-specific sessions;
- SMS or phone-number verification;
- Cross-device account recognition;
- Student accounts and passwords;
- Private admin authentication;
- GPS or physical-presence verification;
- Attendance editing, approval, or disciplinary actions;
- Native Android/iOS applications;
- Automatic printing or scheduled code generation.
