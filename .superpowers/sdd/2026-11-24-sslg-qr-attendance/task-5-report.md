# Task 5 Report: Local Preview Server and API Integration Tests

**Status:** Complete  
**Working directory:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`  
**Commits:** None

## Summary

Implemented a Node-only local preview server that renders the real app includes, loads the real `Core.gs` helpers in a VM, and supports all five dotted client API actions with in-memory state. Added the two brief-specified integration tests plus one regression test for CSV export. Focused preview tests and the full suite pass, and the admin page was verified in Playwright with generated QR images and the empty attendance state visible.

## Files Changed

- Created `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/preview/server.cjs`
- Created `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/preview.test.cjs`
- Created `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-5-report.md`
- `package.json` was not modified because it already contained the required script: `"preview": "node preview/server.cjs"`.
- No other app files were changed. No Git commands or commits were used.

## Implementation Details

- Uses only Node built-ins: `node:http`, `node:fs`, `node:path`, `node:vm`, and `node:crypto`.
- Loads `Core.gs` into a fresh VM context for each `createPreviewServer()` call.
- Reuses `createDailyCodeRecord_`, `validateScan_`, `normalizeName_`, `manilaTimestamp_`, `ATTENDANCE_HEADERS`, and `toCsv_`.
- Renders `Index.html` by replacing the `Styles`, `QRCodeLib`, and `Client` scriptlets with the real include files.
- Uses replacement callbacks so JavaScript replacement tokens in the vendored QR library are inserted literally.
- Exposes the VM's lexical `ATTENDANCE_HEADERS` constant on the context for CSV export.
- Keeps codes, people, and attendance in per-server in-memory maps/arrays; no disk or Sheet persistence is used.
- Supports `GET /` and admin/scan query URLs, plus `POST /api/admin.generate`, `scan.status`, `scan.record`, `admin.list`, and `admin.export`.
- Returns `UNKNOWN_ACTION` for unknown API actions and `NOT_FOUND` for unsupported routes.
- Uses `PREVIEW_PUBLIC_URL` for generated QR URLs and `PORT` for standalone startup, with the brief's defaults.
- Requires no Google credentials and makes no external network calls.

## TDD Evidence

### 1. Expected initial RED

The brief-specified tests were written before `preview/server.cjs` existed.

Command:

```bash
node --test tests/preview.test.cjs
```

Output:

```text
node:internal/modules/cjs/loader:1607
  throw err;
  ^

Error: Cannot find module '../preview/server.cjs'
Require stack:
- C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs
    at Module._resolveFilename (node:internal/modules/cjs/loader:1607:15)
    at wrapResolveFilename (node:internal/modules/cjs/loader:1606:10)
    at Module._compile (node:internal/modules/cjs/loader:1644:14)
    at Object.Module._extensions..js (node:internal/modules/cjs/loader:1755:10)
    at Module.load (node:internal/modules/cjs/loader:1818:32)
    at Function._load (node:internal/modules/cjs/loader:1375:27)
    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/cjs/loader:1673:12)
    at node:internal/main/run_main_module:1809:13)

Node.js v26.13.1
✖ tests\preview.test.cjs (1777.5532ms)
ℹ tests 1
ℹ suites 0
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1834.5827

✖ failing tests:

test at tests\preview.test.cjs:1:1
✖ tests\preview.test.cjs (1777.5532ms)
  'test failed'
```

### 2. Renderer regression found during implementation

The first implementation passed the API flow test but left a `Client` scriptlet in the rendered HTML. Root cause: `QRCodeLib.html` contains the literal sequence `$'`, which `String.replace` interpreted as a replacement token when the library was passed as a replacement string. The include replacements were changed to callback functions.

Command:

```bash
node --test tests/preview.test.cjs
```

Failure excerpt (the assertion printed the full rendered HTML, omitted here):

```text
✖ renders all include files without scriptlet placeholders (503.4813ms)
✔ preview supports registration, recognition, and repeated scans (1753.849ms)
ℹ tests 2
ℹ suites 0
ℹ pass 1
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4727.3858

✖ failing tests:

test at tests\preview.test.cjs:19:1
✖ renders all include files without scriptlet placeholders (503.4813ms)
  AssertionError [ERR_ASSERTION]: The input was expected to not match the regular expression /include\(/.
```

### 3. CSV export regression RED

Self-review found that `admin.export` returned `{"ok":false,"error":"Cannot read properties of undefined (reading 'map')"}`. Root cause: `ATTENDANCE_HEADERS` is a top-level `const` in `Core.gs`, so it is a lexical VM binding rather than a property on the context object. A focused export integration test was added before the fix.

Command:

```bash
node --test tests/preview.test.cjs
```

Output:

```text
✔ renders all include files without scriptlet placeholders (226.3924ms)
✔ preview supports registration, recognition, and repeated scans (235.7794ms)
✖ preview exports recorded attendance as CSV (84.7677ms)
ℹ tests 3
ℹ suites 0
ℹ pass 2
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1347.0596

✖ failing tests:

test at tests\preview.test.cjs:55:1
✖ preview exports recorded attendance as CSV (84.7677ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:

  false !== true

      at C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:66:12
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
      at Test.run (node:internal/test_runner/test:1217:16)
      at Test.run (node:internal/test_runner/test:1163:13)
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
  generatedMessage: true
  code: 'ERR_ASSERTION',
  actual: false,
  expected: true,
  operator: 'strictEqual',
```

The fix reads `ATTENDANCE_HEADERS` from the VM and assigns that array to `context.ATTENDANCE_HEADERS`.

### 4. Final focused GREEN

Command:

```bash
node --test tests/preview.test.cjs
```

Output:

```text
✔ renders all include files without scriptlet placeholders (700.1974ms)
✔ preview supports registration, recognition, and repeated scans (405.9078ms)
✔ preview exports recorded attendance as CSV (164.6629ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2289.6466
```

Final syntax command:

```bash
node --check preview/server.cjs && node --check tests/preview.test.cjs
```

The syntax checks produced no output and exited successfully.

## Full Test Suite

Command:

```bash
npm test
```

Output:

```text
> sslg-office-attendance@1.0.0 test
> node --test

✔ creates the documented Sheet tabs and headers (30.3551ms)
✔ generates daily codes and invalidates the previous pair (160.9079ms)
✔ registers a device once and records every valid scan (38.8766ms)
✔ rejects invalid codes without writing attendance (17.9267ms)
✔ filters attendance and exports CSV (19.5366ms)
✔ a late generation response cannot redisplay QR cards for a previous date (211.4361ms)
✔ an older attendance response cannot overwrite a newer search result (20.0314ms)
✔ an older attendance failure cannot resurface an error after a newer search succeeds (16.0143ms)
✔ starting list and export requests hides a recovered office error (13.3781ms)
✔ client script parses as JavaScript (19.6297ms)
✔ landing and student navigation contain no admin link (1.5499ms)
✔ index includes every client asset exactly once (1.2916ms)
✔ Apps Script adapter maps every API action to a public server function (7.5079ms)
✔ normalizes a registered name and rejects blank names (4.6469ms)
✔ uses the Manila calendar date across UTC midnight (171.4793ms)
✔ rejects impossible calendar dates (8.712ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (3.4024ms)
✔ validates matching code, mode, and current Manila date (20.6573ms)
✔ escapes CSV commas, quotes, and newlines (11.3383ms)
✔ renders all include files without scriptlet placeholders (602.6957ms)
✔ preview supports registration, recognition, and repeated scans (322.0097ms)
✔ preview exports recorded attendance as CSV (64.0642ms)
✔ IN QR payload decodes exactly (570.3676ms)
✔ OUT QR payload decodes exactly (332.7811ms)
ℹ tests 24
ℹ suites 0
ℹ pass 24
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3472.471
```

## State Reset and Export Verification

A separate real-HTTP check generated codes, recorded one scan, exported CSV, closed the server, and created a new server for the same date.

Command shape:

```bash
node <<'NODE'
// Real HTTP integration check using createPreviewServer(), fetch(), and two server lifecycles.
NODE
```

Output:

```json
{"beforeRestartScans":1,"afterRestartScans":0,"export":"PASS"}
```

This confirms that attendance is not shared between server instances and that restarting the preview clears state.

## Browser Verification

Started the final server with:

```bash
npm run preview
```

Startup output:

```text
> sslg-office-attendance@1.0.0 preview
> node preview/server.cjs

SSLG attendance preview: http://127.0.0.1:4173
```

Used Playwright against `http://127.0.0.1:4173/?page=admin`. The check loaded the page, confirmed the empty-table message, accepted the generation confirmation, clicked **Generate QR pair**, and inspected both generated images.

Result:

```json
{"title":"SSLG Office Attendance","initialEmpty":true,"emptyAfterGeneration":true,"qrImages":[{"alt":"Check-in QR code","loaded":true,"width":336},{"alt":"Check-out QR code","loaded":true,"width":336}],"totals":"0\nScans\n0\nPeople\n0\nIN\n0\nOUT","errors":[]}
```

The final preview server remains running at `http://127.0.0.1:4173/` for Task 7 browser checks.

## Self-Review

- **Real helpers:** Preview validation, code generation, name normalization, Manila timestamps, and CSV formatting all call the real `Core.gs` implementations.
- **Client/API contract:** All five dotted actions used by `Client.html` are implemented, including CSV export, with the expected JSON envelopes.
- **Rendering:** All three include files are inserted, and the integration test confirms no `include(` scriptlet remains.
- **State:** Codes, people, and attendance live only in memory. The two-lifecycle check confirmed `1` scan before restart and `0` after restart.
- **Credentials/network:** The server contains no Google service usage, credential access, external HTTP client, or persistence writes.
- **Scope:** Only the two allowed app files and this explicitly requested report were created. `package.json` already met the requirement.
- **Mutation check:** Removing callback-based include replacement reproduces the renderer failure; omitting the VM header exposure reproduces the export failure; removing attendance append breaks the repeated-scan total; sharing state across server instances breaks the restart check.
- **Verification:** Focused tests pass 3/3, the full suite passes 24/24, syntax checks pass, browser QR images load, and no page errors were reported.

## Concerns

- The preview is intentionally single-process and in-memory; it does not provide Apps Script locking, Sheet persistence, or multi-process coordination.
- Generated QR URLs default to `http://127.0.0.1:4173`. For phone or LAN testing, set `PREVIEW_PUBLIC_URL` to the reachable host before generating codes.
- The browser-use MCP navigation timed out, so the permitted Playwright MCP was used instead. Playwright reported only platform-level WebGL `powerPreference` warnings and no page errors.

## Fix round 1

**Status:** Complete  
**Commits:** None  
**Command working directory:** `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

### Findings Addressed

1. **Malformed JSON handling:** Moved request-body reading and `JSON.parse` inside the existing `try`. Parse/read failures now use the same JSON error envelope as other request failures instead of escaping as unhandled rejections. Added a real-HTTP regression test that checks the JSON response and confirms the server remains responsive.
2. **Scan device-token parity:** Both preview scan handlers now derive `String(payload.device_token || '')`, reject missing/empty or more-than-100-character tokens with `DEVICE_TOKEN_REQUIRED`, and do so before person lookup or attendance writes. A 100-character token remains valid. Scan status now returns `validation.date`, `validation.mode`, and `validation.qr_created_at`; recorded events also use the validated fields and normalized token. Added tests for missing tokens, 101-character tokens, no attendance/people writes on rejection, the 100-character boundary, and lowercase-mode status normalization.
3. **Search parity:** `admin.list` now computes `String(payload.query || '').trim().toLowerCase()` and compares it with `String(row.name).toLowerCase()`, matching the backend. Added a test covering a whitespace-padded uppercase string query and a numeric non-string query.
4. **Test cleanup:** The malformed-body regression uses a bounded fetch timeout, and the server test helper closes outstanding connections during cleanup so the pre-fix hang produces a terminating RED failure rather than leaving the test process open.

### Files Changed

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/preview/server.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/preview.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-5-report.md` (this appended section)

No changes were made to `Code.gs`, `Core.gs`, UI files, package configuration, or other tests. No Git commands or commits were used.

### TDD Evidence

#### RED

The five focused regression tests were added before the production fixes. The final pre-fix focused run exited 1 with all five new tests failing for the reviewed behaviors: unhandled JSON parsing, accepted missing/oversized tokens, raw lowercase status mode, and incorrect search results.

Command:

```bash
node --test tests/preview.test.cjs
```

Output:

```text
✔ renders all include files without scriptlet placeholders (3548.5081ms)
✔ preview supports registration, recognition, and repeated scans (2185.8964ms)
✔ preview exports recorded attendance as CSV (1751.8302ms)
✖ preview returns a JSON error for malformed request bodies (290.4911ms)
✖ preview scan handlers reject missing device tokens without writing attendance (1021.3525ms)
✖ preview scan handlers reject 101-character device tokens without writing attendance (485.639ms)
✖ preview accepts 100-character device tokens and returns validated scan status fields (301.5451ms)
✖ preview search trims and stringifies queries like the backend (432.9545ms)
ℹ tests 8
ℹ suites 0
ℹ pass 3
ℹ fail 5
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 19362.8996

✖ failing tests:

test at tests\preview.test.cjs:86:1
✖ preview returns a JSON error for malformed request bodies (290.4911ms)
  SyntaxError [Error]: Unexpected end of JSON input
      at JSON.parse (<anonymous>)
      at Server.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\preview\server.cjs:39:28)
      at process.processTicksAndRejections (node:internal/process/task_queues:104:5)

test at tests\preview.test.cjs:104:1
✖ preview scan handlers reject missing device tokens without writing attendance (1021.3525ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected
  
    [
      {
  +     date: '2026-11-24',
  +     mode: 'IN',
  +     name: null,
  +     ok: true,
  +     qr_created_at: '2026-11-24T15:54:38+08:00'
  -     error: 'DEVICE_TOKEN_REQUIRED',
  -     ok: false
      },
      {
  +     event: {
  +       date: '2026-11-24',
  +       event_id: '5f69ce23-f84a-4fc4-9aae-843fe254ad87',
  +       mode: 'IN',
  +       name: 'Ana Cruz',
  +       qr_created_at: '2026-11-24T15:54:38+08:00',
  +       scanned_at: '2026-11-24T15:54:38+08:00'
  +     },
  +     ok: true
  -     error: 'DEVICE_TOKEN_REQUIRED',
  -     ok: false
      }
    ]
  
      at C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:112:12
      at process.processTicksAndRejections (node:internal/process/task_queues:104:5)
      at async withServer (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:9:9)
      at async TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:105:3)
      at async Test.run (node:internal/test_runner/test:1409:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:974:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: [ { ok: true, date: '2026-11-24', mode: 'IN', name: null, qr_created_at: '2026-11-24T15:54:38+08:00' }, { ok: true, event: [Object] } ],
    expected: [ { ok: false, error: 'DEVICE_TOKEN_REQUIRED' }, { ok: false, error: 'DEVICE_TOKEN_REQUIRED' } ],
    operator: 'deepStrictEqual',
    diff: 'simple'
  }

test at tests\preview.test.cjs:122:1
✖ preview scan handlers reject 101-character device tokens without writing attendance (485.639ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected
  
    [
      {
  +     date: '2026-11-24',
  +     device_token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  +     mode: 'IN',
  +     name: null,
  +     ok: true,
  +     qr_created_at: '2026-11-24T15:54:38+08:00'
  -     error: 'DEVICE_TOKEN_REQUIRED',
  -     ok: false
      },
      {
  +     event: {
  +       date: '2026-11-24',
  +       device_token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  +       event_id: '119897e2-c274-493a-8d45-3daa4924baca',
  +       mode: 'IN',
  +       name: 'Ana Cruz',
  +       qr_created_at: '2026-11-24T15:54:38+08:00',
  +       scanned_at: '2026-11-24T15:54:39+08:00'
  +     },
  +     ok: true
  -     error: 'DEVICE_TOKEN_REQUIRED',
  -     ok: false
      }
    ]
  
      at C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:133:12
      at process.processTicksAndRejections (node:internal/process/task_queues:104:5)
      at async withServer (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:9:9)
      at async TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:123:3)
      at async Test.run (node:internal/test_runner/test:1409:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:974:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: [ { ok: true, date: '2026-11-24', mode: 'IN', name: null, device_token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', qr_created_at: '2026-11-24T15:54:38+08:00' }, { ok: true, event: [Object] } ],
    expected: [ { ok: false, error: 'DEVICE_TOKEN_REQUIRED' }, { ok: false, error: 'DEVICE_TOKEN_REQUIRED' } ],
    operator: 'deepStrictEqual',
    diff: 'simple'
  }

test at tests\preview.test.cjs:143:1
✖ preview accepts 100-character device tokens and returns validated scan status fields (301.5451ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected
  
    {
      date: '2026-11-24',
      device_token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  +   mode: 'out',
  -   mode: 'OUT',
      name: 'Ana Cruz',
      ok: true,
      qr_created_at: '2026-11-24T15:54:39+08:00'
    }
  
      at C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:154:12
      at process.processTicksAndRejections (node:internal/process/task_queues:104:5)
      at async withServer (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:9:9)
      at async TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:144:3)
      at async Test.run (node:internal/test_runner/test:1409:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:974:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: { ok: true, date: '2026-11-24', mode: 'out', name: 'Ana Cruz', device_token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', qr_created_at: '2026-11-24T15:54:39+08:00' },
    expected: { ok: true, date: '2026-11-24', mode: 'OUT', name: 'Ana Cruz', device_token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', qr_created_at: '2026-11-24T15:54:39+08:00' },
    operator: 'deepStrictEqual',
    diff: 'simple'
  }

test at tests\preview.test.cjs:161:1
✖ preview search trims and stringifies queries like the backend (432.9545ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
  + actual - expected
  
    {
  +   nonString: [],
  +   whitespace: []
  -   nonString: [
  -     'Agent 42'
  -   ],
  -   whitespace: [
  -     'Ana Cruz'
  -   ]
    }
  
      at C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:175:12
      at process.processTicksAndRejections (node:internal/process/task_queues:104:5)
      at async withServer (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:9:9)
      at async TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\preview.test.cjs:162:3)
      at async Test.run (node:internal/test_runner/test:1409:7)
      at async Test.processPendingSubtests (node:internal/test_runner/test:974:7) {
    generatedMessage: true,
    code: 'ERR_ASSERTION',
    actual: { whitespace: [], nonString: [] },
    expected: { whitespace: [ 'Ana Cruz' ], nonString: [ 'Agent 42' ] },
    operator: 'deepStrictEqual',
    diff: 'simple'
  }
```

#### GREEN

The same focused command was rerun after the minimal server changes. It exited 0 with 8/8 tests passing.

Command:

```bash
node --test tests/preview.test.cjs
```

Output:

```text
✔ renders all include files without scriptlet placeholders (95.9398ms)
✔ preview supports registration, recognition, and repeated scans (101.2318ms)
✔ preview exports recorded attendance as CSV (33.3613ms)
✔ preview returns a JSON error for malformed request bodies (28.2778ms)
✔ preview scan handlers reject missing device tokens without writing attendance (25.3917ms)
✔ preview scan handlers reject 101-character device tokens without writing attendance (28.12ms)
✔ preview accepts 100-character device tokens and returns validated scan status fields (21.9669ms)
✔ preview search trims and stringifies queries like the backend (25.2019ms)
ℹ tests 8
ℹ suites 0
ℹ pass 8
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 599.7077
```

### Full Suite GREEN

Command:

```bash
npm test
```

Output:

```text

> sslg-office-attendance@1.0.0 test
> node --test

✔ creates the documented Sheet tabs and headers (11.6722ms)
✔ generates daily codes and invalidates the previous pair (70.1897ms)
✔ registers a device once and records every valid scan (16.1764ms)
✔ rejects invalid codes without writing attendance (8.6391ms)
✔ filters attendance and exports CSV (16.0802ms)
✔ a late generation response cannot redisplay QR cards for a previous date (82.5869ms)
✔ an older attendance response cannot overwrite a newer search result (14.8686ms)
✔ an older attendance failure cannot resurface an error after a newer search succeeds (8.0503ms)
✔ starting list and export requests hides a recovered office error (5.8351ms)
✔ client script parses as JavaScript (3.8085ms)
✔ landing and student navigation contain no admin link (1.0065ms)
✔ index includes every client asset exactly once (0.6752ms)
✔ Apps Script adapter maps every API action to a public server function (0.6522ms)
✔ normalizes a registered name and rejects blank names (3.0895ms)
✔ uses the Manila calendar date across UTC midnight (60.3164ms)
✔ rejects impossible calendar dates (1.903ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (5.8492ms)
✔ validates matching code, mode, and current Manila date (23.0845ms)
✔ escapes CSV commas, quotes, and newlines (0.7143ms)
✔ renders all include files without scriptlet placeholders (412.9476ms)
✔ preview supports registration, recognition, and repeated scans (224.6766ms)
✔ preview exports recorded attendance as CSV (75.0385ms)
✔ preview returns a JSON error for malformed request bodies (72.9071ms)
✔ preview scan handlers reject missing device tokens without writing attendance (43.6995ms)
✔ preview scan handlers reject 101-character device tokens without writing attendance (49.9878ms)
✔ preview accepts 100-character device tokens and returns validated scan status fields (44.1939ms)
✔ preview search trims and stringifies queries like the backend (135.8825ms)
✔ IN QR payload decodes exactly (483.5379ms)
✔ OUT QR payload decodes exactly (408.9542ms)
ℹ tests 29
ℹ suites 0
ℹ pass 29
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1985.1116
```

Syntax verification command:

```bash
node --check preview/server.cjs && node --check tests/preview.test.cjs
```

It produced no output and exited 0.

### Self-Review

- Verified each finding against `Code.gs`/`Core.gs` before changing the preview.
- The RED run demonstrated all five new regression tests failing for the intended reasons; the three pre-existing preview tests remained green.
- Mutation review: moving JSON parsing outside the `try` reproduces the unhandled rejection; removing the token guard reproduces invalid lookups/writes; returning raw `payload.mode` reproduces lowercase status output; restoring the old query expression reproduces both search failures.
- Missing and oversized-token tests assert zero scans and zero people after rejected record attempts, covering the no-write requirement rather than only the error envelope.
- The boundary test proves the guard does not reject a valid 100-character token and checks normalized status fields after a real registration.
- Existing rendering, registration/repeated-scan, and CSV export tests still pass, and the full suite passes 29/29.
- Snapshot diffs were reviewed: production changes are limited to request parsing, scan token/status handling, and search normalization. `Code.gs` and UI behavior were not changed.
- No credentials, subagents, Git commands, or commits were used.

### Concerns

- Per the controller's explicit 101-character requirement, the preview applies the 100-character cap to both scan handlers. `Code.gs` currently applies the length cap only in `recordScan_`; `getScanStatus_` checks only token presence. The preview follows this fix round's explicit requirement, and no out-of-scope backend change was made.
- The preview remains single-process and in-memory; it does not emulate Apps Script locking, Sheet persistence, or multi-process coordination.
