# Task 6 Report: Apps Script Manifest, Setup Guide, and Packaging Checks

**Status:** COMPLETE

**Working directory:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

## Summary

Added the Apps Script manifest, exact owner setup/deployment guide, and packaging tests. Captured the required RED failure before creating the manifest and guide, then verified focused packaging tests and the complete automated suite are GREEN. No live deployment was created or claimed.

## Files Changed

Created:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/appsscript.json`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/SETUP.md`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/packaging.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-6-report.md`

Verified without modification:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/package.json` already uses `"test": "node --test"`.
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/package-lock.json` exists; `npm install` reported dependencies up to date.

No Git commands or commits were run.

## RED: Packaging Test Before Manifest and Guide

Created `tests/packaging.test.cjs` first, then ran:

```bash
node --test tests/packaging.test.cjs
```

Output (summary and failure reasons; stack frames omitted):

```text
✖ manifest uses Manila time and anonymous access
✖ required Apps Script files exist
✔ project contains no hard-coded spreadsheet ID or secret assignment
ℹ tests 3
ℹ suites 0
ℹ pass 1
ℹ fail 2
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1215.3345

✖ failing tests:

test at tests\packaging.test.cjs:8:1
✖ manifest uses Manila time and anonymous access
  Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\appsscript.json'

test at tests\packaging.test.cjs:16:1
✖ required Apps Script files exist
  AssertionError [ERR_ASSERTION]: appsscript.json
  false !== true
```

The failure was expected: both required artifacts were absent. The existing secret-assignment packaging check passed.

## Dependency and Lockfile Verification

Ran:

```bash
npm install
```

Output:

```text
up to date, audited 4 packages in 18s

found 0 vulnerabilities
```

Confirmed `package-lock.json` exists after the command.

## GREEN: Packaging Test After Manifest and Guide

Ran:

```bash
node --test tests/packaging.test.cjs
```

Output:

```text
✔ manifest uses Manila time and anonymous access (3.8043ms)
✔ required Apps Script files exist (16.2655ms)
✔ project contains no hard-coded spreadsheet ID or secret assignment (4.0325ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 637.5939
```

## GREEN: Full Automated Test Suite

Ran:

```bash
npm test
```

Output:

```text
> sslg-office-attendance@1.0.0 test
> node --test

✔ creates the documented Sheet tabs and headers (16.1155ms)
✔ generates daily codes and invalidates the previous pair (84.2434ms)
✔ registers a device once and records every valid scan (17.8038ms)
✔ rejects invalid codes without writing attendance (10.9783ms)
✔ filters attendance and exports CSV (9.9145ms)
✔ a late generation response cannot redisplay QR cards for a previous date (118.882ms)
✔ an older attendance response cannot overwrite a newer search result (6.6453ms)
✔ an older attendance failure cannot resurface an error after a newer search succeeds (10.6089ms)
✔ starting list and export requests hides a recovered office error (10.0743ms)
✔ client script parses as JavaScript (14.0094ms)
✔ landing and student navigation contain no admin link (1.3132ms)
✔ index includes every client asset exactly once (0.7137ms)
✔ Apps Script adapter maps every API action to a public server function (2.1575ms)
✔ normalizes a registered name and rejects blank names (8.2698ms)
✔ uses the Manila calendar date across UTC midnight (65.0903ms)
✔ rejects impossible calendar dates (2.2111ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (4.5017ms)
✔ validates matching code, mode, and current Manila date (5.6647ms)
✔ escapes CSV commas, quotes, and newlines (0.8762ms)
✔ manifest uses Manila time and anonymous access (3.9866ms)
✔ required Apps Script files exist (10.0377ms)
✔ project contains no hard-coded spreadsheet ID or secret assignment (5.1653ms)
✔ renders all include files without scriptlet placeholders (270.2025ms)
✔ preview supports registration, recognition, and repeated scans (445.5156ms)
✔ preview exports recorded attendance as CSV (133.1944ms)
✔ preview returns a JSON error for malformed request bodies (100.6484ms)
✔ preview scan handlers reject missing device tokens without writing attendance (58.6498ms)
✔ preview scan handlers reject 101-character device tokens without writing attendance (53.8459ms)
✔ preview accepts 100-character device tokens and returns validated scan status fields (61.9883ms)
✔ preview search trims and stringifies queries like the backend (68.4659ms)
✔ IN QR payload decodes exactly (412.913ms)
✔ OUT QR payload decodes exactly (532.6513ms)
ℹ tests 32
ℹ suites 0
ℹ pass 32
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3542.6451
```

## Self-Review

### Manifest and deployment accuracy

- Manifest matches the brief exactly: `Asia/Manila`, empty dependencies, `USER_DEPLOYING`, `ANYONE_ANONYMOUS`, `STACKDRIVER`, `V8`, and the single Spreadsheet OAuth scope.
- There are no external API scopes.
- Guide instructs the owner to create `SSLG Office Attendance`, copy only the ID between `/d/` and `/edit`, open `Extensions → Apps Script`, add all six source files, and replace the generated manifest through Project Settings.
- Guide instructs the owner to save `SPREADSHEET_ID` as a Script Property and deploy a new Web app as the deploying user with `Anyone` access.
- Guide explains appending `?page=admin` to the deployed `/exec` URL, generating today's QR pair, performing the same-phone IN/OUT scan test, checking the Sheet/office list, daily QR replacement, CSV export, and required troubleshooting cases.
- The guide contains the exact statement: “A live deployment is not verified until the owner completes the scan test in this guide.”
- No deployment was performed, no live URL was recorded, and no deployment-success claim was made.

### Public-admin warning and data disclosure

- Setup prominently states that the admin page has no password and anyone with its direct URL can view names and timestamps.
- Guide accurately describes storage as names, random browser tokens, daily QR tokens, and timestamps, with no phone numbers.

### Secrets and identifiers

- Automated packaging assertions pass for hard-coded Spreadsheet ID and secret-assignment patterns in `Core.gs`, `Code.gs`, `Client.html`, and `preview/server.cjs`.
- Manual project searches found no real Spreadsheet ID, credential, password, API key, private key, OAuth client secret, service-account JSON, bearer token, or live deployment URL.
- Search matches were reviewed: the only credential-like source match is the packaging test's negative-match regex; test values such as `in-token`, `device-a`, `preview-device`, and `https://script.test/...` are explicit synthetic fixtures. Package hashes, dependency registry URLs, vendored library comments, and the required Google Sheets scope are not secrets.
- The guide never requests a service-account JSON file or any credentials. The actual Sheet ID is supplied by the owner through Script Properties at deployment time.

## Concerns

- The admin endpoint is intentionally public and unauthenticated; anyone who obtains its direct URL can view names and timestamps. This is disclosed in `SETUP.md`.
- A real Google Sheet, Apps Script authorization, Web app deployment, and same-phone scan test remain owner actions. Automated tests validate packaging and local behavior only; they do not verify a live deployment.
- OAuth consent and deployment access may still require the deploying Google account and the owner's Google Workspace policy to permit anonymous Web app access.
