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

test('preview exports recorded attendance as CSV', async () => {
  await withServer(async base => {
    const date = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(new Date());
    const generated = await post(base, 'admin.generate', { date });
    await post(base, 'scan.record', {
      date, mode: 'IN', code: generated.record.in_code,
      device_token: 'export-device', name: 'Ana Cruz'
    });
    const exported = await post(base, 'admin.export', { date });
    assert.equal(exported.ok, true);
    assert.equal(exported.filename, `SSLG-attendance-${date}.csv`);
    assert.match(exported.csv, /^"event_id","date","scanned_at","mode","name","device_token","qr_created_at"\n/);
    assert.match(exported.csv, /"Ana Cruz"/);
  });
});
