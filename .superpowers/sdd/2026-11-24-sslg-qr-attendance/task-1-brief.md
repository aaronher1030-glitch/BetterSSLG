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

