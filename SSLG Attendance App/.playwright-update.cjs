async (page) => {
  const fs = require('node:fs');
  const text = fs.readFileSync('C:/Users/Ma Christine/Downloads/SSLG MEMOS/SSLG Attendance App/deploy/SSLG Attendance.gs', 'utf8');
  return { length: text.length, marker: text.includes('requestParamsScript_') };
}
