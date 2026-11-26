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
