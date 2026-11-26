# BSANHS SSLG Site Update (November 2026) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the public BSANHS SSLG Google Site up to date with every completed SSLG activity that has a completion report or photo album in the vault and the public Drive collection, and add an auto-updating photo gallery fed by the PIO's public Drive albums.

**Architecture:** Google Sites remains the shell. The site has no write API, so this plan edits the existing draft through the Sites editor, then publishes once. Photos are never copied into the site: each album is embedded with Drive's public `embeddedfolderview` endpoint, which re-reads the album on every visit, so new photos appear without a site edit. No backend code or credentials are involved.

**Tech Stack:** Google Sites editor (signed-in editor account), public Google Drive endpoints (`lh3.googleusercontent.com`, `drive.google.com/thumbnail`, `drive.google.com/embeddedfolderview`), Python 3 + Pillow for local cover preparation, `urllib` for unauthenticated post-publish verification, and the `browser-use` MCP for editor automation.

**Spec:** No separate design doc. The approved scope is recorded in "Scope and decisions" below; this plan is the specification for the update.

## Reference data

Use these exact IDs and URLs. Never open the Drive website or the Drive picker for these folders: the signed-in account is not the folder owner. All folders below are public ("anyone with the link"), so the direct URLs work without sign-in.

**Site**

| Item | Value |
| --- | --- |
| Site ID | `1d9AXxMQ3JdQgHpWq36NrwywYisfLW19y` |
| Editor | `https://sites.google.com/d/1d9AXxMQ3JdQgHpWq36NrwywYisfLW19y/edit` |
| Published site | `https://sites.google.com/view/bsanhs-site/` |
| Home page ID | `1VPs9L0Roqf74xuZkVmvboV9RL94mX5bd` |
| Pages | `/home`, `/finance`, `/accomplishments`, `/transparency`, `/about-us`, `/feedback` |

**Drive**

| Item | ID |
| --- | --- |
| Records root | `1XU9s-pHPCk_zJQo7LSOjcmtGeIiI9JeM` |
| Photo root (PIO drop) | `1QbMxIfTuL9-qJ3T9YgfuYyErHexqxBiQ` |
| Photo S.Y. 2026-2027 | `1uJN4P33nAximCW7Brh_HgUVmpyZPf28A` |
| Photo TERM 1 | `1kkiVLZp4s033QhW3eIiviu9lTWgX9P5b` |
| Photo TERM 2 (empty) | `1Mtmvl9hy7D20sx6wCuEvx72UW-m6r3L8` |
| Photo TERM 3 (empty) | `1FmahBcX1E6Phziz14kuOknU9iPXizS_l` |
| Album — Brigada Eskwela | `1p-60nKJtTiACOF1Kkj8OLCuEFlnhR1sn` |
| Album — Club Fair (empty) | `1S6yMnWlYO_ilgiwc5akv32WAOYmI3rtf` |
| Album — Grade 7 Election | `1y2tKu7-5uoxBK-jQ2dN0sEIqCj2tL8av` |
| Album — Induction (empty) | `1iPxMcxI61C0pIZDc_2raj4IYFzaYXLL_` |
| Album — Earthquake Drill | `1UT4M9b8TrctZ-d-tGjAEPbLADbUo_ik8` |
| Album — LGCC Clean-Up | `1_0DykrJF1DVEzwo19m9mbgAp2HRi85ix` |
| Album — Teachers' Day | `1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz` |
| ACR folder | `1_44iCUzUJAaBi0cc0a7DcpauUPpRJIxj` |
| ACR-001 Brigada | `16KFJZmhSiTPeEV0JIO8ttj894RZBbuQQ` |
| ACR-002 Grade 7 Election | `168M9PVEHlju8RL0DRNUwljBU9BPS0pGa` |
| ACR-003 Club Fair | `1ZRyWYuL4w1oZcgo0V5HU-vr0JMq6g-4Y` |
| ACR-004 Election of Registered Clubs | `11NW0ZtYcFbPeRcNgpFwT26_IJUln8n1S` |
| ACR-005 GPOA | `1pdEWqxhVOBNwM71FUpsyVNdwUjCbezWJ` |
| ACR-006 Induction | `1omiyOdHtxgngsb7WMcpNGTaZsaMBgrYE` |
| Finance folder | `1NhgG1fkfxch70E3hzb5YhTgCK0PWKcdV` |
| Finance — Grade 7 report | `1r8_e9PQ7l29iDLbQrkMyjasVdGZvCc3X` |
| Finance — Induction report | `1AKXTRjZx7_jPLUi5GWe6QcYuREKsSP0d` |
| AP-002 Project ECOLEAD | `10EnbVjEL94AXwWm4IeW5QRCi29Z9tJy5` |
| AP-006 Teachers' Day | `1KiYs31znp_3EKYMNV0hxJCQvcK90mtws` |

**Cover sources** (download only; never paste these URLs into the site)

| Card | Source |
| --- | --- |
| Teachers' Day | `https://lh3.googleusercontent.com/d/1iNZf_8gBnZeVMaaIy6jqc3RSOdBikzUD=w1200` |
| LGCC Clean-Up | `https://lh3.googleusercontent.com/d/1Qe81jPahSrMs4gethkShO2s_diAvLPIb=w1200` |
| Earthquake Drill | `https://lh3.googleusercontent.com/d/18RA3CxRMNmM-nXw9JW5hdM9jh4tzYPoo=w1200` |
| Brigada Eskwela | `https://lh3.googleusercontent.com/d/1-Q_HRJ79wNIxNp9-qx4CcQJOI5XWD36w=w1200` |
| GPOA document page | `https://drive.google.com/thumbnail?id=1pdEWqxhVOBNwM71FUpsyVNdwUjCbezWJ&sz=w1600` |
| Election of Registered Clubs document page | `https://drive.google.com/thumbnail?id=11NW0ZtYcFbPeRcNgpFwT26_IJUln8n1S&sz=w1600` |

## Scope and decisions

Approved changes:

1. **Home → Latest** becomes World Teachers' Day 2026, replacing the Induction card in that slot. Induction remains a published accomplishment card.
2. **Accomplishments** gains the six documented activities missing from the site: Brigada Eskwela, Crafting of the GPOA, Election of Registered School Clubs and Organizations, National Simultaneous Earthquake Drill, LGCC Clean-Up Drive (Project ECOLEAD), and World Teachers' Day.
3. **Finance** replaces the single "SSLG Financial Report (July 26, 2026)" entry with the two reports that actually exist in the public folder.
4. **Photos** is a new page with five live album embeds. Adding photos to an album updates the page with no site edit. A new album needs one two-minute page edit.
5. Everything reuses the site's existing sections, card anatomy (image, centred heading, one-sentence description), fonts, and colours.
6. No automation code, credentials, or backend files are placed in Drive. The site reads public folders directly.

Out of scope for this plan: an Apps Script gallery web app (deferred until the native embeds are proven in use; see "Phase 2"), and any page other than Home, Accomplishments, Finance, and the new Photos page.

## Open items to confirm with the adviser

These are flagged, not silently resolved. Each has a default already used by this plan; change the default only on instruction.

| # | Item | Evidence | Default used here |
| --- | --- | --- | --- |
| 1 | Teachers' Day date | Revised proposal copies say 2 October 2026; `AP_SSLG_2026_006 (3).docx` says 5 October 2026 | Cards and page copy display no date, so nothing false is published. Confirm for the record. |
| 2 | Teachers' Day / Foundation Day pairing | Album cover reads "Teachers' Day and 78th Foundation Day Celebration" | Card title stays "World Teachers' Day 2026" as approved; the uploaded cover itself shows the pairing. Confirm whether the title should name both. |
| 3 | Two earthquake drills | EL-005 documents a 24 June 2026 drill; the photo album is the September National Simultaneous Earthquake Drill | One card for the September NSED (the one with photos). Confirm whether the June drill also needs a card. |
| 4 | July 26 finance line | The public Finance folder contains only the Grade 7 and Induction reports; no July 26 file exists | Replace with the two named reports. If a July 26 report exists elsewhere, add it as a third entry instead of removing the date. |
| 5 | Club Fair naming | ACR-003 is the Club Fair; the site calls it "Club and Organizations Membership Drive" | Keep the published name; do not rename without approval. |
| 6 | Empty albums | Club Fair and Induction albums are empty | Not embedded on Photos yet; listed in the runbook. |
| 7 | Grade 7 album format | Album contains `.HEIC` files | Embed and verify thumbnails render; if blank, convert to JPEG and re-upload (runbook step). |

## Global constraints

- Work only from public links. Never use the Drive website, the Drive picker, or a Drive MCP connection: the signed-in account is not the folder owner.
- Never type, store, or request Google credentials. If a sign-in screen appears, stop and hand it to the user.
- Do not publish until every edit task passes its Preview check. Publishing is the single final step.
- Do not modify, move, rename, or upload anything in the Drive folders. This update is read-only on Drive.
- Do not invent dates, names, approvals, or outcomes. Use the exact copy in this plan; the cards display no dates.
- Keep the site's visual language: same page header, section spacing, card image size, centred heading, and one-sentence description.
- Upload images from local files. Do not hotlink `lh3` URLs into Sites: Sites re-hosts uploaded images, which keeps the page independent of Drive permissions.
- Keep the existing `Prepared By: Samantha C. De Venecia ( SSLG Treasurer)` line and the existing nav order, inserting Photos directly after Accomplishments.
- No comments or documentation are added to Drive. The runbook lives in the vault.
- This workspace is not a git repository. Replace commit steps with named verification checkpoints.

## File structure

- `docs/site-assets/2026-11/`: six local cover images used for upload; kept for future re-edits.
- `tools/verify_site_update.py`: unauthenticated post-publish checker for the strings and album IDs this plan adds.
- `docs/sslg-site-photo-runbook.md`: PIO instructions for adding photos; created in Task 8.
- Google Sites: Home draft, Accomplishments draft, Finance draft, new Photos page.

---

### Task 1: Stage and verify the six cover images

**Files:**
- Create: `docs/site-assets/2026-11/world-teachers-day-2026.jpg`
- Create: `docs/site-assets/2026-11/lgcc-clean-up-2026.jpg`
- Create: `docs/site-assets/2026-11/earthquake-drill-2026.jpg`
- Create: `docs/site-assets/2026-11/brigada-eskwela-2026.jpg`
- Create: `docs/site-assets/2026-11/gpoa-2026.jpg`
- Create: `docs/site-assets/2026-11/election-registered-clubs-2026.jpg`
- Create (intermediate, delete after): `docs/site-assets/2026-11/gpoa-page.png`, `docs/site-assets/2026-11/election-clubs-page.png`

**Interfaces:**
- Consumes: the six public cover sources in "Reference data".
- Produces: six 1080×1080 JPEGs whose filenames are referenced verbatim by Tasks 3 and 4.

- [ ] **Step 1: Create the staging folder and download the four photo covers**

Run from the vault root:

```bash
mkdir -p "docs/site-assets/2026-11"
curl -sL "https://lh3.googleusercontent.com/d/1iNZf_8gBnZeVMaaIy6jqc3RSOdBikzUD=w1200" -o "docs/site-assets/2026-11/world-teachers-day-2026.jpg"
curl -sL "https://lh3.googleusercontent.com/d/1Qe81jPahSrMs4gethkShO2s_diAvLPIb=w1200" -o "docs/site-assets/2026-11/lgcc-clean-up-2026.jpg"
curl -sL "https://lh3.googleusercontent.com/d/18RA3CxRMNmM-nXw9JW5hdM9jh4tzYPoo=w1200" -o "docs/site-assets/2026-11/earthquake-drill-2026.jpg"
curl -sL "https://lh3.googleusercontent.com/d/1-Q_HRJ79wNIxNp9-qx4CcQJOI5XWD36w=w1200" -o "docs/site-assets/2026-11/brigada-eskwela-2026.jpg"
```

Expected: four files, each 60–160 KB.

- [ ] **Step 2: Download the two document page images**

```bash
curl -sL "https://drive.google.com/thumbnail?id=1pdEWqxhVOBNwM71FUpsyVNdwUjCbezWJ&sz=w1600" -o "docs/site-assets/2026-11/gpoa-page.png"
curl -sL "https://drive.google.com/thumbnail?id=11NW0ZtYcFbPeRcNgpFwT26_IJUln8n1S&sz=w1600" -o "docs/site-assets/2026-11/election-clubs-page.png"
```

Expected: two PNGs, each about 240–260 KB and 800×1035.

- [ ] **Step 3: Compose the document covers on a neutral square**

Run:

```bash
python -X utf8 - <<'PY'
from pathlib import Path
from PIL import Image

stage = Path("docs/site-assets/2026-11")
pairs = [
    ("gpoa-page.png", "gpoa-2026.jpg"),
    ("election-clubs-page.png", "election-registered-clubs-2026.jpg"),
]
for src, dst in pairs:
    page = Image.open(stage / src).convert("RGB")
    canvas = Image.new("RGB", (1080, 1080), (243, 244, 246))
    scale = min(1000 / page.width, 1000 / page.height)
    size = (round(page.width * scale), round(page.height * scale))
    page = page.resize(size, Image.LANCZOS)
    canvas.paste(page, ((1080 - size[0]) // 2, (1080 - size[1]) // 2))
    canvas.save(stage / dst, quality=90)
print("composed")
PY
```

Expected: `composed`.

- [ ] **Step 4: Normalise the Brigada landscape photo to a square**

Run:

```bash
python -X utf8 - <<'PY'
from pathlib import Path
from PIL import Image

p = Path("docs/site-assets/2026-11/brigada-eskwela-2026.jpg")
im = Image.open(p).convert("RGB")
w, h = im.size
s = min(w, h)
im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
im = im.resize((1080, 1080), Image.LANCZOS)
im.save(p, quality=90)
print("cropped")
PY
```

Expected: `cropped`.

- [ ] **Step 5: Delete the two intermediate PNGs and verify the six covers**

```bash
rm "docs/site-assets/2026-11/gpoa-page.png" "docs/site-assets/2026-11/election-clubs-page.png"
python -X utf8 - <<'PY'
from pathlib import Path
from PIL import Image

files = sorted(Path("docs/site-assets/2026-11").glob("*.jpg"))
assert len(files) == 6, files
for f in files:
    size = Image.open(f).size
    assert size == (1080, 1080), (f.name, size)
    print(f.name, size)
PY
```

Expected: exactly six lines, all `(1080, 1080)`.

---

### Task 2: Confirm the unpublished draft is safe to build on

**Files:**
- Modify: Google Sites draft (no content change in this task)

**Interfaces:**
- Consumes: the editor URL and Home page ID from "Reference data".
- Produces: a confirmed starting point; Task 3 overwrites the only card known to have been touched.

- [ ] **Step 1: Open the editor and the Home page**

Open `https://sites.google.com/d/1d9AXxMQ3JdQgHpWq36NrwywYisfLW19y/p/1VPs9L0Roqf74xuZkVmvboV9RL94mX5bd/edit`.

Expected: the editor loads with the site name `BSANHS` and a `Publish` button.

- [ ] **Step 2: Preview the draft and compare it with the published Home page**

Click `Preview`; scroll through Home and check the hero, the `Latest` section, `About Us`, and the three buttons.

Expected: the `Latest` card still reads "Onto the Next Leaders Induction Ceremony" with the induction group photo; no other section differs from `https://sites.google.com/view/bsanhs-site/home`.

- [ ] **Step 3: Exit preview without publishing**

Click the back arrow labelled `Close preview and edit`.

Expected: the editor returns; `Publish` has not been clicked. If the `Latest` card image or link looks wrong, continue anyway: Task 3 replaces its title, description, image, and link.

---

### Task 3: Replace the Home "Latest" card with World Teachers' Day 2026

**Files:**
- Modify: Google Sites Home draft, `Latest` card

**Interfaces:**
- Consumes: `docs/site-assets/2026-11/world-teachers-day-2026.jpg`; the Teachers' Day album ID `1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz`.
- Produces: a Home page whose only change is the `Latest` card, ready for Task 7.

- [ ] **Step 1: Edit the card title**

Click the title text `Onto the Next Leaders Induction Ceremony` inside the `Latest` section. Press `Ctrl+A`, then paste exactly:

```text
World Teachers' Day 2026
```

- [ ] **Step 2: Edit the card description**

Click the description below the title. Press `Ctrl+A`, then paste exactly:

```text
To honor the dedication and service of teachers, this celebration recognized their contributions to learners and the school community through a programme led by the SSLG and LGCC.
```

- [ ] **Step 3: Replace the image by upload**

Select the card image. In the image toolbar choose `More editing options` → `Replace image`. In the dialog select the `Upload` tab (not `Select`), choose `docs/site-assets/2026-11/world-teachers-day-2026.jpg`, and insert it.

Expected: the card shows the pink "TEACHERS' DAY and 78th FOUNDATION DAY Celebration" cover.

- [ ] **Step 4: Point the image at the public album**

With the new image selected, click the link icon (`Insert link` or `Edit link`). Replace any existing URL with:

```text
https://drive.google.com/drive/folders/1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz
```

Click `Apply`. Do not use the Drive picker.

- [ ] **Step 5: Preview the Home page**

Click `Preview`; check that the card reads "World Teachers' Day 2026", uses the new cover, links to the album, and keeps the same size and position as the old card. Exit preview.

Expected: only the `Latest` card changed; the Induction card is untouched elsewhere.

---

### Task 4: Add the six missing Accomplishments cards

**Files:**
- Modify: Google Sites Accomplishments draft, card rows

**Interfaces:**
- Consumes: the six covers from Task 1; the six titles and descriptions below.
- Produces: nine cards in three rows of three, in this order:

| Row | Column 1 | Column 2 | Column 3 |
| --- | --- | --- | --- |
| 1 (new, top) | World Teachers' Day 2026 | LGCC Clean-Up Drive – Project ECOLEAD | National Simultaneous Earthquake Drill 2026 |
| 2 (existing, unchanged) | Onto the Next Leaders Induction Ceremony | Grade 7 Representatives Election for the S.Y 2026-2027 | Club and Organizations Membership Drive |
| 3 (new, bottom) | Crafting of the SSLG General Plan of Action | Election of Registered School Clubs and Organizations | Brigada Eskwela 2026 |

Rows are grouped, not a strict timeline: the site's cards display no dates. The existing row is preserved untouched so its images and links cannot be damaged.

- [ ] **Step 1: Open the Accomplishments page**

In the editor, open the `Accomplishments` page from the Pages panel. Scroll to the row containing the three existing cards.

Expected: one section with three equal columns, each containing an image, a centred heading, and a description.

- [ ] **Step 2: Duplicate the card row twice**

Hover the existing card row until the section toolbar appears. Click the `Duplicate section` icon (two stacked squares). Repeat once.

Expected: two identical copies appear immediately below the original. The page now has three identical rows.

- [ ] **Step 3: Move one copy above the original**

Drag the first copy (the one directly below the original) by its section handle until it sits above the original row. Leave the second copy below the original.

Expected: top = copy, middle = original, bottom = copy.

- [ ] **Step 4: Fill the top row, column 1 — World Teachers' Day 2026**

Set the heading to:

```text
World Teachers' Day 2026
```

Set the description to:

```text
To honor the dedication and service of teachers, this celebration recognized their contributions to learners and the school community through a programme led by the SSLG and LGCC.
```

Replace the image using `More editing options` → `Replace image` → `Upload` → `docs/site-assets/2026-11/world-teachers-day-2026.jpg`.

- [ ] **Step 5: Fill the top row, column 2 — LGCC Clean-Up Drive**

Set the heading to:

```text
LGCC Clean-Up Drive – Project ECOLEAD
```

Set the description to:

```text
To promote environmental stewardship and maintain a clean learning environment, the LGCC and SSLG led a school-wide clean-up drive under Project ECOLEAD.
```

Replace the image with `docs/site-assets/2026-11/lgcc-clean-up-2026.jpg`.

- [ ] **Step 6: Fill the top row, column 3 — National Simultaneous Earthquake Drill 2026**

Set the heading to:

```text
National Simultaneous Earthquake Drill 2026
```

Set the description to:

```text
To strengthen disaster preparedness and safety awareness, SSLG officers and Red Cross Youth members joined the 2026 National Simultaneous Earthquake Drill.
```

Replace the image with `docs/site-assets/2026-11/earthquake-drill-2026.jpg`.

- [ ] **Step 7: Fill the bottom row, column 1 — Crafting of the GPOA**

Set the heading to:

```text
Crafting of the SSLG General Plan of Action
```

Set the description to:

```text
To set the direction of student-led programmes for the school year, the SSLG crafted its General Plan of Action with the guidance of the LGCC and advisers.
```

Replace the image with `docs/site-assets/2026-11/gpoa-2026.jpg`.

- [ ] **Step 8: Fill the bottom row, column 2 — Election of Registered Clubs**

Set the heading to:

```text
Election of Registered School Clubs and Organizations
```

Set the description to:

```text
To promote democratic participation and student leadership, this activity elected the officers of registered school clubs and organizations.
```

Replace the image with `docs/site-assets/2026-11/election-registered-clubs-2026.jpg`.

- [ ] **Step 9: Fill the bottom row, column 3 — Brigada Eskwela 2026**

Set the heading to:

```text
Brigada Eskwela 2026
```

Set the description to:

```text
To prepare the school facilities for the opening of classes, the SSLG, LGCC, and registered clubs and organizations took part in Brigada Eskwela.
```

Replace the image with `docs/site-assets/2026-11/brigada-eskwela-2026.jpg`.

- [ ] **Step 10: Verify the page in Preview**

Click `Preview`. Confirm nine cards in the order in the table above, each with the correct cover, and the existing `READ MORE ACCOMPLISHMENT REPORTS` button still below the last row. Exit preview.

Expected: three rows of three; no duplicated or empty card; no broken image.

---

### Task 5: Replace the Finance entry with the two published reports

**Files:**
- Modify: Google Sites Finance draft, report block

**Interfaces:**
- Consumes: the two finance file IDs from "Reference data".
- Produces: a Finance page listing both reports by name.

- [ ] **Step 1: Open Finance and select the old report block**

Open the `Finance` page in the editor. Click at the start of `SSLG Financial Report (July 26, 2026)`.

- [ ] **Step 2: Replace the title line and URL line**

Select from the start of `SSLG Financial Report (July 26, 2026)` through the end of the `https://drive.google.com/drive/folders/1NhgG1fkfxch70E3hzb5YhTgCK0PWKcdV?usp=drive_link` line. Replace the selection with exactly:

```text
Financial Report — Election of SSLG Grade 7 Representatives 2026
https://drive.google.com/file/d/1r8_e9PQ7l29iDLbQrkMyjasVdGZvCc3X/view

Financial Report — Leaders Induction Ceremony 2026
https://drive.google.com/file/d/1AKXTRjZx7_jPLUi5GWe6QcYuREKsSP0d/view
```

Do not select or change the italic `Prepared By:  Samantha C. De Venecia ( SSLG Treasurer)` line.

- [ ] **Step 3: Confirm both URLs are hyperlinks**

Click each URL. If it is not underlined and clickable, select it, click the link icon, paste the same URL, and click `Apply`.

Expected: both URLs open the corresponding Drive file; the visible text matches the URL exactly, as on the old page.

- [ ] **Step 4: Preview Finance**

Click `Preview`. Confirm the heading `Latest Financial Reports`, the two report names, both links, and the `Prepared By` line. Exit preview.

Expected: no `July 26, 2026` remains anywhere on the page.

---

### Task 6: Create the Photos page with live album embeds

**Files:**
- Create: Google Sites page `Photos` (slug `/photos`)
- Modify: main navigation (insert after Accomplishments)

**Interfaces:**
- Consumes: five album IDs with photos: Teachers' Day, LGCC Clean-Up, Earthquake Drill, Grade 7 Election, Brigada Eskwela.
- Produces: a public page whose embeds re-read Drive on every visit.

- [ ] **Step 1: Duplicate the Accomplishments page**

In the Pages panel, open the menu next to `Accomplishments` and choose `Duplicate`. Rename the copy `Photos`. If it does not land directly after `Accomplishments`, drag it there.

Expected: the new page inherits the header design and sits directly after Accomplishments in the navigation.

- [ ] **Step 2: Reuse the header and clear the body**

Open `Photos`. Edit the inherited page heading from `ACCOMPLISHMENTS` to `PHOTOS`; leave its styling untouched. Delete every body section below the header (hover the section → trash icon).

Expected: a page with the standard header reading `PHOTOS` and an empty body.

- [ ] **Step 3: Add the page intro**

Add a one-column section. Insert a text box and type exactly:

```text
Activity albums from the SSLG and LGCC. Photos are added to each public Drive album by the PIO; the albums below update on every visit.
```

Keep it as normal body text and match the spacing of the other page headers.

- [ ] **Step 4: Add the Teachers' Day album**

Add a one-column section below the intro. Insert a text box with `World Teachers' Day 2026`, styled as Heading 2. Below it, use `Insert` → `Embed` → `Embed code`, paste exactly:

```html
<iframe src="https://drive.google.com/embeddedfolderview?id=1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz#grid" title="World Teachers' Day 2026 photo album" style="width:100%;height:720px;border:0;"></iframe>
```

Click `Insert`. Do not use the Drive picker.

- [ ] **Step 5: Add the LGCC Clean-Up album**

New section, heading `LGCC Clean-Up Drive – October 2026`, embed code:

```html
<iframe src="https://drive.google.com/embeddedfolderview?id=1_0DykrJF1DVEzwo19m9mbgAp2HRi85ix#grid" title="LGCC Clean-Up Drive October 2026 photo album" style="width:100%;height:720px;border:0;"></iframe>
```

- [ ] **Step 6: Add the Earthquake Drill album**

New section, heading `National Simultaneous Earthquake Drill 2026`, embed code:

```html
<iframe src="https://drive.google.com/embeddedfolderview?id=1UT4M9b8TrctZ-d-tGjAEPbLADbUo_ik8#grid" title="National Simultaneous Earthquake Drill 2026 photo album" style="width:100%;height:720px;border:0;"></iframe>
```

- [ ] **Step 7: Add the Grade 7 Election album**

New section, heading `Election of SSLG Grade 7 Representatives 2026`, embed code:

```html
<iframe src="https://drive.google.com/embeddedfolderview?id=1y2tKu7-5uoxBK-jQ2dN0sEIqCj2tL8av#grid" title="Election of SSLG Grade 7 Representatives 2026 photo album" style="width:100%;height:720px;border:0;"></iframe>
```

- [ ] **Step 8: Add the Brigada Eskwela album**

New section, heading `Brigada Eskwela 2026`, embed code:

```html
<iframe src="https://drive.google.com/embeddedfolderview?id=1p-60nKJtTiACOF1Kkj8OLCuEFlnhR1sn#grid" title="Brigada Eskwela 2026 photo album" style="width:100%;height:720px;border:0;"></iframe>
```

- [ ] **Step 9: Preview Photos on desktop and mobile**

Click `Preview`; use the `Phone` preview tab. Confirm each album shows photo thumbnails (not a grey folder icon), the Grade 7 HEIC thumbnails render, and the nav shows `Photos` after `Accomplishments`. Exit preview.

Expected: five album grids; if the Grade 7 grid is blank, stop and apply the HEIC conversion before publishing (Open item 7).

---

### Task 7: Publish and verify as a signed-out visitor

**Files:**
- Create: `tools/verify_site_update.py`
- Modify: public site (publish only)

**Interfaces:**
- Consumes: the published URL and every string added by Tasks 3–6.
- Produces: a PASS/FAIL report from unauthenticated HTTP requests.

- [ ] **Step 1: Write the verification script**

Create `tools/verify_site_update.py` with exactly:

```python
import html
import re
import sys
import urllib.request

BASE = "https://sites.google.com/view/bsanhs-site"
PAGES = {
    "home": "/home",
    "accomplishments": "/accomplishments",
    "finance": "/finance",
    "transparency": "/transparency",
    "photos": "/photos",
}

TEXT_CHECKS = [
    ("home", "World Teachers' Day 2026"),
    ("home", "Stay Updated with Current SSLG Affairs Here"),
    ("accomplishments", "World Teachers' Day 2026"),
    ("accomplishments", "LGCC Clean-Up Drive – Project ECOLEAD"),
    ("accomplishments", "National Simultaneous Earthquake Drill 2026"),
    ("accomplishments", "Onto the Next Leaders Induction Ceremony"),
    ("accomplishments", "Crafting of the SSLG General Plan of Action"),
    ("accomplishments", "Election of Registered School Clubs and Organizations"),
    ("accomplishments", "Grade 7 Representatives Election for the S.Y 2026-2027"),
    ("accomplishments", "Brigada Eskwela 2026"),
    ("accomplishments", "Club and Organizations Membership Drive"),
    ("finance", "Financial Report — Election of SSLG Grade 7 Representatives 2026"),
    ("finance", "Financial Report — Leaders Induction Ceremony 2026"),
    ("finance", "1r8_e9PQ7l29iDLbQrkMyjasVdGZvCc3X"),
    ("finance", "1AKXTRjZx7_jPLUi5GWe6QcYuREKsSP0d"),
    ("finance", "Prepared By: Samantha C. De Venecia ( SSLG Treasurer)"),
]

RAW_CHECKS = [
    ("transparency", "1qm3Z6OmjxFa41OsjTPrBUJEl57-GSGH5"),
    ("transparency", "1SVzssvcj1IkEndY0Mp5Nv8WhDsaQUDl4"),
    ("transparency", "1hiqv7sFda_cGWVo7OtgJs5cpPS-buZ4L"),
    ("transparency", "15vGFBRfifPvEUkN5yo1iv87MQPAoaFHE"),
    ("transparency", "1xszCcvP83aaVus3xLQ4f1RDmjvWqLHUj"),
    ("transparency", "1NhgG1fkfxch70E3hzb5YhTgCK0PWKcdV"),
    ("photos", "1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz"),
    ("photos", "1_0DykrJF1DVEzwo19m9mbgAp2HRi85ix"),
    ("photos", "1UT4M9b8TrctZ-d-tGjAEPbLADbUo_ik8"),
    ("photos", "1y2tKu7-5uoxBK-jQ2dN0sEIqCj2tL8av"),
    ("photos", "1p-60nKJtTiACOF1Kkj8OLCuEFlnhR1sn"),
    ("home", "/view/bsanhs-site/photos"),
]

ABSENT = [
    ("finance", "July 26, 2026"),
]


def fetch(path):
    url = BASE + path
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def visible_text(raw):
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", text).replace("\u2019", "'")


def main():
    raw, text, failures = {}, {}, []

    for name, path in PAGES.items():
        try:
            raw[name] = fetch(path)
            text[name] = visible_text(raw[name])
        except Exception as exc:
            failures.append(f"cannot fetch {name} ({path}): {exc}")

    for page, needle in TEXT_CHECKS:
        if page in text and needle not in text[page]:
            failures.append(f"missing text on {page}: {needle}")
    for page, needle in RAW_CHECKS:
        if page in raw and needle not in raw[page]:
            failures.append(f"missing markup on {page}: {needle}")
    for page, needle in ABSENT:
        if page in text and needle in text[page]:
            failures.append(f"stale text still on {page}: {needle}")

    if failures:
        print("FAIL")
        for failure in failures:
            print("-", failure)
        return 1

    print(f"PASS: {len(TEXT_CHECKS)} text checks, {len(RAW_CHECKS)} markup checks, {len(ABSENT)} absence checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the checker against the still-published old site**

```bash
python -X utf8 tools/verify_site_update.py
```

Expected: `FAIL` listing the missing strings and a `cannot fetch photos` entry, proving the checks detect the old state without crashing.

- [ ] **Step 3: Publish**

In the editor click `Publish` → confirm `Publish`.

Expected: a confirmation that the site is published and a `View published site` link.

- [ ] **Step 4: Run the checker again, unauthenticated**

```bash
python -X utf8 tools/verify_site_update.py
```

Expected: `PASS: 16 text checks, 12 markup checks, 1 absence check`.

- [ ] **Step 5: Verify the live pages visually**

Open `https://sites.google.com/view/bsanhs-site/home`, `/accomplishments`, `/finance`, and `/photos` in a private window. Confirm the cards and embeds render, the nav is unchanged except for Photos, and no page shows a login prompt.

Expected: no sign-in is required for any of the five pages.

- [ ] **Step 6: Record the rollback point**

In the editor open `Open the version history` and note the timestamp of the version immediately before this update. If the adviser rejects the published result, restore that version.

Expected: a recorded pre-update timestamp in the execution report.

---

### Task 8: Write the PIO runbook and hand off

**Files:**
- Create: `docs/sslg-site-photo-runbook.md`

**Interfaces:**
- Consumes: the album IDs and live URLs above.
- Produces: a one-page non-technical procedure; no code and no credentials.

- [ ] **Step 1: Write the runbook**

Create `docs/sslg-site-photo-runbook.md` with exactly:

```markdown
# SSLG Site Photo Runbook

**Photo folder:** https://drive.google.com/drive/folders/1QbMxIfTuL9-qJ3T9YgfuYyErHexqxBiQ
**Live photos page:** https://sites.google.com/view/bsanhs-site/photos

## Add photos to an event that is already on the site

1. Open the photo folder, then `S.Y 2026-2027`, then the current term.
2. Open the event album and upload JPEG or PNG files.
3. Do not upload HEIC or HEIF. On iPhone, use Settings > Camera > Formats > Most Compatible, or share the photo as JPEG first.
4. Do not upload the same filename twice.
5. No site edit is needed. The album on the Photos page shows the new photos on the next visit.

## Add a new event

1. Inside the current term folder, create an album named `EVENT-MONTH-YEAR`, for example `FOUNDATION DAY-OCTOBER-2026`.
2. Upload the photos.
3. Ask the site editor to add one heading and one embed to the Photos page. This is a two-minute edit; the album then updates itself.

## Housekeeping

- The photo root must stay shared as "Anyone with the link".
- The Club Fair and Induction albums are empty; populate or remove them.
- The Brigada album contains repeated copies of several photos; remove duplicates so the gallery does not show the same picture twice.
- Photos are public. Clear close-ups of learners with the adviser before uploading.

## What not to do

- Do not move or rename term folders: the Photos page embeds point at the album IDs.
- Do not add code, scripts, or backups inside the photo folders.
- Do not sign in with an account that does not own the folders; the links are public and need no sign-in.
```

- [ ] **Step 2: Report the open items**

Send the adviser the "Open items to confirm" table from this plan, with the defaults used. Do not change published copy until they answer.

- [ ] **Step 3: Final verification**

Run `python -X utf8 tools/verify_site_update.py` once more and confirm `PASS`. Report the published URLs, the rollback timestamp, and the seven open items.

---

## Phase 2 (deferred): Apps Script gallery

Do not build this in the current update. The native embeds already deliver automatic photo updates with zero code.

If the embeds later prove too plain or too tall on mobile, the fallback is a Google Apps Script web app that lists the public albums and renders a styled grid. Constraints for that future work:

- The script runs under the editor's Google account; public link-sharing on the photo folders is what grants read access, so no folder ownership is needed.
- Source stays in the vault (`tools/`), never in Drive. Only the deployed web app URL is embedded in Sites.
- The app must read folder IDs from a single constant map, use `DriveApp.getFolderById(...).getFiles()`, skip non-image MIME types, and cache results for about five minutes.
- It must not require OAuth scopes beyond Drive read access to those folders and must not store any learner data.

This is a separate plan with its own tests; nothing here depends on it.
