const SSLG_ATTENDANCE_TIME_ZONE = 'Asia/Manila';

const DAILY_CODE_HEADERS = ['date', 'in_code', 'out_code', 'created_at', 'created_by'];
const PEOPLE_HEADERS = ['device_token', 'name', 'first_seen_at', 'last_seen_at'];
const ATTENDANCE_HEADERS = ['event_id', 'date', 'scanned_at', 'mode', 'name', 'device_token', 'qr_created_at'];

function normalizeName_(value) {
  const name = String(value == null ? '' : value).trim().replace(/\s+/g, ' ');
  if (!name) throw new Error('NAME_REQUIRED');
  if (name.length > 80) throw new Error('NAME_TOO_LONG');
  return name;
}

function manilaParts_(date) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: SSLG_ATTENDANCE_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23'
  }).formatToParts(date);
  const result = {};
  parts.forEach(part => {
    if (part.type !== 'literal') result[part.type] = part.value;
  });
  return result;
}

function manilaDateKey_(date = new Date()) {
  const parts = manilaParts_(date);
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function manilaTimestamp_(date = new Date()) {
  const parts = manilaParts_(date);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}+08:00`;
}

function createDailyCodeRecord_(dateKey, now, makeToken) {
  const normalizedDate = String(dateKey);
  const parsedDate = new Date(`${normalizedDate}T00:00:00.000Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(normalizedDate) || Number.isNaN(parsedDate.getTime()) || parsedDate.toISOString().slice(0, 10) !== normalizedDate) {
    throw new Error('INVALID_DATE');
  }
  const inCode = makeToken();
  const outCode = makeToken();
  if (!inCode || !outCode || inCode === outCode) throw new Error('TOKEN_GENERATION_FAILED');
  return {
    date: normalizedDate,
    in_code: inCode,
    out_code: outCode,
    created_at: manilaTimestamp_(now),
    created_by: 'SSLG Office'
  };
}

function validateScan_(params, record, now = new Date()) {
  if (!params || typeof params !== 'object') return { ok: false, error: 'INVALID_REQUEST' };
  const date = String(params.date || '');
  const mode = String(params.mode || '').toUpperCase();
  const code = String(params.code || '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !['IN', 'OUT'].includes(mode) || !code) {
    return { ok: false, error: 'INVALID_REQUEST' };
  }
  if (!record) return { ok: false, error: 'CODE_NOT_FOUND' };
  if (record.date !== date) return { ok: false, error: 'WRONG_DATE' };
  if (manilaDateKey_(now) !== date) return { ok: false, error: 'CODE_EXPIRED' };
  const expected = mode === 'IN' ? record.in_code : record.out_code;
  if (code !== expected) return { ok: false, error: mode === 'IN' ? 'INVALID_CODE' : 'MODE_MISMATCH' };
  return { ok: true, date, mode, qr_created_at: record.created_at };
}

function csvEscape_(value) {
  return `"${String(value == null ? '' : value).replace(/"/g, '""')}"`;
}

function toCsv_(headers, rows) {
  return [headers, ...rows]
    .map(row => row.map(csvEscape_).join(','))
    .join('\n');
}
