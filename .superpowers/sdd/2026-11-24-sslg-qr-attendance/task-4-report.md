# Task 4 Report: Office QR Generation, Attendance List, and CSV Export

## Status

Implemented and verified. Focused client-static/QR tests pass (6/6), and the full suite passes (17/17). No commits were created.

## Files changed

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Client.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Styles.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/QRCodeLib.html` (created)
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/qr.test.cjs` (created)
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-4-report.md` (this report)

`Code.gs`, `Core.gs`, `Index.html`, `package.json`, and `package-lock.json` were compared with the Task 4 baseline and are unchanged. No runtime CDN or new dependency was introduced.

## Implementation

### Local QR encoder

- Vendored the installed `qrcode-generator` 1.4.4 source into `QRCodeLib.html`, retaining Kazuhiko Arase's MIT license comment at the top.
- The existing `Index.html` already includes `QRCodeLib` exactly once before `Client`, so the bundled global `qrcode` is available without a network request.
- Important compatibility detail: upstream `qrcode-generator` 1.4.4 implements `createDataURL()` with a GIF encoder, while the brief's prescribed round-trip test reads the result with `PNG.sync.read`. A small local, dependency-free PNG compatibility implementation replaces only that output-format helper (CRC32, Adler32, uncompressed DEFLATE, PNG chunks, and the existing base64 stream). QR matrix generation and all upstream encoding behavior remain intact. The output MIME type is now `data:image/png;base64,`.

### Office dashboard

- Added the required `defaultAdminDate_()`, `qrDataUrl_()`, `renderAdminPage_()`, `generateCodes_()`, `loadAttendance_()`, and `downloadCsv_()` interfaces, plus `showAdminError_()`.
- The default date uses `Asia/Manila`; the generate button keeps the neutral label `Generate QR pair`.
- IN and OUT images are encoded directly from `record.in_url` and `record.out_url`. The client does not reconstruct URLs or tokens.
- Generation asks for confirmation before calling `admin.generate`, disables the button while pending, displays server/network errors, and re-enables the button in `finally`.
- Changing the attendance date hides the previously displayed pair so a stale date's cards are not accidentally printed.
- Attendance totals, rows, empty state, search, and date changes consume `admin.list`. Dynamic row text is HTML-escaped.
- CSV export consumes `admin.export`, creates a `Blob`, appends and clicks a temporary download link, removes it, and revokes the object URL on the next timer turn. It never navigates to a data URL.
- Office request failures use office-appropriate error text rather than the student scan wording. The error box has `role="alert"`; totals and generated pairs have polite live regions.
- The attendance table wrapper is keyboard-focusable and labelled as a region for horizontal scrolling.

### Print and mobile styles

- Print hides every element outside `#qr-pair` using visibility, then makes only the pair and its descendants visible.
- The pair prints as exactly two columns, one IN card and one OUT card. Cards use both `break-inside: avoid` and `page-break-inside: avoid`.
- Print QR images use `width: 72mm`, `min-width: 240px`, `max-width: 100%`, automatic height, exact color printing, and automatic centering. A four-millimetre quiet card padding and eight-millimetre column gap keep the cards legible without page breaks.
- If no pair has been generated, `#qr-pair` remains `hidden`, so no empty cards or unrelated page content print.
- The existing civic-ledger palette, typography, cards, focus styles, and mobile layout were preserved. At widths up to 620px the QR grid is one column and totals are two columns. `.table-wrap` retains `overflow-x: auto`.

## Strict TDD evidence

Before writing the test, I read:

`C:/Users/Ma Christine/.qoder/plugins/cache/qoder-marketplace/superpowers/6.3.0/skills/test-driven-development/writing-good-tests.md`

The two tests use the brief's literal server-shaped IN and OUT URLs and decode real PNG pixels with `jsQR`. Removing or corrupting the local encoder, changing the payload, or breaking PNG production makes them fail.

### Expected RED

Working directory: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

Command:

```bash
node --test tests/qr.test.cjs
```

Output (exit code 1):

```text
node:fs:624
    return binding.readFileUtf8(path, stringToFlags(options.flag));
                   ^

Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\QRCodeLib.html'
    at Object.readFileSync (node:fs:624:20)
    at Object.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\qr.test.cjs:9:19)
    at Module._compile (node:internal/modules/cjs/loader:936:30)
    at Module._extensions..js (node:internal/modules/cjs/loader:1097:10)
    at Module.load (node:internal/modules/cjs/loader:941:27)
    at Function.executeUserEntryPointAsRunMain (node:internal/modules/run_main:128:12)
    at node:internal/main/run_main_module:135:117)
  errno: -4058,
  syscall: 'open',
  path: 'C:\\Users\\Ma Christine\\Downloads\\SSLG MEMOS\\SSLG Attendance App\\QRCodeLib.html'

Node.js v26.13.1
✖ tests\qr.test.cjs (434.0306ms)
ℹ tests 1
ℹ suites 0
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 476.0678

✖ failing tests:

test at tests\qr.test.cjs:1:1
✖ tests\qr.test.cjs (434.0306ms)
  'test failed'
```

The failure was the missing production artifact, not a test typo.

### Vendor/intermediate observations

The vendor copy command was:

```bash
cp "C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/node_modules/qrcode-generator/qrcode.js" "C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/QRCodeLib.html" && cmp "C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/node_modules/qrcode-generator/qrcode.js" "C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/QRCodeLib.html"
```

It exited 0 with no output, confirming an exact initial copy. Re-running the QR test then exposed the upstream GIF/brief-PNG mismatch: both tests failed in `pngjs` with `Error: unrecognised content at end of stream`. After adding PNG output, a second run failed with `Error: have should not go down`; inspection showed the initial IHDR width/height bytes were not 32-bit big-endian for dimensions above 255. Correcting the header produced the first passing QR run (2/2). These intermediate failures were fixed in production output code, not by weakening the prescribed tests.

### Final GREEN: focused tests

Working directory: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

Commands:

```bash
node --test tests/client-static.test.cjs
node --test tests/qr.test.cjs
```

They were also run sequentially with `&&`; the complete fresh output was:

```text
✔ client script parses as JavaScript (10.9666ms)
✔ landing and student navigation contain no admin link (1.1957ms)
✔ index includes every client asset exactly once (0.8104ms)
✔ Apps Script adapter maps every API action to a public server function (0.7181ms)
ℹ tests 4
ℹ suites 0
ℹ pass 4
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 769.057
✔ IN QR payload decodes exactly (518.317ms)
✔ OUT QR payload decodes exactly (762.7769ms)
ℹ tests 2
ℹ suites 0
ℹ pass 2
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2747.4177
```

### Final GREEN: full suite

Command:

```bash
node --test
```

Output (exit code 0):

```text
✔ creates the documented Sheet tabs and headers (25.0999ms)
✔ generates daily codes and invalidates the previous pair (126.1049ms)
✔ registers a device once and records every valid scan (17.1617ms)
✔ rejects invalid codes without writing attendance (25.8174ms)
✔ filters attendance and exports CSV (54.5669ms)
✔ client script parses as JavaScript (5.6504ms)
✔ landing and student navigation contain no admin link (12.6718ms)
✔ index includes every client asset exactly once (0.7007ms)
✔ Apps Script adapter maps every API action to a public server function (0.4823ms)
✔ normalizes a registered name and rejects blank names (12.3109ms)
✔ uses the Manila calendar date across UTC midnight (129.2538ms)
✔ rejects impossible calendar dates (2.4135ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (3.4026ms)
✔ validates matching code, mode, and current Manila date (10.9635ms)
✔ escapes CSV commas, quotes, and newlines (15.3959ms)
✔ IN QR payload decodes exactly (941.4504ms)
✔ OUT QR payload decodes exactly (437.163ms)
ℹ tests 17
ℹ suites 0
ℹ pass 17
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3898.7875
```

The shell's actual Node version was v26.13.1; it satisfies the package's `>=20` engine requirement.

## Self-review

- **Exact QR payloads:** The QR tests decode both literal payloads exactly. A separate Node VM behavior harness also generated cards from server-shaped `in_url`/`out_url` values, decoded the actual PNG `src` attributes, and got byte-for-byte identical strings. It verified `page=scan`, date `2026-11-24`, distinct `IN`/`OUT` modes, and distinct nonempty tokens.
- **Regeneration/invalidation:** The confirmation explicitly warns that the previous pair will stop working. No generate request occurs when confirmation is cancelled. The unchanged backend test `generates daily codes and invalidates the previous pair` passes.
- **Attendance/error behavior:** The VM harness verified escaped names (`Ada & Luis` rendered as `Ada &amp; Luis`), IN mode styling, `SHEET_BUSY` propagation to the visible office error, and button recovery after failure.
- **CSV:** The VM harness verified one download, filename `attendance-2026-11-24.csv`, and a `blob:` URL rather than a data URL.
- **Print:** Reviewed the final print CSS and DOM contract: only two generated card articles exist; every non-pair descendant is hidden in print; the grid is two columns; images have a 240px minimum and cards avoid page breaks. Date changes hide stale cards.
- **Mobile/accessibility:** Reviewed the 620px breakpoint, single-column QR layout, two-column totals, scrollable table wrapper, keyboard-focusable table region, labels, alt text, live regions, alert role, and visible focus treatment.
- **Office exposure:** `Code.gs` remains unpassworded and permits direct `page=admin` navigation. No admin anchor or redirect was added; the static test `landing and student navigation contain no admin link` passes.
- **Scope:** Baseline comparisons confirmed only `Client.html` and `Styles.html` changed among pre-existing files. The two new app/test files and this explicitly requested report are the only additions.

The additional VM harness printed:

```text
PASS: cancel warning, exact server URL QR decoding, escaped attendance rows, Blob CSV download, and recoverable office errors
```

## Concerns

1. **PNG compatibility patch:** The bundled upstream library normally emits GIF, but the brief requires a PNG-reading test. The local PNG output helper is therefore a deliberate compatibility adaptation, not an unmodified upstream release. It should be revisited if `qrcode-generator` is upgraded; the round-trip tests protect the contract.
2. **Physical output validation:** Print/mobile behavior was reviewed through the final DOM/CSS and behavior harnesses. A shared automated browser session was externally navigated during the attempted visual check, so no reliable browser screenshot or physical printer/phone-camera validation is claimed. Those remain deployment checks.
3. **Overlapping requests:** The brief's direct event wiring does not sequence rapid `admin.list` responses or cancel an in-flight generate when the date changes. A sufficiently slow earlier response could temporarily overwrite newer search/date results. This is outside the prescribed minimal implementation but worth hardening if the office enters search text rapidly or changes dates during generation.

## Fix round 1

### Findings addressed

1. **Important — unsequenced office requests:** Added independent generation counters for QR generation and attendance-list requests. A date change now invalidates an in-flight generation, clears and hides the old QR pair, and re-enables the generate button. Generation responses are rendered only when the request is still current, the selected date still matches, and the returned record has that same date. Attendance responses and failures are accepted only for the latest list request while the selected date and search query still match. The generate button also rejects overlapping calls while disabled, and an invalidated generation's `finally` block cannot re-enable a newer generation.
2. **Minor — stale office errors:** Added `clearAdminError_()` and invoke it at the start of generate, list, and CSV export requests. Stale list failures are discarded rather than re-showing an error after a newer search/date request succeeds.

### Files changed

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Client.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/client-admin.test.cjs` (created)
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-4-report.md` (this appendix)

No other app files were modified. No Git commands or commits were used.

### Strict TDD evidence

The new behavioral tests execute the real `Client.html` script in a Node VM with a minimal DOM and deferred office API responses. They assert rendered QR/list/error state, not API mock call counts. Before implementation, the four tests failed for the reviewed behaviors: old QR cards became visible after a date change, an older search response replaced newer rows, an older failure re-showed the error, and list/export requests left the old error visible.

#### Expected RED

Working directory: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

Command:

```bash
node --test tests/client-admin.test.cjs
```

Output (exit code 1):

```text
✖ a late generation response cannot redisplay QR cards for a previous date (363.1902ms)
✖ an older attendance response cannot overwrite a newer search result (16.8106ms)
✖ an older attendance failure cannot resurface an error after a newer search succeeds (36.506ms)
✖ starting list and export requests hides a recovered office error (20.4532ms)
ℹ tests 4
ℹ suites 0
ℹ pass 0
ℹ fail 4
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1561.2602

✖ failing tests:

test at tests\client-admin.test.cjs:110:1
✖ a late generation response cannot redisplay QR cards for a previous date (363.1902ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  false !== true
  
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\client-admin.test.cjs:133:10)
      at async Test.run (node:internal/test_runner/test_harness:1498:12)
      at async Test.run (node:internal/test_runner/test_harness:1334:11)
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
  generatedMessage: true
  actual: false
  expected: true
  operator: 'strictEqual'
  diff: 'simple'

test at tests\client-admin.test.cjs:139:1
✖ an older attendance response cannot overwrite a newer search result (16.8106ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /Luis/. Input:
  
  '<tr><td>08:00</td><td>Ada</td><td><span class="mode mode-in">IN</span></td></tr>'
  
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\client-admin.test.cjs:156:10)
      at async Test.run (node:internal/test_runner/test_harness:1498:12)
      at async Test.run (node:internal/test_runner/test_harness:1334:11)
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
  generatedMessage: true
  actual: '<tr><td>08:00</td><td>Ada</td><td><span class="mode mode-in">IN</span></td></tr>'
  expected: /Luis/
  operator: 'match'
  diff: 'simple'

test at tests\client-admin.test.cjs:161:1
✖ an older attendance failure cannot resurface an error after a newer search succeeds (36.506ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  false !== true
  
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\client-admin.test.cjs:179:10)
      at async Test.run (node:internal/test_runner/test_harness:1498:12)
      at async Test.run (node:internal/test_runner/test_harness:1334:11)
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
  generatedMessage: true
  actual: false
  expected: true
  operator: 'strictEqual'
  diff: 'simple'

test at tests\client-admin.test.cjs:183:1
✖ starting list and export requests hides a recovered office error (20.4532ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  
  false !== true
  
      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\client-admin.test.cjs:192:10)
      at async Test.run (node:internal/test_runner/test_harness:1498:12)
      at async Test.run (node:internal/test_runner/test_harness:1334:11)
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
  generatedMessage: true
  actual: false
  expected: true
  operator: 'strictEqual'
  diff: 'simple'
```

#### GREEN: focused regression tests

Command:

```bash
node --test tests/client-admin.test.cjs
```

Output (exit code 0):

```text
✔ a late generation response cannot redisplay QR cards for a previous date (342.0137ms)
✔ an older attendance response cannot overwrite a newer search result (5.9109ms)
✔ an older attendance failure cannot resurface an error after a newer search succeeds (43.6606ms)
✔ starting list and export requests hides a recovered office error (18.9198ms)
ℹ tests 4
ℹ suites 0
ℹ pass 4
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1418.5836
```

#### GREEN: full suite

Command:

```bash
node --test
```

Output (exit code 0):

```text
✔ creates the documented Sheet tabs and headers (21.2968ms)
✔ generates daily codes and invalidates the previous pair (208.1168ms)
✔ registers a device once and records every valid scan (28.7089ms)
✔ rejects invalid codes without writing attendance (34.059ms)
✔ filters attendance and exports CSV (67.9775ms)
✔ a late generation response cannot redisplay QR cards for a previous date (420.1921ms)
✔ an older attendance response cannot overwrite a newer search result (14.0517ms)
✔ an older attendance failure cannot resurface an error after a newer search succeeds (26.6439ms)
✔ starting list and export requests hides a recovered office error (34.3305ms)
✔ client script parses as JavaScript (10.1733ms)
✔ landing and student navigation contain no admin link (1.2517ms)
✔ index includes every client asset exactly once (0.697ms)
✔ Apps Script adapter maps every API action to a public server function (20.0949ms)
✔ normalizes a registered name and rejects blank names (9.4168ms)
✔ uses the Manila calendar date across UTC midnight (176.2031ms)
✔ rejects impossible calendar dates (1.8441ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (3.3183ms)
✔ validates matching code, mode, and current Manila date (9.6772ms)
✔ escapes CSV commas, quotes, and newlines (3.8853ms)
✔ IN QR payload decodes exactly (1432.8583ms)
✔ OUT QR payload decodes exactly (931.8137ms)
ℹ tests 21
ℹ suites 0
ℹ pass 21
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5927.4829
```

### Self-review

- The regression tests cover both reviewed races through observable DOM state: late QR generation after a date change and out-of-order list responses for rapid search changes. A further assertion proves stale list failures cannot restore a cleared error.
- Date changes invalidate generation before starting the replacement list request. Both request identity and current date/query are checked, so direct date-value changes and same-date search races are also protected.
- QR rendering additionally checks the server record date. Invalidated generation cleanup cannot alter the button state owned by a newer request.
- Error clearing occurs for every office request type. Current failures still propagate to the existing office error handler; only stale list failures are swallowed.
- Student scan code, QR encoding, backend behavior, CSV download behavior, and styling were not changed. The full suite's existing student, backend, static, and QR round-trip tests remain green.
- Scope was limited to `Client.html`, the new focused test, and this report appendix. No commits were created. No new concerns were identified; the previously documented PNG compatibility and physical print/mobile validation concerns remain unchanged.
