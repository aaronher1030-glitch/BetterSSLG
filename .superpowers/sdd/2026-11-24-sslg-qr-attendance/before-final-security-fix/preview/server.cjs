const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { randomUUID } = require('node:crypto');

const root = path.join(__dirname, '..');

function loadCore() {
  const context = vm.createContext({ console, Date, Intl, JSON });
  vm.runInContext(fs.readFileSync(path.join(root, 'Core.gs'), 'utf8'), context);
  context.ATTENDANCE_HEADERS = vm.runInContext('ATTENDANCE_HEADERS', context);
  return context;
}

function renderIndex() {
  return fs.readFileSync(path.join(root, 'Index.html'), 'utf8')
    .replace(/<\?!= include\('Styles'\); \?>/, () => fs.readFileSync(path.join(root, 'Styles.html'), 'utf8'))
    .replace(/<\?!= include\('QRCodeLib'\); \?>/, () => fs.readFileSync(path.join(root, 'QRCodeLib.html'), 'utf8'))
    .replace(/<\?!= include\('Client'\); \?>/, () => fs.readFileSync(path.join(root, 'Client.html'), 'utf8'));
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
      let payload;
      let result;
      try {
        let raw = '';
        for await (const chunk of request) raw += chunk;
        payload = JSON.parse(raw || '{}');
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
            const deviceToken = String(payload.device_token || '');
            if (!deviceToken || (action === 'scan.record' && deviceToken.length > 100)) result = { ok: false, error: 'DEVICE_TOKEN_REQUIRED' };
            else {
              const person = state.people.get(deviceToken);
              if (action === 'scan.status') {
                result = { ok: true, date: validation.date, mode: validation.mode, name: person ? person.name : null, device_token: deviceToken, qr_created_at: validation.qr_created_at };
              } else {
                const name = core.normalizeName_(person ? person.name : payload.name);
                const now = core.manilaTimestamp_(new Date());
                if (!person) state.people.set(deviceToken, { name, first_seen_at: now, last_seen_at: now });
                else person.last_seen_at = now;
                const event = { event_id: randomUUID(), date: validation.date, scanned_at: now, mode: validation.mode, name, device_token: deviceToken, qr_created_at: validation.qr_created_at };
                state.attendance.push(event);
                result = { ok: true, event };
              }
            }
          }
        } else if (action === 'admin.list') {
          const normalizedQuery = String(payload.query || '').trim().toLowerCase();
          const rows = state.attendance.filter(row => row.date === payload.date && (!normalizedQuery || String(row.name).toLowerCase().includes(normalizedQuery))).reverse();
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
