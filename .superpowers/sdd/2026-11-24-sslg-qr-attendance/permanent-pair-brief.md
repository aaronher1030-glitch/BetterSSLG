# Permanent reusable QR pair — implementation brief

App: `C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App`

## Approved product change

The user explicitly replaced the original daily-regeneration requirement with:

- One permanent IN code and one permanent OUT code.
- The exact same QR images/URLs are reused every day.
- There is no regeneration, rotation, expiration, or replacement option in the app.
- Each accepted scan is still dated with the server's current Asia/Manila calendar date and exact server timestamp.
- Every valid scan remains append-only, including repeated IN and unmatched OUT.
- Name-only registration, same-browser recognition, public unpassworded admin, Google Sheets, and all existing security protections remain unchanged.

## Binding implementation decisions

1. **Date-free QR payloads:** `in_url` and `out_url` contain `page=scan`, `mode`, and `code` only. No `date` parameter. If a caller supplies a date anyway, it is not used to expire or redirect the scan; the server date is authoritative.
2. **Permanent storage:** replace the `Daily Codes` tab with `QR Codes`, with headers `in_code`, `out_code`, `created_at`, `created_by`. It contains exactly one row. No live deployment exists, so no legacy migration is required. `People` and `Attendance` schemas remain unchanged.
3. **Idempotent creation:** `admin.generate` and public `adminGenerate` retain their action/function names for client compatibility, but now mean “get or create the permanent pair.” The first request creates the row; every later request returns the same codes, URLs, and `created_at` without writing or consuming UUIDs. Use the existing script lock to prevent duplicate first creation.
4. **No reset API/UI:** do not add rotate/delete/reset actions. Invalid, unknown, and wrong-mode codes are still rejected without writes.
5. **Admin UI:** heading and helper text must describe a permanent pair reused every day. Replace “Generate QR pair” with “Show permanent QR pair”; remove the regeneration confirmation. Cards show `Reusable every day` and the original creation timestamp. Changing the attendance-date filter must not hide, clear, regenerate, or date-bind the QR cards. Date filtering/search/export remain daily.
6. **Student UI:** scan requests need only mode/code/device token; display the server-returned current Manila date. Remove obsolete wrong-date/expired/newer-code wording. Landing copy refers to the posted permanent codes, not “today's” codes.
7. **Preview parity:** preview must use the same permanent record, idempotent action semantics, date-free URLs, current-Manila scan dates, errors, and zero-write rejection behavior as Apps Script.
8. Keep the client `admin.generate` action mapping and `adminGenerate` wrapper to avoid an unnecessary transport rename.

## Tests required before production edits

Use strict TDD and record actual RED output.

- Core: permanent record has no date; QR validation accepts the same record on different Manila dates and without a request date; server-returned date changes with `now`; wrong mode/unknown code/missing record still reject; token/name/CSV protections remain.
- Backend: `QR Codes` schema; first generation creates exactly one row; repeated generation returns identical codes/URLs/created_at and performs no additional code-sheet writes/UUID consumption; the same code records scans on two simulated Manila dates with the correct per-row dates; supplied stale/future request dates do not override server date; no replacement endpoint exists; all prior valid/invalid, repeated IN, unmatched OUT, returning-user, security, admin-list/export, wrapper, lock, and `doGet` tests are adapted without weakening them.
- Preview: same permanent pair across repeated generate calls and two mocked Manila dates; date-free URLs; daily rows/totals; rejected scans write nothing.
- Client/admin: permanent copy, no confirmation/regeneration language, no date-based QR clearing/stale-generation guard, date filter still controls records only, and permanent cards survive date changes. Preserve attendance list race/error tests.
- QR round-trip: exact date-free IN and OUT payloads decode.
- Packaging/setup-facing tests: `QR Codes` schema naming and no hard-coded secrets remain covered.
- Remove obsolete tests for daily date validation, daily invalidation, and regeneration rather than retaining assertions for removed behavior.

## Documentation scope

Do not edit `SETUP.md`, `VERIFICATION.md`, the design spec, plan, or SDD ledger in this dispatch. The controller will update those after verification. You may report needed wording changes.

## Constraints

- No Git commands or commits; workspace is not a Git repository.
- Do not dispatch subagents.
- No real Google deployment, credentials, Spreadsheet ID, or production URLs.
- Do not add phone numbers, email, grade/section, login, GPS, event sessions, private admin auth, or another database.
- Do not change attendance append-only semantics or weaken formula-injection defenses.

## Report contract

Write the full report to `C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/permanent-pair-report.md`.

Include exact files changed, RED commands/output and why they failed, implementation details, GREEN focused/full output, self-review, documentation needs, and concerns. Return only status, no-commit confirmation, one-line test summary, and concerns.
