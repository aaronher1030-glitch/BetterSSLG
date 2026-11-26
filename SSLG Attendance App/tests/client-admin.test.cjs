const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const client = fs.readFileSync(path.join(__dirname, '..', 'Client.html'), 'utf8');
const script = client.match(/<script>([\s\S]*?)<\/script>/)[1];

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function attendanceResult(date, name, scans) {
  return {
    ok: true,
    totals: { scans, people: 1, in: scans, out: 0 },
    rows: [{ scanned_at: '08:00', name, mode: 'IN' }]
  };
}

function flush() {
  return new Promise(resolve => setImmediate(resolve));
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

async function renderedAdmin(api) {
  const elements = new Map();

  class FakeElement {
    constructor(id) {
      this.id = id;
      this.innerHTML = '';
      this.textContent = '';
      this.value = '';
      this.hidden = false;
      this.disabled = false;
      this.listeners = new Map();
    }

    addEventListener(type, listener) {
      this.listeners.set(type, listener);
    }

    dispatch(type) {
      const listener = this.listeners.get(type);
      if (listener) listener({ preventDefault() {} });
    }

    click() {}
    remove() {}
  }

  for (const id of [
    'app',
    'admin-date',
    'generate-codes',
    'admin-error',
    'qr-pair',
    'attendance-search',
    'attendance-totals',
    'attendance-body',
    'export-csv'
  ]) {
    elements.set(id, new FakeElement(id));
  }
  elements.get('admin-date').value = '2026-11-24';
  elements.get('admin-error').hidden = true;
  elements.get('qr-pair').hidden = true;

  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, new FakeElement(id));
      return elements.get(id);
    },
    addEventListener() {},
    createElement() { return new FakeElement(); },
    body: { appendChild() {} }
  };
  const context = vm.createContext({
    console,
    document,
    window: {
      qrcode() {
        return {
          addData(value) { this.value = value; },
          make() {},
          createDataURL() { return `data:image/png;base64,${this.value}`; }
        };
      }
    },
    confirm: () => { throw new Error('UNEXPECTED_CONFIRMATION'); },
    location: { search: '?page=admin' },
    URLSearchParams,
    Blob,
    URL: { createObjectURL: () => 'blob:attendance', revokeObjectURL() {} },
    setTimeout: callback => callback()
  });
  vm.runInContext(script, context, { filename: 'Client.html' });
  context.api = api;
  await context.renderAdminPage_();
  return { context, elements };
}

test('shows a permanent pair without confirmation or a date-bound generation request', async () => {
  const requests = [];
  const { context, elements } = await renderedAdmin(() => Promise.resolve(attendanceResult('2026-11-24', 'Initial', 1)));
  assert.match(elements.get('app').innerHTML, /Permanent QR codes/);
  assert.match(elements.get('app').innerHTML, /same permanent IN and OUT codes every day/i);
  assert.match(elements.get('app').innerHTML, /id="generate-codes"[^>]*>Show permanent QR pair/);
  assert.doesNotMatch(elements.get('app').innerHTML, /invalidates|Generate QR pair|Daily QR codes/i);

  const record = {
    created_at: '2026-11-24T07:00:00+08:00',
    in_url: 'https://script.test/exec?page=scan&mode=IN&code=permanent-in',
    out_url: 'https://script.test/exec?page=scan&mode=OUT&code=permanent-out'
  };
  context.api = async (action, payload) => {
    requests.push({ action, payload });
    return action === 'admin.generate'
      ? { ok: true, record }
      : attendanceResult(payload.date, 'Initial', 1);
  };
  await context.generateCodes_('2026-11-24');

  assert.deepEqual(plain(requests[0]), { action: 'admin.generate', payload: {} });
  assert.equal(elements.get('qr-pair').hidden, false);
  assert.match(elements.get('qr-pair').innerHTML, /Reusable every day/);
  assert.match(elements.get('qr-pair').innerHTML, /Created 2026-11-24T07:00:00\+08:00/);
  assert.match(elements.get('qr-pair').innerHTML, /permanent-in/);
  assert.match(elements.get('qr-pair').innerHTML, /permanent-out/);
});

test('changing the attendance date preserves permanent QR cards and only reloads records', async () => {
  const requests = [];
  const { context, elements } = await renderedAdmin(() => Promise.resolve(attendanceResult('2026-11-24', 'Initial', 1)));
  const record = {
    created_at: '2026-11-24T07:00:00+08:00',
    in_url: 'https://script.test/exec?page=scan&mode=IN&code=permanent-in',
    out_url: 'https://script.test/exec?page=scan&mode=OUT&code=permanent-out'
  };
  context.api = async (action, payload) => {
    requests.push({ action, payload });
    return action === 'admin.generate'
      ? { ok: true, record }
      : attendanceResult(payload.date, payload.date === '2026-11-25' ? 'New date' : 'Initial', 1);
  };
  await context.generateCodes_('2026-11-24');
  elements.get('admin-date').value = '2026-11-25';
  elements.get('admin-date').dispatch('change');
  await flush();

  assert.equal(elements.get('qr-pair').hidden, false);
  assert.match(elements.get('qr-pair').innerHTML, /Reusable every day/);
  assert.match(elements.get('qr-pair').innerHTML, /permanent-in/);
  assert.equal(requests.filter(request => request.action === 'admin.generate').length, 1);
  assert.deepEqual(plain(requests.at(-1)), { action: 'admin.list', payload: { date: '2026-11-25', query: '' } });
  assert.match(elements.get('attendance-body').innerHTML, /New date/);
  assert.doesNotMatch(elements.get('attendance-body').innerHTML, /Initial/);
});

test('an older attendance response cannot overwrite a newer search result', async () => {
  const requests = [];
  const { context, elements } = await renderedAdmin(() => Promise.resolve(attendanceResult('2026-11-24', 'Initial', 1)));
  context.api = () => {
    const request = deferred();
    requests.push(request);
    return request.promise;
  };

  const olderRequest = context.loadAttendance_('2026-11-24', 'Ada');
  elements.get('attendance-search').value = 'Luis';
  elements.get('attendance-search').dispatch('input');
  requests[1].resolve(attendanceResult('2026-11-24', 'Luis', 3));
  await flush();
  requests[0].resolve(attendanceResult('2026-11-24', 'Ada', 1));
  await olderRequest;

  assert.match(elements.get('attendance-body').innerHTML, /Luis/);
  assert.doesNotMatch(elements.get('attendance-body').innerHTML, /Ada/);
  assert.match(elements.get('attendance-totals').innerHTML, /<strong>3<\/strong>/);
});

test('an older attendance failure cannot resurface an error after a newer search succeeds', async () => {
  const requests = [];
  const { context, elements } = await renderedAdmin(() => Promise.resolve(attendanceResult('2026-11-24', 'Initial', 1)));
  context.api = () => {
    const request = deferred();
    requests.push(request);
    return request.promise;
  };

  elements.get('attendance-search').value = 'Ada';
  elements.get('attendance-search').dispatch('input');
  elements.get('attendance-search').value = 'Luis';
  elements.get('attendance-search').dispatch('input');
  requests[1].resolve(attendanceResult('2026-11-24', 'Luis', 1));
  await flush();
  requests[0].reject(new Error('SHEET_BUSY'));
  await flush();

  assert.equal(elements.get('admin-error').hidden, true);
  assert.match(elements.get('attendance-body').innerHTML, /Luis/);
});

test('starting list and export requests hides a recovered office error', async () => {
  const listRequest = deferred();
  const exportRequest = deferred();
  const { context, elements } = await renderedAdmin(() => Promise.resolve(attendanceResult('2026-11-24', 'Initial', 1)));

  elements.get('admin-error').textContent = 'Previous failure';
  elements.get('admin-error').hidden = false;
  context.api = () => listRequest.promise;
  const pendingList = context.loadAttendance_('2026-11-24', '');
  assert.equal(elements.get('admin-error').hidden, true);
  listRequest.resolve(attendanceResult('2026-11-24', 'Recovered', 1));
  await pendingList;

  elements.get('admin-error').textContent = 'Previous failure';
  elements.get('admin-error').hidden = false;
  context.api = () => exportRequest.promise;
  const pendingExport = context.downloadCsv_('2026-11-24');
  assert.equal(elements.get('admin-error').hidden, true);
  exportRequest.resolve({ ok: true, csv: 'Time,Name\n', filename: 'attendance-2026-11-24.csv' });
  await pendingExport;
});
