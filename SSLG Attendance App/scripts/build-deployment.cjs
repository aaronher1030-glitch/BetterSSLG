const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const deploy = path.join(root, 'deploy');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const html = read('Index.html')
  .replace(/<\?!= include\('Styles'\); \?>/, () => read('Styles.html'))
  .replace(/<\?!= include\('QRCodeLib'\); \?>/, () => read('QRCodeLib.html'))
  .replace(/<\?!= include\('Client'\); \?>/, () => read('Client.html'))
  .replace(/<\?!= requestParamsScript_\(event\); \?>/, () => '<script>window.SSLG_SERVER_PARAMS = SSLG_SERVER_PARAMS_JSON;</script>');
const backend = read('Code.gs').replace(/function doGet\(event\) \{[\s\S]*$/, '');
const bundle = `${read('Core.gs')}\n${backend}\nconst SSLG_DEPLOYMENT_HTML = ${JSON.stringify(html)};\n\nfunction doGet(event) {\n  const html = SSLG_DEPLOYMENT_HTML.replace(\n    '<script>window.SSLG_SERVER_PARAMS = SSLG_SERVER_PARAMS_JSON;</script>',\n    () => requestParamsScript_(event)\n  );\n  return HtmlService.createHtmlOutput(html);\n}\n`;

fs.mkdirSync(deploy, { recursive: true });
fs.writeFileSync(path.join(deploy, 'SSLG Attendance.gs'), bundle);
fs.copyFileSync(path.join(root, 'appsscript.json'), path.join(deploy, 'appsscript.json'));
fs.writeFileSync(path.join(deploy, 'START HERE.txt'), `SSLG OFFICE ATTENDANCE — GOOGLE APPS SCRIPT DEPLOYMENT

The admin page is public and has no password. Anyone with its direct URL can view names and scan timestamps.

1. Create a blank Google Spreadsheet named: SSLG Office Attendance
2. Copy its ID from the URL between /d/ and /edit.
3. In that Spreadsheet, choose Extensions > Apps Script.
4. In the Apps Script editor, open Code.gs, select all, and paste the entire contents of:
   SSLG Attendance.gs
   Save. You do not need to create any other .gs or .html files.
5. Choose Project Settings > Show appsscript.json. Replace its contents with the included:
   appsscript.json
6. Choose Project Settings > Script Properties. Add:
   Name: SPREADSHEET_ID
   Value: the Spreadsheet ID copied in step 2
   Save.
7. Choose Deploy > New deployment > Web app.
   Execute as: Me
   Who has access: Anyone
   Deploy and authorize the requested Google permissions.
8. Copy the web app URL ending in /exec.
9. Append ?page=admin to that URL and open it.
10. Click Show permanent QR pair. Print and post the same IN and OUT cards every day.
11. Test on a phone: scan IN, register a name, scan OUT, and confirm the remembered name.
12. Check the Google Sheet's QR Codes, People, and Attendance tabs. QR Codes must have exactly one permanent pair.

Do not regenerate or replace the codes. The app provides no replacement option.
For detailed testing and troubleshooting, see SETUP.md in the full project.
`);

console.log(`Built ${path.join(deploy, 'SSLG Attendance.gs')} (${bundle.length} characters).`);
