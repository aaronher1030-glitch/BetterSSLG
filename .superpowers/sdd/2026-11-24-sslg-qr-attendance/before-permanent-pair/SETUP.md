# SSLG Office Attendance Setup

## What this app stores

The app stores names, random browser tokens, daily QR tokens, and timestamps. It does not store phone numbers.

## Public admin warning

The admin page has no password; anyone with its direct URL can view names and timestamps.

## 1. Create the Sheet

1. Create a blank Google Spreadsheet named `SSLG Office Attendance`.
2. Copy its ID from the URL between `/d/` and `/edit`.

## 2. Create the Apps Script project

1. Open the new Spreadsheet.
2. Select `Extensions → Apps Script`.

## 3. Add files

1. In the Apps Script project, create `Code.gs`, `Core.gs`, `Index.html`, `Styles.html`, `Client.html`, and `QRCodeLib.html`.
2. Paste the contents of each matching project file into its corresponding Apps Script file.
3. Open `Project Settings → Show appsscript.json` and replace the generated `appsscript.json` with the manifest from this project.

## 4. Configure the Sheet

1. In Apps Script, open `Project Settings → Script Properties`.
2. Add a property named `SPREADSHEET_ID` and set its value to the ID copied from the Spreadsheet URL.
3. Click `Save`.

## 5. Deploy

1. Click `Deploy → New deployment → Web app`.
2. Set **Execute as** to **Me** (the deploying user).
3. Set **Who has access** to **Anyone**.
4. Click `Deploy` and authorize the requested Google permissions.
5. Copy the deployment's web app URL for use by the office.

## 6. Open the office page

1. Append `?page=admin` to the deployed `/exec` URL.
2. Open that admin URL and generate a QR pair for today.

## 7. Test

1. On a phone, scan the IN code.
2. Register a name and confirm.
3. Scan the OUT code on the same phone and confirm the remembered name.
4. Regenerate the codes and confirm the earlier codes are rejected without writes.
5. Confirm the real office list and exported CSV show the test records.
6. Inspect the real `Daily Codes`, `People`, and `Attendance` tabs and document their columns against the app headers.

A live deployment is not verified until the owner completes the scan test in this guide.

## 8. Daily use

1. Generate a fresh pair each morning.
2. Print the cards.
3. Do not reuse yesterday’s codes.

## 9. CSV

1. On the office page, choose a date.
2. Click `Export CSV`.

## 10. Troubleshooting

- `SPREADSHEET_NOT_CONFIGURED`: In Apps Script `Project Settings → Script Properties`, add `SPREADSHEET_ID` with the copied Spreadsheet ID, save it, and deploy a new version of the web app.
- `NAME_INVALID`: The name starts with a spreadsheet formula character. Ask the student to enter a name that does not start with `=`, `+`, `-`, or `@`. If a remembered name was manually edited in the `People` tab, correct that stored name before the next scan.
- `DEVICE_TOKEN_INVALID`: The browser's saved attendance token is unsafe or damaged. Clear this site's stored data in the browser, reopen the QR link, and register the name again. Do not edit the token manually.
- Expired or invalid codes: Use today's freshly generated pair. Codes from a different date expire at the end of that Manila calendar day; generating a new pair replaces an older pair. If a scan says the code is invalid or the action does not match, ask the office to generate and print a new pair.
- Sheet permission errors: Confirm that the deploying user owns or can edit `SSLG Office Attendance`, that `SPREADSHEET_ID` identifies that Sheet, and that the requested Google permissions were authorized. After fixing access or configuration, deploy a new version.
- Browser local-storage loss: The remembered name depends on browser site storage. If storage is blocked or cleared, the phone may ask for the name again. Use the same browser and allow site storage to retain it.
