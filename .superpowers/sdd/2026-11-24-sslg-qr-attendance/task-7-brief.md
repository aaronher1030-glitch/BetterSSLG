### Task 7: End-to-End Browser Verification and Acceptance Audit

**Files:**
- Modify only if verification reveals a defect: files inside `SSLG Attendance App/`
- Create: `SSLG Attendance App/VERIFICATION.md`

**Interfaces:**
- Consumes: the running preview from Task 5 and all automated tests.
- Produces: a dated verification record with exact commands, browser checks, observed results, and any deployment checks still pending.

**Binding decisions from prior tasks:**
- Workspace is not a Git repository: do not run Git or create commits.
- Preview API parity with `Code.gs` takes precedence over omissions in the Task 5 plan snippet.
- Do not collect phone numbers or add login; recognition uses the same browser localStorage device token.
- Admin is intentionally public and unauthenticated, as explicitly approved by the owner.
- No real Google deployment or owner credentials are available. Real deployment checks must remain pending.

- [ ] **Step 1: Run the full automated suite**

Working directory: `SSLG Attendance App/`.

```bash
npm install
npm test
```

Expected: core, backend, client static/admin race, QR round-trip, preview, and packaging tests all PASS. Record exact counts and command output.

- [ ] **Step 2: Start the preview**

```bash
npm run preview
```

Expected: `SSLG attendance preview: http://127.0.0.1:4173`.

Use Bash background execution or another bounded local process mechanism. Do not leave an untracked long-running process behind when finished; stop only the preview process you started.

- [ ] **Step 3: Verify the office golden path in a browser**

Use the installed Playwright MCP (preferred) or browser-use MCP. Discover deferred tools through `mcp_list`, inspect schemas with `mcp_get`, and invoke through `mcp_call`. Do not install a replacement browser stack.

1. Open `http://127.0.0.1:4173/?page=admin` at desktop width.
2. Select today's Manila date.
3. Click `Generate QR pair` and accept the confirmation.
4. Confirm two QR images render with IN and OUT labels and a creation timestamp.
5. Confirm the empty attendance list and zero totals render.
6. Type a search term and confirm no console error occurs.
7. Click `Export CSV` and confirm a download named `SSLG-attendance-YYYY-MM-DD.csv` is offered.

- [ ] **Step 4: Verify new-user registration in a mobile browser**

1. Open the generated IN URL in a fresh mobile browser context at 390×844.
2. Confirm the page asks for a name and shows no admin link.
3. Enter `Ana Cruz` and submit.
4. Confirm the success screen shows `Checked in`, `Ana Cruz`, and a Philippines timestamp.
5. Return to the office page and confirm one IN row and totals of one scan and one person.

- [ ] **Step 5: Verify returning recognition and repeated scans**

1. In the same mobile browser context, open the generated OUT URL.
2. Confirm `Ana Cruz` appears without a name form or login.
3. Confirm check-out and verify a second row on the office page.
4. Open the IN URL again, confirm the remembered name, and record another scan.
5. Confirm three separate rows exist and no duplicate-open-session message appears.

- [ ] **Step 6: Verify invalidation and failure states**

1. On the office page, regenerate the pair for the same date.
2. Open the previous IN URL in the mobile browser.
3. Confirm an invalid-code message appears and no row is added.
4. Open the new IN URL, disconnect the network before confirmation, and confirm a not-recorded message rather than success.
5. Reconnect, retry, and confirm one new row is added.
6. Check browser console and network panels for uncaught errors.

- [ ] **Step 7: Verify print layout**

1. Open the office page and generate a valid pair.
2. Invoke print preview or emulate print media.
3. Confirm only the two QR cards print, both are legible, and buttons, filters, attendance records, header, and footer are absent.

- [ ] **Step 8: Write the verification record**

Create `SSLG Attendance App/VERIFICATION.md` containing:

- date and environment;
- exact `npm test` result counts;
- desktop and mobile URLs tested;
- checklist results for Steps 3–7;
- screenshots or exact observed text for registration, recognition, invalidation, and print preview;
- explicit status `Pending owner deployment` for the real Google Apps Script smoke test;
- any defects found and fixed.

Do not write “deployed,” “live,” or a production URL unless the owner's real deployment has been tested. Distinguish automated/local-preview evidence from real Google Apps Script/Sheets evidence.

- [ ] **Step 9: Audit every spec acceptance criterion**

Create a table in `VERIFICATION.md` with all ten acceptance criteria from `docs/superpowers/specs/2026-11-24-sslg-qr-attendance-design.md`, a PASS/PENDING/FAIL verdict, and evidence for each. Criteria 1–7 and 9 can be verified locally where evidence supports them; criterion 8 requires real Sheets evidence and must remain PENDING. Criterion 10 is PASS only if automated tests and local browser checks pass and pending deployment is explicitly disclosed.

- [ ] **Step 10: Final review checkpoint**

Run `npm test` once more after any fixes. Confirm all existing SSLG vault files remain unchanged and all new files are under `SSLG Attendance App/` plus the approved spec, plan, and SDD artifacts. Report any unperformed live-deployment checks explicitly.

If browser verification reveals a defect, stop feature expansion, reproduce it, apply the smallest fix with focused regression coverage where practical, rerun affected/full tests, and document the RED/GREEN evidence and before/after behavior. Do not alter product requirements to make a check pass.

Write the full report to:
`C:/Users/Ma Christine/Downloads/SSLG MEMOS/.superpowers/sdd/2026-11-24-sslg-qr-attendance/task-7-report.md`

Include commands and exact results, browser tool/viewport/environment, observed evidence, defects/fixes, acceptance audit summary, self-review, and pending owner checks. Do not dispatch subagents or reviewers. Return only Status, no commits, one-line test summary, browser-check summary, concerns, and report path.
