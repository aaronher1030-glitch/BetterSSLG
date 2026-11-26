const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createPreviewServer } = require('../preview/server.cjs');

const MANILA_TEST_NOW = '2026-11-24T12:00:00.000Z';
const DANGEROUS_DEVICE_TOKENS = ['=', '+', '-', '@', '\t', '\r', '\n'].flatMap(trigger => [
  `${trigger}device`,
  `  ${trigger}device`
]);
let manilaTestNow = MANILA_TEST_NOW;
let manilaDateSequence = null;
class FixedDate extends Date {
  constructor(...args) {
    if (!args.length && manilaDateSequence) return new Date(manilaDateSequence.shift());
    super(...(args.length ? args : [manilaTestNow]));
  }
  static now() {
    return new Date(manilaTestNow).getTime();
  }
}

function loadBackend() {
  manilaTestNow = MANILA_TEST_NOW;
  manilaDateSequence = null;
  const sheets = new Map();
  const properties = { SPREADSHEET_ID: 'sheet-test-id' };
  let uuid = 0;
  let baseUrl = 'https://script.test/exec';
  let lockAvailable = true;
  const requestedTemplates = [];
  const writes = new Map();

  function makeSheet(name) {
    if (!sheets.has(name)) sheets.set(name, []);
    const rows = sheets.get(name);
    return {
      getLastRow: () => rows.length,
      getRange: (row, column, rowCount, columnCount = 1) => ({
        getValues: () => rows.slice(row - 1, row - 1 + rowCount)
          .map(value => value.slice(column - 1, column - 1 + columnCount)),
        setValues: values => {
          if (values.length !== rowCount || values.some(value => value.length !== columnCount)) {
            throw new Error('The number of data rows does not match the number of rows in the range.');
          }
          writes.set(name, (writes.get(name) || 0) + 1);
          rows.splice(row - 1, rowCount, ...values.map(value => value.slice()));
        }
      }),
      appendRow: row => {
        writes.set(name, (writes.get(name) || 0) + 1);
        rows.push(row);
      },
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
    writes,
    requestedTemplates,
    setNow(value) { manilaTestNow = value; },
    setDateSequence(values) { manilaDateSequence = values; },
    getUuidCount() { return uuid; },
    setLockAvailable(value) { lockAvailable = value; }
  };
}

function post(backend, action, payload) {
  const output = backend.context.doPost({ postData: { contents: JSON.stringify({ action, payload }) } });
  return JSON.parse(output.text);
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

async function withPreviewServer(run) {
  const server = createPreviewServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try { await run(base); } finally {
    const closed = new Promise(resolve => server.close(resolve));
    server.closeAllConnections();
    await closed;
  }
}

async function previewPost(base, action, payload) {
  const response = await fetch(`${base}/api/${action}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  return response.json();
}

function today_(backend) {
  return backend.context.manilaDateKey_(new backend.context.Date());
}

test('backend test requests stay on 2026-11-24 when the host clock advances', t => {
  t.mock.timers.enable({ apis: ['Date'], now: new Date('2026-11-26T02:00:00.000Z') });
  const hostDate = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(new Date());
  assert.equal(hostDate, '2026-11-26');

  const backend = loadBackend();
  const date = today_(backend);
  assert.equal(date, '2026-11-24');
  const generated = backend.context.generatePermanentCodes_();
  const status = post(backend, 'scan.status', {
    mode: 'IN', code: generated.in_code, device_token: 'clock-device'
  });
  assert.equal(status.ok, true);
  assert.equal(status.date, '2026-11-24');
  const recorded = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: 'clock-device', name: 'Ana Cruz'
  });
  assert.equal(recorded.ok, true);
  assert.equal(recorded.event.date, '2026-11-24');
  assert.equal(recorded.event.scanned_at, '2026-11-24T20:00:00+08:00');
});

test('creates the documented Sheet tabs and headers', () => {
  const backend = loadBackend();
  backend.context.ensureSchema_();
  assert.deepEqual(Array.from(backend.sheets.get('QR Codes')[0]), ['in_code', 'out_code', 'created_at', 'created_by']);
  assert.deepEqual(Array.from(backend.sheets.get('People')[0]), ['device_token', 'name', 'first_seen_at', 'last_seen_at']);
  assert.deepEqual(Array.from(backend.sheets.get('Attendance')[0]), ['event_id', 'date', 'scanned_at', 'mode', 'name', 'device_token', 'qr_created_at']);
});

test('restores documented headers on existing sheets without changing data rows', () => {
  const backend = loadBackend();
  backend.context.ensureSchema_();
  const attendance = backend.sheets.get('Attendance');
  attendance[0][0] = '';
  const dataRow = ['event-1', '2026-11-26', '2026-11-26T08:00:00+08:00', 'IN', 'Ana Cruz', 'device-a', '2026-11-25T16:39:10+08:00'];
  attendance.push(dataRow.slice());

  backend.context.ensureSchema_();

  assert.deepEqual(Array.from(attendance[0]), ['event_id', 'date', 'scanned_at', 'mode', 'name', 'device_token', 'qr_created_at']);
  assert.deepEqual(Array.from(attendance[1]), dataRow);
});

test('creates one permanent pair and returns it without later writes or UUID consumption', () => {
  const backend = loadBackend();
  const first = backend.context.generatePermanentCodes_();
  const writesAfterCreation = backend.writes.get('QR Codes');
  const uuidsAfterCreation = backend.getUuidCount();
  assert.equal(backend.sheets.get('QR Codes').length, 2);
  assert.equal(uuidsAfterCreation, 2);

  backend.setNow('2026-11-25T02:00:00.000Z');
  const second = post(backend, 'admin.generate', { date: '2099-12-31' });
  assert.deepEqual(second, { ok: true, record: plain(first) });
  assert.equal(backend.sheets.get('QR Codes').length, 2);
  assert.equal(backend.writes.get('QR Codes'), writesAfterCreation);
  assert.equal(backend.getUuidCount(), uuidsAfterCreation);
  assert.equal(Object.hasOwn(first, 'date'), false);
  assert.equal(new URL(first.in_url).searchParams.has('date'), false);
  assert.equal(new URL(first.out_url).searchParams.has('date'), false);
});

test('dates repeated and unmatched scans by the current Manila server day', () => {
  const backend = loadBackend();
  const generated = backend.context.generatePermanentCodes_();
  const first = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: 'device-a', name: 'Ana Cruz'
  });
  const repeated = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: 'device-a'
  });
  backend.setNow('2026-11-25T02:00:00.000Z');
  const staleDate = post(backend, 'scan.record', {
    date: '2020-01-01', mode: 'IN', code: generated.in_code, device_token: 'device-a'
  });
  const futureDate = post(backend, 'scan.record', {
    date: '2099-12-31', mode: 'OUT', code: generated.out_code,
    device_token: 'unmatched-out-device', name: 'Luis Santos'
  });

  for (const result of [first, repeated, staleDate, futureDate]) assert.equal(result.ok, true);
  assert.equal(first.event.date, '2026-11-24');
  assert.equal(repeated.event.date, '2026-11-24');
  assert.equal(staleDate.event.date, '2026-11-25');
  assert.equal(staleDate.event.scanned_at, '2026-11-25T10:00:00+08:00');
  assert.equal(futureDate.event.date, '2026-11-25');
  assert.equal(futureDate.event.mode, 'OUT');
  assert.deepEqual(plain(backend.context.listAttendance_('2026-11-24', '').totals), { in: 2, out: 0, people: 1, scans: 2 });
  assert.deepEqual(plain(backend.context.listAttendance_('2026-11-25', '').totals), { in: 1, out: 1, people: 2, scans: 2 });
});

test('uses one server instant for a scan date and its exact timestamp across Manila midnight', () => {
  const backend = loadBackend();
  const generated = backend.context.generatePermanentCodes_();
  backend.setDateSequence([
    '2026-11-24T15:59:59.000Z',
    '2026-11-24T16:00:00.000Z'
  ]);
  const result = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: 'midnight-device', name: 'Ana Cruz'
  });
  assert.equal(result.ok, true);
  assert.equal(result.event.date, '2026-11-24');
  assert.equal(result.event.scanned_at, '2026-11-24T23:59:59+08:00');
});

test('rejects missing records, malformed requests, unknown codes, and wrong modes without scan writes', () => {
  const missingBackend = loadBackend();
  assert.deepEqual(post(missingBackend, 'scan.record', {
    mode: 'IN', code: 'unknown', device_token: 'device-a', name: 'Ana Cruz'
  }), { ok: false, error: 'CODE_NOT_FOUND' });
  assert.equal(missingBackend.sheets.get('People').length, 1);
  assert.equal(missingBackend.sheets.get('Attendance').length, 1);

  const backend = loadBackend();
  const generated = backend.context.generatePermanentCodes_();
  const peopleBefore = JSON.parse(JSON.stringify(backend.sheets.get('People')));
  const attendanceBefore = JSON.parse(JSON.stringify(backend.sheets.get('Attendance')));
  const peopleWritesBefore = backend.writes.get('People');
  const attendanceWritesBefore = backend.writes.get('Attendance');
  const cases = [
    [{ mode: 'IN', code: 'unknown', device_token: 'device-a', name: 'Ana Cruz' }, 'INVALID_CODE'],
    [{ mode: 'OUT', code: generated.in_code, device_token: 'device-a', name: 'Ana Cruz' }, 'MODE_MISMATCH'],
    [{ mode: 'SIDEWAYS', code: generated.in_code, device_token: 'device-a', name: 'Ana Cruz' }, 'INVALID_REQUEST'],
    [{ mode: 'IN', device_token: 'device-a', name: 'Ana Cruz' }, 'INVALID_REQUEST']
  ];
  for (const [payload, error] of cases) {
    assert.deepEqual(post(backend, 'scan.record', payload), { ok: false, error });
  }
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('People'))), peopleBefore);
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('Attendance'))), attendanceBefore);
  assert.equal(backend.writes.get('People'), peopleWritesBefore);
  assert.equal(backend.writes.get('Attendance'), attendanceWritesBefore);
});

test('exposes no rotate, reset, or delete action', () => {
  const backend = loadBackend();
  const generated = backend.context.generatePermanentCodes_();
  const before = JSON.parse(JSON.stringify(backend.sheets.get('QR Codes')));
  const uuidCount = backend.getUuidCount();
  for (const action of ['admin.rotate', 'admin.reset', 'admin.delete']) {
    assert.deepEqual(post(backend, action, { date: today_(backend) }), { ok: false, error: 'UNKNOWN_ACTION' });
  }
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('QR Codes'))), before);
  assert.equal(backend.getUuidCount(), uuidCount);
  assert.equal(post(backend, 'scan.status', {
    mode: 'IN', code: generated.in_code, device_token: 'device-a'
  }).ok, true);
});

test('a busy generation lock creates no pair and consumes no UUIDs', () => {
  const backend = loadBackend();
  backend.setLockAvailable(false);
  assert.deepEqual(post(backend, 'admin.generate', {}), { ok: false, error: 'SHEET_BUSY' });
  assert.equal(backend.sheets.has('QR Codes'), false);
  assert.equal(backend.getUuidCount(), 0);
});

test('registers a device once and records every valid scan', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generatePermanentCodes_();
  const first = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code,
    device_token: 'device-a', name: '  Ana   Cruz '
  });
  assert.equal(first.ok, true);
  assert.equal(first.event.name, 'Ana Cruz');
  const status = post(backend, 'scan.status', {
    mode: 'OUT', code: generated.out_code, device_token: 'device-a'
  });
  assert.equal(status.name, 'Ana Cruz');
  const second = post(backend, 'scan.record', {
    mode: 'OUT', code: generated.out_code, device_token: 'device-a'
  });
  const third = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: 'device-a'
  });
  assert.equal(second.ok, true);
  assert.equal(third.ok, true);
  assert.equal(backend.sheets.get('People').length, 2);
  assert.equal(backend.sheets.get('Attendance').length, 4);
});

test('rejects invalid codes without writing attendance', () => {
  const backend = loadBackend();
  const date = today_(backend);
  backend.context.generatePermanentCodes_();
  const result = post(backend, 'scan.record', {
    mode: 'IN', code: 'wrong', device_token: 'device-a', name: 'Ana Cruz'
  });
  assert.equal(result.ok, false);
  assert.equal(backend.sheets.get('Attendance').length, 1);
});

test('filters attendance and exports CSV', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generatePermanentCodes_();
  post(backend, 'scan.record', { mode: 'IN', code: generated.in_code, device_token: 'device-a', name: 'Ana Cruz' });
  const listed = backend.context.listAttendance_(date, 'ana');
  assert.equal(listed.rows.length, 1);
  assert.equal(listed.totals.in, 1);
  const exported = backend.context.exportAttendanceCsv_(date);
  assert.equal(exported.ok, true);
  assert.match(exported.csv, /"Ana Cruz"/);
});

test('normalizes Sheets date values for attendance filtering and CSV export', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generatePermanentCodes_();
  post(backend, 'scan.record', { mode: 'IN', code: generated.in_code, device_token: 'device-a', name: 'Ana Cruz' });
  backend.sheets.get('Attendance')[1][1] = new Date(`${date}T00:00:00.000Z`);

  const listed = backend.context.listAttendance_(date, 'ana');
  assert.equal(listed.rows.length, 1);
  assert.equal(listed.rows[0].date, date);
  assert.deepEqual(plain(listed.totals), { in: 1, out: 0, people: 1, scans: 1 });
  const exported = backend.context.exportAttendanceCsv_(date);
  assert.match(exported.csv, new RegExp(`"${date}"`));
});

test('records an unmatched OUT as the first scan', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generatePermanentCodes_();
  const result = post(backend, 'scan.record', {
    mode: 'OUT', code: generated.out_code,
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
    const generated = backend.context.generatePermanentCodes_();
    const result = post(backend, 'scan.record', {
      mode: 'IN', code: generated.in_code,
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
  const generated = backend.context.generatePermanentCodes_();
  backend.context.ensureSchema_();
  for (const [index, trigger] of ['=', '+', '-', '@'].entries()) {
    backend.sheets.get('People').push([`legacy-formula-${index}`, `${trigger}legacy`, 'old', 'old']);
  }
  const peopleBefore = JSON.parse(JSON.stringify(backend.sheets.get('People')));
  for (const [index, trigger] of ['=', '+', '-', '@'].entries()) {
    const result = post(backend, 'scan.record', {
      mode: 'IN', code: generated.in_code,
      device_token: `legacy-formula-${index}`, name: 'Ignored replacement'
    });
    assert.deepEqual(result, { ok: false, error: 'NAME_INVALID' }, trigger);
  }
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('People'))), peopleBefore);
  assert.equal(backend.sheets.get('Attendance').length, 1);
});

test('backend and preview reject dangerous device tokens with matching errors and zero writes', async () => {
  const backend = loadBackend();
  const backendCodes = backend.context.generatePermanentCodes_();
  const peopleBefore = JSON.parse(JSON.stringify(backend.sheets.get('People')));
  const attendanceBefore = JSON.parse(JSON.stringify(backend.sheets.get('Attendance')));
  const peopleWritesBefore = backend.writes.get('People');
  const attendanceWritesBefore = backend.writes.get('Attendance');

  await withPreviewServer(async base => {
    const previewDate = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(new Date());
    const previewGenerated = await previewPost(base, 'admin.generate', { date: previewDate });
    assert.equal(previewGenerated.ok, true);

    for (const action of ['scan.status', 'scan.record']) {
      const cases = [
        ...DANGEROUS_DEVICE_TOKENS.map(device_token => ({ device_token, error: 'DEVICE_TOKEN_INVALID' })),
        { device_token: '', error: 'DEVICE_TOKEN_REQUIRED' },
        ...(action === 'scan.record' ? [{ device_token: 'x'.repeat(101), error: 'DEVICE_TOKEN_REQUIRED' }] : [])
      ];
      for (const { device_token, error } of cases) {
        const backendResult = post(backend, action, {
          mode: 'IN', code: backendCodes.in_code, device_token, name: 'Ana Cruz'
        });
        const previewResult = await previewPost(base, action, {
          mode: 'IN', code: previewGenerated.record.in_code, device_token, name: 'Ana Cruz'
        });
        assert.deepEqual(backendResult, { ok: false, error }, `${action} backend ${JSON.stringify(device_token)}`);
        assert.deepEqual(previewResult, backendResult, `${action} preview ${JSON.stringify(device_token)}`);
      }
    }

    const listed = await previewPost(base, 'admin.list', { date: previewDate, query: '' });
    assert.deepEqual(listed.totals, { scans: 0, people: 0, in: 0, out: 0 });
  });

  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('People'))), peopleBefore);
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('Attendance'))), attendanceBefore);
  assert.equal(backend.writes.get('People'), peopleWritesBefore);
  assert.equal(backend.writes.get('Attendance'), attendanceWritesBefore);
});

test('backend preserves safe device tokens exactly and keeps the 100/101 character boundaries', () => {
  const backend = loadBackend();
  const date = today_(backend);
  const generated = backend.context.generatePermanentCodes_();
  const spacedToken = '  safe-device  ';
  const recorded = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: spacedToken, name: 'Ana Cruz'
  });
  assert.equal(recorded.ok, true);
  assert.equal(recorded.event.device_token, spacedToken);
  assert.equal(backend.sheets.get('People')[1][0], spacedToken);
  const recognized = post(backend, 'scan.status', {
    mode: 'OUT', code: generated.out_code, device_token: spacedToken
  });
  assert.equal(recognized.name, 'Ana Cruz');
  assert.equal(recognized.device_token, spacedToken);

  const hundredCharacterToken = 'x'.repeat(100);
  const hundred = post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: hundredCharacterToken, name: 'Luis Santos'
  });
  assert.equal(hundred.ok, true);
  assert.equal(hundred.event.device_token, hundredCharacterToken);

  const peopleBefore = JSON.parse(JSON.stringify(backend.sheets.get('People')));
  const attendanceBefore = JSON.parse(JSON.stringify(backend.sheets.get('Attendance')));
  const peopleWritesBefore = backend.writes.get('People');
  const attendanceWritesBefore = backend.writes.get('Attendance');
  const hundredOneCharacterToken = 'y'.repeat(101);
  const status = post(backend, 'scan.status', {
    mode: 'IN', code: generated.in_code, device_token: hundredOneCharacterToken
  });
  assert.deepEqual(status, {
    ok: true, date, mode: 'IN', name: null,
    device_token: hundredOneCharacterToken, qr_created_at: generated.created_at
  });
  assert.deepEqual(post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code, device_token: hundredOneCharacterToken, name: 'Maria Clara'
  }), { ok: false, error: 'DEVICE_TOKEN_REQUIRED' });
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('People'))), peopleBefore);
  assert.deepEqual(JSON.parse(JSON.stringify(backend.sheets.get('Attendance'))), attendanceBefore);
  assert.equal(backend.writes.get('People'), peopleWritesBefore);
  assert.equal(backend.writes.get('Attendance'), attendanceWritesBefore);
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
      in_code: 'uuid-1',
      out_code: 'uuid-2',
      created_at: '2026-11-24T20:00:00+08:00',
      created_by: 'SSLG Office',
      in_url: 'https://script.test/exec?page=scan&mode=IN&code=uuid-1',
      out_url: 'https://script.test/exec?page=scan&mode=OUT&code=uuid-2'
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
  assert.equal(Object.hasOwn(generated.record, 'date'), false);
  assert.deepEqual(JSON.parse(JSON.stringify(backend.context.scanStatus({
    mode: 'IN', code: generated.record.in_code, device_token: 'wrapper-device'
  }))), {
    ok: true, date, mode: 'IN', name: null,
    device_token: 'wrapper-device', qr_created_at: generated.record.created_at
  });
  const recorded = backend.context.scanRecord({
    mode: 'IN', code: generated.record.in_code,
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
  const generated = backend.context.generatePermanentCodes_();
  backend.setLockAvailable(false);
  assert.deepEqual(post(backend, 'scan.record', {
    mode: 'IN', code: generated.in_code,
    device_token: 'busy-device', name: 'Ana Cruz'
  }), { ok: false, error: 'SHEET_BUSY' });
  assert.throws(() => backend.context.generatePermanentCodes_(), /SHEET_BUSY/);
  assert.equal(backend.sheets.get('People').length, 1);
  assert.equal(backend.sheets.get('Attendance').length, 1);
  assert.equal(backend.sheets.get('QR Codes').length, 2);
});
