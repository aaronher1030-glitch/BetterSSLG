# Task 2 Report: Google Sheets Backend and Daily Code Lifecycle

## Status

PASS — backend implementation and focused tests are complete. No commits were created.

## Scope and files changed

Created:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Code.gs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/backend.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-2-report.md`

Task 1's `Core.gs`, interfaces, constants, and helpers were consumed unchanged. No other application files were modified.

## TDD evidence

### RED — tests written before implementation

Working directory:

```text
C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App
```

Command:

```bash
node --test tests/backend.test.cjs
```

Exit code: `1` (expected). The five tests failed because `Code.gs` did not yet exist, which is the brief's required RED condition.

Exact output:

```text
✖ creates the documented Sheet tabs and headers (9.3921ms)
✖ generates daily codes and invalidates the previous pair (7.7884ms)
✖ registers a device once and records every valid scan (4.5711ms)
✖ rejects invalid codes without writing attendance (4.6031ms)
✖ filters attendance and exports CSV (6.8057ms)
ℹ tests 5
ℹ suites 0
ℹ pass 0
ℹ fail 5
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1232.4504

✖ failing tests:

test at tests\backend.test.cjs:65:1
✖ creates the documented Sheet tabs and headers (9.3921ms)
  Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\Code.gs'
      at Object.readFileSync (node:fs:624:20)
      at loadBackend (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:52:22)
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:66:19)
      at Test.runInAsyncScope (node:async_hooks:226:9)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
  generatedMessage: false
  code: 'ENOENT'
  errno: -4058
  syscall: 'open'
  path: 'C:\\Users\\Ma Christine\\Downloads\\SSLG MEMOS\\SSLG Attendance App\\Code.gs'

test at tests\backend.test.cjs:73:1
✖ generates daily codes and invalidates the previous pair (7.7884ms)
  Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\Code.gs'
      at Object.readFileSync (node:fs:624:20)
      at loadBackend (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:52:22)
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:74:19)
      at Test.runInAsyncScope (node:async_hooks:226:9)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
  generatedMessage: false
  code: 'ENOENT'
  errno: -4058
  syscall: 'open'
  path: 'C:\\Users\\Ma Christine\\Downloads\\SSLG MEMOS\\SSLG Attendance App\\Code.gs'

test at tests\backend.test.cjs:84:1
✖ registers a device once and records every valid scan (4.5711ms)
  Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\Code.gs'
      at Object.readFileSync (node:fs:624:20)
      at loadBackend (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:52:22)
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:85:19)
      at Test.runInAsyncScope (node:async_hooks:226:9)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
  generatedMessage: false
  code: 'ENOENT'
  errno: -4058
  syscall: 'open'
  path: 'C:\\Users\\Ma Christine\\Downloads\\SSLG MEMOS\\SSLG Attendance App\\Code.gs'

test at tests\backend.test.cjs:110:1
✖ rejects invalid codes without writing attendance (4.6031ms)
  Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\Code.gs'
      at Object.readFileSync (node:fs:624:20)
      at loadBackend (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:52:22)
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:111:19)
      at Test.runInAsyncScope (node:async_hooks:226:9)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
  generatedMessage: false
  code: 'ENOENT'
  errno: -4058
  syscall: 'open'
  path: 'C:\\Users\\Ma Christine\\Downloads\\SSLG MEMOS\\SSLG Attendance App\\Code.gs'

test at tests\backend.test.cjs:121:1
✖ filters attendance and exports CSV (6.8057ms)
  Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\Code.gs'
      at Object.readFileSync (node:fs:624:20)
      at loadBackend (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:52:22)
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:122:19)
      at Test.runInAsyncScope (node:async_hooks:226:9)
      at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
  generatedMessage: false
  code: 'ENOENT'
  errno: -4058
  syscall: 'open'
  path: 'C:\\Users\\Ma Christine\\Downloads\\SSLG MEMOS\\SSLG Attendance App\\Code.gs'
```

### Test-harness correction during first GREEN attempt

The supplied schema assertion referenced `backend.context.DAILY_CODE_HEADERS` and the other top-level `const` arrays. In Node's VM, top-level lexical `const` declarations are available to scripts in the context but are not properties of `backend.context`, so the expected side was `undefined`. Replacing those references with independent literal header arrays exposed a second harness issue: `assert.deepStrictEqual` distinguishes arrays created in different VM realms even when their contents match.

The test-only correction used independent literal expectations and `Array.from(...)` to compare observable header contents in the test realm. Production code was not changed for either harness issue. This also follows the test-quality requirement to derive expectations independently rather than mirroring the production constants.

Intermediate command and result after implementation:

```bash
node --test tests/backend.test.cjs
```

```text
✖ creates the documented Sheet tabs and headers (23.6831ms)
✔ generates daily codes and invalidates the previous pair (174.0747ms)
✔ registers a device once and records every valid scan (39.4679ms)
✔ rejects invalid codes without writing attendance (13.5618ms)
✔ filters attendance and exports CSV (17.6669ms)
ℹ tests 5
ℹ suites 0
ℹ pass 4
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1407.8646

✖ creates the documented Sheet tabs and headers (23.6831ms)
  AssertionError [ERR_ASSERTION]: Values have same structure but are not reference-equal
```

### GREEN — focused core tests

Command:

```bash
npm run test:core
```

Exit code: `0`.

Exact output:

```text
> sslg-office-attendance@1.0.0 test:core
> node --test tests/core.test.cjs

✔ normalizes a registered name and rejects blank names (4.8397ms)
✔ uses the Manila calendar date across UTC midnight (30.915ms)
✔ rejects impossible calendar dates (3.4771ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (1.6824ms)
✔ validates matching code, mode, and current Manila date (1.1602ms)
✔ escapes CSV commas, quotes, and newlines (0.347ms)
ℹ tests 6
ℹ suites 0
ℹ pass 6
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 295.9091
```

### GREEN — focused backend tests

Command:

```bash
node --test tests/backend.test.cjs
```

Exit code: `0`.

Exact output:

```text
✔ creates the documented Sheet tabs and headers (8.0717ms)
✔ generates daily codes and invalidates the previous pair (34.1491ms)
✔ registers a device once and records every valid scan (5.0265ms)
✔ rejects invalid codes without writing attendance (3.4268ms)
✔ filters attendance and exports CSV (8.2716ms)
ℹ tests 5
ℹ suites 0
ℹ pass 5
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 272.9151
```

### Final combined verification

Command:

```bash
npm run test:core && node --test tests/backend.test.cjs
```

Exit code: `0`. All 11 focused tests passed with no failures, errors, or skipped tests.

## Implementation summary

- Added configuration lookup requiring the `SPREADSHEET_ID` script property.
- Added idempotent creation of `Daily Codes`, `People`, and `Attendance` tabs with the exact Task 1 headers and frozen header rows.
- Added schema-to-object row conversion and daily-code lookup.
- Added locked daily-code generation. Regeneration updates the single row for that date, replacing both tokens and invalidating the previous pair. Returned URLs include the web app URL, date, mode, and encoded code.
- Added device-token profile lookup and upsert. A registered device's normalized name is retained; `first_seen_at` is preserved and `last_seen_at` is refreshed.
- Added scan status and scan recording. Validation precedes person or attendance writes. Every valid scan appends exactly one attendance event, including repeated IN scans and OUT scans without a preceding IN.
- Added filtered, reverse-chronological attendance listing with totals for IN, OUT, unique devices, and total scans. Totals are calculated from all attendance for the date, not only filtered rows.
- Added CSV export using the shared Task 1 escaping helper and the `SSLG-attendance-<date>.csv` filename.
- Added JSON POST routing for all five specified actions, error responses, all five public `google.script.run` wrappers, and GET routing to the `Index` template.
- Used the unchanged `Core.gs` Manila date/timestamp helpers and `Asia/Manila` timezone constant.

## Self-review

- Console logging: none found in `Code.gs`.
- Credentials/secrets: none stored or logged. The only configuration input is the spreadsheet ID supplied through `PropertiesService`.
- Phone-number/contact fields: none present.
- IN/OUT pairing or sequencing rules: none present. The only scan rules are current Manila date, mode, and matching active daily token.
- Writes before code validation: schema initialization may create missing tabs/headers, but no person or attendance write occurs until `validateScan_` succeeds. The invalid-code test confirms attendance remains header-only.
- Regeneration behavior: the existing date row is updated in place under the script lock; the test confirms old IN invalidation, new OUT acceptance, and exactly one `Daily Codes` data row.
- Repeated scans: the test confirms IN, OUT, and another IN each produce a successful event while the device remains one People data row.
- Timezone: application date boundaries and stored timestamps use the unchanged Task 1 `Asia/Manila` helpers.
- Interface check: all required backend functions and public wrappers are present; Task 1 files were not modified.

## Concerns and deployment notes

- The in-memory backend tests exercise Apps Script service boundaries, not a live Google Sheet. Live deployment still requires a configured spreadsheet ID and appropriate Apps Script permissions/scopes.
- `Index` is referenced by `doGet` as required, but the frontend template is outside Task 2's allowed file scope and remains a later integration dependency.
- No `appsscript.json` exists in the scaffold, and creating or modifying it was outside the allowed Task 2 paths. The code enforces `Asia/Manila` through `Core.gs`; the deployed Apps Script project's own timezone setting must also be configured as `Asia/Manila`.
- The brief's backend test set does not explicitly cover lock contention, malformed JSON, every public wrapper, or `doGet`; those paths were implemented exactly as specified but remain integration-test opportunities.
