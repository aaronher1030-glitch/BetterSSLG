# SSLG.ph — prototype

A national registry and publishing standard for Supreme Secondary Learner Governments.
Seven school records, sixty-two generated pages, no database, no server.

See **[PLAN.md](PLAN.md)** for the proposal, the rollout phases and the privacy rules.

---

## Run it

```powershell
python -X utf8 prototype\build.py
```

Then open `prototype/site/index.html` in a browser. That is the whole build.

To preview over HTTP (needed for the directory filter to behave exactly as it will in
production):

```powershell
cd prototype\site
python -m http.server 8899
# http://127.0.0.1:8899/
```

---

## What to look at

| Page | Path | What it shows |
|---|---|---|
| National home | `site/index.html` | Counts, latest activity feed, directory, the three-layer pitch |
| Directory | `site/schools.html` | Seven schools, filter by region, search |
| Divisions | `site/divisions.html` | The same records rolled up by division |
| Division page | `site/divisions/tarlac-province.html` | One division: schools, activities, clubs, finance |
| National feed | `site/activities.html` | Every dated activity record across all schools |
| Issuances | `site/documents.html` | One index of memoranda and resolutions |
| Transparency | `site/transparency.html` | Who publishes finance reports, how often, how fresh |
| Submit | `site/submit.html` | The form that produces a record; nothing is uploaded |
| About | `site/about.html` | What is real, the privacy rule, the schema, the plan |
| School site | `site/s/bsanhs/index.html` | The verified record |
| Officers | `site/s/bsanhs/officers.html` | The consent rule in practice |
| Clubs | `site/s/bsanhs/clubs.html` | Twenty clubs, four clusters |
| Demo record | `site/s/sanisidro/index.html` | Same template, synthetic data, different badge |

---

## Layout

```
prototype/
├── build.py                 generator, standard library only
├── PLAN.md                  the proposal
├── README.md                this file
├── assets/
│   ├── style.css            all styling
│   ├── app.js               directory filter, 40 lines
│   └── submit.js            the submission form, no dependencies
├── data/schools/
│   ├── bsanhs.json          verified — drawn from the vault
│   ├── concepcion-east.json demo, Tarlac Province
│   ├── bamban.json          demo, Tarlac Province
│   ├── sanisidro.json       demo
│   ├── stacruz.json         demo
│   ├── tugbok.json          demo
│   └── bantay.json          demo
└── site/                    generated; safe to delete and rebuild
```

Generated output includes `site/divisions/` — one page per division, rebuilt every time.

Photographs are copied from `docs/site-assets/2026-11` at build time. Nothing is uploaded
anywhere.

---

## File a record

`site/submit.html` is the intake form. It runs entirely in the browser: it validates the
required fields, shows the JSON record live as you type, and downloads a `<slug>.json` file.
Nothing is sent anywhere, which is the point — a school can prepare its record without an
account, and the division receives a file it can read.

Open `site/submit.html?example=1` to prefill the form with a worked example. That link is the
fastest way to demo the intake side.

The form never asks for a learner's name. It collects the officer **roles** and writes
`name: null, consent: false` for each one, so a record produced by the form is private by
construction. A name is added later, by the adviser, against a signed consent form.

---

## Division pages

`site/divisions.html` lists every division with at least one record, and
`site/divisions/<slug>.html` is the roll-up: schools, activities, clubs by cluster, and
finance publication.

Nothing extra is filed for this. The division is the `school.division` string already on each
record; the page is grouped, slugged and rendered at build time. Add a school, rebuild, and its
division page appears or updates. A division with no records has no page, which is the honest
result.

This is the page you show a division coordinator or a Superintendent. It answers four
questions on one screen: which schools are registered, what they did, what clubs they run, and
whether they publish their financial reports.

---

## Add a school

1. Copy `data/schools/sanisidro.json` to `data/schools/<slug>.json`.
2. Change `slug`, `school`, `sslg`, and the rest. The `division` field decides which division
   page the school joins.
3. Set `"status": "demo"` until the adviser has attested it.
4. Run `python -X utf8 prototype\build.py`.

The new school appears in the directory, the feed, the document index, the transparency table
and its division page with no further work.

The build validates every record before writing anything. A missing field, an invalid status
or a club without a cluster stops the build and names the file and the field, so a bad record
never produces a half-broken page.

---

## What is not real

Six of the seven records are synthetic and are badged **Demo record** on every page that
shows them. Their school names, divisions and school IDs are placeholders. The BSANHS record
is real in its activities, dates, record IDs, memoranda and club list; its officer names are
withheld, and its financial reports are listed by period and publication date only, without
figures.

This is not an official DepEd service and has no connection to the Department of Education.
