const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const MANILA_TEST_NOW = '2026-11-24T12:00:00.000Z';
class FixedDate extends Date {
  constructor(...args) {
    super(...(args.length ? args : [MANILA_TEST_NOW]));
  }
  static now() {
    return new Date(MANILA_TEST_NOW).getTime();
  }
}

function loadBackend() {
  const sheets = new Map();
  const properties = { SPREADSHEET_ID: 'sheet-test-id' };
  let uuid = 0;
  let baseUrl = 'https://script.test/exec';
  let lockAvailable = true;
  const requestedTemplates = [];

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
    Date: FixedDate,
    Intl,
    JSON,
    PropertiesService: { getScriptProperties: () => ({ getProperty: key => properties[key] || null }) },
    SpreadsheetApp: { openById: () => spreadsheet },
    LockService: { getScriptLock: () => ({ tryLock: () => lockAvailable, releaseLock: () => {} }) },
    Utilities: { getUuid: () => `uuid-${++uuid}` },
    ScriptApp: { getService: () => ({ getUrl: () => baseUrl }) },
    HtmlService: { createTemplateFromFile: name => { requestedTemplates.push(name); return { evaluate: () => 'html' }; } },
    ContentService: {
      MimeType: { JSON: 'application/json' },
      createTextOutput: text => ({ setMimeType: () => ({ text }) })
    }
  });

  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Core.gs'), 'utf8'), context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'Code.gs'), 'utf8'), context);
  return {
    context,
    sheets,
    requestedTemplates,
    setLockAvailable(value) { lockAvailable = value; }
  };
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
  assert.deepEqual(Array.from(backend.sheets.get('Daily Codes')[0]), ['date', 'in_code', 'out_code', 'created_at', 'created_by']);
  assert.deepEqual(Array.from(backend.sheets.get('People')[0]), ['device_token', 'name', 'first_seen_at', 'last_seen_at']);
  assert.deepEqual(Array.from(backend.sheets.get('Attendance')[0]), ['event_id', 'date', 'scanned_at', 'mode', 'name', 'device_token', 'qr_created_at']);
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

test('records an unmatched OUT as the first scan', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generateDailyCodes_(date);
  const result = post(backend, 'scan.record', {
    date, mode: 'OUT', code: generated.out_code,
    device_token: 'first-out-device', name: 'Luis Santos'
  });
  assert.equal(result.ok, true);
  assert.equal(result.event.mode, 'OUT');
  assert.equal(result.event.scanned_at, '2026-11-24T20:00:00+08:00');
  assert.equal(backend.sheets.get('People').length, 2);
  assert.equal(backend.sheets.get('Attendance').length, 2);
});

test('rejects every formula-leading new name before People or Attendance writes', () => {
  for (const [index, trigger] of ['=', '+', '-', '@'].entries()) {
    const backend = loadBackend();
    const date = today_(backend);
    const generated = backend.context.generateDailyCodes_(date);
    const result = post(backend, 'scan.record', {
      date, mode: 'IN', code: generated.in_code,
      device_token: `new-formula-${index}`, name: ` \t${trigger}SUM(A1)\r\n`
    });
    assert.deepEqual(result, { ok: false, error: 'NAME_INVALID' });
    assert.equal(backend.sheets.get('People').length, 1);
    assert.equal(backend.sheets.get('Attendance').length, 1);
  }
});

test('rejects formula-leading legacy names on returning scans without writes', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generateDailyCodes_(date);
  backend.context.ensureSchema_();
  for (const [index, trigger] of ['=', '+', '-', '@'].entries()) {
    backend.sheets.get('People').push([`legacy-formula-${index}`, `${trigger}legacy`, 'old', 'old']);
  }
  const peopleBefore = JSON.parse(JSON.stringify(backend.sheets.get('People')));
  for (const [index, trigger] of ['=', '+', '-', '@'].entries()) {
    const result = post(backend, 'scan.record', {
      date, mode: 'IN', code: generated.in_code,
      device_token: `legacy-formula-${index}`, name: 'Ignored replacement'
    });
    assert.deepEqual(result, { ok: false, error: 'NAME_INVALID' }, trigger);
  }
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('People'))), peopleBefore);
  assert.equal(backend.sheets.get('Attendance').length, 1);
});

test('neutralizes dangerous legacy CSV fields without changing stored rows', () => {
  const backend = loadBackend();
  const date = today_(backend);
  backend.context.ensureSchema_();
  const legacyRow = ['=event', date, '\tscanned', '+IN', '-@name', '@device', '\rcreated'];
  backend.sheets.get('Attendance').push(legacyRow);
  const exported = backend.context.exportAttendanceCsv_(date);
  const expectedRow = [
    '"\'=event"', `"${date}"`, '"\'\tscanned"', '"\'+IN"',
    '"\'-@name"', '"\'@device"', '"\'\rcreated"'
  ].join(',');
  assert.equal(exported.csv, `"event_id","date","scanned_at","mode","name","device_token","qr_created_at"\n${expectedRow}`);
  assert.deepEqual(Array.from(backend.sheets.get('Attendance')[1]), legacyRow);
});

test('direct admin HTTP actions return generation, list, and export shapes', () => {
  const backend = loadBackend();
  const date = today_(backend);
  assert.deepEqual(post(backend, 'admin.generate', { date }), {
    ok: true,
    record: {
      date,
      in_code: 'uuid-1',
      out_code: 'uuid-2',
      created_at: '2026-11-24T20:00:00+08:00',
      created_by: 'SSLG Office',
      in_url: `https://script.test/exec?page=scan&date=${date}&mode=IN&code=uuid-1`,
      out_url: `https://script.test/exec?page=scan&date=${date}&mode=OUT&code=uuid-2`
    }
  });
  assert.deepEqual(post(backend, 'admin.list', { date, query: '' }), {
    ok: true, rows: [], totals: { in: 0, out: 0, people: 0, scans: 0 }
  });
  assert.deepEqual(post(backend, 'admin.export', { date }), {
    ok: true,
    csv: '"event_id","date","scanned_at","mode","name","device_token","qr_created_at"',
    filename: `SSLG-attendance-${date}.csv`
  });
});

test('public wrappers return scan and admin result shapes', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.adminGenerate({ date });
  assert.equal(generated.ok, true);
  assert.equal(generated.record.date, date);
  assert.deepEqual(JSON.parse(JSON.stringify(backend.context.scanStatus({
    date, mode: 'IN', code: generated.record.in_code, device_token: 'wrapper-device'
  }))), {
    ok: true, date, mode: 'IN', name: null,
    device_token: 'wrapper-device', qr_created_at: generated.record.created_at
  });
  const recorded = backend.context.scanRecord({
    date, mode: 'IN', code: generated.record.in_code,
    device_token: 'wrapper-device', name: 'Ana Cruz'
  });
  assert.deepEqual(Object.keys(recorded).sort(), ['event', 'ok']);
  assert.equal(recorded.event.name, 'Ana Cruz');
  const listed = backend.context.adminList({ date, query: 'ana' });
  assert.deepEqual(Object.keys(listed).sort(), ['ok', 'rows', 'totals']);
  assert.equal(listed.rows.length, 1);
  assert.deepEqual(JSON.parse(JSON.stringify(listed.totals)), { in: 1, out: 0, people: 1, scans: 1 });
  const exported = backend.context.adminExport({ date });
  assert.deepEqual(Object.keys(exported).sort(), ['csv', 'filename', 'ok']);
  assert.match(exported.csv, /"Ana Cruz"/);
});

test('doGet evaluates Index HTML for landing, scan, admin, and missing events', () => {
  const backend = loadBackend();
  assert.equal(backend.context.doGet(), 'html');
  assert.equal(backend.context.doGet({ parameter: {} }), 'html');
  assert.equal(backend.context.doGet({ parameter: { page: 'scan' } }), 'html');
  assert.equal(backend.context.doGet({ parameter: { page: 'admin' } }), 'html');
  assert.deepEqual(backend.requestedTemplates, ['Index', 'Index', 'Index', 'Index']);
});

test('a busy Sheet lock returns SHEET_BUSY without People or Attendance writes', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generateDailyCodes_(date);
  backend.setLockAvailable(false);
  assert.deepEqual(post(backend, 'scan.record', {
    date, mode: 'IN', code: generated.in_code,
    device_token: 'busy-device', name: 'Ana Cruz'
  }), { ok: false, error: 'SHEET_BUSY' });
  assert.throws(() => backend.context.generateDailyCodes_(date), /SHEET_BUSY/);
  assert.equal(backend.sheets.get('People').length, 1);
  assert.equal(backend.sheets.get('Attendance').length, 1);
  assert.equal(backend.sheets.get('Daily Codes').length, 2);
});
