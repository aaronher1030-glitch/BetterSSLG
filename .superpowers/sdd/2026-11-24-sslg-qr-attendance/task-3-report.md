# Task 3 Report: Student Registration, Recognition, and Confirmation UI

## Status

Implemented Task 3 exactly as specified in `task-3-brief.md`. No commits were created. `Core.gs` and `Code.gs` were left unchanged, and no Task 4 files or admin runtime were created.

## Files changed

Created:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Index.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Styles.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Client.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/client-static.test.cjs`

Created this required report:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-3-report.md`

## TDD evidence

### RED

The four prescribed static tests were written before any production file. The focused command failed because `Client.html` did not yet exist: the expected missing-feature failure.

Working directory: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

Command:

```bash
node --test tests/client-static.test.cjs
```

Captured output:

```text
node:fs:624
    return binding.readFileUtf8(path, stringToFlags(options.flag));
                   ^

Error: ENOENT: no such file or directory, open 'C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\Client.html'
    at Object.readFileSync (node:fs:624:20)
    at Object.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\client-static.test.cjs:7:19)
    at Module._compile (node:internal/modules/cjs/loader:19)
    at Function._compile (node:internal/modules/cjs/loader:36)
    at Function.executeUserEntryPoint (node:internal/modules/run_main:37)
    at node:internal/modules/run_main:43)
    at node:internal/modules/run_main:54)
    at node:internal/modules/run_main:63)
    at node:internal/modules/run_main:82)
    at node:internal/modules/run_main:92)
    at node:internal/modules/run_main:104)
    at node:internal/modules/run_main:117)
    at node:internal/modules/run_main:138)
    at node:internal/modules/run_main:163)
    at node:internal/modules/run_main:181)
    at node:internal/modules/run_main:199)
    at node:internal/modules/run_main:217)
    at node:internal/modules/run_main:236)
    at node:internal/modules/run_main:256)
    at node:internal/modules/run_main:276)
    at node:internal/modules/run_main:296)
    at node:internal/modules/run_main:316)
    at node:internal/modules/run_main:336)
    at node:internal/modules/run_main:356)
    at node:internal/modules/run_main:376)
    at node:internal/modules/run_main:396)
    at node:internal/modules/run_main:416)
    at node:internal/modules/run_main:436)
    at node:internal/modules/run_main:456)
    at node:internal/modules/run_main:476)
    at node:internal/modules/run_main:496)
    at node:internal/modules/run_main:516)
    at node:internal/modules/run_main:536)
    at node:internal/modules/run_main:556)
    at node:internal/modules/run_main:576)
    at node:internal/modules/run_main:596)

Node.js v26.13.1
✖ tests\client-static.test.cjs (269.3519ms)
ℹ tests 1
ℹ suites 0
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 307.1385

✖ failing tests:

test at tests\client-static.test.cjs:1:1
✖ tests\client-static.test.cjs (269.3519ms)
  'test failed'
```

Exit code: `1`.

### GREEN

After implementing the three prescribed production files, the exact focused command passed.

Command:

```bash
node --test tests/client-static.test.cjs
```

Captured output:

```text
✔ client script parses as JavaScript (9.697ms)
✔ landing and student navigation contain no admin link (4.9856ms)
✔ index includes every client asset exactly once (3.1336ms)
✔ Apps Script adapter maps every API action to a public server function (0.7746ms)
ℹ tests 4
ℹ suites 0
ℹ pass 4
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 789.852ms
```

Exit code: `0`.

### Full existing suite

Working directory: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

Command:

```bash
npm test
```

Captured output:

```text
> sslg-office-attendance@1.0.0 test
> node --test

✔ creates the documented Sheet tabs and headers (33.0897ms)
✔ generates daily codes and invalidates the previous pair (95.8113ms)
✔ registers a device once and records every valid scan (19.3443ms)
✔ rejects invalid codes without writing attendance (12.0511ms)
✔ filters attendance and exports CSV (11.9421ms)
✔ client script parses as JavaScript (2.9288ms)
✔ landing and student navigation contain no admin link (1.9650ms)
✔ index includes every client asset exactly once (1.1142ms)
✔ Apps Script adapter maps every API action to a public server function (0.8407ms)
✔ normalizes a registered name and rejects blank names (8.1008ms)
✔ uses the Manila calendar date across UTC midnight (81.8492ms)
✔ rejects impossible calendar dates (1.2501ms)
✔ creates distinct IN and OUT tokens and a creation timestamp (2.3017ms)
✔ validates matching code, mode, and current Manila date (2.3017ms)
✔ escapes CSV commas, quotes, and newlines (0.9456ms)
ℹ tests 15
ℹ suites 0
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1563.4201ms
```

Exit code: `0`.

### Behavioral smoke check

A controlled Node `vm` smoke check executed the real client script with browser API stubs. It verified:

- `scan.status` receives the persistent device token.
- A recognized device renders the explicit confirmation button.
- A malicious recognized name is escaped before HTML insertion.
- A `{ ok: false, error: 'SHEET_BUSY' }` result keeps the scan form, re-enables its button, and displays the busy error rather than success.
- A successful OUT result renders only after `{ ok: true, event }` and escapes the recorded name.
- An unknown thrown error falls back to copy containing “not recorded” and does not render success.

Final captured output:

```text
Behavioral smoke checks passed: recognition, escaping, failure, success, unknown-error fallback.
```

The first smoke-check setup omitted `window.crypto`; the client correctly displayed its device-token storage error. The harness was corrected to provide `window.crypto.randomUUID`, and the check passed. This was a harness issue, not a production change.

## Requirements and self-review

### Student flow and privacy

- First registration asks only for a name, using `autocomplete="name"`, `maxlength="80"`, and `required`.
- The persistent `sslg.attendance.device.v1` token supports same-phone recognition.
- No login, phone-number field, admin hyperlink, or attendance list exists in the landing or student flow.
- `admin.list` appears only in the action map required for the later admin runtime; student rendering and submission call only `scan.status` and `scan.record`.
- The landing page gives scan instructions without linking to admin or displaying records.

### Confirmation and failures

- Registration requires an explicit form submission; recognition requires an explicit confirmation click.
- The button is disabled while submission is pending and re-enabled after failure.
- The success card is rendered only when `scan.record` resolves with `ok: true` and an event.
- Backend `{ ok: false }` results and thrown failures render error copy, never success. Unknown/network/Apps Script failures use the prescribed “The scan was not recorded” fallback.
- All prescribed backend error codes have readable messages.

### Escaping

- Status date, recognized name, recorded event name, and timestamp pass through `escapeHtml_` before HTML insertion.
- Dynamic server-provided error codes select fixed trusted message strings; unknown codes fall back to a fixed safe message.
- Submit errors use `textContent`, not HTML interpolation.

### Accessibility

- Semantic header, main, section, form, label, and footer structure is present.
- The name input has an implicit label, name autocomplete, required state, and an 80-character limit.
- Loading and success regions use `aria-live="polite"`; decorative spinner and success mark are hidden from assistive technology.
- Inputs and buttons have visible focus styles and 52px minimum heights.
- The document has `lang="en"`, a descriptive title, viewport settings, and a theme color.

### Responsiveness and visual direction

- Fluid widths use `min(100% - 32px, 960px)` and fluid card padding/heading sizes.
- Student cards are capped at 480px for comfortable phone use.
- Long names wrap anywhere, avoiding horizontal overflow.
- The 620px breakpoint reduces radii and collapses later admin grids; Task 3 student content is already single-column.
- Warm paper, navy ink, teal actions, serif display headings, sans-serif body text, and restrained shadows follow the civic-ledger direction.

## Concerns and later dependencies

- `QRCodeLib.html` and `renderAdminPage_` remain intentionally absent for Task 4. The full Apps Script page and `?page=admin` runtime were therefore not executed in Task 3.
- The prescribed tests are static contract tests. The additional controlled behavioral smoke check improves confidence but is not a real-browser or live Apps Script integration test.
- Per the exact brief, submission error markup is a visually revealed hidden paragraph rather than an assertive live region, and route transitions do not programmatically move focus. These are potential follow-up accessibility improvements, not Task 3 scope changes.
- Real-device localStorage behavior, mobile browser rendering, and network failure behavior remain deployment/integration checks.
