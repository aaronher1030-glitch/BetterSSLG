### Task 6: Apps Script Manifest, Setup Guide, and Packaging Checks

**Files:**
- Create: `SSLG Attendance App/appsscript.json`
- Create: `SSLG Attendance App/SETUP.md`
- Modify: `SSLG Attendance App/package.json`
- Test: `SSLG Attendance App/tests/packaging.test.cjs`

**Interfaces:**
- Consumes: all implementation files from Tasks 1–5.
- Produces: a manifest with `Asia/Manila`, V8, anonymous web-app access, and Spreadsheet scope; an exact deployment guide; packaging assertions.

- [ ] **Step 1: Create the Apps Script manifest**

Write `SSLG Attendance App/appsscript.json`:

```json
{
  "timeZone": "Asia/Manila",
  "dependencies": {},
  "webapp": {
    "executeAs": "USER_DEPLOYING",
    "access": "ANYONE_ANONYMOUS"
  },
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets"
  ]
}
```

- [ ] **Step 2: Write failing packaging tests**

Create `SSLG Attendance App/tests/packaging.test.cjs`:

```javascript
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
```

Run:

```bash
node --test tests/packaging.test.cjs
```

Expected: FAIL until the manifest and setup guide exist.

- [ ] **Step 3: Write the setup guide**

Create `SSLG Attendance App/SETUP.md` with these exact sections and instructions:

1. **What this app stores:** names, random browser tokens, daily QR tokens, and timestamps; no phone numbers.
2. **Public admin warning:** the admin page has no password; anyone with its direct URL can view names and timestamps.
3. **Create the Sheet:** create a blank Google Spreadsheet named `SSLG Office Attendance`; copy its ID from the URL between `/d/` and `/edit`.
4. **Create the Apps Script project:** open `Extensions → Apps Script` from that Sheet.
5. **Add files:** create `Code.gs`, `Core.gs`, `Index.html`, `Styles.html`, `Client.html`, and `QRCodeLib.html`; paste the matching project files. Replace the generated `appsscript.json` through Project Settings → Show `appsscript.json`.
6. **Configure the Sheet:** in Project Settings → Script Properties, add `SPREADSHEET_ID` with the copied ID. Save.
7. **Deploy:** click `Deploy → New deployment → Web app`; execute as the deploying user; set access to `Anyone`; deploy and authorize the requested Google permissions.
8. **Open the office page:** append `?page=admin` to the deployed `/exec` URL; generate a QR pair for today.
9. **Test:** scan the IN code on a phone, register a name, confirm; scan OUT on the same phone and confirm the remembered name; check the Sheet and office list.
10. **Daily use:** generate a fresh pair each morning; print the cards; do not reuse yesterday’s codes.
11. **CSV:** choose a date on the office page and click `Export CSV`.
12. **Troubleshooting:** explain `SPREADSHEET_NOT_CONFIGURED`, expired/invalid codes, Sheet permission errors, and browser local-storage loss.

Include the exact statement: “A live deployment is not verified until the owner completes the scan test in this guide.”

- [ ] **Step 4: Add packaging tests to the default test command**

Verify `package.json` uses `"test": "node --test"` so Node discovers every `*.test.cjs` file on Windows and Unix without shell glob expansion. Verify `package-lock.json` exists after `npm install`.

- [ ] **Step 5: Run packaging and full automated tests**

Run:

```bash
npm test
```

Expected: all test files PASS.

- [ ] **Step 6: Review checkpoint**

Confirm the manifest contains no external API scopes, the setup guide never asks for a service-account JSON file, and no test or source file contains a real Spreadsheet ID, token, password, or Google credential.

---

