# SSLG.ph — proposed plan

A national registry and publishing standard for Supreme Secondary Learner Governments.
This folder holds a working prototype: five records, forty-one generated pages, no server,
no database, no build tooling beyond Python.

---

## 1. The one-paragraph version

Every SSLG already produces the same documents every year — activity completion reports,
memoranda, financial reports, a club list. Those documents are written for the division and
then disappear into a folder. This project puts each school's record in one standard file,
generates the school's public site from it, and builds the national directory, activity feed,
issuance index and transparency table from the same files. The website is a by-product. The
record is the product.

The model is BetterGov.ph: volunteer-run, open source, one shared schema, data in a public
repository, and the value sitting in the consistency of the data rather than the design of
any single page.

---

## 2. The demo, in five minutes

| Minute | Open | Say |
|---|---|---|
| 0:00 | `site/index.html` | "This is the national view. Five learner governments, three regions, 34 activities, 60 clubs." |
| 0:45 | `site/schools.html` | "Filter by region. Every school is one record, not one hand-built site." |
| 1:30 | `site/s/bsanhs/index.html` | "Here is Benigno S. Aquino NHS. The stats, the latest activities, the four clusters — all generated." |
| 2:15 | `site/s/bsanhs/activities.html` | "Eighteen activity records with IDs. These are the ACRs the school already files." |
| 2:45 | `site/s/bsanhs/clubs.html` | "Twenty clubs in four clusters. This is the classification framework, published." |
| 3:15 | `site/s/bsanhs/officers.html` | "Roles are public, names are not. That is the privacy default, and it is the hard part." |
| 3:45 | `site/transparency.html` | "Who publishes financial reports, how often, and when they last filed." |
| 4:15 | `site/about.html` | "What is real, what is synthetic, and what the rollout looks like." |

The strongest moment is the officers page. Every other student-government site on the
internet publishes a roster of minors with names and sections. This one explains why it
does not.

---

## 3. What is real in the prototype

| Item | Status |
|---|---|
| Registry, directory, feed, documents index, transparency table | Working, generated from JSON |
| BSANHS activities, dates, record IDs, memoranda, 20 clubs | From the school's own vault records |
| Four other school records | Synthetic, badged **Demo record** on every page |
| Officer names | Withheld everywhere except one demo record, to show the consent rule |
| Financial figures | Not shown at all — only the fact and date of publication |
| Photographs | Six real school photographs from `docs/site-assets/2026-11` |

---

## 4. Architecture

```
data/schools/<slug>.json   →  build.py  →  site/s/<slug>/*.html
                                      →  site/index.html, schools.html, ...
```

- **One file per school.** No database, no CMS, no login. A record is a text file that can be
  reviewed in a pull request, diffed, and rolled back.
- **Static output.** 41 HTML pages for 5 schools. A thousand schools would be roughly 7,000
  pages, still static, still free to host on Cloudflare Pages or GitHub Pages.
- **No JavaScript framework.** One 40-line filter script for the directory. The pages work
  with JavaScript disabled.
- **The generator is disposable.** If the project outgrows Python, the same JSON feeds Astro,
  Eleventy or a CMS without touching a single record.

### Why static, and why now

A dynamic platform needs a server, a database, backups, an administrator and a security
posture — all of which cost money and attention that a student-led project does not have.
Static files need none of that. The cost of the whole thing at 1,000 schools is a domain name.

---

## 5. The record

```json
{
  "slug": "bsanhs",
  "status": "verified",
  "verified_on": "2026-11-20",
  "updated": "2026-11-24",
  "school":  { "name", "short", "school_id", "division", "region",
               "region_name", "cluster", "address" },
  "sslg":    { "term", "adviser": {"name", "position", "consent"},
               "officers": [{"role", "grade", "name", "consent"}],
               "contact", "facebook" },
  "activities": [{ "id", "title", "date", "status", "kind", "summary", "photo" }],
  "documents":  [{ "number", "series", "type", "direction", "title", "date" }],
  "finance":    { "frequency", "reports": [{ "period", "published", "type" }] },
  "clubs":      [{ "name", "cluster" }]
}
```

Field rules worth writing down:

- `status` is `verified` or `demo`. Nothing else is publishable.
- `date` accepts `YYYY-MM-DD` or `YYYY-MM`. A missing date sorts last and prints an em dash;
  it is never guessed.
- `direction` on a document is `issued` or `received`. Only final issuances are published;
  drafts stay in the school's archive.
- `consent` is per person. `true` requires a signed form on file at the school, not a
  checkbox in a form.
- `cluster` is one of `A` AGHAM, `B` SINING, `C` LAKAS, `D` BAYANIHAN.

---

## 6. Governance

| Question | Answer |
|---|---|
| Who writes a record? | The SSLG secretary or PIO, using a form. Not a developer. |
| Who approves it? | The SSLG adviser, by attestation. |
| Who confirms the school exists? | The division, once, at registration. |
| Who can take a page down? | The school, immediately, without asking anyone. |
| Who owns the data? | The school. The platform holds a copy, not the original. |
| What happens when an officer graduates? | The record is versioned by term. Last year's page stays, read-only. |

The failure mode to design against is a platform that becomes a second job for the adviser.
Every field in the schema must be something the school already writes down.

---

## 7. Privacy

Learner governments are made of minors, which puts this project under RA 10173 and the DepEd
data privacy manual in a way that a directory of adult officials is not.

**Published by default:** school name, school ID, division, region, cluster, term, officer
roles, activity titles, dates, statuses, document numbers and titles, the existence and date
of financial reports, club names and clusters.

**Never published:** learner names without consent, section names, learner addresses, birth
dates, LRNs, personal mobile numbers, adviser personal numbers, photographs of identifiable
learners without consent, grades or class rankings, disciplinary records.

**The consent rule, stated plainly:** a name renders only when a signed consent form is
recorded against that name at the school. Absence of consent is not a bug to be fixed; it is
the default state of every new record.

**Why not just publish everything?** Because a roster with names, grades and sections is a
searchable map of children, and the harm does not require malice — it requires one person
with a grudge and a working search engine.

---

## 8. Verification flow

```
School submits record
        │
        ▼
Adviser attests  ──►  Division confirms school ID
        │                        │
        └────────┬───────────────┘
                 ▼
        status: verified
                 │
        (any step missing)
                 ▼
        status: demo  ──►  page stays up, badged
```

The badge is not cosmetic. A demo record must never be able to pass for a verified one in a
screenshot, which is why it appears in the school band and in every directory row.

---

## 9. Rollout

| Phase | Scope | Deliverable | Success test | Cost |
|---|---|---|---|---|
| **0** | One school, schema, generator | This prototype | 62 pages from 7 JSON files, no manual HTML | ₱0 |
| **1** | Five schools, one division | Records collected by form, not by interview | Five verified records with zero hand-editing | ₱0 |
| **2** | Division endorsement | Adviser attestation flow, takedown process | A record can be verified without emailing the maintainer | ₱0 |
| **3** | Cluster / regional roll-up | Region view above the division pages | One screen per region, built from the same records | Domain only |
| **4** | National | Public launch, contribution guide | A school you have never met submits a record unaided | Domain + hosting |

Phase 1 is the real test. Five schools in one division will surface every schema gap that a
single school hides.

The division view ships earlier than planned because it needs no new data: it is a group-by on
a field every record already has. That is the general rule for this platform — if a view needs
a new field, it is a new burden on the school, and it should wait.

---

## 10. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Records go stale after the first term | High | The site shows the last-updated date; the directory sorts by freshness; a stale record is visibly stale |
| Advisers treat it as extra work | High | Every field maps to a document the school already files. If a field cannot be sourced from an existing record, cut the field |
| A school publishes learner names without consent | Medium | Names are off by default and require an explicit `consent: true`; the form does not offer a bulk "select all" |
| Someone registers a fake SSLG | Medium | Adviser attestation plus division confirmation before `verified` |
| The project depends on one person | High | Everything is a text file in a repository. Any successor can rebuild the site with one command |
| DepEd objects to the use of school names | Low–Medium | Ask the division first. Offer to run it as a division pilot rather than a national launch |

---

## 11. Decisions needed before Phase 1

1. **Domain.** `sslg.ph`, `sslgov.ph`, or run it under an existing federation domain.
   Check availability before printing the name on anything.
2. **Host.** Cloudflare Pages is free and handles custom domains and HTTPS. GitHub Pages is
   the alternative if the repository is already there.
3. **Repository owner.** A personal account is fine for a prototype and wrong for a service.
   Decide before the first outside school joins.
4. **Who verifies.** The adviser, the division, or both. The prototype assumes both.
5. **Whether the club clusters ship with it.** They are in this prototype because the
   classification framework already exists. They are not required for the registry to work.

---

## 12. What is deliberately missing

- **Search across documents.** Full-text search is a Phase 3 problem and needs an index.
- **Accounts and logins.** The prototype has none. The form at `site/submit.html` produces a
  record without one; Phase 2 adds an authenticated path for a school to file it, and that
  path should be as small as possible.
- **A CMS.** If advisers will not touch JSON, the answer is a form that writes JSON, not a
  CMS. Fewer moving parts. The prototype's form already does this, client-side.
- **Filipino translation.** The interface should be bilingual before national launch, not
  after.
- **Analytics.** Not until there is something worth measuring.

---

## 13. The argument, in one line

> The reason no one can tell you what the country's 47,000 learner governments did this year
> is that each one files its records into a different folder. Put them in one schema and the
> answer builds itself.
