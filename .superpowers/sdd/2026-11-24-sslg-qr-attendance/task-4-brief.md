### Task 4: Office QR Generation, Attendance List, and CSV Export

**Files:**
- Modify: `SSLG Attendance App/Client.html`
- Modify: `SSLG Attendance App/Styles.html`
- Create: `SSLG Attendance App/QRCodeLib.html`
- Test: `SSLG Attendance App/tests/qr.test.cjs`

**Interfaces:**
- Consumes: `admin.generate`, `admin.list`, and `admin.export`; bundled global `qrcode`.
- Produces:
  - `renderAdminPage_() -> Promise<void>`
  - `generateCodes_(dateKey) -> Promise<void>`
  - `loadAttendance_(dateKey, query) -> Promise<void>`
  - `downloadCsv_(dateKey) -> Promise<void>`
  - `qrDataUrl_(value) -> string`

- [ ] **Step 1: Vendor the QR encoder with its license**

Install dependencies if needed:

```bash
npm install
```

Copy the contents of `node_modules/qrcode-generator/qrcode.js` into `SSLG Attendance App/QRCodeLib.html`, preserving its MIT license comment at the top. Do not use a CDN at runtime.

- [ ] **Step 2: Write a failing QR round-trip test**

Create `SSLG Attendance App/tests/qr.test.cjs`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const jsQR = require('jsqr');
const { PNG } = require('pngjs');

const source = fs.readFileSync(path.join(__dirname, '..', 'QRCodeLib.html'), 'utf8');
const context = vm.createContext({});
vm.runInContext(source, context, { filename: 'QRCodeLib.html' });

function decodeQr(value) {
  const qr = context.qrcode(0, 'M');
  qr.addData(value);
  qr.make();
  const dataUrl = qr.createDataURL(8, 4);
  const png = PNG.sync.read(Buffer.from(dataUrl.split(',')[1], 'base64'));
  const decoded = jsQR(new Uint8ClampedArray(png.data), png.width, png.height);
  return decoded && decoded.data;
}

test('IN QR payload decodes exactly', () => {
  const value = 'https://script.test/exec?page=scan&date=2026-11-24&mode=IN&code=in-token';
  assert.equal(decodeQr(value), value);
});

test('OUT QR payload decodes exactly', () => {
  const value = 'https://script.test/exec?page=scan&date=2026-11-24&mode=OUT&code=out-token';
  assert.equal(decodeQr(value), value);
});
```

Run:

```bash
node --test tests/qr.test.cjs
```

Expected: PASS after the library is vendored.

- [ ] **Step 3: Implement the office dashboard**

Add the following to `Client.html`:

```javascript
function defaultAdminDate_() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(new Date());
}

function qrDataUrl_(value) {
  const qr = window.qrcode(0, 'M');
  qr.addData(value);
  qr.make();
  return qr.createDataURL(8, 4);
}

async function renderAdminPage_() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <section class="card admin-card">
      <p class="eyebrow">Office tools</p>
      <h2>Daily QR codes</h2>
      <p class="helper-text">Generating a new pair invalidates the old pair for this date.</p>
      <label class="field">Attendance date
        <input id="admin-date" type="date" value="${defaultAdminDate_()}">
      </label>
      <button id="generate-codes" class="button button-primary">Generate QR pair</button>
      <p id="admin-error" class="notice notice-error" hidden></p>
      <div id="qr-pair" class="admin-grid" hidden></div>
    </section>
    <section class="card admin-card">
      <p class="eyebrow">Shared Sheet</p>
      <h2>Attendance records</h2>
      <label class="field">Search name
        <input id="attendance-search" type="search" placeholder="Search registered names">
      </label>
      <div id="attendance-totals" class="totals" aria-live="polite"></div>
      <div class="table-wrap"><table class="attendance-table"><thead><tr><th>Time</th><th>Name</th><th>Action</th></tr></thead><tbody id="attendance-body"></tbody></table></div>
      <button id="export-csv" class="button">Export CSV</button>
    </section>`;

  const dateInput = document.getElementById('admin-date');
  const searchInput = document.getElementById('attendance-search');
  document.getElementById('generate-codes').addEventListener('click', () => generateCodes_(dateInput.value));
  dateInput.addEventListener('change', () => loadAttendance_(dateInput.value, searchInput.value).catch(showAdminError_));
  searchInput.addEventListener('input', () => loadAttendance_(dateInput.value, searchInput.value).catch(showAdminError_));
  document.getElementById('export-csv').addEventListener('click', () => downloadCsv_(dateInput.value).catch(showAdminError_));
  await loadAttendance_(dateInput.value, '').catch(showAdminError_);
}

function showAdminError_(error) {
  const errorBox = document.getElementById('admin-error');
  if (!errorBox) return;
  errorBox.textContent = errorMessage_(error);
  errorBox.hidden = false;
}

async function generateCodes_(dateKey) {
  const button = document.getElementById('generate-codes');
  const errorBox = document.getElementById('admin-error');
  if (!confirm('Generate new IN and OUT codes? The previous pair for this date will stop working.')) return;
  button.disabled = true;
  errorBox.hidden = true;
  try {
    const result = await api('admin.generate', { date: dateKey });
    if (!result.ok) throw new Error(result.error);
    const record = result.record;
    document.getElementById('qr-pair').innerHTML = `
      <article class="qr-card qr-in"><p class="eyebrow">Check in</p><img alt="Check-in QR code" src="${qrDataUrl_(record.in_url)}"><p>${escapeHtml_(record.date)}</p><small>Created ${escapeHtml_(record.created_at)}</small></article>
      <article class="qr-card qr-out"><p class="eyebrow">Check out</p><img alt="Check-out QR code" src="${qrDataUrl_(record.out_url)}"><p>${escapeHtml_(record.date)}</p><small>Created ${escapeHtml_(record.created_at)}</small></article>`;
    document.getElementById('qr-pair').hidden = false;
    await loadAttendance_(dateKey, document.getElementById('attendance-search').value);
  } catch (error) {
    errorBox.textContent = errorMessage_(error);
    errorBox.hidden = false;
  } finally {
    button.disabled = false;
  }
}

async function loadAttendance_(dateKey, query) {
  const result = await api('admin.list', { date: dateKey, query });
  if (!result.ok) throw new Error(result.error);
  document.getElementById('attendance-totals').innerHTML = `
    <div><strong>${result.totals.scans}</strong><span>Scans</span></div>
    <div><strong>${result.totals.people}</strong><span>People</span></div>
    <div><strong>${result.totals.in}</strong><span>IN</span></div>
    <div><strong>${result.totals.out}</strong><span>OUT</span></div>`;
  document.getElementById('attendance-body').innerHTML = result.rows.length
    ? result.rows.map(row => `<tr><td>${escapeHtml_(row.scanned_at)}</td><td>${escapeHtml_(row.name)}</td><td><span class="mode mode-${row.mode === 'IN' ? 'in' : 'out'}">${escapeHtml_(row.mode)}</span></td></tr>`).join('')
    : '<tr><td colspan="3">No scans recorded for this date.</td></tr>';
}

async function downloadCsv_(dateKey) {
  const result = await api('admin.export', { date: dateKey });
  if (!result.ok) throw new Error(result.error);
  const blob = new Blob([result.csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = result.filename;
  link.click();
  URL.revokeObjectURL(url);
}
```

Update the date button label when the selected date changes, or keep the neutral label `Generate QR pair` to avoid a stale “today” label. Use the neutral label.

- [ ] **Step 4: Add print and table styles**

Extend `Styles.html` so:

- `@media print` hides the header, footer, filters, buttons, attendance section, and helper text;
- only `#qr-pair` prints, with one IN and one OUT card per row;
- QR images are at least 240px wide in print and do not break across pages;
- table rows remain readable on mobile through a horizontally scrollable wrapper.

- [ ] **Step 5: Run static and QR tests**

Run:

```bash
node --test tests/client-static.test.cjs
node --test tests/qr.test.cjs
```

Expected: all tests PASS.

- [ ] **Step 6: Review checkpoint**

Confirm both QR codes carry `page=scan`, the selected date, distinct modes, and the server-generated tokens. Confirm CSV downloads use a Blob rather than navigating to a data URL. Confirm the admin URL appears only in direct navigation, never as a student link.

---

