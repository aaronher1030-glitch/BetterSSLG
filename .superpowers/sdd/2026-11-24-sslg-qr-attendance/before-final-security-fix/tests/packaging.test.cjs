const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

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

test('project contains no hard-coded spreadsheet ID or secret assignment', () => {
  for (const file of ['Core.gs', 'Code.gs', 'Client.html', 'preview/server.cjs']) {
    const text = fs.readFileSync(path.join(root, file), 'utf8');
    assert.doesNotMatch(text, /SPREADSHEET_ID\s*=\s*['"][^'"]+/);
    assert.doesNotMatch(text, /API_KEY\s*=|PRIVATE_KEY\s*=|client_secret/i);
  }
});
