# SSLG QR Office Attendance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deployment-ready Google Apps Script web app that creates one permanent SSLG office IN/OUT QR pair, recognizes returning users on the same phone, and records every valid scan under the current Manila date in a Google Spreadsheet.

**Architecture:** A single Apps Script deployment serves the student and office pages and reads/writes three Spreadsheet tabs. Pure JavaScript helpers handle dates, code validation, names, and CSV; Apps Script services handle routing, Sheets, locks, and HTML. A local Node preview mocks the Apps Script API so the complete flow can be tested without Google credentials.

**Tech Stack:** Google Apps Script V8, Google Sheets, HtmlService, vanilla HTML/CSS/JavaScript, `qrcode-generator`, Node.js built-in test runner, `jsqr`, and `pngjs` for QR verification.

**Spec:** `docs/superpowers/specs/2026-11-24-sslg-qr-attendance-design.md`

> **2026-11-25 amendment:** The user replaced daily regeneration with one permanent, date-free, non-replaceable IN/OUT pair. This amendment and the updated spec supersede daily-generation, date-expiry, replacement, and `Daily Codes` details in the historical task steps below. The implemented change and evidence are recorded in `.superpowers/sdd/2026-11-24-sslg-qr-attendance/permanent-pair-report.md`.

## Global Constraints

- Project root: `SSLG Attendance App/` inside the current workspace.
- Script timezone: `Asia/Manila`.
- Attendance scope: daily office attendance only.
- QR lifecycle: one permanent date-free IN/OUT pair, created idempotently once and reused every day; no regeneration, reset, rotation, or expiry.
- Scan semantics: every valid scan creates one row; repeated IN scans and unmatched OUT scans are allowed.
- Registration: name only, once per phone/browser.
- Recognition: random device token in local storage; no phone number, email, grade, section, login, or SMS.
- Admin access: no password and no admin link in the student flow; anyone with the direct admin URL can access it.
- Source of truth: one Google Spreadsheet with `QR Codes`, `People`, and `Attendance` tabs.
- No credentials, API keys, or live deployment claims are committed.
- The workspace is not a Git repository. Do not create commits; use review checkpoints and preserve all existing files.

---

## File Structure

```text
SSLG Attendance App/
├── appsscript.json
├── .gitignore
├── Core.gs
├── Code.gs
├── Index.html
├── Styles.html
├── Client.html
├── QRCodeLib.html
├── package.json
├── package-lock.json
├── SETUP.md
├── preview/
│   └── server.cjs
└── tests/
    ├── core.test.cjs
    ├── backend.test.cjs
    ├── client-static.test.cjs
    ├── qr.test.cjs
    ├── preview.test.cjs
    └── packaging.test.cjs
```

- `Core.gs`: pure, testable helpers and schema constants.
- `Code.gs`: Apps Script routes, Sheet persistence, locks, and deployment URL handling.
- `Index.html`: document shell and include points.
- `Styles.html`: responsive visual system and print styles.
- `Client.html`: student and office browser logic plus the Apps Script/local-fetch adapter.
- `QRCodeLib.html`: locally bundled QR encoder with its license notice.
- `preview/server.cjs`: static include renderer and in-memory API with the same action names as `Code.gs`.
- `tests/`: isolated unit, backend, QR-decoding, and preview API tests.
- `SETUP.md`: exact Google Sheet and Apps Script deployment procedure.

---

### Task 1: Project Scaffold and Pure Attendance Rules

**Files:**
- Create: `SSLG Attendance App/package.json`
- Create: `SSLG Attendance App/.gitignore`
- Create: `SSLG Attendance App/Core.gs`
- Test: `SSLG Attendance App/tests/core.test.cjs`

**Interfaces:**
- Consumes: standard JavaScript `Date`, strings, arrays, and an injected token factory.
- Produces:
  - `SSLG_ATTENDANCE_TIME_ZONE = 'Asia/Manila'`
  - `DAILY_CODE_HEADERS`, `PEOPLE_HEADERS`, `ATTENDANCE_HEADERS`
  - `normalizeName_(value) -> string`
  - `manilaDateKey_(date = new Date()) -> string`
  - `manilaTimestamp_(date = new Date()) -> string`
  - `createDailyCodeRecord_(dateKey, now, makeToken) -> {date,in_code,out_code,created_at,created_by}`
  - `validateScan_(params, record, now = new Date()) -> {ok:true,date,mode,qr_created_at}|{ok:false,error}`
  - `csvEscape_(value) -> string`
  - `toCsv_(headers, rows) -> string`

- [ ] **Step 1: Create package metadata**

Write `SSLG Attendance App/package.json`:

```json
{
  "name": "sslg-office-attendance",
  "version": "1.0.0",
  "private": true,
  "description": "Daily SSLG office QR check-in and check-out app for Google Sheets",
  "scripts": {
    "test": "node --test",
    "test:core": "node --test tests/core.test.cjs",
    "preview": "node preview/server.cjs"
  },
  "devDependencies": {
    "jsqr": "^1.4.0",
    "pngjs": "^7.0.0",
    "qrcode-generator": "^1.4.4"
  },
  "engines": {
    "node": ">=20"
  }
}
```

Write `SSLG Attendance App/.gitignore`:

```gitignore
node_modules/
.env
.env.*
*.log
.DS_Store
```

- [ ] **Step 2: Write failing core tests**

Create `SSLG Attendance App/tests/core.test.cjs`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'Core.gs'), 'utf8');
const context = vm.createContext({ console });
vm.runInContext(source, context, { filename: 'Core.gs' });

const api = (name, ...args) => context[name](...args);

test('normalizes a registered name and rejects blank names', () => {
  assert.equal(api('normalizeName_', '  Maria   Clara  '), 'Maria Clara');
  assert.throws(() => api('normalizeName_', '   '), /NAME_REQUIRED/);
  assert.throws(() => api('normalizeName_', 'x'.repeat(81)), /NAME_TOO_LONG/);
});

test('uses the Manila calendar date across UTC midnight', () => {
  const date = new Date('2026-11-23T16:30:00.000Z');
  assert.equal(api('manilaDateKey_', date), '2026-11-24');
  assert.equal(api('manilaTimestamp_', date), '2026-11-24T00:30:00+08:00');
});

test('rejects impossible calendar dates', () => {
  assert.throws(() => api('createDailyCodeRecord_', '2026-02-30', new Date(), () => 'token-a'), /INVALID_DATE/);
  assert.throws(() => api('createDailyCodeRecord_', '2026-13-01', new Date(), () => 'token-a'), /INVALID_DATE/);
});

test('creates distinct IN and OUT tokens and a creation timestamp', () => {
  const tokens = ['in-token', 'out-token'];
  const record = api('createDailyCodeRecord_', '2026-11-24', new Date('2026-11-24T01:00:00Z'), () => tokens.shift());
  assert.deepEqual(JSON.parse(JSON.stringify(record)), {
    date: '2026-11-24',
    in_code: 'in-token',
    out_code: 'out-token',
    created_at: '2026-11-24T09:00:00+08:00',
    created_by: 'SSLG Office'
  });
});

test('validates matching code, mode, and current Manila date', () => {
  const record = {
    date: '2026-11-24',
    in_code: 'in-token',
    out_code: 'out-token',
    created_at: '2026-11-24T00:00:00+08:00'
  };
  const now = new Date('2026-11-24T02:00:00Z');
  assert.deepEqual(JSON.parse(JSON.stringify(api('validateScan_', { date: '2026-11-24', mode: 'IN', code: 'in-token' }, record, now))), {
    ok: true,
    date: '2026-11-24',
    mode: 'IN',
    qr_created_at: '2026-11-24T00:00:00+08:00'
  });
  assert.equal(api('validateScan_', { date: '2026-11-24', mode: 'IN', code: 'old-token' }, record, now).error, 'INVALID_CODE');
  assert.equal(api('validateScan_', { date: '2026-11-24', mode: 'OUT', code: 'in-token' }, record, now).error, 'MODE_MISMATCH');
  assert.equal(api('validateScan_', { date: '2026-11-24', mode: 'IN', code: 'in-token' }, record, new Date('2026-11-25T02:00:00Z')).error, 'CODE_EXPIRED');
});

test('escapes CSV commas, quotes, and newlines', () => {
  assert.equal(api('csvEscape_', 'Dela Cruz, "Ana"'), '"Dela Cruz, ""Ana"""');
  assert.equal(api('csvEscape_', 'Line one\nLine two'), '"Line one\nLine two"');
  assert.equal(api('toCsv_', ['name', 'mode'], [['Ana', 'IN']]), '"name","mode"\n"Ana","IN"');
});
```

- [ ] **Step 3: Run tests and verify the expected failure**

Run:

```bash
cd "SSLG Attendance App"
npm install
npm run test:core
```

Expected: FAIL because `Core.gs` does not exist.

- [ ] **Step 4: Implement the pure core**

Create `SSLG Attendance App/Core.gs`:

```javascript
const SSLG_ATTENDANCE_TIME_ZONE = 'Asia/Manila';

const DAILY_CODE_HEADERS = ['date', 'in_code', 'out_code', 'created_at', 'created_by'];
const PEOPLE_HEADERS = ['device_token', 'name', 'first_seen_at', 'last_seen_at'];
const ATTENDANCE_HEADERS = ['event_id', 'date', 'scanned_at', 'mode', 'name', 'device_token', 'qr_created_at'];

function normalizeName_(value) {
  const name = String(value == null ? '' : value).trim().replace(/\s+/g, ' ');
  if (!name) throw new Error('NAME_REQUIRED');
  if (name.length > 80) throw new Error('NAME_TOO_LONG');
  return name;
}

function manilaParts_(date) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: SSLG_ATTENDANCE_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23'
  }).formatToParts(date);
  const result = {};
  parts.forEach(part => {
    if (part.type !== 'literal') result[part.type] = part.value;
  });
  return result;
}

function manilaDateKey_(date = new Date()) {
  const parts = manilaParts_(date);
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function manilaTimestamp_(date = new Date()) {
  const parts = manilaParts_(date);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}+08:00`;
}

function createDailyCodeRecord_(dateKey, now, makeToken) {
  const normalizedDate = String(dateKey);
  const parsedDate = new Date(`${normalizedDate}T00:00:00.000Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(normalizedDate) || Number.isNaN(parsedDate.getTime()) || parsedDate.toISOString().slice(0, 10) !== normalizedDate) {
    throw new Error('INVALID_DATE');
  }
  const inCode = makeToken();
  const outCode = makeToken();
  if (!inCode || !outCode || inCode === outCode) throw new Error('TOKEN_GENERATION_FAILED');
  return {
    date: normalizedDate,
    in_code: inCode,
    out_code: outCode,
    created_at: manilaTimestamp_(now),
    created_by: 'SSLG Office'
  };
}

function validateScan_(params, record, now = new Date()) {
  if (!params || typeof params !== 'object') return { ok: false, error: 'INVALID_REQUEST' };
  const date = String(params.date || '');
  const mode = String(params.mode || '').toUpperCase();
  const code = String(params.code || '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !['IN', 'OUT'].includes(mode) || !code) {
    return { ok: false, error: 'INVALID_REQUEST' };
  }
  if (!record) return { ok: false, error: 'CODE_NOT_FOUND' };
  if (record.date !== date) return { ok: false, error: 'WRONG_DATE' };
  if (manilaDateKey_(now) !== date) return { ok: false, error: 'CODE_EXPIRED' };
  const expected = mode === 'IN' ? record.in_code : record.out_code;
  if (code !== expected) return { ok: false, error: mode === 'IN' ? 'INVALID_CODE' : 'MODE_MISMATCH' };
  return { ok: true, date, mode, qr_created_at: record.created_at };
}

function csvEscape_(value) {
  return `"${String(value == null ? '' : value).replace(/"/g, '""')}"`;
}

function toCsv_(headers, rows) {
  return [headers, ...rows]
    .map(row => row.map(csvEscape_).join(','))
    .join('\n');
}
```

- [ ] **Step 5: Run tests and verify they pass**

Run:

```bash
npm run test:core
```

Expected: all core tests PASS.

- [ ] **Step 6: Review checkpoint**

Confirm the project directory contains only the intended scaffold and pure core. Do not modify any existing vault files. No commit is created because the workspace is not a Git repository.

---

### Task 2: Google Sheets Backend and Daily Code Lifecycle

**Files:**
- Create: `SSLG Attendance App/Code.gs`
- Test: `SSLG Attendance App/tests/backend.test.cjs`

**Interfaces:**
- Consumes: all Task 1 helpers; Apps Script `PropertiesService`, `SpreadsheetApp`, `LockService`, `Utilities`, `ScriptApp`, `HtmlService`, and `ContentService`.
- Produces:
  - `doGet(event) -> HtmlOutput`
  - `doPost(event) -> TextOutput`
  - `ensureSchema_() -> void`
  - `generateDailyCodes_(dateKey) -> record with in_url and out_url`
  - `getScanStatus_(params) -> {ok,date,mode,name,device_token,qr_created_at}`
  - `recordScan_(params) -> {ok,event}`
  - `listAttendance_(dateKey, query) -> {ok,rows,totals}`
  - `exportAttendanceCsv_(dateKey) -> {ok,csv,filename}`
  - `scanStatus(payload)`, `scanRecord(payload)`, `adminGenerate(payload)`, `adminList(payload)`, `adminExport(payload)` as public `google.script.run` wrappers

- [ ] **Step 1: Write a failing backend test harness**

Create `SSLG Attendance App/tests/backend.test.cjs`. The harness must load `Core.gs` and `Code.gs` into one VM context and provide in-memory implementations of `SpreadsheetApp`, `PropertiesService`, `LockService`, `Utilities`, `ScriptApp`, `HtmlService`, and `ContentService`.

Include these tests:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function loadBackend() {
  const sheets = new Map();
  const properties = { SPREADSHEET_ID: 'sheet-test-id' };
  let uuid = 0;
  let baseUrl = 'https://script.test/exec';

  function makeSheet(name) {
    if (!sheets.has(name)) sheets.set(name, []);
    const rows = sheets.get(name);
    return {
      getLastRow: () => rows.length,
      getRange: (row, column, count) => ({
        getValues: () => rows.slice(row - 1, row - 1 + count),
        setValues: values => { rows.splice(row - 1, count, ...values); }
      }),
      appendRow: row => rows.push(row),
      getLastColumn: () => rows[0] ? rows[0].length : 0,
      getFrozenRows: () => 0,
      setFrozenRows: () => {}
    };
  }

  const spreadsheet = {
    getSheetByName: name => sheets.has(name) ? makeSheet(name) : null,
    insertSheet: name => { sheets.set(name, []); return makeSheet(name); }
  };

  const context = vm.createContext({
    console,
    Date,
    Intl,
    JSON,
    PropertiesService: { getScriptProperties: () => ({ getProperty: key => properties[key] || null }) },
    SpreadsheetApp: { openById: () => spreadsheet },
    LockService: { getScriptLock: () => ({ tryLock: () => true, releaseLock: () => {} }) },
    Utilities: { getUuid: () => `uuid-${++uuid}` },
    ScriptApp: { getService: () => ({ getUrl: () => baseUrl }) },
    HtmlService: { createTemplateFromFile: () => ({ evaluate: () => 'html' }) },
    ContentService: {
      MimeType: { JSON: 'application/json' },
      createTextOutput: text => ({ setMimeType: () => ({ text }) })
    }
  });

  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Core.gs'), 'utf8'), context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Code.gs'), 'utf8'), context);
  return { context, sheets };
}

function post(backend, action, payload) {
  const output = backend.context.doPost({ postData: { contents: JSON.stringify({ action, payload }) } });
  return JSON.parse(output.text);
}

function today_(backend) {
  return backend.context.manilaDateKey_(new Date());
}

test('creates the documented Sheet tabs and headers', () => {
  const backend = loadBackend();
  backend.context.ensureSchema_();
  assert.deepEqual(backend.sheets.get('Daily Codes')[0], backend.context.DAILY_CODE_HEADERS);
  assert.deepEqual(backend.sheets.get('People')[0], backend.context.PEOPLE_HEADERS);
  assert.deepEqual(backend.sheets.get('Attendance')[0], backend.context.ATTENDANCE_HEADERS);
});

test('generates daily codes and invalidates the previous pair', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const first = backend.context.generateDailyCodes_(date);
  const second = backend.context.generateDailyCodes_(date);
  assert.notEqual(first.in_code, second.in_code);
  assert.equal(post(backend, 'scan.status', { date, mode: 'IN', code: first.in_code, device_token: 'device-a' }).error, 'INVALID_CODE');
  assert.equal(post(backend, 'scan.status', { date, mode: 'OUT', code: second.out_code, device_token: 'device-a' }).ok, true);
  assert.equal(backend.sheets.get('Daily Codes').length, 2);
});

test('registers a device once and records every valid scan', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generateDailyCodes_(date);
  const first = post(backend, 'scan.record', {
    date, mode: 'IN', code: generated.in_code,
    device_token: 'device-a', name: '  Ana   Cruz '
  });
  assert.equal(first.ok, true);
  assert.equal(first.event.name, 'Ana Cruz');
  const status = post(backend, 'scan.status', {
    date, mode: 'OUT', code: generated.out_code, device_token: 'device-a'
  });
  assert.equal(status.name, 'Ana Cruz');
  const second = post(backend, 'scan.record', {
    date, mode: 'OUT', code: generated.out_code, device_token: 'device-a'
  });
  const third = post(backend, 'scan.record', {
    date, mode: 'IN', code: generated.in_code, device_token: 'device-a'
  });
  assert.equal(second.ok, true);
  assert.equal(third.ok, true);
  assert.equal(backend.sheets.get('People').length, 2);
  assert.equal(backend.sheets.get('Attendance').length, 4);
});

test('rejects invalid codes without writing attendance', () => {
  const backend = loadBackend();
  const date = today_(backend);
  backend.context.generateDailyCodes_(date);
  const result = post(backend, 'scan.record', {
    date, mode: 'IN', code: 'wrong', device_token: 'device-a', name: 'Ana Cruz'
  });
  assert.equal(result.ok, false);
  assert.equal(backend.sheets.get('Attendance').length, 1);
});

test('filters attendance and exports CSV', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generateDailyCodes_(date);
  post(backend, 'scan.record', { date, mode: 'IN', code: generated.in_code, device_token: 'device-a', name: 'Ana Cruz' });
  const listed = backend.context.listAttendance_(date, 'ana');
  assert.equal(listed.rows.length, 1);
  assert.equal(listed.totals.in, 1);
  const exported = backend.context.exportAttendanceCsv_(date);
  assert.equal(exported.ok, true);
  assert.match(exported.csv, /"Ana Cruz"/);
});
```

- [ ] **Step 2: Run tests and verify the expected failure**

Run:

```bash
node --test tests/backend.test.cjs
```

Expected: FAIL because `Code.gs` does not exist.

- [ ] **Step 3: Implement configuration, schema, routing, and persistence**

Create `SSLG Attendance App/Code.gs` with these exact responsibilities:

```javascript
function getConfig_() {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
  if (!spreadsheetId) throw new Error('SPREADSHEET_NOT_CONFIGURED');
  return { spreadsheetId };
}

function openSpreadsheet_() {
  return SpreadsheetApp.openById(getConfig_().spreadsheetId);
}

function ensureSheet_(spreadsheet, name, headers) {
  let sheet = spreadsheet.getSheetByName(name);
  if (!sheet) sheet = spreadsheet.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function ensureSchema_() {
  const spreadsheet = openSpreadsheet_();
  ensureSheet_(spreadsheet, 'Daily Codes', DAILY_CODE_HEADERS);
  ensureSheet_(spreadsheet, 'People', PEOPLE_HEADERS);
  ensureSheet_(spreadsheet, 'Attendance', ATTENDANCE_HEADERS);
}

function sheetRows_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  return values.map(row => Object.fromEntries(headers.map((header, index) => [header, row[index]])));
}

function getDailyCodeRecord_(dateKey) {
  ensureSchema_();
  const rows = sheetRows_(openSpreadsheet_().getSheetByName('Daily Codes'));
  return rows.find(row => row.date === dateKey) || null;
}

function getWebAppUrl_() {
  return ScriptApp.getService().getUrl();
}

function generateDailyCodes_(dateKey) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) throw new Error('SHEET_BUSY');
  try {
    ensureSchema_();
    const spreadsheet = openSpreadsheet_();
    const sheet = spreadsheet.getSheetByName('Daily Codes');
    const rows = sheetRows_(sheet);
    const existingIndex = rows.findIndex(row => row.date === dateKey);
    const record = createDailyCodeRecord_(dateKey, new Date(), () => Utilities.getUuid());
    const values = DAILY_CODE_HEADERS.map(header => record[header]);
    if (existingIndex >= 0) {
      sheet.getRange(existingIndex + 2, 1, 1, values.length).setValues([values]);
    } else {
      sheet.appendRow(values);
    }
    const baseUrl = getWebAppUrl_();
    return {
      ...record,
      in_url: `${baseUrl}?page=scan&date=${encodeURIComponent(dateKey)}&mode=IN&code=${encodeURIComponent(record.in_code)}`,
      out_url: `${baseUrl}?page=scan&date=${encodeURIComponent(dateKey)}&mode=OUT&code=${encodeURIComponent(record.out_code)}`
    };
  } finally {
    lock.releaseLock();
  }
}
```

Implement profile lookup and scan recording with these rules:

```javascript
function findPersonByToken_(deviceToken) {
  ensureSchema_();
  const rows = sheetRows_(openSpreadsheet_().getSheetByName('People'));
  return rows.find(row => row.device_token === deviceToken) || null;
}

function upsertPerson_(deviceToken, name, now) {
  const spreadsheet = openSpreadsheet_();
  const sheet = spreadsheet.getSheetByName('People');
  const rows = sheetRows_(sheet);
  const existingIndex = rows.findIndex(row => row.device_token === deviceToken);
  if (existingIndex >= 0) {
    const existing = rows[existingIndex];
    sheet.getRange(existingIndex + 2, 1, 1, PEOPLE_HEADERS.length).setValues([[
      deviceToken,
      name,
      existing.first_seen_at,
      manilaTimestamp_(now)
    ]]);
  } else {
    sheet.appendRow([deviceToken, name, manilaTimestamp_(now), manilaTimestamp_(now)]);
  }
}

function getScanStatus_(params) {
  const record = getDailyCodeRecord_(String(params.date || ''));
  const validation = validateScan_(params, record, new Date());
  if (!validation.ok) return validation;
  const deviceToken = String(params.device_token || '');
  if (!deviceToken) return { ok: false, error: 'DEVICE_TOKEN_REQUIRED' };
  const person = findPersonByToken_(deviceToken);
  return {
    ok: true,
    date: validation.date,
    mode: validation.mode,
    name: person ? person.name : null,
    device_token: deviceToken,
    qr_created_at: validation.qr_created_at
  };
}

function recordScan_(params) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) throw new Error('SHEET_BUSY');
  try {
    const record = getDailyCodeRecord_(String(params.date || ''));
    const validation = validateScan_(params, record, new Date());
    if (!validation.ok) return validation;
    const deviceToken = String(params.device_token || '');
    if (!deviceToken || deviceToken.length > 100) return { ok: false, error: 'DEVICE_TOKEN_REQUIRED' };
    const now = new Date();
    const existing = findPersonByToken_(deviceToken);
    const name = normalizeName_(existing ? existing.name : params.name);
    upsertPerson_(deviceToken, name, now);
    const event = {
      event_id: Utilities.getUuid(),
      date: validation.date,
      scanned_at: manilaTimestamp_(now),
      mode: validation.mode,
      name,
      device_token: deviceToken,
      qr_created_at: validation.qr_created_at
    };
    openSpreadsheet_().getSheetByName('Attendance').appendRow(
      ATTENDANCE_HEADERS.map(header => event[header])
    );
    return { ok: true, event };
  } finally {
    lock.releaseLock();
  }
}
```

Implement attendance reads and CSV using the same schema:

```javascript
function filteredAttendance_(dateKey, query) {
  ensureSchema_();
  const rows = sheetRows_(openSpreadsheet_().getSheetByName('Attendance'));
  const normalizedQuery = String(query || '').trim().toLowerCase();
  return rows
    .filter(row => row.date === dateKey)
    .filter(row => !normalizedQuery || String(row.name).toLowerCase().includes(normalizedQuery))
    .sort((a, b) => String(b.scanned_at).localeCompare(String(a.scanned_at)));
}

function listAttendance_(dateKey, query) {
  const rows = filteredAttendance_(dateKey, query);
  const allRows = filteredAttendance_(dateKey, '');
  return {
    ok: true,
    rows,
    totals: {
      in: allRows.filter(row => row.mode === 'IN').length,
      out: allRows.filter(row => row.mode === 'OUT').length,
      people: new Set(allRows.map(row => row.device_token)).size,
      scans: allRows.length
    }
  };
}

function exportAttendanceCsv_(dateKey) {
  const rows = filteredAttendance_(dateKey, '');
  return {
    ok: true,
    csv: toCsv_(ATTENDANCE_HEADERS, rows.map(row => ATTENDANCE_HEADERS.map(header => row[header]))),
    filename: `SSLG-attendance-${dateKey}.csv`
  };
}
```

Implement request and page routing:

```javascript
function jsonResponse_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(ContentService.MimeType.JSON);
}

function errorCode_(error) {
  return error && error.message ? error.message : 'REQUEST_FAILED';
}

function doPost(event) {
  try {
    const body = JSON.parse(event.postData.contents);
    const payload = body.payload || {};
    let result;
    switch (body.action) {
      case 'scan.status':
        result = getScanStatus_(payload);
        break;
      case 'scan.record':
        result = recordScan_(payload);
        break;
      case 'admin.generate':
        result = { ok: true, record: generateDailyCodes_(payload.date) };
        break;
      case 'admin.list':
        result = listAttendance_(payload.date, payload.query);
        break;
      case 'admin.export':
        result = exportAttendanceCsv_(payload.date);
        break;
      default:
        result = { ok: false, error: 'UNKNOWN_ACTION' };
    }
    return jsonResponse_(result);
  } catch (error) {
    return jsonResponse_({ ok: false, error: errorCode_(error) });
  }
}

function scanStatus(payload) {
  return getScanStatus_(payload || {});
}

function scanRecord(payload) {
  return recordScan_(payload || {});
}

function adminGenerate(payload) {
  return { ok: true, record: generateDailyCodes_((payload || {}).date) };
}

function adminList(payload) {
  return listAttendance_((payload || {}).date, (payload || {}).query);
}

function adminExport(payload) {
  return exportAttendanceCsv_((payload || {}).date);
}

function doGet(event) {
  const page = event && event.parameter && event.parameter.page;
  if (page === 'admin' || page === 'scan') {
    return HtmlService.createTemplateFromFile('Index').evaluate();
  }
  return HtmlService.createTemplateFromFile('Index').evaluate();
}
```

- [ ] **Step 4: Run backend and core tests**

Run:

```bash
npm run test:core
node --test tests/backend.test.cjs
```

Expected: all tests PASS.

- [ ] **Step 5: Review checkpoint**

Inspect `Code.gs` for console logging, credentials, phone-number fields, in/out pairing rules, and any write before code validation. None are allowed. Verify a regenerated code pair leaves one `Daily Codes` data row for the date.

---

### Task 3: Student Registration, Recognition, and Confirmation UI

**Files:**
- Create: `SSLG Attendance App/Index.html`
- Create: `SSLG Attendance App/Styles.html`
- Create: `SSLG Attendance App/Client.html`
- Test: `SSLG Attendance App/tests/client-static.test.cjs`

**Interfaces:**
- Consumes: `scan.status` and `scan.record` actions from Task 2.
- Produces:
  - `api(action, payload) -> Promise<object>`
  - `getDeviceToken_() -> string`
  - `renderScanPage_(params) -> Promise<void>`
  - `submitScan_(name) -> Promise<void>`
  - readable error messages for every backend error code.

- [ ] **Step 1: Create the HTML shell and include points**

Create `SSLG Attendance App/Index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#102a43">
  <title>SSLG Office Attendance</title>
  <?!= include('Styles'); ?>
</head>
<body>
  <header class="site-header">
    <div class="brand-mark" aria-hidden="true">S</div>
    <div>
      <p class="eyebrow">SSLG Office</p>
      <h1>Attendance</h1>
    </div>
  </header>
  <main id="app" tabindex="-1">
    <section class="loading-card" aria-live="polite">
      <div class="spinner" aria-hidden="true"></div>
      <p>Loading attendance…</p>
    </section>
  </main>
  <footer class="site-footer">Benigno S. Aquino National High School · SSLG</footer>
  <script><?!= include('QRCodeLib'); ?></script>
  <?!= include('Client'); ?>
</body>
</html>
```

- [ ] **Step 2: Add the responsive visual system**

Create `SSLG Attendance App/Styles.html`:

```html
<style>
  :root {
    color-scheme: light;
    --navy: #102a43;
    --teal: #0f766e;
    --teal-dark: #0b5d56;
    --paper: #f6f3ec;
    --white: #ffffff;
    --ink: #172b4d;
    --muted: #627d98;
    --line: #d9e2ec;
    --amber: #b45309;
    --amber-bg: #fff7ed;
    --red: #b42318;
    --red-bg: #fef3f2;
    --green-bg: #ecfdf3;
    --shadow: 0 18px 50px rgba(16, 42, 67, 0.10);
    --font-body: "Segoe UI", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    --font-display: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
    font-family: var(--font-body);
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    color: var(--ink);
    background:
      radial-gradient(circle at 10% 0%, rgba(15, 118, 110, 0.12), transparent 32rem),
      var(--paper);
  }
  button, input { font: inherit; }
  button { cursor: pointer; }
  button:disabled { cursor: wait; opacity: 0.65; }
  [hidden] { display: none !important; }

  .site-header {
    width: min(100% - 32px, 960px);
    margin: 24px auto 18px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-mark {
    width: 46px;
    height: 46px;
    display: grid;
    place-items: center;
    border-radius: 14px;
    color: var(--white);
    background: var(--navy);
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.04em;
  }
  .eyebrow {
    margin: 0 0 4px;
    color: var(--teal);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.13em;
    text-transform: uppercase;
  }
  h1, h2, p { margin-top: 0; }
  h1 { margin-bottom: 0; color: var(--navy); font-family: var(--font-display); font-size: 1.25rem; }
  h2 { margin-bottom: 12px; color: var(--navy); font-family: var(--font-display); font-size: clamp(1.55rem, 5vw, 2rem); font-weight: 600; letter-spacing: -0.035em; }

  #app {
    width: min(100% - 32px, 960px);
    margin: 0 auto;
    outline: none;
  }
  .card {
    margin-bottom: 18px;
    padding: clamp(22px, 5vw, 34px);
    border: 1px solid rgba(217, 226, 236, 0.9);
    border-radius: 24px;
    background: var(--white);
    box-shadow: var(--shadow);
  }
  .scan-card, .success-card, .loading-card { max-width: 480px; margin-inline: auto; }
  .scan-meta { color: var(--muted); font-size: 0.9rem; }
  .welcome { margin: 26px 0 4px; color: var(--muted); }
  .registered-name { margin-bottom: 24px; color: var(--navy); font-size: 1.45rem; font-weight: 750; overflow-wrap: anywhere; }
  .helper-text { margin: 14px 0 0; color: var(--muted); font-size: 0.84rem; line-height: 1.55; }

  .field { display: grid; gap: 8px; margin: 18px 0; color: var(--navy); font-size: 0.86rem; font-weight: 700; }
  .field input {
    width: 100%;
    min-height: 52px;
    padding: 12px 14px;
    border: 1px solid var(--line);
    border-radius: 12px;
    color: var(--ink);
    background: #fbfcfd;
    outline: none;
  }
  .field input:focus { border-color: var(--teal); box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.13); }
  .button {
    width: 100%;
    min-height: 52px;
    padding: 13px 18px;
    border: 0;
    border-radius: 12px;
    color: var(--navy);
    background: #eaf0f5;
    font-weight: 800;
  }
  .button-primary { color: var(--white); background: var(--teal); }
  .button-primary:hover { background: var(--teal-dark); }
  .button-out { color: var(--white); background: var(--navy); }
  .button-out:hover { background: #0b1f33; }
  .button:focus-visible { outline: 3px solid rgba(15, 118, 110, 0.35); outline-offset: 3px; }

  .notice { margin: 18px 0 0; padding: 13px 15px; border-radius: 12px; font-size: 0.9rem; line-height: 1.5; }
  .notice-error { color: var(--red); background: var(--red-bg); }
  .success-card { text-align: center; }
  .success-mark {
    width: 64px;
    height: 64px;
    margin: 0 auto 22px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    color: var(--teal);
    background: var(--green-bg);
    font-size: 1.1rem;
    font-weight: 850;
  }
  .spinner {
    width: 34px;
    height: 34px;
    margin: 0 auto 16px;
    border: 3px solid var(--line);
    border-top-color: var(--teal);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .admin-card { max-width: 960px; margin-inline: auto; }
  .admin-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 24px; }
  .qr-card { padding: 20px; border: 2px solid var(--line); border-radius: 18px; text-align: center; break-inside: avoid; }
  .qr-card img { display: block; width: min(100%, 320px); height: auto; margin: 12px auto; image-rendering: pixelated; }
  .qr-card p { margin-bottom: 6px; font-weight: 750; }
  .qr-card small { color: var(--muted); }
  .qr-in { border-color: rgba(15, 118, 110, 0.42); background: #f2fbf9; }
  .qr-out { border-color: rgba(16, 42, 67, 0.30); background: #f5f8fb; }

  .totals { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 18px 0; }
  .totals div { padding: 14px; border-radius: 12px; background: #f3f6f9; }
  .totals strong { display: block; color: var(--navy); font-size: 1.35rem; }
  .totals span { color: var(--muted); font-size: 0.76rem; }
  .table-wrap { overflow-x: auto; margin-bottom: 18px; border: 1px solid var(--line); border-radius: 12px; }
  .attendance-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
  .attendance-table th, .attendance-table td { padding: 12px 14px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }
  .attendance-table th { color: var(--muted); background: #f8fafc; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em; }
  .attendance-table tr:last-child td { border-bottom: 0; }
  .mode { display: inline-block; min-width: 44px; padding: 4px 8px; border-radius: 999px; text-align: center; font-size: 0.72rem; font-weight: 850; }
  .mode-in { color: var(--teal); background: #d9f3ee; }
  .mode-out { color: var(--navy); background: #e4ebf2; }

  .site-footer { width: min(100% - 32px, 960px); margin: 26px auto; color: var(--muted); font-size: 0.76rem; text-align: center; }

  @media (max-width: 620px) {
    .site-header { margin-top: 16px; }
    .card { border-radius: 18px; }
    .admin-grid { grid-template-columns: 1fr; }
    .totals { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }

  @media print {
    body { background: #fff; }
    .site-header, .site-footer, .admin-card:not(:first-child), .field, .button, .helper-text, .notice, #admin-error { display: none !important; }
    #app, .admin-card { width: 100%; margin: 0; padding: 0; border: 0; box-shadow: none; }
    .admin-card:first-child > .eyebrow, .admin-card:first-child > h2 { text-align: center; }
    .admin-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12mm; margin: 8mm 0; }
    .qr-card { padding: 6mm; border: 1px solid #999; background: #fff !important; }
    .qr-card img { width: 78mm; max-width: 100%; }
  }
</style>
```

- [ ] **Step 3: Add the API adapter and device token helper**

Create `SSLG Attendance App/Client.html` with a `<script>` block containing:

```javascript
const SERVER_ACTIONS = {
  'scan.status': 'scanStatus',
  'scan.record': 'scanRecord',
  'admin.generate': 'adminGenerate',
  'admin.list': 'adminList',
  'admin.export': 'adminExport'
};

async function api(action, payload = {}) {
  if (window.google && window.google.script && window.google.script.run) {
    return new Promise((resolve, reject) => {
      window.google.script.run
        .withSuccessHandler(resolve)
        .withFailureHandler(error => reject(new Error(error && error.message ? error.message : 'APPS_SCRIPT_FAILED')))
        [SERVER_ACTIONS[action]](payload);
    });
  }
  const response = await fetch(`/api/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok || !data.ok) throw new Error(data.error || 'REQUEST_FAILED');
  return data;
}

function getDeviceToken_() {
  const key = 'sslg.attendance.device.v1';
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  let token;
  if (window.crypto && window.crypto.randomUUID) {
    token = window.crypto.randomUUID();
  } else {
    const bytes = new Uint8Array(24);
    window.crypto.getRandomValues(bytes);
    token = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  localStorage.setItem(key, token);
  return token;
}
```

- [ ] **Step 4: Implement scan status, registration, confirmation, and success screens**

Add these functions to `Client.html`:

```javascript
const ERROR_MESSAGES = {
  NAME_REQUIRED: 'Please enter your name.',
  NAME_TOO_LONG: 'Please use a name of 80 characters or fewer.',
  DEVICE_TOKEN_REQUIRED: 'This browser could not create a device token. Enable site storage and try again.',
  INVALID_REQUEST: 'This QR link is incomplete or invalid.',
  CODE_NOT_FOUND: 'This code is not registered. Ask the SSLG office for today’s code.',
  WRONG_DATE: 'This QR code belongs to a different date.',
  CODE_EXPIRED: 'This QR code has expired. Ask the SSLG office for today’s code.',
  INVALID_CODE: 'This QR code is no longer valid. A newer code may have been generated.',
  MODE_MISMATCH: 'This is not the correct code for this attendance action.',
  SPREADSHEET_NOT_CONFIGURED: 'The attendance Sheet is not configured yet. Please contact the SSLG office.',
  SHEET_BUSY: 'The office Sheet is busy. Please try again in a moment.',
  REQUEST_FAILED: 'The scan was not recorded. Check your connection and try again.',
  APPS_SCRIPT_FAILED: 'The scan was not recorded. Check your connection and try again.'
};

function errorMessage_(error) {
  return ERROR_MESSAGES[error && error.message] || ERROR_MESSAGES.REQUEST_FAILED;
}

function scanParams_() {
  return {
    date: new URLSearchParams(location.search).get('date'),
    mode: new URLSearchParams(location.search).get('mode'),
    code: new URLSearchParams(location.search).get('code')
  };
}

async function renderScanPage_(params) {
  const app = document.getElementById('app');
  let deviceToken;
  try {
    deviceToken = getDeviceToken_();
  } catch (error) {
    app.innerHTML = `<section class="card"><p class="notice notice-error">${errorMessage_({ message: 'DEVICE_TOKEN_REQUIRED' })}</p></section>`;
    return;
  }
  let status;
  try {
    status = await api('scan.status', { ...params, device_token: deviceToken });
  } catch (error) {
    app.innerHTML = `<section class="card"><p class="notice notice-error">${errorMessage_(error)}</p></section>`;
    return;
  }
  if (!status.ok) {
    app.innerHTML = `<section class="card"><p class="notice notice-error">${errorMessage_({ message: status.error })}</p></section>`;
    return;
  }
  const isIn = status.mode === 'IN';
  app.innerHTML = `
    <section class="card scan-card">
      <p class="eyebrow">${isIn ? 'Check in' : 'Check out'}</p>
      <h2>${isIn ? 'Record your arrival' : 'Record your departure'}</h2>
      <p class="scan-meta">${escapeHtml_(status.date)} · SSLG Office</p>
      ${status.name ? `
        <p class="welcome">Continuing as</p>
        <p class="registered-name">${escapeHtml_(status.name)}</p>
        <button id="confirm-scan" class="button ${isIn ? 'button-primary' : 'button-out'}">Confirm ${isIn ? 'check in' : 'check out'}</button>
      ` : `
        <form id="registration-form">
          <label class="field">Your name
            <input name="name" autocomplete="name" maxlength="80" required placeholder="Enter your full name">
          </label>
          <button class="button ${isIn ? 'button-primary' : 'button-out'}" type="submit">Register and ${isIn ? 'check in' : 'check out'}</button>
          <p class="helper-text">You only need to enter your name once on this phone.</p>
        </form>
      `}
      <p id="scan-error" class="notice notice-error" hidden></p>
    </section>`;

  const submit = name => submitScan_(params, deviceToken, name);
  const form = document.getElementById('registration-form');
  if (form) {
    form.addEventListener('submit', event => {
      event.preventDefault();
      submit(new FormData(form).get('name'));
    });
  }
  const confirm = document.getElementById('confirm-scan');
  if (confirm) confirm.addEventListener('click', () => submit(status.name));
}

async function submitScan_(params, deviceToken, name) {
  const button = document.querySelector('#app button');
  const errorBox = document.getElementById('scan-error');
  if (button) button.disabled = true;
  if (errorBox) errorBox.hidden = true;
  try {
    const result = await api('scan.record', { ...params, device_token: deviceToken, name });
    if (!result.ok) throw new Error(result.error);
    const event = result.event;
    document.getElementById('app').innerHTML = `
      <section class="card success-card" aria-live="polite">
        <div class="success-mark" aria-hidden="true">OK</div>
        <p class="eyebrow">Recorded</p>
        <h2>${event.mode === 'IN' ? 'Checked in' : 'Checked out'}</h2>
        <p class="registered-name">${escapeHtml_(event.name)}</p>
        <p class="scan-meta">${escapeHtml_(event.scanned_at)} · Philippines time</p>
        <p class="helper-text">You may close this page.</p>
      </section>`;
  } catch (error) {
    if (button) button.disabled = false;
    if (errorBox) {
      errorBox.textContent = errorMessage_(error);
      errorBox.hidden = false;
    }
  }
}

function escapeHtml_(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderLandingPage_() {
  document.getElementById('app').innerHTML = `
    <section class="card scan-card">
      <p class="eyebrow">SSLG Office</p>
      <h2>Scan to record attendance</h2>
      <p>Use your phone camera to scan today’s check-in or check-out QR code posted by the office.</p>
      <p class="helper-text">First time here? You will be asked for your name once. This phone will remember it for later scans.</p>
    </section>`;
}
```

Add the bootstrap call:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  const page = new URLSearchParams(location.search).get('page');
  if (page === 'admin') renderAdminPage_();
  else if (page === 'scan') renderScanPage_(scanParams_());
  else renderLandingPage_();
});
```

`renderLandingPage_()` must show a short instruction to scan an office QR code and must not link to the admin page or display records.

- [ ] **Step 5: Write and run static client tests**

Create `SSLG Attendance App/tests/client-static.test.cjs`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const client = fs.readFileSync(path.join(root, 'Client.html'), 'utf8');
const index = fs.readFileSync(path.join(root, 'Index.html'), 'utf8');

test('client script parses as JavaScript', () => {
  const script = client.match(/<script>([\s\S]*?)<\/script>/)[1];
  assert.doesNotThrow(() => new Function(script));
});

test('landing and student navigation contain no admin link', () => {
  assert.doesNotMatch(client, /href=["'][^"']*page=admin/);
  assert.doesNotMatch(client, /location\.href\s*=\s*[^;]*page=admin/);
});

test('index includes every client asset exactly once', () => {
  for (const asset of ['Styles', 'QRCodeLib', 'Client']) {
    assert.equal(index.split(`include('${asset}')`).length - 1, 1);
  }
});

test('Apps Script adapter maps every API action to a public server function', () => {
  for (const mapping of [
    "'scan.status': 'scanStatus'",
    "'scan.record': 'scanRecord'",
    "'admin.generate': 'adminGenerate'",
    "'admin.list': 'adminList'",
    "'admin.export': 'adminExport'"
  ]) {
    assert.ok(client.includes(mapping), mapping);
  }
});
```

Run:

```bash
node --test tests/client-static.test.cjs
```

Expected: PASS after the files exist.

- [ ] **Step 6: Review checkpoint**

Verify the student page never requests `admin.list`, contains no phone-number input, and displays “not recorded” rather than success when an API call fails. Confirm names are escaped before insertion into HTML.

---

### Task 4: Office QR Generation, Attendance List, and CSV Export

**Files:**
- Modify: `SSLG Attendance App/Client.html`
- Modify: `SSLG Attendance App/Styles.html`
- Create: `SSLG Attendance App/QRCodeLib.html`
- Test: `SSLG Attendance App/tests/qr.test.cjs`

**Interfaces:**
- Consumes: `admin.generate`, `admin.list`, and `admin.export`; bundled global `qrcode`.
- Produces:
  - `renderAdminPage_() -> Promise<void>`
  - `generateCodes_(dateKey) -> Promise<void>`
  - `loadAttendance_(dateKey, query) -> Promise<void>`
  - `downloadCsv_(dateKey) -> Promise<void>`
  - `qrDataUrl_(value) -> string`

- [ ] **Step 1: Vendor the QR encoder with its license**

Install dependencies if needed:

```bash
npm install
```

Copy the contents of `node_modules/qrcode-generator/qrcode.js` into `SSLG Attendance App/QRCodeLib.html`, preserving its MIT license comment at the top. Do not use a CDN at runtime.

- [ ] **Step 2: Write a failing QR round-trip test**

Create `SSLG Attendance App/tests/qr.test.cjs`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const jsQR = require('jsqr');
const { PNG } = require('pngjs');

const source = fs.readFileSync(path.join(__dirname, '..', 'QRCodeLib.html'), 'utf8');
const context = vm.createContext({});
vm.runInContext(source, context, { filename: 'QRCodeLib.html' });

function decodeQr(value) {
  const qr = context.qrcode(0, 'M');
  qr.addData(value);
  qr.make();
  const dataUrl = qr.createDataURL(8, 4);
  const png = PNG.sync.read(Buffer.from(dataUrl.split(',')[1], 'base64'));
  const decoded = jsQR(new Uint8ClampedArray(png.data), png.width, png.height);
  return decoded && decoded.data;
}

test('IN QR payload decodes exactly', () => {
  const value = 'https://script.test/exec?page=scan&date=2026-11-24&mode=IN&code=in-token';
  assert.equal(decodeQr(value), value);
});

test('OUT QR payload decodes exactly', () => {
  const value = 'https://script.test/exec?page=scan&date=2026-11-24&mode=OUT&code=out-token';
  assert.equal(decodeQr(value), value);
});
```

Run:

```bash
node --test tests/qr.test.cjs
```

Expected: PASS after the library is vendored.

- [ ] **Step 3: Implement the office dashboard**

Add the following to `Client.html`:

```javascript
function defaultAdminDate_() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(new Date());
}

function qrDataUrl_(value) {
  const qr = window.qrcode(0, 'M');
  qr.addData(value);
  qr.make();
  return qr.createDataURL(8, 4);
}

async function renderAdminPage_() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <section class="card admin-card">
      <p class="eyebrow">Office tools</p>
      <h2>Daily QR codes</h2>
      <p class="helper-text">Generating a new pair invalidates the old pair for this date.</p>
      <label class="field">Attendance date
        <input id="admin-date" type="date" value="${defaultAdminDate_()}">
      </label>
      <button id="generate-codes" class="button button-primary">Generate QR pair</button>
      <p id="admin-error" class="notice notice-error" hidden></p>
      <div id="qr-pair" class="admin-grid" hidden></div>
    </section>
    <section class="card admin-card">
      <p class="eyebrow">Shared Sheet</p>
      <h2>Attendance records</h2>
      <label class="field">Search name
        <input id="attendance-search" type="search" placeholder="Search registered names">
      </label>
      <div id="attendance-totals" class="totals" aria-live="polite"></div>
      <div class="table-wrap"><table class="attendance-table"><thead><tr><th>Time</th><th>Name</th><th>Action</th></tr></thead><tbody id="attendance-body"></tbody></table></div>
      <button id="export-csv" class="button">Export CSV</button>
    </section>`;

  const dateInput = document.getElementById('admin-date');
  const searchInput = document.getElementById('attendance-search');
  document.getElementById('generate-codes').addEventListener('click', () => generateCodes_(dateInput.value));
  dateInput.addEventListener('change', () => loadAttendance_(dateInput.value, searchInput.value).catch(showAdminError_));
  searchInput.addEventListener('input', () => loadAttendance_(dateInput.value, searchInput.value).catch(showAdminError_));
  document.getElementById('export-csv').addEventListener('click', () => downloadCsv_(dateInput.value).catch(showAdminError_));
  await loadAttendance_(dateInput.value, '').catch(showAdminError_);
}

function showAdminError_(error) {
  const errorBox = document.getElementById('admin-error');
  if (!errorBox) return;
  errorBox.textContent = errorMessage_(error);
  errorBox.hidden = false;
}

async function generateCodes_(dateKey) {
  const button = document.getElementById('generate-codes');
  const errorBox = document.getElementById('admin-error');
  if (!confirm('Generate new IN and OUT codes? The previous pair for this date will stop working.')) return;
  button.disabled = true;
  errorBox.hidden = true;
  try {
    const result = await api('admin.generate', { date: dateKey });
    if (!result.ok) throw new Error(result.error);
    const record = result.record;
    document.getElementById('qr-pair').innerHTML = `
      <article class="qr-card qr-in"><p class="eyebrow">Check in</p><img alt="Check-in QR code" src="${qrDataUrl_(record.in_url)}"><p>${escapeHtml_(record.date)}</p><small>Created ${escapeHtml_(record.created_at)}</small></article>
      <article class="qr-card qr-out"><p class="eyebrow">Check out</p><img alt="Check-out QR code" src="${qrDataUrl_(record.out_url)}"><p>${escapeHtml_(record.date)}</p><small>Created ${escapeHtml_(record.created_at)}</small></article>`;
    document.getElementById('qr-pair').hidden = false;
    await loadAttendance_(dateKey, document.getElementById('attendance-search').value);
  } catch (error) {
    errorBox.textContent = errorMessage_(error);
    errorBox.hidden = false;
  } finally {
    button.disabled = false;
  }
}

async function loadAttendance_(dateKey, query) {
  const result = await api('admin.list', { date: dateKey, query });
  if (!result.ok) throw new Error(result.error);
  document.getElementById('attendance-totals').innerHTML = `
    <div><strong>${result.totals.scans}</strong><span>Scans</span></div>
    <div><strong>${result.totals.people}</strong><span>People</span></div>
    <div><strong>${result.totals.in}</strong><span>IN</span></div>
    <div><strong>${result.totals.out}</strong><span>OUT</span></div>`;
  document.getElementById('attendance-body').innerHTML = result.rows.length
    ? result.rows.map(row => `<tr><td>${escapeHtml_(row.scanned_at)}</td><td>${escapeHtml_(row.name)}</td><td><span class="mode mode-${row.mode === 'IN' ? 'in' : 'out'}">${escapeHtml_(row.mode)}</span></td></tr>`).join('')
    : '<tr><td colspan="3">No scans recorded for this date.</td></tr>';
}

async function downloadCsv_(dateKey) {
  const result = await api('admin.export', { date: dateKey });
  if (!result.ok) throw new Error(result.error);
  const blob = new Blob([result.csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = result.filename;
  link.click();
  URL.revokeObjectURL(url);
}
```

Update the date button label when the selected date changes, or keep the neutral label `Generate QR pair` to avoid a stale “today” label. Use the neutral label.

- [ ] **Step 4: Add print and table styles**

Extend `Styles.html` so:

- `@media print` hides the header, footer, filters, buttons, attendance section, and helper text;
- only `#qr-pair` prints, with one IN and one OUT card per row;
- QR images are at least 240px wide in print and do not break across pages;
- table rows remain readable on mobile through a horizontally scrollable wrapper.

- [ ] **Step 5: Run static and QR tests**

Run:

```bash
node --test tests/client-static.test.cjs
node --test tests/qr.test.cjs
```

Expected: all tests PASS.

- [ ] **Step 6: Review checkpoint**

Confirm both QR codes carry `page=scan`, the selected date, distinct modes, and the server-generated tokens. Confirm CSV downloads use a Blob rather than navigating to a data URL. Confirm the admin URL appears only in direct navigation, never as a student link.

---

### Task 5: Local Preview Server and API Integration Tests

**Files:**
- Create: `SSLG Attendance App/preview/server.cjs`
- Test: `SSLG Attendance App/tests/preview.test.cjs`
- Modify: `SSLG Attendance App/package.json`

**Interfaces:**
- Consumes: `Index.html`, `Styles.html`, `QRCodeLib.html`, `Client.html`, and `Core.gs`.
- Produces:
  - `createPreviewServer() -> http.Server`
  - `GET /` and `GET /?page=admin|scan` -> rendered HTML
  - `POST /api/:action` -> JSON using the same action contract as `Code.gs`

- [ ] **Step 1: Write failing preview API tests**

Create `SSLG Attendance App/tests/preview.test.cjs`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const { createPreviewServer } = require('../preview/server.cjs');

async function withServer(run) {
  const server = createPreviewServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try { await run(base); } finally { await new Promise(resolve => server.close(resolve)); }
}

async function post(base, action, payload) {
  const response = await fetch(`${base}/api/${action}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  return response.json();
}

test('renders all include files without scriptlet placeholders', async () => {
  await withServer(async base => {
    const html = await (await fetch(base)).text();
    assert.match(html, /<style>/);
    assert.match(html, /function renderAdminPage_/);
    assert.doesNotMatch(html, /include\(/);
  });
});

test('preview supports registration, recognition, and repeated scans', async () => {
  await withServer(async base => {
    const date = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(new Date());
    const generated = await post(base, 'admin.generate', { date });
    assert.equal(generated.ok, true);
    const first = await post(base, 'scan.record', {
      date, mode: 'IN', code: generated.record.in_code,
      device_token: 'preview-device', name: 'Ana Cruz'
    });
    assert.equal(first.ok, true);
    const status = await post(base, 'scan.status', {
      date, mode: 'OUT', code: generated.record.out_code,
      device_token: 'preview-device'
    });
    assert.equal(status.name, 'Ana Cruz');
    const second = await post(base, 'scan.record', {
      date, mode: 'OUT', code: generated.record.out_code,
      device_token: 'preview-device'
    });
    assert.equal(second.ok, true);
    const list = await post(base, 'admin.list', { date, query: '' });
    assert.equal(list.totals.scans, 2);
  });
});
```

Run:

```bash
node --test tests/preview.test.cjs
```

Expected: FAIL because `preview/server.cjs` does not exist.

- [ ] **Step 2: Implement the preview server**

Create `SSLG Attendance App/preview/server.cjs` using only Node built-ins:

```javascript
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { randomUUID } = require('node:crypto');

const root = path.join(__dirname, '..');

function loadCore() {
  const context = vm.createContext({ console, Date, Intl, JSON });
  vm.runInContext(fs.readFileSync(path.join(root, 'Core.gs'), 'utf8'), context);
  return context;
}

function renderIndex() {
  return fs.readFileSync(path.join(root, 'Index.html'), 'utf8')
    .replace(/<\?!= include\('Styles'\); \?>/, fs.readFileSync(path.join(root, 'Styles.html'), 'utf8'))
    .replace(/<\?!= include\('QRCodeLib'\); \?>/, fs.readFileSync(path.join(root, 'QRCodeLib.html'), 'utf8'))
    .replace(/<\?!= include\('Client'\); \?>/, fs.readFileSync(path.join(root, 'Client.html'), 'utf8'));
}

function createPreviewServer() {
  const core = loadCore();
  const state = { codes: new Map(), people: new Map(), attendance: [] };
  const baseUrl = process.env.PREVIEW_PUBLIC_URL || 'http://127.0.0.1:4173';

  const server = http.createServer(async (request, response) => {
    response.setHeader('Content-Type', 'application/json; charset=utf-8');
    if (request.method === 'GET' && request.url.startsWith('/')) {
      response.setHeader('Content-Type', 'text/html; charset=utf-8');
      response.end(renderIndex());
      return;
    }
    if (request.method === 'POST' && request.url.startsWith('/api/')) {
      const action = request.url.slice('/api/'.length);
      let raw = '';
      for await (const chunk of request) raw += chunk;
      const payload = JSON.parse(raw || '{}');
      let result;
      try {
        if (action === 'admin.generate') {
          const record = core.createDailyCodeRecord_(payload.date, new Date(), randomUUID);
          state.codes.set(payload.date, {
            ...record,
            in_url: `${baseUrl}/?page=scan&date=${payload.date}&mode=IN&code=${record.in_code}`,
            out_url: `${baseUrl}/?page=scan&date=${payload.date}&mode=OUT&code=${record.out_code}`
          });
          result = { ok: true, record: state.codes.get(payload.date) };
        } else if (action === 'scan.status' || action === 'scan.record') {
          const code = state.codes.get(payload.date);
          const validation = core.validateScan_(payload, code, new Date());
          if (!validation.ok) result = validation;
          else {
            const person = state.people.get(payload.device_token);
            if (action === 'scan.status') {
              result = { ok: true, date: payload.date, mode: payload.mode, name: person ? person.name : null, device_token: payload.device_token, qr_created_at: code.created_at };
            } else {
              const name = core.normalizeName_(person ? person.name : payload.name);
              const now = core.manilaTimestamp_(new Date());
              if (!person) state.people.set(payload.device_token, { name, first_seen_at: now, last_seen_at: now });
              else person.last_seen_at = now;
              const event = { event_id: randomUUID(), date: payload.date, scanned_at: now, mode: payload.mode.toUpperCase(), name, device_token: payload.device_token, qr_created_at: code.created_at };
              state.attendance.push(event);
              result = { ok: true, event };
            }
          }
        } else if (action === 'admin.list') {
          const rows = state.attendance.filter(row => row.date === payload.date && (!payload.query || row.name.toLowerCase().includes(payload.query.toLowerCase()))).reverse();
          const all = state.attendance.filter(row => row.date === payload.date);
          result = { ok: true, rows, totals: { scans: all.length, people: new Set(all.map(row => row.device_token)).size, in: all.filter(row => row.mode === 'IN').length, out: all.filter(row => row.mode === 'OUT').length } };
        } else if (action === 'admin.export') {
          const rows = state.attendance.filter(row => row.date === payload.date);
          result = { ok: true, csv: core.toCsv_(core.ATTENDANCE_HEADERS, rows.map(row => core.ATTENDANCE_HEADERS.map(header => row[header]))), filename: `SSLG-attendance-${payload.date}.csv` };
        } else {
          result = { ok: false, error: 'UNKNOWN_ACTION' };
        }
      } catch (error) {
        result = { ok: false, error: error.message || 'REQUEST_FAILED' };
      }
      response.end(JSON.stringify(result));
      return;
    }
    response.statusCode = 404;
    response.end(JSON.stringify({ ok: false, error: 'NOT_FOUND' }));
  });
  return server;
}

if (require.main === module) {
  const port = Number(process.env.PORT || 4173);
  createPreviewServer().listen(port, '127.0.0.1', () => {
    console.log(`SSLG attendance preview: http://127.0.0.1:${port}`);
  });
}

module.exports = { createPreviewServer };
```

- [ ] **Step 3: Run preview tests**

Run:

```bash
node --test tests/preview.test.cjs
```

Expected: all tests PASS.

- [ ] **Step 4: Run the browser preview**

Run in one terminal:

```bash
npm run preview
```

Open `http://127.0.0.1:4173/?page=admin` with Playwright or browser-use. Verify the page renders, codes generate, QR images appear, and the empty table message is visible. Keep the server running for Task 7 browser checks.

- [ ] **Step 5: Review checkpoint**

Confirm the preview uses the same `Core.gs` validation functions as the backend, stores data only in memory, and restarts empty. Confirm no Google credentials are needed for preview.

---

### Task 6: Apps Script Manifest, Setup Guide, and Packaging Checks

**Files:**
- Create: `SSLG Attendance App/appsscript.json`
- Create: `SSLG Attendance App/SETUP.md`
- Modify: `SSLG Attendance App/package.json`
- Test: `SSLG Attendance App/tests/packaging.test.cjs`

**Interfaces:**
- Consumes: all implementation files from Tasks 1–5.
- Produces: a manifest with `Asia/Manila`, V8, anonymous web-app access, and Spreadsheet scope; an exact deployment guide; packaging assertions.

- [ ] **Step 1: Create the Apps Script manifest**

Write `SSLG Attendance App/appsscript.json`:

```json
{
  "timeZone": "Asia/Manila",
  "dependencies": {},
  "webapp": {
    "executeAs": "USER_DEPLOYING",
    "access": "ANYONE_ANONYMOUS"
  },
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets"
  ]
}
```

- [ ] **Step 2: Write failing packaging tests**

Create `SSLG Attendance App/tests/packaging.test.cjs`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');

test('manifest uses Manila time and anonymous access', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'appsscript.json'), 'utf8'));
  assert.equal(manifest.timeZone, 'Asia/Manila');
  assert.equal(manifest.runtimeVersion, 'V8');
  assert.equal(manifest.webapp.executeAs, 'USER_DEPLOYING');
  assert.equal(manifest.webapp.access, 'ANYONE_ANONYMOUS');
});

test('required Apps Script files exist', () => {
  for (const file of ['Core.gs', 'Code.gs', 'Index.html', 'Styles.html', 'Client.html', 'QRCodeLib.html', 'appsscript.json', 'SETUP.md']) {
    assert.equal(fs.existsSync(path.join(root, file)), true, file);
  }
});

test('project contains no hard-coded spreadsheet ID or secret assignment', () => {
  for (const file of ['Core.gs', 'Code.gs', 'Client.html', 'preview/server.cjs']) {
    const text = fs.readFileSync(path.join(root, file), 'utf8');
    assert.doesNotMatch(text, /SPREADSHEET_ID\s*=\s*['"][^'"]+/);
    assert.doesNotMatch(text, /API_KEY\s*=|PRIVATE_KEY\s*=|client_secret/i);
  }
});
```

Run:

```bash
node --test tests/packaging.test.cjs
```

Expected: FAIL until the manifest and setup guide exist.

- [ ] **Step 3: Write the setup guide**

Create `SSLG Attendance App/SETUP.md` with these exact sections and instructions:

1. **What this app stores:** names, random browser tokens, daily QR tokens, and timestamps; no phone numbers.
2. **Public admin warning:** the admin page has no password; anyone with its direct URL can view names and timestamps.
3. **Create the Sheet:** create a blank Google Spreadsheet named `SSLG Office Attendance`; copy its ID from the URL between `/d/` and `/edit`.
4. **Create the Apps Script project:** open `Extensions → Apps Script` from that Sheet.
5. **Add files:** create `Code.gs`, `Core.gs`, `Index.html`, `Styles.html`, `Client.html`, and `QRCodeLib.html`; paste the matching project files. Replace the generated `appsscript.json` through Project Settings → Show `appsscript.json`.
6. **Configure the Sheet:** in Project Settings → Script Properties, add `SPREADSHEET_ID` with the copied ID. Save.
7. **Deploy:** click `Deploy → New deployment → Web app`; execute as the deploying user; set access to `Anyone`; deploy and authorize the requested Google permissions.
8. **Open the office page:** append `?page=admin` to the deployed `/exec` URL; generate a QR pair for today.
9. **Test:** scan the IN code on a phone, register a name, confirm; scan OUT on the same phone and confirm the remembered name; check the Sheet and office list.
10. **Daily use:** generate a fresh pair each morning; print the cards; do not reuse yesterday’s codes.
11. **CSV:** choose a date on the office page and click `Export CSV`.
12. **Troubleshooting:** explain `SPREADSHEET_NOT_CONFIGURED`, expired/invalid codes, Sheet permission errors, and browser local-storage loss.

Include the exact statement: “A live deployment is not verified until the owner completes the scan test in this guide.”

- [ ] **Step 4: Add packaging tests to the default test command**

Verify `package.json` uses `"test": "node --test"` so Node discovers every `*.test.cjs` file on Windows and Unix without shell glob expansion. Verify `package-lock.json` exists after `npm install`.

- [ ] **Step 5: Run packaging and full automated tests**

Run:

```bash
npm test
```

Expected: all test files PASS.

- [ ] **Step 6: Review checkpoint**

Confirm the manifest contains no external API scopes, the setup guide never asks for a service-account JSON file, and no test or source file contains a real Spreadsheet ID, token, password, or Google credential.

---

### Task 7: End-to-End Browser Verification and Acceptance Audit

**Files:**
- Modify only if verification reveals a defect: files inside `SSLG Attendance App/`
- Create: `SSLG Attendance App/VERIFICATION.md`

**Interfaces:**
- Consumes: the running preview from Task 5 and all automated tests.
- Produces: a dated verification record with exact commands, browser checks, observed results, and any deployment checks still pending.

- [ ] **Step 1: Run the full automated suite**

Run:

```bash
cd "SSLG Attendance App"
npm install
npm test
```

Expected: core, backend, client static, QR round-trip, preview, and packaging tests all PASS.

- [ ] **Step 2: Start the preview**

Run:

```bash
npm run preview
```

Expected: `SSLG attendance preview: http://127.0.0.1:4173`.

- [ ] **Step 3: Verify the office golden path in a browser**

Using Playwright or browser-use:

1. Open `http://127.0.0.1:4173/?page=admin` at desktop width.
2. Select today’s Manila date.
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
2. Invoke print preview.
3. Confirm only the two QR cards print, both are legible, and buttons, filters, attendance records, header, and footer are absent.

- [ ] **Step 8: Write the verification record**

Create `SSLG Attendance App/VERIFICATION.md` containing:

- date and environment;
- exact `npm test` result counts;
- desktop and mobile URLs tested;
- checklist results for Steps 3–7;
- screenshots or observed text for registration, recognition, invalidation, and print preview;
- explicit status `Pending owner deployment` for the real Google Apps Script smoke test;
- any defects found and fixed.

Do not write “deployed,” “live,” or a production URL unless the owner’s real deployment has been tested.

- [ ] **Step 9: Audit every spec acceptance criterion**

Create a table in `VERIFICATION.md` with the ten acceptance criteria from the spec, a PASS/PENDING/FAIL verdict, and evidence for each. The real deployment criteria must remain PENDING until the owner completes `SETUP.md`.

- [ ] **Step 10: Final review checkpoint**

Run `npm test` once more after any fixes. Confirm all existing SSLG vault files remain unchanged and all new files are under `SSLG Attendance App/` plus the approved spec and plan. Report any unperformed live-deployment checks explicitly.
