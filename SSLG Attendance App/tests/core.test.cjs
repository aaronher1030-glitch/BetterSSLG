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

test('creates distinct permanent IN and OUT tokens without a date field', () => {
  const tokens = ['in-token', 'out-token'];
  const record = api('createPermanentCodeRecord_', new Date('2026-11-24T01:00:00Z'), () => tokens.shift());
  assert.deepEqual(JSON.parse(JSON.stringify(record)), {
    in_code: 'in-token',
    out_code: 'out-token',
    created_at: '2026-11-24T09:00:00+08:00',
    created_by: 'SSLG Office'
  });
});

test('validates a permanent record on different Manila dates without a request date', () => {
  const record = {
    in_code: 'in-token',
    out_code: 'out-token',
    created_at: '2026-11-24T00:00:00+08:00'
  };
  for (const [now, date] of [
    [new Date('2026-11-24T02:00:00Z'), '2026-11-24'],
    [new Date('2026-11-25T02:00:00Z'), '2026-11-25']
  ]) {
    assert.deepEqual(JSON.parse(JSON.stringify(api('validateScan_', { mode: 'IN', code: 'in-token' }, record, now))), {
      ok: true,
      date,
      mode: 'IN',
      qr_created_at: '2026-11-24T00:00:00+08:00'
    });
  }
});

test('ignores supplied stale and future dates when validating permanent scans', () => {
  const record = {
    in_code: 'in-token',
    out_code: 'out-token',
    created_at: '2026-11-24T00:00:00+08:00'
  };
  const now = new Date('2026-11-24T02:00:00Z');
  for (const date of ['2020-01-01', '2099-12-31', 'not-a-date']) {
    assert.equal(api('validateScan_', { date, mode: 'OUT', code: 'out-token' }, record, now).date, '2026-11-24');
  }
});

test('rejects malformed, unknown, wrong-mode, and missing permanent records', () => {
  const record = {
    in_code: 'in-token',
    out_code: 'out-token',
    created_at: '2026-11-24T00:00:00+08:00'
  };
  const now = new Date('2026-11-24T02:00:00Z');
  assert.equal(api('validateScan_', null, record, now).error, 'INVALID_REQUEST');
  assert.equal(api('validateScan_', { mode: 'SIDEWAYS', code: 'in-token' }, record, now).error, 'INVALID_REQUEST');
  assert.equal(api('validateScan_', { mode: 'IN' }, record, now).error, 'INVALID_REQUEST');
  assert.equal(api('validateScan_', { mode: 'IN', code: 'in-token' }, null, now).error, 'CODE_NOT_FOUND');
  assert.equal(api('validateScan_', { mode: 'IN', code: 'unknown' }, record, now).error, 'INVALID_CODE');
  assert.equal(api('validateScan_', { mode: 'OUT', code: 'in-token' }, record, now).error, 'MODE_MISMATCH');
});

test('escapes CSV commas, quotes, and newlines', () => {
  assert.equal(api('csvEscape_', 'Dela Cruz, "Ana"'), '"Dela Cruz, ""Ana"""');
  assert.equal(api('csvEscape_', 'Line one\nLine two'), '"Line one\nLine two"');
  assert.equal(api('toCsv_', ['name', 'mode'], [['Ana', 'IN']]), '"name","mode"\n"Ana","IN"');
});

test('rejects formula-leading names after normalization', () => {
  for (const trigger of ['=', '+', '-', '@']) {
    assert.throws(() => api('normalizeName_', `${trigger}SUM(A1)`), /NAME_INVALID/);
    assert.throws(() => api('normalizeName_', ` \t${trigger}SUM(A1)\r\n`), /NAME_INVALID/);
  }
});

test('keeps ordinary names, internal punctuation, and length rules', () => {
  assert.equal(api('normalizeName_', "  Ana  O'Neil-Cruz, Jr.  "), "Ana O'Neil-Cruz, Jr.");
  assert.equal(api('normalizeName_', '\tAna\nCruz\r'), 'Ana Cruz');
  assert.equal(api('normalizeName_', 'x'.repeat(80)), 'x'.repeat(80));
  assert.throws(() => api('normalizeName_', 'x'.repeat(81)), /NAME_TOO_LONG/);
});

test('neutralizes every formula-leading CSV field before quoting without changing the input', () => {
  const dangerous = [
    '=1+1', '+1', '-1', '@SUM(A1)', '\tvalue', '\rvalue', '\nvalue',
    '  =1+1', '  +1', '  -1', '  @SUM(A1)', '  \tvalue', '  \rvalue', '  \nvalue'
  ];
  for (const value of dangerous) {
    assert.equal(api('csvEscape_', value), `"'${value.replace(/"/g, '""')}"`, JSON.stringify(value));
  }
  assert.equal(api('csvEscape_', '  Ana Cruz'), '"  Ana Cruz"');
  assert.equal(api('csvEscape_', 'Ana-Cruz'), '"Ana-Cruz"');
});
