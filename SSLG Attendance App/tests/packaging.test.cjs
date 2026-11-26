const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

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

test('packaged backend initializes the permanent QR Codes schema', () => {
  const sheets = new Map();
  function makeSheet(name) {
    if (!sheets.has(name)) sheets.set(name, []);
    const rows = sheets.get(name);
    return {
      getLastRow: () => rows.length,
      getRange: (row, column, count) => ({
        setValues: values => rows.splice(row - 1, count, ...values)
      }),
      setFrozenRows() {}
    };
  }
  const spreadsheet = {
    getSheetByName: name => sheets.has(name) ? makeSheet(name) : null,
    insertSheet: name => { sheets.set(name, []); return makeSheet(name); }
  };
  const context = vm.createContext({
    PropertiesService: { getScriptProperties: () => ({ getProperty: () => 'sheet-test-id' }) },
    SpreadsheetApp: { openById: () => spreadsheet }
  });
  for (const file of ['Core.gs', 'Code.gs']) {
    vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
  }
  context.ensureSchema_();
  assert.deepEqual(Array.from(sheets.keys()), ['QR Codes', 'People', 'Attendance']);
  assert.deepEqual(Array.from(sheets.get('QR Codes')[0]), ['in_code', 'out_code', 'created_at', 'created_by']);
});

test('single-file deployment renders the complete app without include dependencies', () => {
  const bundle = fs.readFileSync(path.join(root, 'deploy', 'SSLG Attendance.gs'), 'utf8');
  const expected = fs.readFileSync(path.join(root, 'Index.html'), 'utf8')
    .replace(/<\?!= include\('Styles'\); \?>/, () => fs.readFileSync(path.join(root, 'Styles.html'), 'utf8'))
    .replace(/<\?!= include\('QRCodeLib'\); \?>/, () => fs.readFileSync(path.join(root, 'QRCodeLib.html'), 'utf8'))
    .replace(/<\?!= include\('Client'\); \?>/, () => fs.readFileSync(path.join(root, 'Client.html'), 'utf8'))
    .replace(/<\?!= requestParamsScript_\(event\); \?>/, () => '<script>window.SSLG_SERVER_PARAMS = {};</script>');
  const context = vm.createContext({
    HtmlService: { createHtmlOutput: html => ({ getContent: () => html }) }
  });
  vm.runInContext(bundle, context, { filename: 'SSLG Attendance.gs' });
  assert.equal(context.doGet().getContent(), expected);
  assert.doesNotMatch(bundle, /include\(['"](?:Styles|QRCodeLib|Client)['"]\)/);
  assert.doesNotMatch(bundle, /SPREADSHEET_ID\s*=\s*['"][^'"]+/);
  assert.ok(bundle.length < 100000, `bundle is ${bundle.length} characters`);
});

test('deployment bundle injects safely escaped request parameters', () => {
  const bundle = fs.readFileSync(path.join(root, 'deploy', 'SSLG Attendance.gs'), 'utf8');
  const context = vm.createContext({
    HtmlService: { createHtmlOutput: html => ({ getContent: () => html }) }
  });
  vm.runInContext(bundle, context, { filename: 'SSLG Attendance.gs' });
  const html = context.doGet({ parameter: {
    page: 'scan', mode: 'IN', code: '</script><script>alert(1)</script>&\u2028', ignored: 'secret'
  } }).getContent();
  const match = html.match(/window\.SSLG_SERVER_PARAMS = (.*?);<\/script>/);
  assert.ok(match);
  assert.deepEqual(JSON.parse(match[1]), { page: 'scan', mode: 'IN', code: '</script><script>alert(1)</script>&\u2028' });
  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  assert.doesNotMatch(match[1], /<\/script>|&|\u2028/);
});

test('deployment bundle includes a matching manifest and owner checklist', () => {
  const deploy = path.join(root, 'deploy');
  assert.equal(fs.existsSync(path.join(deploy, 'appsscript.json')), true);
  assert.equal(fs.existsSync(path.join(deploy, 'START HERE.txt')), true);
  assert.deepEqual(
    JSON.parse(fs.readFileSync(path.join(deploy, 'appsscript.json'), 'utf8')),
    JSON.parse(fs.readFileSync(path.join(root, 'appsscript.json'), 'utf8'))
  );
});

test('project contains no hard-coded spreadsheet ID or secret assignment', () => {
  for (const file of ['Core.gs', 'Code.gs', 'Client.html', 'preview/server.cjs']) {
    const text = fs.readFileSync(path.join(root, file), 'utf8');
    assert.doesNotMatch(text, /SPREADSHEET_ID\s*=\s*['"][^'"]+/);
    assert.doesNotMatch(text, /API_KEY\s*=|PRIVATE_KEY\s*=|client_secret/i);
  }
});
