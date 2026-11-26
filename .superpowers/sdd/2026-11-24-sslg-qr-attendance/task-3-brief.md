### Task 3: Student Registration, Recognition, and Confirmation UI

**Files:**
- Create: `SSLG Attendance App/Index.html`
- Create: `SSLG Attendance App/Styles.html`
- Create: `SSLG Attendance App/Client.html`
- Test: `SSLG Attendance App/tests/client-static.test.cjs`

**Interfaces:**
- Consumes: `scan.status` and `scan.record` actions from Task 2.
- Produces:
  - `api(action, payload) -> Promise<object>`
  - `getDeviceToken_() -> string`
  - `renderScanPage_(params) -> Promise<void>`
  - `submitScan_(name) -> Promise<void>`
  - readable error messages for every backend error code.

- [ ] **Step 1: Create the HTML shell and include points**

Create `SSLG Attendance App/Index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#102a43">
  <title>SSLG Office Attendance</title>
  <?!= include('Styles'); ?>
</head>
<body>
  <header class="site-header">
    <div class="brand-mark" aria-hidden="true">S</div>
    <div>
      <p class="eyebrow">SSLG Office</p>
      <h1>Attendance</h1>
    </div>
  </header>
  <main id="app" tabindex="-1">
    <section class="loading-card" aria-live="polite">
      <div class="spinner" aria-hidden="true"></div>
      <p>Loading attendance…</p>
    </section>
  </main>
  <footer class="site-footer">Benigno S. Aquino National High School · SSLG</footer>
  <script><?!= include('QRCodeLib'); ?></script>
  <?!= include('Client'); ?>
</body>
</html>
```

- [ ] **Step 2: Add the responsive visual system**

Create `SSLG Attendance App/Styles.html`:

```html
<style>
  :root {
    color-scheme: light;
    --navy: #102a43;
    --teal: #0f766e;
    --teal-dark: #0b5d56;
    --paper: #f6f3ec;
    --white: #ffffff;
    --ink: #172b4d;
    --muted: #627d98;
    --line: #d9e2ec;
    --amber: #b45309;
    --amber-bg: #fff7ed;
    --red: #b42318;
    --red-bg: #fef3f2;
    --green-bg: #ecfdf3;
    --shadow: 0 18px 50px rgba(16, 42, 67, 0.10);
    --font-body: "Segoe UI", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    --font-display: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
    font-family: var(--font-body);
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    color: var(--ink);
    background:
      radial-gradient(circle at 10% 0%, rgba(15, 118, 110, 0.12), transparent 32rem),
      var(--paper);
  }
  button, input { font: inherit; }
  button { cursor: pointer; }
  button:disabled { cursor: wait; opacity: 0.65; }
  [hidden] { display: none !important; }

  .site-header {
    width: min(100% - 32px, 960px);
    margin: 24px auto 18px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-mark {
    width: 46px;
    height: 46px;
    display: grid;
    place-items: center;
    border-radius: 14px;
    color: var(--white);
    background: var(--navy);
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.04em;
  }
  .eyebrow {
    margin: 0 0 4px;
    color: var(--teal);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.13em;
    text-transform: uppercase;
  }
  h1, h2, p { margin-top: 0; }
  h1 { margin-bottom: 0; color: var(--navy); font-family: var(--font-display); font-size: 1.25rem; }
  h2 { margin-bottom: 12px; color: var(--navy); font-family: var(--font-display); font-size: clamp(1.55rem, 5vw, 2rem); font-weight: 600; letter-spacing: -0.035em; }

  #app {
    width: min(100% - 32px, 960px);
    margin: 0 auto;
    outline: none;
  }
  .card {
    margin-bottom: 18px;
    padding: clamp(22px, 5vw, 34px);
    border: 1px solid rgba(217, 226, 236, 0.9);
    border-radius: 24px;
    background: var(--white);
    box-shadow: var(--shadow);
  }
  .scan-card, .success-card, .loading-card { max-width: 480px; margin-inline: auto; }
  .scan-meta { color: var(--muted); font-size: 0.9rem; }
  .welcome { margin: 26px 0 4px; color: var(--muted); }
  .registered-name { margin-bottom: 24px; color: var(--navy); font-size: 1.45rem; font-weight: 750; overflow-wrap: anywhere; }
  .helper-text { margin: 14px 0 0; color: var(--muted); font-size: 0.84rem; line-height: 1.55; }

  .field { display: grid; gap: 8px; margin: 18px 0; color: var(--navy); font-size: 0.86rem; font-weight: 700; }
  .field input {
    width: 100%;
    min-height: 52px;
    padding: 12px 14px;
    border: 1px solid var(--line);
    border-radius: 12px;
    color: var(--ink);
    background: #fbfcfd;
    outline: none;
  }
  .field input:focus { border-color: var(--teal); box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.13); }
  .button {
    width: 100%;
    min-height: 52px;
    padding: 13px 18px;
    border: 0;
    border-radius: 12px;
    color: var(--navy);
    background: #eaf0f5;
    font-weight: 800;
  }
  .button-primary { color: var(--white); background: var(--teal); }
  .button-primary:hover { background: var(--teal-dark); }
  .button-out { color: var(--white); background: var(--navy); }
  .button-out:hover { background: #0b1f33; }
  .button:focus-visible { outline: 3px solid rgba(15, 118, 110, 0.35); outline-offset: 3px; }

  .notice { margin: 18px 0 0; padding: 13px 15px; border-radius: 12px; font-size: 0.9rem; line-height: 1.5; }
  .notice-error { color: var(--red); background: var(--red-bg); }
  .success-card { text-align: center; }
  .success-mark {
    width: 64px;
    height: 64px;
    margin: 0 auto 22px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    color: var(--teal);
    background: var(--green-bg);
    font-size: 1.1rem;
    font-weight: 850;
  }
  .spinner {
    width: 34px;
    height: 34px;
    margin: 0 auto 16px;
    border: 3px solid var(--line);
    border-top-color: var(--teal);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .admin-card { max-width: 960px; margin-inline: auto; }
  .admin-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 24px; }
  .qr-card { padding: 20px; border: 2px solid var(--line); border-radius: 18px; text-align: center; break-inside: avoid; }
  .qr-card img { display: block; width: min(100%, 320px); height: auto; margin: 12px auto; image-rendering: pixelated; }
  .qr-card p { margin-bottom: 6px; font-weight: 750; }
  .qr-card small { color: var(--muted); }
  .qr-in { border-color: rgba(15, 118, 110, 0.42); background: #f2fbf9; }
  .qr-out { border-color: rgba(16, 42, 67, 0.30); background: #f5f8fb; }

  .totals { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 18px 0; }
  .totals div { padding: 14px; border-radius: 12px; background: #f3f6f9; }
  .totals strong { display: block; color: var(--navy); font-size: 1.35rem; }
  .totals span { color: var(--muted); font-size: 0.76rem; }
  .table-wrap { overflow-x: auto; margin-bottom: 18px; border: 1px solid var(--line); border-radius: 12px; }
  .attendance-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
  .attendance-table th, .attendance-table td { padding: 12px 14px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }
  .attendance-table th { color: var(--muted); background: #f8fafc; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em; }
  .attendance-table tr:last-child td { border-bottom: 0; }
  .mode { display: inline-block; min-width: 44px; padding: 4px 8px; border-radius: 999px; text-align: center; font-size: 0.72rem; font-weight: 850; }
  .mode-in { color: var(--teal); background: #d9f3ee; }
  .mode-out { color: var(--navy); background: #e4ebf2; }

  .site-footer { width: min(100% - 32px, 960px); margin: 26px auto; color: var(--muted); font-size: 0.76rem; text-align: center; }

  @media (max-width: 620px) {
    .site-header { margin-top: 16px; }
    .card { border-radius: 18px; }
    .admin-grid { grid-template-columns: 1fr; }
    .totals { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }

  @media print {
    body { background: #fff; }
    .site-header, .site-footer, .admin-card:not(:first-child), .field, .button, .helper-text, .notice, #admin-error { display: none !important; }
    #app, .admin-card { width: 100%; margin: 0; padding: 0; border: 0; box-shadow: none; }
    .admin-card:first-child > .eyebrow, .admin-card:first-child > h2 { text-align: center; }
    .admin-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12mm; margin: 8mm 0; }
    .qr-card { padding: 6mm; border: 1px solid #999; background: #fff !important; }
    .qr-card img { width: 78mm; max-width: 100%; }
  }
</style>
```

- [ ] **Step 3: Add the API adapter and device token helper**

Create `SSLG Attendance App/Client.html` with a `<script>` block containing:

```javascript
const SERVER_ACTIONS = {
  'scan.status': 'scanStatus',
  'scan.record': 'scanRecord',
  'admin.generate': 'adminGenerate',
  'admin.list': 'adminList',
  'admin.export': 'adminExport'
};

async function api(action, payload = {}) {
  if (window.google && window.google.script && window.google.script.run) {
    return new Promise((resolve, reject) => {
      window.google.script.run
        .withSuccessHandler(resolve)
        .withFailureHandler(error => reject(new Error(error && error.message ? error.message : 'APPS_SCRIPT_FAILED')))
        [SERVER_ACTIONS[action]](payload);
    });
  }
  const response = await fetch(`/api/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok || !data.ok) throw new Error(data.error || 'REQUEST_FAILED');
  return data;
}

function getDeviceToken_() {
  const key = 'sslg.attendance.device.v1';
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  let token;
  if (window.crypto && window.crypto.randomUUID) {
    token = window.crypto.randomUUID();
  } else {
    const bytes = new Uint8Array(24);
    window.crypto.getRandomValues(bytes);
    token = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  localStorage.setItem(key, token);
  return token;
}
```

- [ ] **Step 4: Implement scan status, registration, confirmation, and success screens**

Add these functions to `Client.html`:

```javascript
const ERROR_MESSAGES = {
  NAME_REQUIRED: 'Please enter your name.',
  NAME_TOO_LONG: 'Please use a name of 80 characters or fewer.',
  DEVICE_TOKEN_REQUIRED: 'This browser could not create a device token. Enable site storage and try again.',
  INVALID_REQUEST: 'This QR link is incomplete or invalid.',
  CODE_NOT_FOUND: 'This code is not registered. Ask the SSLG office for today’s code.',
  WRONG_DATE: 'This QR code belongs to a different date.',
  CODE_EXPIRED: 'This QR code has expired. Ask the SSLG office for today’s code.',
  INVALID_CODE: 'This QR code is no longer valid. A newer code may have been generated.',
  MODE_MISMATCH: 'This is not the correct code for this attendance action.',
  SPREADSHEET_NOT_CONFIGURED: 'The attendance Sheet is not configured yet. Please contact the SSLG office.',
  SHEET_BUSY: 'The office Sheet is busy. Please try again in a moment.',
  REQUEST_FAILED: 'The scan was not recorded. Check your connection and try again.',
  APPS_SCRIPT_FAILED: 'The scan was not recorded. Check your connection and try again.'
};

function errorMessage_(error) {
  return ERROR_MESSAGES[error && error.message] || ERROR_MESSAGES.REQUEST_FAILED;
}

function scanParams_() {
  return {
    date: new URLSearchParams(location.search).get('date'),
    mode: new URLSearchParams(location.search).get('mode'),
    code: new URLSearchParams(location.search).get('code')
  };
}

async function renderScanPage_(params) {
  const app = document.getElementById('app');
  let deviceToken;
  try {
    deviceToken = getDeviceToken_();
  } catch (error) {
    app.innerHTML = `<section class="card"><p class="notice notice-error">${errorMessage_({ message: 'DEVICE_TOKEN_REQUIRED' })}</p></section>`;
    return;
  }
  let status;
  try {
    status = await api('scan.status', { ...params, device_token: deviceToken });
  } catch (error) {
    app.innerHTML = `<section class="card"><p class="notice notice-error">${errorMessage_(error)}</p></section>`;
    return;
  }
  if (!status.ok) {
    app.innerHTML = `<section class="card"><p class="notice notice-error">${errorMessage_({ message: status.error })}</p></section>`;
    return;
  }
  const isIn = status.mode === 'IN';
  app.innerHTML = `
    <section class="card scan-card">
      <p class="eyebrow">${isIn ? 'Check in' : 'Check out'}</p>
      <h2>${isIn ? 'Record your arrival' : 'Record your departure'}</h2>
      <p class="scan-meta">${escapeHtml_(status.date)} · SSLG Office</p>
      ${status.name ? `
        <p class="welcome">Continuing as</p>
        <p class="registered-name">${escapeHtml_(status.name)}</p>
        <button id="confirm-scan" class="button ${isIn ? 'button-primary' : 'button-out'}">Confirm ${isIn ? 'check in' : 'check out'}</button>
      ` : `
        <form id="registration-form">
          <label class="field">Your name
            <input name="name" autocomplete="name" maxlength="80" required placeholder="Enter your full name">
          </label>
          <button class="button ${isIn ? 'button-primary' : 'button-out'}" type="submit">Register and ${isIn ? 'check in' : 'check out'}</button>
          <p class="helper-text">You only need to enter your name once on this phone.</p>
        </form>
      `}
      <p id="scan-error" class="notice notice-error" hidden></p>
    </section>`;

  const submit = name => submitScan_(params, deviceToken, name);
  const form = document.getElementById('registration-form');
  if (form) {
    form.addEventListener('submit', event => {
      event.preventDefault();
      submit(new FormData(form).get('name'));
    });
  }
  const confirm = document.getElementById('confirm-scan');
  if (confirm) confirm.addEventListener('click', () => submit(status.name));
}

async function submitScan_(params, deviceToken, name) {
  const button = document.querySelector('#app button');
  const errorBox = document.getElementById('scan-error');
  if (button) button.disabled = true;
  if (errorBox) errorBox.hidden = true;
  try {
    const result = await api('scan.record', { ...params, device_token: deviceToken, name });
    if (!result.ok) throw new Error(result.error);
    const event = result.event;
    document.getElementById('app').innerHTML = `
      <section class="card success-card" aria-live="polite">
        <div class="success-mark" aria-hidden="true">OK</div>
        <p class="eyebrow">Recorded</p>
        <h2>${event.mode === 'IN' ? 'Checked in' : 'Checked out'}</h2>
        <p class="registered-name">${escapeHtml_(event.name)}</p>
        <p class="scan-meta">${escapeHtml_(event.scanned_at)} · Philippines time</p>
        <p class="helper-text">You may close this page.</p>
      </section>`;
  } catch (error) {
    if (button) button.disabled = false;
    if (errorBox) {
      errorBox.textContent = errorMessage_(error);
      errorBox.hidden = false;
    }
  }
}

function escapeHtml_(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderLandingPage_() {
  document.getElementById('app').innerHTML = `
    <section class="card scan-card">
      <p class="eyebrow">SSLG Office</p>
      <h2>Scan to record attendance</h2>
      <p>Use your phone camera to scan today’s check-in or check-out QR code posted by the office.</p>
      <p class="helper-text">First time here? You will be asked for your name once. This phone will remember it for later scans.</p>
    </section>`;
}
```

Add the bootstrap call:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  const page = new URLSearchParams(location.search).get('page');
  if (page === 'admin') renderAdminPage_();
  else if (page === 'scan') renderScanPage_(scanParams_());
  else renderLandingPage_();
});
```

`renderLandingPage_()` must show a short instruction to scan an office QR code and must not link to the admin page or display records.

- [ ] **Step 5: Write and run static client tests**

Create `SSLG Attendance App/tests/client-static.test.cjs`:

```javascript
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
```

Run:

```bash
node --test tests/client-static.test.cjs
```

Expected: PASS after the files exist.

- [ ] **Step 6: Review checkpoint**

Verify the student page never requests `admin.list`, contains no phone-number input, and displays “not recorded” rather than success when an API call fails. Confirm names are escaped before insertion into HTML.

---

