# Final security correction brief

App: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

This is a tightly scoped correction to two open final-review findings. Do not redesign the app or change attendance semantics.

## Finding 1: backend test clock is not fully frozen

`tests/backend.test.cjs` injects a VM `FixedDate` whose no-argument value is `2026-11-24T12:00:00.000Z`, but `today_(backend)` calls the host-runtime `new Date()`. Make `today_(backend)` obtain the date from the VM's fixed clock. Add a regression that advances/mocks the host clock to a different Manila date and proves the backend test request date remains `2026-11-24`. Keep production code unchanged for this finding.

## Finding 2: formula/control-leading device tokens can reach Sheets

`Code.gs` accepts caller-controlled `device_token` based only on presence and, for writes, length. `recordScan_` passes it to `upsertPerson_` and the Attendance append. A token beginning with `=`, `+`, `-`, `@`, tab, CR, or LF (including after leading spaces) can therefore become an active/dangerous Sheet value despite a safe name.

Requirements:

- Reject dangerous formula/control-leading device tokens at the backend boundary before any People or Attendance write.
- Apply the same rejection to `scan.status` and `scan.record`, and mirror it in `preview/server.cjs`.
- Return a distinct stable error such as `DEVICE_TOKEN_INVALID`; add a readable client error message.
- Preserve valid tokens, including existing 100-character tokens and the existing status-only acceptance of a safe 101-character token.
- Reject empty tokens with the existing `DEVICE_TOKEN_REQUIRED` and reject write tokens over 100 characters with the existing `DEVICE_TOKEN_REQUIRED`.
- Do not silently trim or transform a supplied token.
- Tests must cover every trigger (`=`, `+`, `-`, `@`, tab, CR, LF), leading-space variants, both backend actions, preview actions, unchanged/zero People and Attendance writes, and continued recognition for a valid token.
- The test helper and parity tests should prove backend/preview error behavior matches.

## Binding constraints

- Daily office attendance; every valid scan recorded, including repeated IN and unmatched OUT.
- Asia/Manila dates/timestamps.
- Name-only registration; same-phone no-login recognition through the existing browser token.
- Google Sheets/Drive remains the source of truth.
- Public unpassworded admin remains unchanged.
- No phone numbers, email, grade/section, login, GPS, event sessions, credentials, real deployment, or Git commands/commits.
- Use strict TDD: write/modify tests, run and record the expected RED, then make the minimal production changes and run GREEN.
- Do not dispatch subagents.
- Do not edit `VERIFICATION.md`, `SETUP.md`, or ledger files; the controller will update those after independent verification.

## Report contract

Write the full report to `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/final-security-fix-report.md`.

Include exact files changed, RED command/output and expected failures, GREEN command/output, implementation rationale, self-review, and concerns. Return only status, no-commit confirmation, one-line test summary, and concerns.
