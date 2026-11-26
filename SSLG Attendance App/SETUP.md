# SSLG Office Attendance Setup

## What this app stores

The app stores names, random browser tokens, one permanent IN/OUT QR pair, and timestamps. It does not store phone numbers. The same QR codes are reused every day; each scan receives the current Asia/Manila date and time from the server.

## Public admin warning

The admin page has no password; anyone with its direct URL can view names and timestamps.

## 1. Create the Sheet

1. Create a blank Google Spreadsheet named `SSLG Office Attendance`.
2. Copy its ID from the URL between `/d/` and `/edit`.

## 2. Create the Apps Script project

1. Open the new Spreadsheet.
2. Select `Extensions → Apps Script`.

## 3. Add files

Use the included single-file deployment bundle:

1. Open `deploy/SSLG Attendance.gs`, copy its entire contents, and paste them into the Apps Script project's existing `Code.gs` file. Save. No other `.gs` or `.html` files are needed.
2. Open `Project Settings → Show appsscript.json` and replace the generated manifest with `deploy/appsscript.json`.
3. Open `deploy/START HERE.txt` for the same instructions in a standalone checklist.

The split source files (`Core.gs`, `Index.html`, `Styles.html`, `Client.html`, and `QRCodeLib.html`) remain available for development. After changing them, run `npm run build:deployment` to refresh the single-file bundle.

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
2. Open that admin URL and click **Show permanent QR pair**. The first request creates the pair; later requests return the same codes and creation time.

## 7. Test

1. On a phone, scan the IN code.
2. Register a name and confirm.
3. Scan the OUT code on the same phone and confirm the remembered name.
4. Reopen the same IN and OUT links and confirm further valid scans are recorded. Try an unknown code and a wrong-mode code; confirm neither creates a row.
5. Confirm the real office list and exported CSV show the test records under the server's Manila date.
6. Inspect the real `QR Codes`, `People`, and `Attendance` tabs and document their columns against the app headers. `QR Codes` must contain exactly one permanent pair.
7. On a later day, reuse the exact same printed QR links and confirm they still work and create rows under that later Manila date.

A live deployment is not verified until the owner completes the scan test in this guide.

## 8. Daily use

1. Show the permanent pair once and print the cards.
2. Post the same IN and OUT cards every day.
3. Do not regenerate or replace the codes; the app provides no replacement option.

## 9. CSV

1. On the office page, choose a date.
2. Click `Export CSV`.

## 10. Troubleshooting

- `SPREADSHEET_NOT_CONFIGURED`: In Apps Script `Project Settings → Script Properties`, add `SPREADSHEET_ID` with the copied Spreadsheet ID, save it, and deploy a new version of the web app.
- `NAME_INVALID`: The name starts with a spreadsheet formula character. Ask the student to enter a name that does not start with `=`, `+`, `-`, or `@`. If a remembered name was manually edited in the `People` tab, correct that stored name before the next scan.
- `DEVICE_TOKEN_INVALID`: The browser's saved attendance token is unsafe or damaged. Clear this site's stored data in the browser, reopen the QR link, and register the name again. Do not edit the token manually.
- Invalid or wrong-mode codes: The permanent pair does not expire. Check that the phone scanned the posted IN or OUT card and that the link contains the correct mode and full code. The app cannot replace a lost code; if the permanent pair is lost, contact the app maintainer rather than generating a new pair in the office page.
- Sheet permission errors: Confirm that the deploying user owns or can edit `SSLG Office Attendance`, that `SPREADSHEET_ID` identifies that Sheet, and that the requested Google permissions were authorized. After fixing access or configuration, deploy a new version.
- Browser local-storage loss: The remembered name depends on browser site storage. If storage is blocked or cleared, the phone may ask for the name again. Use the same browser and allow site storage to retain it.
