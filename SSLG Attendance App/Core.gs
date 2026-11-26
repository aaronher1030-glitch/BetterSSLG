const SSLG_ATTENDANCE_TIME_ZONE = 'Asia/Manila';

const QR_CODE_HEADERS = ['in_code', 'out_code', 'created_at', 'created_by'];
const PEOPLE_HEADERS = ['device_token', 'name', 'first_seen_at', 'last_seen_at'];
const ATTENDANCE_HEADERS = ['event_id', 'date', 'scanned_at', 'mode', 'name', 'device_token', 'qr_created_at'];

function normalizeName_(value) {
  const name = String(value == null ? '' : value).trim().replace(/\s+/g, ' ');
  if (!name) throw new Error('NAME_REQUIRED');
  if (/^[=+\-@]/.test(name)) throw new Error('NAME_INVALID');
  if (name.length > 80) throw new Error('NAME_TOO_LONG');
  return name;
}

function deviceTokenError_(deviceToken, forWrite) {
  if (!deviceToken || (forWrite && deviceToken.length > 100)) return 'DEVICE_TOKEN_REQUIRED';
  if (/^[ \t\r\n]*[=+\-@\t\r\n]/.test(deviceToken)) return 'DEVICE_TOKEN_INVALID';
  return null;
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

function sheetDateKey_(value) {
  if (value && typeof value.getTime === 'function' && !Number.isNaN(value.getTime())) {
    return manilaDateKey_(value);
  }
  return String(value == null ? '' : value).trim();
}

function manilaTimestamp_(date = new Date()) {
  const parts = manilaParts_(date);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}+08:00`;
}

function createPermanentCodeRecord_(now, makeToken) {
  const inCode = makeToken();
  const outCode = makeToken();
  if (!inCode || !outCode || inCode === outCode) throw new Error('TOKEN_GENERATION_FAILED');
  return {
    in_code: inCode,
    out_code: outCode,
    created_at: manilaTimestamp_(now),
    created_by: 'SSLG Office'
  };
}

function validateScan_(params, record, now = new Date()) {
  if (!params || typeof params !== 'object') return { ok: false, error: 'INVALID_REQUEST' };
  const mode = String(params.mode || '').toUpperCase();
  const code = String(params.code || '');
  if (!['IN', 'OUT'].includes(mode) || !code) return { ok: false, error: 'INVALID_REQUEST' };
  if (!record) return { ok: false, error: 'CODE_NOT_FOUND' };
  const expected = mode === 'IN' ? record.in_code : record.out_code;
  if (code !== expected) return { ok: false, error: mode === 'IN' ? 'INVALID_CODE' : 'MODE_MISMATCH' };
  return { ok: true, date: manilaDateKey_(now), mode, qr_created_at: record.created_at };
}

function csvEscape_(value) {
  const text = String(value == null ? '' : value);
  const safeText = /^[ \t\r\n]*[=+\-@\t\r\n]/.test(text) ? `'${text}` : text;
  return `"${safeText.replace(/"/g, '""')}"`;
}

function toCsv_(headers, rows) {
  return [headers, ...rows]
    .map(row => row.map(csvEscape_).join(','))
    .join('\n');
}
