function getConfig_() {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
  if (!spreadsheetId) throw new Error('SPREADSHEET_NOT_CONFIGURED');
  return { spreadsheetId };
}

function openSpreadsheet_() {
  return SpreadsheetApp.openById(getConfig_().spreadsheetId);
}

function ensureSheet_(spreadsheet, name, headers) {
  let sheet = spreadsheet.getSheetByName(name);
  if (!sheet) sheet = spreadsheet.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
  } else {
    const current = sheet.getRange(1, 1, 1, headers.length).getValues()[0] || [];
    const normalized = headers.map((header, index) => current[index] == null ? '' : String(current[index]));
    if (headers.some((header, index) => normalized[index] !== header)) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    }
  }
  return sheet;
}

function ensureSchema_() {
  const spreadsheet = openSpreadsheet_();
  ensureSheet_(spreadsheet, 'QR Codes', QR_CODE_HEADERS);
  ensureSheet_(spreadsheet, 'People', PEOPLE_HEADERS);
  ensureSheet_(spreadsheet, 'Attendance', ATTENDANCE_HEADERS);
}

function sheetRows_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  return values.map(row => Object.fromEntries(headers.map((header, index) => [header, row[index]])));
}

function getPermanentCodeRecord_() {
  ensureSchema_();
  const rows = sheetRows_(openSpreadsheet_().getSheetByName('QR Codes'));
  return rows[0] || null;
}

function getWebAppUrl_() {
  return ScriptApp.getService().getUrl();
}

function generatePermanentCodes_() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) throw new Error('SHEET_BUSY');
  try {
    ensureSchema_();
    const spreadsheet = openSpreadsheet_();
    const sheet = spreadsheet.getSheetByName('QR Codes');
    const rows = sheetRows_(sheet);
    const record = rows[0] || createPermanentCodeRecord_(new Date(), () => Utilities.getUuid());
    if (!rows.length) sheet.appendRow(QR_CODE_HEADERS.map(header => record[header]));
    const baseUrl = getWebAppUrl_();
    return {
      ...record,
      in_url: `${baseUrl}?page=scan&mode=IN&code=${encodeURIComponent(record.in_code)}`,
      out_url: `${baseUrl}?page=scan&mode=OUT&code=${encodeURIComponent(record.out_code)}`
    };
  } finally {
    lock.releaseLock();
  }
}

function findPersonByToken_(deviceToken) {
  ensureSchema_();
  const rows = sheetRows_(openSpreadsheet_().getSheetByName('People'));
  return rows.find(row => row.device_token === deviceToken) || null;
}

function upsertPerson_(deviceToken, name, now) {
  const spreadsheet = openSpreadsheet_();
  const sheet = spreadsheet.getSheetByName('People');
  const rows = sheetRows_(sheet);
  const existingIndex = rows.findIndex(row => row.device_token === deviceToken);
  if (existingIndex >= 0) {
    const existing = rows[existingIndex];
    sheet.getRange(existingIndex + 2, 1, 1, PEOPLE_HEADERS.length).setValues([[
      deviceToken,
      name,
      existing.first_seen_at,
      manilaTimestamp_(now)
    ]]);
  } else {
    sheet.appendRow([deviceToken, name, manilaTimestamp_(now), manilaTimestamp_(now)]);
  }
}

function getScanStatus_(params) {
  const record = getPermanentCodeRecord_();
  const validation = validateScan_(params, record, new Date());
  if (!validation.ok) return validation;
  const deviceToken = String(params.device_token || '');
  const tokenError = deviceTokenError_(deviceToken, false);
  if (tokenError) return { ok: false, error: tokenError };
  const person = findPersonByToken_(deviceToken);
  return {
    ok: true,
    date: validation.date,
    mode: validation.mode,
    name: person ? person.name : null,
    device_token: deviceToken,
    qr_created_at: validation.qr_created_at
  };
}

function recordScan_(params) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) throw new Error('SHEET_BUSY');
  try {
    const now = new Date();
    const record = getPermanentCodeRecord_();
    const validation = validateScan_(params, record, now);
    if (!validation.ok) return validation;
    const deviceToken = String(params.device_token || '');
    const tokenError = deviceTokenError_(deviceToken, true);
    if (tokenError) return { ok: false, error: tokenError };
    const existing = findPersonByToken_(deviceToken);
    const name = normalizeName_(existing ? existing.name : params.name);
    upsertPerson_(deviceToken, name, now);
    const event = {
      event_id: Utilities.getUuid(),
      date: validation.date,
      scanned_at: manilaTimestamp_(now),
      mode: validation.mode,
      name,
      device_token: deviceToken,
      qr_created_at: validation.qr_created_at
    };
    openSpreadsheet_().getSheetByName('Attendance').appendRow(
      ATTENDANCE_HEADERS.map(header => event[header])
    );
    return { ok: true, event };
  } finally {
    lock.releaseLock();
  }
}

function filteredAttendance_(dateKey, query) {
  ensureSchema_();
  const rows = sheetRows_(openSpreadsheet_().getSheetByName('Attendance'))
    .map(row => ({ ...row, date: sheetDateKey_(row.date) }));
  const normalizedQuery = String(query || '').trim().toLowerCase();
  return rows
    .filter(row => row.date === dateKey)
    .filter(row => !normalizedQuery || String(row.name).toLowerCase().includes(normalizedQuery))
    .sort((a, b) => String(b.scanned_at).localeCompare(String(a.scanned_at)));
}

function listAttendance_(dateKey, query) {
  const rows = filteredAttendance_(dateKey, query);
  const allRows = filteredAttendance_(dateKey, '');
  return {
    ok: true,
    rows,
    totals: {
      in: allRows.filter(row => row.mode === 'IN').length,
      out: allRows.filter(row => row.mode === 'OUT').length,
      people: new Set(allRows.map(row => row.device_token)).size,
      scans: allRows.length
    }
  };
}

function exportAttendanceCsv_(dateKey) {
  const rows = filteredAttendance_(dateKey, '');
  return {
    ok: true,
    csv: toCsv_(ATTENDANCE_HEADERS, rows.map(row => ATTENDANCE_HEADERS.map(header => row[header]))),
    filename: `SSLG-attendance-${dateKey}.csv`
  };
}

function jsonResponse_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(ContentService.MimeType.JSON);
}

function errorCode_(error) {
  return error && error.message ? error.message : 'REQUEST_FAILED';
}

function doPost(event) {
  try {
    const body = JSON.parse(event.postData.contents);
    const payload = body.payload || {};
    let result;
    switch (body.action) {
      case 'scan.status':
        result = getScanStatus_(payload);
        break;
      case 'scan.record':
        result = recordScan_(payload);
        break;
      case 'admin.generate':
        result = { ok: true, record: generatePermanentCodes_() };
        break;
      case 'admin.list':
        result = listAttendance_(payload.date, payload.query);
        break;
      case 'admin.export':
        result = exportAttendanceCsv_(payload.date);
        break;
      default:
        result = { ok: false, error: 'UNKNOWN_ACTION' };
    }
    return jsonResponse_(result);
  } catch (error) {
    return jsonResponse_({ ok: false, error: errorCode_(error) });
  }
}

function scanStatus(payload) {
  return getScanStatus_(payload || {});
}

function scanRecord(payload) {
  return recordScan_(payload || {});
}

function adminGenerate(payload) {
  return { ok: true, record: generatePermanentCodes_() };
}

function adminList(payload) {
  return listAttendance_((payload || {}).date, (payload || {}).query);
}

function adminExport(payload) {
  return exportAttendanceCsv_((payload || {}).date);
}

function requestParamsScript_(event) {
  const source = event && event.parameter ? event.parameter : {};
  const params = {};
  for (const key of ['page', 'mode', 'code']) {
    if (typeof source[key] === 'string') params[key] = source[key];
  }
  const json = JSON.stringify(params).replace(/[<>&\u2028\u2029]/g, character => ({
    '<': '\\u003c', '>': '\\u003e', '&': '\\u0026', '\u2028': '\\u2028', '\u2029': '\\u2029'
  })[character]);
  return `<script>window.SSLG_SERVER_PARAMS = ${json};</script>`;
}

function doGet(event) {
  return HtmlService.createTemplateFromFile('Index').evaluate();
}
