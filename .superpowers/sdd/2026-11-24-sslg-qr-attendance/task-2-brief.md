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

