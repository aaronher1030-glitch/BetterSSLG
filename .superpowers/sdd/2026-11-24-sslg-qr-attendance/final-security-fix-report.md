# Final security correction report

Date: 2026-11-25

Status: Complete

Workspace: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

Snapshot baseline: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/before-final-security-fix`

No Git commands were run and no commit was created. Scope was reviewed with filesystem snapshot diffs only.

## Exact files changed

1. `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Core.gs`
2. `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Code.gs`
3. `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/Client.html`
4. `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/preview/server.cjs`
5. `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/backend.test.cjs`
6. `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/tests/client-static.test.cjs`

Report deliverable:

- `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/final-security-fix-report.md`

`VERIFICATION.md` and `SETUP.md` were compared with the pre-fix snapshot and are unchanged. No ledger files were edited. A recursive snapshot comparison excluding `node_modules`, `VERIFICATION.md`, and `SETUP.md` reported only the six application/test files listed above.

## Baseline verification

Command, run from the app directory:

```text
npm test
```

Observed baseline result:

```text
ℹ tests 47
ℹ suites 0
ℹ pass 47
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1726.317
```

The pre-fix snapshot comparison produced no differences before test edits.

## Finding 1: backend test clock

### RED

The regression was added before changing the helper. It mocks the host `Date` to `2026-11-26T02:00:00.000Z` (Manila date `2026-11-26`), then proves the backend request date, status date, recorded event date, and Manila timestamp remain on `2026-11-24`.

Command:

```text
node --test --test-name-pattern="backend test requests stay" tests/backend.test.cjs
```

Observed output (exit code 1):

```text
✖ backend test requests stay on 2026-11-24 when the host clock advances (49.2663ms)
ℹ tests 1
ℹ suites 0
ℹ pass 0
ℹ fail 1
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 257.8221

✖ failing tests:

test at tests\backend.test.cjs:82:1
✖ backend test requests stay on 2026-11-24 when the host clock advances (49.2663ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:
  + actual - expected

  + '2026-11-26'
  - '2026-11-24'

      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:91:10)
      at Test.runInAsyncScope (node:async_hooks:226:14)
      at Test.run (node:test:684:25)
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
  generatedMessage: true
  actual: '2026-11-26'
  expected: '2026-11-24'
  operator: 'strictEqual'
  diff: 'simple'
```

Expected failure confirmed: `today_(backend)` used the host-runtime `new Date()` and therefore returned the mocked host date instead of the VM fixed date.

### Minimal correction and GREEN

Only the test helper changed for this finding:

```js
function today_(backend) {
  return backend.context.manilaDateKey_(new backend.context.Date());
}
```

No production code was changed for Finding 1.

Command:

```text
node --test --test-name-pattern="backend test requests stay" tests/backend.test.cjs
```

Observed output (exit code 0):

```text
✔ backend test requests stay on 2026-11-24 when the host clock advances (43.3554ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 242.8215
```

## Finding 2: dangerous device tokens

### RED

Tests were added before validation code. The parity test uses the real backend VM and a real local preview server. It covers:

- Every trigger: `=`, `+`, `-`, `@`, tab, CR, and LF.
- Every trigger after leading spaces.
- Both `scan.status` and `scan.record`.
- Backend/preview response parity.
- Empty-token behavior.
- Write-token rejection above 100 characters.
- Unchanged People and Attendance rows plus unchanged backend write-call counts.
- Zero preview People and Attendance records.
- Exact preservation and recognition of a safe token with leading/trailing spaces.
- Continued acceptance of a 100-character write token.
- Continued status-only acceptance of a safe 101-character token.

A behavioral client test was also added to prove `DEVICE_TOKEN_INVALID` produces readable device-token/site-storage guidance rather than the generic connection error.

Command:

```text
node --test --test-name-pattern="dangerous device tokens|invalid device tokens" tests/backend.test.cjs tests/client-static.test.cjs
```

Observed output (exit code 1):

```text
✖ backend and preview reject dangerous device tokens with matching errors and zero writes (155.2465ms)
✖ invalid device tokens have readable client guidance (3.9004ms)
ℹ tests 2
ℹ suites 0
ℹ pass 0
ℹ fail 2
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 458.9346

✖ failing tests:

test at tests\backend.test.cjs:256:1
✖ backend and preview reject dangerous device tokens with matching errors and zero writes (155.2465ms)
  AssertionError [ERR_ASSERTION]: scan.status backend "=device"
  + actual - expected

  + {
  +   date: '2026-11-24',
  +   device_token: '=device',
  +   mode: 'IN',
  +   name: null,
  +   ok: true,
  +   qr_created_at: '2026-11-24T20:00:00+08:00',
  + }
  - {
  -   error: 'DEVICE_TOKEN_INVALID',
  -   ok: false,
  - }

      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:285:16)
      at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
      at async withPreviewServer (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\backend.test.cjs:95:9)
      at async Test.run (node:test:684:25)
  generatedMessage: false
  actual: { ok: true, date: '2026-11-24', device_token: '=device', mode: 'IN', name: null, qr_created_at: '2026-11-24T20:00:00+08:00' }
  expected: { ok: false, error: 'DEVICE_TOKEN_INVALID' }
  operator: 'deepStrictEqual'
  diff: 'simple'

test at tests\client-static.test.cjs:53:1
✖ invalid device tokens have readable client guidance (3.9004ms)
  AssertionError [ERR_ASSERTION]: The input did not match the regular expression /device token/i. Input:

  'The scan was not recorded. Check your connection and try again.'

      at TestContext.<anonymous> (C:\Users\Ma Christine\Downloads\SSLG MEMOS\SSLG Attendance App\tests\client-static.test.cjs:58:10)
      at Test.runInAsyncScope (node:test:684:25)
  generatedMessage: false
  actual: 'The scan was not recorded. Check your connection and try again.'
  expected: /device token/i
  operator: 'match'
  diff: 'simple'
```

Expected failures confirmed:

1. The backend accepted `=device` for `scan.status` instead of returning `DEVICE_TOKEN_INVALID`.
2. The client mapped `DEVICE_TOKEN_INVALID` to the generic connection failure instead of readable token guidance.

The valid-token boundary guard was also run before implementation and passed, confirming the test preserved existing behavior rather than changing it:

```text
node --test --test-name-pattern="preserves safe device tokens" tests/backend.test.cjs

✔ backend preserves safe device tokens exactly and keeps the 100/101 character boundaries (54.4875ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 317.3051
```

### Minimal implementation

A shared pure validator was added to `Core.gs`:

```js
function deviceTokenError_(deviceToken, forWrite) {
  if (!deviceToken || (forWrite && deviceToken.length > 100)) return 'DEVICE_TOKEN_REQUIRED';
  if (/^[ \t\r\n]*[=+\-@\t\r\n]/.test(deviceToken)) return 'DEVICE_TOKEN_INVALID';
  return null;
}
```

`Code.gs` calls it in both scan handlers before person lookup/upsert or Attendance append. `preview/server.cjs` calls the same validator with `action === 'scan.record'` as the write flag. The validator does not trim or transform the token.

`Client.html` now maps the stable error to:

```text
This browser’s saved device token is invalid. Clear site storage and try again.
```

### Focused GREEN

Command:

```text
node --test --test-name-pattern="backend test requests stay|dangerous device tokens|preserves safe device tokens|invalid device tokens" tests/backend.test.cjs tests/client-static.test.cjs
```

Observed output (exit code 0):

```text
✔ backend test requests stay on 2026-11-24 when the host clock advances (62.9749ms)
✔ backend and preview reject dangerous device tokens with matching errors and zero writes (299.8783ms)
✔ backend preserves safe device tokens exactly and keeps the 100/101 character boundaries (9.4104ms)
✔ invalid device tokens have readable client guidance (3.2019ms)
ℹ tests 4
ℹ suites 0
ℹ pass 4
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 715.2396
```

### Full GREEN

Command, run from the app directory:

```text
npm test
```

Observed result (exit code 0):

```text
ℹ tests 51
ℹ suites 0
ℹ pass 51
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1949.4358
```

The full run included all existing attendance, repeated-IN, unmatched-OUT, CSV, admin, packaging, QR, client, backend, and preview tests.

A final fresh `npm test` rerun after writing this report also passed all 51 tests with zero failures:

```text
ℹ tests 51
ℹ suites 0
ℹ pass 51
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 9282.1772
```

## Implementation rationale

- The backend test helper now constructs `Date` from the VM context, so host-clock changes cannot alter backend fixture dates. Production date behavior is untouched.
- One shared validator keeps Apps Script and preview error behavior aligned and avoids two independently drifting security checks.
- Required/length handling remains first, preserving `DEVICE_TOKEN_REQUIRED` for empty tokens and write tokens over 100 characters.
- The dangerous-prefix check rejects the specified formula/control leaders even after leading spaces or control whitespace, while leaving the original token unchanged.
- Backend validation occurs before person lookup/upsert and Attendance append. Preview validation occurs before map updates or attendance insertion.
- The client error is actionable without adding login, credentials, or new attendance semantics.

## Self-review

- Confirmed the clock regression failed for the intended reason before the helper change and passed afterward.
- Confirmed token/client regressions failed for the intended reasons before production changes.
- Confirmed all seven dangerous triggers and their leading-space variants are exercised for both backend and preview actions.
- Confirmed backend row snapshots and write-call counters remain unchanged after rejected requests.
- Confirmed preview People and Attendance totals remain zero after rejected requests.
- Confirmed safe tokens are not trimmed or transformed, remain recognizable, and retain the 100-character write and 101-character status boundaries.
- Confirmed empty and over-100 write tokens still return `DEVICE_TOKEN_REQUIRED`.
- Confirmed existing repeated scans, unmatched OUT recording, Manila timestamps, name-only registration, admin behavior, and CSV behavior remain green.
- Confirmed only six scoped app/test files differ from the pre-fix snapshot.
- Confirmed `VERIFICATION.md` and `SETUP.md` are unchanged.
- Confirmed no Git commands, commits, subagents, deployment, credentials, or real Sheet writes were used.

## Concerns

No known implementation concerns. Live Apps Script/Google Sheets deployment was intentionally not exercised because the brief prohibits real deployment; verification used the backend VM harness and local preview server. Pre-existing legacy rows are not migrated by this scoped correction; new dangerous token submissions are rejected, and existing CSV neutralization remains unchanged.
