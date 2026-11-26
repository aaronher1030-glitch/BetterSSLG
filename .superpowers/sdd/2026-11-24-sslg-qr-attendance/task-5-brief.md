### Task 5: Local Preview Server and API Integration Tests

**Files:**
- Create: `SSLG Attendance App/preview/server.cjs`
- Test: `SSLG Attendance App/tests/preview.test.cjs`
- Modify: `SSLG Attendance App/package.json`

**Interfaces:**
- Consumes: `Index.html`, `Styles.html`, `QRCodeLib.html`, `Client.html`, and `Core.gs`.
- Produces:
  - `createPreviewServer() -> http.Server`
  - `GET /` and `GET /?page=admin|scan` -> rendered HTML
  - `POST /api/:action` -> JSON using the same action contract as `Code.gs`

- [ ] **Step 1: Write failing preview API tests**

Create `SSLG Attendance App/tests/preview.test.cjs`:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const { createPreviewServer } = require('../preview/server.cjs');

async function withServer(run) {
  const server = createPreviewServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try { await run(base); } finally { await new Promise(resolve => server.close(resolve)); }
}

async function post(base, action, payload) {
  const response = await fetch(`${base}/api/${action}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  return response.json();
}

test('renders all include files without scriptlet placeholders', async () => {
  await withServer(async base => {
    const html = await (await fetch(base)).text();
    assert.match(html, /<style>/);
    assert.match(html, /function renderAdminPage_/);
    assert.doesNotMatch(html, /include\(/);
  });
});

test('preview supports registration, recognition, and repeated scans', async () => {
  await withServer(async base => {
    const date = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(new Date());
    const generated = await post(base, 'admin.generate', { date });
    assert.equal(generated.ok, true);
    const first = await post(base, 'scan.record', {
      date, mode: 'IN', code: generated.record.in_code,
      device_token: 'preview-device', name: 'Ana Cruz'
    });
    assert.equal(first.ok, true);
    const status = await post(base, 'scan.status', {
      date, mode: 'OUT', code: generated.record.out_code,
      device_token: 'preview-device'
    });
    assert.equal(status.name, 'Ana Cruz');
    const second = await post(base, 'scan.record', {
      date, mode: 'OUT', code: generated.record.out_code,
      device_token: 'preview-device'
    });
    assert.equal(second.ok, true);
    const list = await post(base, 'admin.list', { date, query: '' });
    assert.equal(list.totals.scans, 2);
  });
});
```

Run:

```bash
node --test tests/preview.test.cjs
```

Expected: FAIL because `preview/server.cjs` does not exist.

- [ ] **Step 2: Implement the preview server**

Create `SSLG Attendance App/preview/server.cjs` using only Node built-ins:

```javascript
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { randomUUID } = require('node:crypto');

const root = path.join(__dirname, '..');

function loadCore() {
  const context = vm.createContext({ console, Date, Intl, JSON });
  vm.runInContext(fs.readFileSync(path.join(root, 'Core.gs'), 'utf8'), context);
  return context;
}

function renderIndex() {
  return fs.readFileSync(path.join(root, 'Index.html'), 'utf8')
    .replace(/<\?!= include\('Styles'\); \?>/, fs.readFileSync(path.join(root, 'Styles.html'), 'utf8'))
    .replace(/<\?!= include\('QRCodeLib'\); \?>/, fs.readFileSync(path.join(root, 'QRCodeLib.html'), 'utf8'))
    .replace(/<\?!= include\('Client'\); \?>/, fs.readFileSync(path.join(root, 'Client.html'), 'utf8'));
}

function createPreviewServer() {
  const core = loadCore();
  const state = { codes: new Map(), people: new Map(), attendance: [] };
  const baseUrl = process.env.PREVIEW_PUBLIC_URL || 'http://127.0.0.1:4173';

  const server = http.createServer(async (request, response) => {
    response.setHeader('Content-Type', 'application/json; charset=utf-8');
    if (request.method === 'GET' && request.url.startsWith('/')) {
      response.setHeader('Content-Type', 'text/html; charset=utf-8');
      response.end(renderIndex());
      return;
    }
    if (request.method === 'POST' && request.url.startsWith('/api/')) {
      const action = request.url.slice('/api/'.length);
      let raw = '';
      for await (const chunk of request) raw += chunk;
      const payload = JSON.parse(raw || '{}');
      let result;
      try {
        if (action === 'admin.generate') {
          const record = core.createDailyCodeRecord_(payload.date, new Date(), randomUUID);
          state.codes.set(payload.date, {
            ...record,
            in_url: `${baseUrl}/?page=scan&date=${payload.date}&mode=IN&code=${record.in_code}`,
            out_url: `${baseUrl}/?page=scan&date=${payload.date}&mode=OUT&code=${record.out_code}`
          });
          result = { ok: true, record: state.codes.get(payload.date) };
        } else if (action === 'scan.status' || action === 'scan.record') {
          const code = state.codes.get(payload.date);
          const validation = core.validateScan_(payload, code, new Date());
          if (!validation.ok) result = validation;
          else {
            const person = state.people.get(payload.device_token);
            if (action === 'scan.status') {
              result = { ok: true, date: payload.date, mode: payload.mode, name: person ? person.name : null, device_token: payload.device_token, qr_created_at: code.created_at };
            } else {
              const name = core.normalizeName_(person ? person.name : payload.name);
              const now = core.manilaTimestamp_(new Date());
              if (!person) state.people.set(payload.device_token, { name, first_seen_at: now, last_seen_at: now });
              else person.last_seen_at = now;
              const event = { event_id: randomUUID(), date: payload.date, scanned_at: now, mode: payload.mode.toUpperCase(), name, device_token: payload.device_token, qr_created_at: code.created_at };
              state.attendance.push(event);
              result = { ok: true, event };
            }
          }
        } else if (action === 'admin.list') {
          const rows = state.attendance.filter(row => row.date === payload.date && (!payload.query || row.name.toLowerCase().includes(payload.query.toLowerCase()))).reverse();
          const all = state.attendance.filter(row => row.date === payload.date);
          result = { ok: true, rows, totals: { scans: all.length, people: new Set(all.map(row => row.device_token)).size, in: all.filter(row => row.mode === 'IN').length, out: all.filter(row => row.mode === 'OUT').length } };
        } else if (action === 'admin.export') {
          const rows = state.attendance.filter(row => row.date === payload.date);
          result = { ok: true, csv: core.toCsv_(core.ATTENDANCE_HEADERS, rows.map(row => core.ATTENDANCE_HEADERS.map(header => row[header]))), filename: `SSLG-attendance-${payload.date}.csv` };
        } else {
          result = { ok: false, error: 'UNKNOWN_ACTION' };
        }
      } catch (error) {
        result = { ok: false, error: error.message || 'REQUEST_FAILED' };
      }
      response.end(JSON.stringify(result));
      return;
    }
    response.statusCode = 404;
    response.end(JSON.stringify({ ok: false, error: 'NOT_FOUND' }));
  });
  return server;
}

if (require.main === module) {
  const port = Number(process.env.PORT || 4173);
  createPreviewServer().listen(port, '127.0.0.1', () => {
    console.log(`SSLG attendance preview: http://127.0.0.1:${port}`);
  });
}

module.exports = { createPreviewServer };
```

- [ ] **Step 3: Run preview tests**

Run:

```bash
node --test tests/preview.test.cjs
```

Expected: all tests PASS.

- [ ] **Step 4: Run the browser preview**

Run in one terminal:

```bash
npm run preview
```

Open `http://127.0.0.1:4173/?page=admin` with Playwright or browser-use. Verify the page renders, codes generate, QR images appear, and the empty table message is visible. Keep the server running for Task 7 browser checks.

- [ ] **Step 5: Review checkpoint**

Confirm the preview uses the same `Core.gs` validation functions as the backend, stores data only in memory, and restarts empty. Confirm no Google credentials are needed for preview.

---

