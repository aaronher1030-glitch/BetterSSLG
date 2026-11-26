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
