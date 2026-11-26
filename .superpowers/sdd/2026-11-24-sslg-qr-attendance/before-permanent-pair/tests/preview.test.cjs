const test = require('node:test');
const assert = require('node:assert/strict');
const { createPreviewServer } = require('../preview/server.cjs');

async function withServer(run) {
  const server = createPreviewServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try { await run(base); } finally {
    const closed = new Promise(resolve => server.close(resolve));
    server.closeAllConnections();
    await closed;
  }
}

async function post(base, action, payload) {
  const response = await fetch(`${base}/api/${action}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  return response.json();
}

async function generateForToday(base) {
  const date = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(new Date());
  const generated = await post(base, 'admin.generate', { date });
  assert.equal(generated.ok, true);
  return { date, record: generated.record };
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

test('preview returns a JSON error for malformed request bodies', async () => {
  await withServer(async base => {
    const response = await fetch(`${base}/api/admin.list`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"date":',
      signal: AbortSignal.timeout(2000)
    });
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /^application\/json/);
    const result = await response.json();
    assert.equal(result.ok, false);
    assert.equal(typeof result.error, 'string');
    assert.ok(result.error.length > 0);
    assert.deepEqual(await post(base, 'admin.list', {}), {
      ok: true, rows: [], totals: { scans: 0, people: 0, in: 0, out: 0 }
    });
  });
});

test('preview scan handlers reject missing device tokens without writing attendance', async () => {
  await withServer(async base => {
    const { date, record } = await generateForToday(base);
    const payload = { date, mode: 'IN', code: record.in_code, name: 'Ana Cruz' };
    const results = [];
    for (const action of ['scan.status', 'scan.record']) {
      results.push(await post(base, action, payload));
    }
    assert.deepEqual(results, [
      { ok: false, error: 'DEVICE_TOKEN_REQUIRED' },
      { ok: false, error: 'DEVICE_TOKEN_REQUIRED' }
    ]);
    const list = await post(base, 'admin.list', { date });
    assert.equal(list.totals.scans, 0);
    assert.equal(list.totals.people, 0);
  });
});

test('preview status accepts a 101-character device token while record rejects it without writing', async () => {
  await withServer(async base => {
    const { date, record } = await generateForToday(base);
    const deviceToken = 'x'.repeat(101);
    const payload = {
      date, mode: 'IN', code: record.in_code,
      device_token: deviceToken, name: 'Ana Cruz'
    };
    assert.deepEqual(await post(base, 'scan.status', payload), {
      ok: true, date, mode: 'IN', name: null,
      device_token: deviceToken, qr_created_at: record.created_at
    });
    assert.deepEqual(await post(base, 'scan.record', payload), {
      ok: false, error: 'DEVICE_TOKEN_REQUIRED'
    });
    const list = await post(base, 'admin.list', { date });
    assert.equal(list.totals.scans, 0);
    assert.equal(list.totals.people, 0);
  });
});

test('preview rejects formula-leading names without registering or recording them', async () => {
  await withServer(async base => {
    const { date, record } = await generateForToday(base);
    for (const [index, trigger] of ['=', '+', '-', '@'].entries()) {
      const result = await post(base, 'scan.record', {
        date, mode: 'IN', code: record.in_code,
        device_token: `formula-device-${index}`, name: `  ${trigger}SUM(A1)  `
      });
      assert.deepEqual(result, { ok: false, error: 'NAME_INVALID' });
    }
    const list = await post(base, 'admin.list', { date });
    assert.equal(list.totals.scans, 0);
    assert.equal(list.totals.people, 0);
  });
});

test('preview accepts 100-character device tokens and returns validated scan status fields', async () => {
  await withServer(async base => {
    const { date, record } = await generateForToday(base);
    const deviceToken = 'x'.repeat(100);
    const recorded = await post(base, 'scan.record', {
      date, mode: 'in', code: record.in_code, device_token: deviceToken, name: 'Ana Cruz'
    });
    assert.equal(recorded.ok, true);
    const status = await post(base, 'scan.status', {
      date, mode: 'out', code: record.out_code, device_token: deviceToken
    });
    assert.deepEqual(status, {
      ok: true, date, mode: 'OUT', name: 'Ana Cruz',
      device_token: deviceToken, qr_created_at: record.created_at
    });
  });
});

test('preview search trims and stringifies queries like the backend', async () => {
  await withServer(async base => {
    const { date, record } = await generateForToday(base);
    for (const [device_token, name] of [
      ['search-device-1', 'Ana Cruz'],
      ['search-device-2', 'Agent 42']
    ]) {
      const recorded = await post(base, 'scan.record', {
        date, mode: 'IN', code: record.in_code, device_token, name
      });
      assert.equal(recorded.ok, true);
    }
    const whitespace = await post(base, 'admin.list', { date, query: '  ANA  ' });
    const nonString = await post(base, 'admin.list', { date, query: 42 });
    assert.deepEqual({
      whitespace: (whitespace.rows || []).map(row => row.name),
      nonString: (nonString.rows || []).map(row => row.name)
    }, { whitespace: ['Ana Cruz'], nonString: ['Agent 42'] });
  });
});
