const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

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

test('student submission errors are assertive atomic live alerts', () => {
  assert.match(client, /<p\b(?=[^>]*\bid="scan-error")(?=[^>]*\brole="alert")(?=[^>]*\baria-live="assertive")(?=[^>]*\baria-atomic="true")[^>]*>/);
});

test('successful scans focus the success heading', () => {
  assert.match(client, /<h2\b(?=[^>]*\bid="scan-success")(?=[^>]*\btabindex="-1")[^>]*>/);
  assert.match(client, /document\.getElementById\(['"]scan-success['"]\)\.focus\(\)/);
});

test('formula-leading names and missing configuration have readable guidance', () => {
  assert.match(client, /NAME_INVALID:\s*'[^']*(name|start)[^']*'/i);
  assert.match(client, /SPREADSHEET_NOT_CONFIGURED:\s*'[^']*SPREADSHEET_ID[^']*Project Settings[^']*Script Properties[^']*'/);
});

test('invalid device tokens have readable client guidance', () => {
  const script = client.match(/<script>([\s\S]*?)<\/script>/)[1];
  const context = vm.createContext({ document: { addEventListener() {} } });
  vm.runInContext(script, context, { filename: 'Client.html' });
  const message = context.errorMessage_({ message: 'DEVICE_TOKEN_INVALID' });
  assert.match(message, /device token/i);
  assert.match(message, /clear site storage/i);
});

test('student scan parameters omit caller-supplied dates', () => {
  const script = client.match(/<script>([\s\S]*?)<\/script>/)[1];
  const context = vm.createContext({
    document: { addEventListener() {} },
    location: { search: '?page=scan&date=2020-01-01&mode=IN&code=permanent-in' },
    URLSearchParams
  });
  vm.runInContext(script, context, { filename: 'Client.html' });
  assert.deepEqual(JSON.parse(JSON.stringify(context.scanParams_())), {
    mode: 'IN', code: 'permanent-in'
  });
});

test('student errors refer to permanent codes without date expiry or replacement wording', () => {
  const script = client.match(/<script>([\s\S]*?)<\/script>/)[1];
  const context = vm.createContext({ document: { addEventListener() {} } });
  vm.runInContext(script, context, { filename: 'Client.html' });
  assert.match(context.errorMessage_({ message: 'CODE_NOT_FOUND' }), /permanent codes/i);
  assert.doesNotMatch(context.errorMessage_({ message: 'INVALID_CODE' }), /newer|generated|today/i);
  assert.equal(context.errorMessage_({ message: 'WRONG_DATE' }), context.errorMessage_({ message: 'REQUEST_FAILED' }));
  assert.equal(context.errorMessage_({ message: 'CODE_EXPIRED' }), context.errorMessage_({ message: 'REQUEST_FAILED' }));
});

test('landing copy directs students to the posted permanent codes', () => {
  const script = client.match(/<script>([\s\S]*?)<\/script>/)[1];
  const app = { innerHTML: '' };
  const context = vm.createContext({
    document: { addEventListener() {}, getElementById: () => app }
  });
  vm.runInContext(script, context, { filename: 'Client.html' });
  context.renderLandingPage_();
  assert.match(app.innerHTML, /permanent check-in or check-out QR codes/i);
  assert.doesNotMatch(app.innerHTML, /today's|today’s/i);
});
