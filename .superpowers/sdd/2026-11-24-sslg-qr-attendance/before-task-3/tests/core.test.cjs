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
