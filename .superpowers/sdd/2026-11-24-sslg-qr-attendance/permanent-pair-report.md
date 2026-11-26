# Permanent reusable QR pair — implementation report

Date: 2026-11-25

Status: Implemented and verified locally. No Git commands or commits were used; this workspace is not a Git repository.

## Scope and baseline

Implemented the approved permanent-pair change from `permanent-pair-brief.md` in:

`C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

Before editing, `diff -qr` against `before-permanent-pair` reported no differences. The baseline `npm test` run passed all 51 existing tests.

No real Google deployment, credentials, Spreadsheet ID, production URL, phone number, email, grade/section, login, GPS, event session, private admin authentication, or additional database was introduced.

## Exact files changed

Production:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Core.gs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Code.gs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Client.html`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/preview/server.cjs`

Tests:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/core.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/backend.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/preview.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/client-admin.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/client-static.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/qr.test.cjs`
- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/packaging.test.cjs`

Required report:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/permanent-pair-report.md`

`SETUP.md`, `VERIFICATION.md`, the design spec, plan, SDD ledger, and all other files were not edited. A final `cmp` check confirmed both setup and verification documents are byte-identical to the baseline.

## TDD evidence

### Baseline GREEN

Command:

```sh
npm test
```

Result before test or production edits:

```text
ℹ tests 51
ℹ suites 0
ℹ pass 51
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
```

### Permanent-pair RED before production edits

The obsolete daily date-validation, expiry, and regeneration tests were removed or rewritten. New permanent-record, idempotency, server-date, preview-parity, UI, QR, and packaging tests were written while production files were still unchanged.

Command:

```sh
node --test tests/core.test.cjs tests/backend.test.cjs tests/preview.test.cjs tests/client-admin.test.cjs tests/client-static.test.cjs tests/qr.test.cjs tests/packaging.test.cjs
```

Exact summary output:

```text
ℹ tests 63
ℹ suites 0
ℹ pass 27
ℹ fail 36
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 10544.8264
```

The 36 failing tests were:

```text
✖ backend test requests stay on 2026-11-24 when the host clock advances
✖ creates the documented Sheet tabs and headers
✖ creates one permanent pair and returns it without later writes or UUID consumption
✖ dates repeated and unmatched scans by the current Manila server day
✖ rejects missing records, malformed requests, unknown codes, and wrong modes without scan writes
✖ exposes no rotate, reset, or delete action
✖ registers a device once and records every valid scan
✖ rejects invalid codes without writing attendance
✖ filters attendance and exports CSV
✖ records an unmatched OUT as the first scan
✖ rejects every formula-leading new name before People or Attendance writes
✖ rejects formula-leading legacy names on returning scans without writes
✖ backend and preview reject dangerous device tokens with matching errors and zero writes
✖ backend preserves safe device tokens exactly and keeps the 100/101 character boundaries
✖ direct admin HTTP actions return generation, list, and export shapes
✖ public wrappers return scan and admin result shapes
✖ a busy Sheet lock returns SHEET_BUSY without People or Attendance writes
✖ shows a permanent pair without confirmation or a date-bound generation request
✖ changing the attendance date preserves permanent QR cards and only reloads records
✖ student scan parameters omit caller-supplied dates
✖ student errors refer to permanent codes without date expiry or replacement wording
✖ landing copy directs students to the posted permanent codes
✖ creates distinct permanent IN and OUT tokens without a date field
✖ validates a permanent record on different Manila dates without a request date
✖ ignores supplied stale and future dates when validating permanent scans
✖ rejects malformed, unknown, wrong-mode, and missing permanent records
✖ packaged backend initializes the permanent QR Codes schema
✖ preview supports registration, recognition, and repeated scans
✖ preview reuses one permanent pair across Manila dates while attendance stays daily
✖ preview rejects missing and invalid permanent codes without attendance writes
✖ preview exports recorded attendance as CSV
✖ preview scan handlers reject missing device tokens without writing attendance
✖ preview status accepts a 101-character device token while record rejects it without writing
✖ preview rejects formula-leading names without registering or recording them
✖ preview accepts 100-character device tokens and returns validated scan status fields
✖ preview search trims and stringifies queries like the backend
```

Representative exact failures and their causes:

```text
TypeError [Error]: backend.context.generatePermanentCodes_ is not a function
```

The backend still exposed only daily generation.

```text
+   error: 'INVALID_REQUEST'
-   error: 'CODE_NOT_FOUND'
```

Core validation still required a request date before considering the permanent record.

```text
+     date: '2026-11-24'
+     in_url: 'https://script.test/exec?page=scan&date=2026-11-24&mode=IN&code=uuid-1'
-     in_url: 'https://script.test/exec?page=scan&mode=IN&code=uuid-1'
```

The generated record and QR URLs were still date-bound.

```text
+   'Daily Codes'
-   'QR Codes'
```

The packaged backend still created the obsolete tab.

```text
Error: UNEXPECTED_CONFIRMATION
```

The admin client still opened the regeneration confirmation.

```text
+     date: '2020-01-01'
```

The student client still forwarded a caller-supplied date.

```text
+   date: '2026-11-25'
```

Two preview status expectations had accidentally lost their required server-date field during test adaptation; this was a test-harness defect, not a production defect.

The complete raw RED output was saved by the tool at:

`C:/Users/Ma Christine/.qoder/tmp/C--Users-Ma-Christine-Downloads-SSLG-MEMOS/tool-outputs/session-d7dc46dd-24c6-4ffc-a76f-5e8db5e19a53/b16qjq411.output`

### Additional midnight-consistency RED

A further regression test proved that a scan must use one server instant for both its Manila date and exact timestamp. It was added and run before the corresponding production correction.

Command:

```sh
node --test --test-name-pattern="one server instant" tests/backend.test.cjs
```

Exact output:

```text
✖ uses one server instant for a scan date and its exact timestamp across Manila midnight
ℹ tests 1
ℹ suites 0
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0

AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
+ actual - expected
+ '2026-11-25T00:00:00+08:00'
- '2026-11-24T23:59:59+08:00'
```

Cause: validation and event timestamping read the clock separately, allowing a midnight boundary to split one scan across two dates.

### Intermediate harness corrections

The first post-implementation focused run reached 43/64. The remaining failures were diagnosed as test-harness issues:

- Mock date state leaked between backend tests; `loadBackend()` now resets it.
- Node 24 `MockTimers.setTime` requires a numeric epoch, not a `Date` object.
- Two preview expected status objects had been over-edited to omit `date`.
- VM-realm objects require JSON normalization before strict deep equality.

The assertions were not weakened. After these corrections, backend, client-admin, and preview suites each passed independently before the combined focused run.

## Implementation details

### Core

- Replaced daily code headers with `QR_CODE_HEADERS = ['in_code', 'out_code', 'created_at', 'created_by']`.
- Replaced `createDailyCodeRecord_` with `createPermanentCodeRecord_`; the record has no date and still generates distinct IN/OUT tokens plus the original Manila creation timestamp.
- `validateScan_` now requires only a valid mode and code. It ignores any supplied date, rejects malformed requests, missing records, unknown codes, and wrong-mode codes, and returns the current server Manila date.
- Name normalization, device-token validation, CSV escaping, and attendance headers are unchanged.

### Apps Script backend

- `ensureSchema_` creates `QR Codes`, `People`, and `Attendance` with the approved headers.
- `generatePermanentCodes_` retains the existing script lock. Under the lock it returns the first stored row unchanged or creates exactly one row on the first request.
- Repeated generation performs no `QR Codes` write and consumes no UUIDs. URLs contain only `page=scan`, `mode`, and `code`.
- `admin.generate` and public `adminGenerate` retain their names and now call the idempotent permanent generator. Payload dates are ignored.
- Scan status and recording read the one permanent row. Recording uses one `new Date()` for validation, person timestamps, event date, and exact event timestamp.
- No rotate, reset, delete, or replacement action exists.
- Append-only attendance, repeated IN, unmatched OUT, same-browser recognition, list/search/export filtering, wrapper shapes, lock errors, and `doGet` behavior remain intact.

### Preview

- Replaced the date-keyed code map with one in-memory permanent record.
- Repeated `admin.generate` calls return the same record without generating new UUIDs.
- Preview uses the same core permanent-record creation and validation functions, date-free URLs, server Manila dates, errors, token/name rules, CSV escaping, and zero-write rejection ordering as Apps Script.
- Attendance remains an append-only array filtered into daily rows and totals.

### Client

- Kept the `admin.generate` → `adminGenerate` transport mapping.
- Admin heading/helper/button now describe a permanent pair; the regeneration confirmation is removed.
- Cards show `Reusable every day` and the original creation timestamp.
- Attendance-date changes reload only attendance records; they do not clear, hide, regenerate, or date-bind QR cards.
- Generation sends no date and has no date-based stale-response guard.
- Student requests contain only mode, code, device token, and the existing name field when registration is needed.
- Student status displays the server-returned Manila date. Obsolete wrong-date, expired, newer-code, and “today's code” wording was removed.
- Landing copy refers to the posted permanent codes.

### QR and packaging

- IN and OUT round-trip fixtures are exactly `...?page=scan&mode=IN&code=in-token` and `...?page=scan&mode=OUT&code=out-token`; both decode exactly.
- Packaging tests execute the packaged core/backend and assert `QR Codes` with the approved four headers.
- Existing manifest and no-hard-coded-secret tests remain unchanged and passing.

## GREEN verification

### Focused permanent-pair suite

Command:

```sh
node --test tests/core.test.cjs tests/backend.test.cjs tests/preview.test.cjs tests/client-admin.test.cjs tests/client-static.test.cjs tests/qr.test.cjs tests/packaging.test.cjs
```

Exact summary output:

```text
ℹ tests 64
ℹ suites 0
ℹ pass 64
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 3943.7194
```

### Fresh full suite

Command:

```sh
npm test
```

Exact summary output:

```text
ℹ tests 64
ℹ suites 0
ℹ pass 64
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 4486.4527
```

### Local browser smoke

Started the real preview server with:

```sh
PREVIEW_PUBLIC_URL=http://127.0.0.1:4174 PORT=4174 npm run preview
```

Observed in Chromium through Playwright:

- Admin rendered `Permanent QR codes`, the permanent-pair helper, and `Show permanent QR pair`.
- Two QR cards rendered with `Reusable every day` and the original creation timestamp.
- Changing the attendance date preserved the exact two image data URLs.
- A second `Show permanent QR pair` request returned the same record and images.
- Generated URLs were date-free.
- Opening the exact generated IN URL displayed server date `2026-11-25`.
- Registering `Browser Smoke` recorded IN at `2026-11-25T08:07:47+08:00`.
- Opening the exact generated OUT URL recognized `Browser Smoke` in the same browser and recorded OUT at `2026-11-25T08:08:23+08:00`.
- `admin.list` for 2026-11-25 returned 2 scans, 1 person, 1 IN, and 1 OUT; 2026-11-24 remained empty.

The preview server and browser were then stopped/closed.

## Requirement self-review

| Approved requirement | Evidence |
|---|---|
| Date-free permanent QR payloads | Backend/preview URL assertions and exact QR decode tests |
| Caller date ignored | Core, backend, and preview stale/future-date tests |
| `QR Codes` has exactly the approved headers and one created row | Backend and packaging schema/idempotency tests |
| First creation only; later calls do not write or consume UUIDs | Backend write-count and UUID-count test |
| Script lock prevents duplicate first creation | Existing lock retained; busy-generation and busy-scan tests |
| No reset/rotate/delete endpoint | `UNKNOWN_ACTION` tests with unchanged row/UUID count |
| Current Manila date and exact timestamp per accepted scan | Two-date backend/preview tests and midnight regression |
| Repeated IN and unmatched OUT remain append-only | Backend/preview tests |
| Invalid scans write nothing | Missing/unknown/wrong-mode/malformed and token/name zero-write tests |
| Name/token/CSV/security behavior preserved | All prior security, boundary, returning-user, and CSV tests pass |
| Admin copy and permanent cards | Client behavior tests and browser smoke |
| Date filter affects records only | Client race/date-change tests and browser image-identity check |
| Student copy/request/date display | Client parameter/error/landing tests and browser smoke |
| Preview parity | Shared core plus repeated-generation/two-date/rejection tests |
| Transport names retained | Existing adapter mapping and wrapper tests |
| No hard-coded secrets | Packaging test passes |
| Setup/verification/spec/plan/ledger untouched | `cmp` and final diff file list |

Mutation review: reintroducing a date requirement, request-date authority, repeat generation writes/UUID consumption, date-keyed preview storage, date-based card clearing, reset actions, or removal of token/name/CSV guards would each break at least one listed test.

## Documentation changes needed by the controller

Not edited in this dispatch:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/SETUP.md`
  - Change “daily QR tokens” to one permanent IN/OUT pair.
  - Change “generate a QR pair for today” to show/create the permanent pair once.
  - Replace the regeneration/old-code-rejection test with repeated valid scans, unmatched OUT, invalid-code zero-write checks, and next-day reuse of the same pair.
  - Replace `Daily Codes` with `QR Codes` and document `in_code`, `out_code`, `created_at`, `created_by`.
  - Replace daily fresh-pair instructions with print once and reuse every day.
  - Remove expiry/regeneration troubleshooting; explain that codes are permanent and invalid/mode errors require checking the posted pair, not generating another.

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/VERIFICATION.md`
  - Replace Pair B regeneration and invalid-regenerated-code evidence with idempotent repeated-show evidence.
  - Replace date-bound/expiry criterion with permanent date-free acceptance across simulated Manila dates.
  - Replace generation wording with showing the permanent pair.
  - Replace `Daily Codes` inspection with `QR Codes` and its four columns.
  - Update owner deployment/test steps to create/show once, reuse daily, and verify exactly one row.

- Design spec, implementation plan, and SDD ledger under `.superpowers/sdd/2026-11-24-sslg-qr-attendance`
  - Supersede daily regeneration, rotation, expiry, and replacement decisions with the approved permanent-pair decisions.
  - Record the RED/GREEN and local-browser evidence from this report.

## Concerns

- No live Google Apps Script/Sheets deployment was performed, as required. Owner deployment verification remains necessary, especially confirming one `QR Codes` row and real phone scans.
- The controller still needs to update the intentionally untouched setup/verification/spec/plan/ledger documents before operational rollout.
- The admin page remains public and unpassworded by explicit approved requirement; this is an existing accepted exposure, not a new regression.
- No unresolved code or test failures remain.
