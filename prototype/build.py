#!/usr/bin/env python
"""Build the SSLG.ph prototype: a national directory plus one site per SSLG.

    python -X utf8 prototype/build.py

Reads  prototype/data/schools/*.json
Writes prototype/site/**  (open prototype/site/index.html in a browser)

No dependencies beyond the standard library.
"""
from __future__ import annotations

import html
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "schools"
OUT = ROOT / "site"
ASSETS = ROOT / "assets"
PHOTO_SRC = ROOT.parent / "docs" / "site-assets" / "2026-11"
PHOTO_DST = OUT / "assets" / "photos"

BUILD_DATE = "24 November 2026"

CLUSTERS = {
    "A": ("AGHAM", "Academic and STEM"),
    "B": ("SINING", "Arts, Culture and Media"),
    "C": ("LAKAS", "Sports, Health and Wellness"),
    "D": ("BAYANIHAN", "Socio-Civic, Service and Spiritual"),
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

REGION_NAMES = {
    "I": "Ilocos Region", "II": "Cagayan Valley", "III": "Central Luzon",
    "IV-A": "CALABARZON", "IV-B": "MIMAROPA", "V": "Bicol Region",
    "VI": "Western Visayas", "VII": "Central Visayas", "VIII": "Eastern Visayas",
    "IX": "Zamboanga Peninsula", "X": "Northern Mindanao", "XI": "Davao Region",
    "XII": "SOCCSKSARGEN", "XIII": "Caraga", "NCR": "National Capital Region",
    "CAR": "Cordillera", "BARMM": "Bangsamoro",
}


# ------------------------------------------------------------------ helpers
def e(value) -> str:
    return html.escape(str(value), quote=True)


def fmt_date(value) -> str:
    """'2026-07-22' -> '22 Jul 2026'; '2026-10' -> 'Oct 2026'; None -> em dash."""
    if not value:
        return "&mdash;"
    parts = str(value).split("-")
    if len(parts) == 3:
        y, m, d = parts
        return f"{int(d)} {MONTHS[int(m) - 1]} {y}"
    if len(parts) == 2:
        y, m = parts
        return f"{MONTHS[int(m) - 1]} {y}"
    return e(value)


def sort_key(value) -> str:
    return str(value or "")


def status_badge(status: str) -> str:
    label = status.replace("-", " ")
    return f'<span class="badge {e(status)}">{e(label)}</span>'


def initials(text: str) -> str:
    words = [w for w in text.replace(".", " ").split() if w]
    return "".join(w[0] for w in words[:2]).upper() or "SS"


def slugify(text: str) -> str:
    """'Tarlac Province' -> 'tarlac-province'. Used for division page names."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "division"


def division_groups(schools: list[dict]) -> dict[str, list[dict]]:
    """Group schools by the division named on their record. No extra config."""
    groups: dict[str, list[dict]] = {}
    for school in schools:
        groups.setdefault(school["school"]["division"], []).append(school)
    return dict(sorted(groups.items()))


def validate_record(record: dict, source: Path) -> list[str]:
    """Return a list of problems with one school record. Empty means it will build."""
    errors: list[str] = []

    def need(path: str, kinds) -> None:
        node = record
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                errors.append(f"{source.name}: missing {path}")
                return
            node = node[part]
        if not isinstance(node, kinds):
            errors.append(f"{source.name}: {path} should be {kinds}")

    for path, kinds in [
        ("slug", str), ("status", str), ("school", dict),
        ("school.name", str), ("school.short", str), ("school.school_id", (str, int)),
        ("school.division", str), ("school.region", str), ("school.address", str),
        ("sslg", dict), ("sslg.term", str), ("sslg.officers", list),
        ("activities", list), ("documents", list),
        ("finance", dict), ("finance.frequency", str), ("finance.reports", list),
        ("clubs", list),
    ]:
        need(path, kinds)

    if record.get("status") not in ("demo", "verified"):
        errors.append(f"{source.name}: status must be 'demo' or 'verified'")

    for i, activity in enumerate(record.get("activities") or []):
        for field in ("id", "title", "status", "kind"):
            if not activity.get(field):
                errors.append(f"{source.name}: activities[{i}] is missing {field}")
    for i, document in enumerate(record.get("documents") or []):
        for field in ("number", "type", "direction", "title"):
            if not document.get(field):
                errors.append(f"{source.name}: documents[{i}] is missing {field}")
    for i, report in enumerate((record.get("finance") or {}).get("reports") or []):
        if not report.get("period"):
            errors.append(f"{source.name}: finance.reports[{i}] is missing period")
    for i, club in enumerate(record.get("clubs") or []):
        if not club.get("name"):
            errors.append(f"{source.name}: clubs[{i}] is missing name")
        if club.get("cluster") not in "ABCD":
            errors.append(f"{source.name}: clubs[{i}] cluster must be A, B, C or D")
    for i, officer in enumerate((record.get("sslg") or {}).get("officers") or []):
        if not officer.get("role"):
            errors.append(f"{source.name}: sslg.officers[{i}] is missing role")

    return errors


def record_badge(school: dict) -> str:
    if school.get("status") == "verified":
        return '<span class="badge verified">Verified</span>'
    return '<span class="badge demo">Demo record</span>'


# ------------------------------------------------------------------ chrome
NAV = [
    ("index.html", "Home"),
    ("schools.html", "Directory"),
    ("divisions.html", "Divisions"),
    ("activities.html", "Activities"),
    ("documents.html", "Documents"),
    ("transparency.html", "Transparency"),
    ("submit.html", "Submit"),
    ("about.html", "About"),
]

SCHOOL_NAV = [
    ("index.html", "Overview"),
    ("officers.html", "Officers"),
    ("activities.html", "Activities"),
    ("documents.html", "Documents"),
    ("finance.html", "Finance"),
    ("clubs.html", "Clubs"),
    ("photos.html", "Photos"),
]


def topbar(root: str, active: str) -> str:
    links = "".join(
        f'<a href="{root}{href}"{" class=\"on\"" if href == active else ""}>{label}</a>'
        for href, label in NAV
    )
    return f"""
<div class="topline"></div>
<header class="topbar">
  <div class="wrap">
    <a class="wordmark" href="{root}index.html">
      <span class="mark">SG</span>
      <span>SSLG.ph<small>Learner governments, in the open</small></span>
    </a>
    <nav class="nav">{links}</nav>
  </div>
</header>"""


def footer(root: str) -> str:
    return f"""
<footer class="footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="wordmark" href="{root}index.html">
          <span class="mark">SG</span>
          <span>SSLG.ph<small>Learner governments, in the open</small></span>
        </a>
        <p>A shared registry and publishing standard for Supreme Secondary Learner Governments.
           Built so that a school's records can be read, compared and trusted.</p>
      </div>
      <div>
        <h4>Browse</h4>
        <a href="{root}schools.html">School directory</a>
        <a href="{root}divisions.html">Divisions</a>
        <a href="{root}activities.html">Activity feed</a>
        <a href="{root}documents.html">Issuances</a>
        <a href="{root}transparency.html">Transparency</a>
      </div>
      <div>
        <h4>Standards</h4>
        <a href="{root}submit.html">Submit a record</a>
        <a href="{root}about.html">How it works</a>
        <a href="{root}about.html#privacy">Privacy rules</a>
        <a href="{root}about.html#verification">Verification</a>
        <a href="{root}about.html#schema">Record schema</a>
      </div>
      <div>
        <h4>Prototype</h4>
        <a href="{root}about.html#status">What is real here</a>
        <a href="{root}about.html#plan">Rollout plan</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>Prototype build, {BUILD_DATE}. Not an official DepEd service.</span>
      <span>Records marked <em>Demo</em> are synthetic and exist to test the layout.</span>
    </div>
  </div>
</footer>"""


def page(title: str, body: str, *, root: str = "", active: str = "", desc: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#02133e">
<link rel="icon" href="data:,">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400&amp;family=IBM+Plex+Mono:wght@400;500;600&amp;family=IBM+Plex+Sans:wght@400;500;600;700&amp;family=Montserrat:wght@700;800;900&amp;display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
{topbar(root, active)}
{body}
{footer(root)}
<script src="{root}assets/app.js"></script>
<script src="{root}assets/submit.js"></script>
</body>
</html>
"""


def school_page(school: dict, title: str, body: str, active: str) -> str:
    s = school["school"]
    root = "../../"
    links = "".join(
        f'<a href="{href}"{" class=\"on\"" if href == active else ""}>{label}</a>'
        for href, label in SCHOOL_NAV
    )
    head = f"""
<section class="school-band">
  <div class="wrap">
    {record_badge(school)}
    <h1>{e(s['name'])}</h1>
    <div class="meta">
      <span>Supreme Secondary Learner Government &middot; <strong>SY {e(school['sslg']['term'])}</strong></span>
      <span>School ID <strong>{e(s['school_id'])}</strong></span>
      <span>SDO <strong>{e(s['division'])}</strong></span>
      <span>Region <strong>{e(s['region'])}</strong></span>
      <span>Federation cluster <strong>{e(s['cluster'])}</strong></span>
    </div>
  </div>
</section>
<div class="subnav"><div class="wrap">{links}</div></div>
<div class="wrap"><div class="crumbs"><a href="../../index.html">SSLG.ph</a><span>/</span><a href="../../schools.html">Directory</a><span>/</span>{e(s['short'])}</div></div>
"""
    return page(f"{s['short']} — {title}", head + body, root=root, active="schools")


# ------------------------------------------------------------------ fragments
def activity_card(act: dict, *, school: dict | None = None, root: str = "", href: str = "#") -> str:
    photo = act.get("photo")
    if photo:
        thumb = f'<div class="thumb"><img src="{root}assets/photos/{e(photo)}" alt="" loading="lazy"></div>'
    else:
        mark = school["school"]["short"] if school else "SSLG"
        tone = school.get("_tone", 0) if school else 0
        thumb = (f'<div class="thumb blank ph-{tone}"><span class="ph-mark">{e(mark)}</span>'
                 f'<span class="ph-kind">{e(act.get("kind", "Activity"))}</span></div>')
    meta = [f'<span>{fmt_date(act.get("date"))}</span>']
    if school:
        meta.append('<span class="dot"></span>')
        meta.append(f'<span>{e(school["school"]["short"])}</span>')
    return f"""
<a class="card" href="{href}">
  {thumb}
  <div class="body">
    <div class="meta">{''.join(meta)}</div>
    <h3>{e(act['title'])}</h3>
    <p>{e(act.get('summary', ''))}</p>
    <div class="foot">{status_badge(act['status'])}</div>
  </div>
</a>"""


def school_row(school: dict, root: str = "", link_division: bool = True) -> str:
    s = school["school"]
    acts = len(school["activities"])
    clubs = len(school["clubs"])
    division = e(s['division'])
    if link_division:
        division = (f'<a class="division-link" '
                    f'href="{root}divisions/{slugify(s["division"])}.html">{division}</a>')
    return f"""
<tr data-row data-region="{e(s['region'])}"
    data-text="{e((s['name'] + ' ' + s['division'] + ' ' + s['short'] + ' ' + REGION_NAMES.get(s['region'], '')).lower())}">
  <td><a href="{root}s/{e(school['slug'])}/index.html"><strong>{e(s['name'])}</strong></a>
      <span class="sub">{e(s['address'])}</span></td>
  <td>{division}<span class="sub">Region {e(s['region'])} &middot; Cluster {e(s['cluster'])}</span></td>
  <td class="num">{acts}</td>
  <td class="num">{clubs}</td>
  <td>{fmt_date(school.get('updated'))}</td>
  <td>{record_badge(school)}</td>
</tr>"""


def finance_row(school: dict, root: str = "") -> str:
    fin = school["finance"]
    reports = fin["reports"]
    last = max((r.get("published") for r in reports), default=None)
    status = ('<span class="badge completed">Publishing</span>' if reports
              else '<span class="badge planned">Nothing filed</span>')
    return f"""
<tr>
  <td><a href="{root}s/{e(school['slug'])}/finance.html"><strong>{e(school['school']['name'])}</strong></a>
      <span class="sub">{e(school['school']['division'])}</span></td>
  <td>{e(fin['frequency'])}</td>
  <td class="num">{len(reports)}</td>
  <td>{fmt_date(last)}</td>
  <td>{status}</td>
  <td>{fmt_date(school.get('updated'))}</td>
</tr>"""


# ------------------------------------------------------------------ national pages
def build_home(schools: list[dict]) -> str:
    all_acts = []
    for school in schools:
        for act in school["activities"]:
            all_acts.append((school, act))
    dated = [(s, a) for s, a in all_acts if a.get("date")]
    dated.sort(key=lambda pair: sort_key(pair[1]["date"]), reverse=True)

    cards = "".join(activity_card(a, school=s, href=f"s/{e(s['slug'])}/activities.html")
                    for s, a in dated[:6])

    photo_pairs = [(s, a) for s, a in all_acts if a.get("photo")]
    photo_pairs.sort(key=lambda pair: sort_key(pair[1]["date"]), reverse=True)
    seen_photos, unique_pairs = set(), []
    for pair in photo_pairs:
        if pair[1]["photo"] in seen_photos:
            continue
        seen_photos.add(pair[1]["photo"])
        unique_pairs.append(pair)
    photo_tiles = "".join(
        f'<figure><a href="s/{e(s["slug"])}/photos.html">'
        f'<img src="assets/photos/{e(a["photo"])}" alt="" loading="lazy"></a>'
        f'<figcaption>{e(a["title"])} &middot; {e(s["school"]["short"])} '
        f'&middot; {fmt_date(a.get("date"))}</figcaption></figure>'
        for s, a in unique_pairs[:3]
    )

    total_acts = len(all_acts)
    total_docs = sum(len(s["documents"]) for s in schools)
    total_clubs = sum(len(s["clubs"]) for s in schools)
    total_reports = sum(len(s["finance"]["reports"]) for s in schools)
    regions = len({s["school"]["region"] for s in schools})
    verified = sum(1 for s in schools if s["status"] == "verified")

    rows = "".join(school_row(s) for s in schools)

    ticker_items = [
        f"{len(schools)} learner governments",
        f"{regions} regions",
        f"{total_acts} activity records",
        f"{total_clubs} clubs in four clusters",
        f"{total_docs} issuances indexed",
        f"{total_reports} finance reports",
        f"{verified} adviser-verified",
        f"build {BUILD_DATE}",
    ]
    ticker = '<i>&bull;</i>'.join(f"<span>{e(x)}</span>" for x in ticker_items)
    ticker += '<i>&bull;</i>'

    body = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <div class="eyebrow">Prototype &middot; {BUILD_DATE}</div>
      <h1>Every learner government, <em>in one place</em>.</h1>
      <p class="lede">A shared registry and publishing standard for Supreme Secondary Learner
         Governments: one record per school, one public page per record, one national view
         built from both.</p>
      <div class="hero-actions">
        <a class="btn primary" href="schools.html">Browse the directory</a>
        <a class="btn ghost" href="submit.html">File a record</a>
      </div>
    </div>
    <aside class="hero-panel">
      <div class="label">In the registry</div>
      <div class="panel-row"><span>Learner governments</span><strong>{len(schools)}</strong></div>
      <div class="panel-row"><span>Regions covered</span><strong>{regions}</strong></div>
      <div class="panel-row"><span>Activities on record</span><strong>{total_acts}</strong></div>
      <div class="panel-row"><span>Clubs classified</span><strong>{total_clubs}</strong></div>
      <div class="panel-row"><span>Issuances indexed</span><strong>{total_docs}</strong></div>
      <div class="panel-row"><span>Finance reports</span><strong>{total_reports}</strong></div>
      <div class="panel-row"><span>Adviser-verified</span><strong>{verified} of {len(schools)}</strong></div>
    </aside>
  </div>
  <div class="ticker"><div class="ticker-track">{ticker}{ticker}</div></div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">Latest</div>
        <h2>Recently published</h2>
        <p>Activity records filed by learner governments, newest first. Each one is an
           ACR that already had to be written for the division.</p>
      </div>
      <a class="more" href="activities.html">All activities</a>
    </div>
    <div class="grid g3">{cards}</div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">In pictures</div>
        <h2>From the record</h2>
        <p>Photographs attached to activity records. An image belongs to the record it was
           filed with, never to a separate album that drifts out of date.</p>
      </div>
      <a class="more" href="activities.html">All activities</a>
    </div>
    <div class="photo-grid">{photo_tiles}</div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">Directory</div>
        <h2>{len(schools)} learner governments</h2>
        <p>Filter by region or search by school, division or town.</p>
      </div>
      <a class="more" href="schools.html">Open directory</a>
    </div>
    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>School</th><th>Division</th><th>Activities</th><th>Clubs</th><th>Updated</th><th>Status</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</section>

<section class="section dark">
  <div class="wrap split">
    <div>
      <div class="eyebrow">The idea</div>
      <h2 style="margin-bottom:10px">Three layers, one record</h2>
      <p class="on-dark" style="max-width:60ch">The website is the smallest part of this.
         What makes it work is that every school fills the same record, so the national view
         can be built from it without anyone copying anything by hand.</p>
      <div class="steps" style="margin-top:26px">
        <div class="step">
          <div>
            <h3>Register</h3>
            <p>School, division, region, cluster, term, adviser, officers. One JSON file per
               learner government, verified by the adviser.</p>
          </div>
        </div>
        <div class="step">
          <div>
            <h3>Publish</h3>
            <p>The record generates the school's own site. Activities, issuances and finance
               reports appear the moment they are filed, not three weeks later.</p>
          </div>
        </div>
        <div class="step">
          <div>
            <h3>Aggregate</h3>
            <p>Every school feeds the national feed, the issuance index and the transparency
               table. A division can see all of its schools on one screen &mdash;
               <a href="divisions.html">see a division</a>.</p>
          </div>
        </div>
      </div>
    </div>
    <aside class="callout">
      <h3>Privacy by default</h3>
      <p style="margin-bottom:12px">Officers are listed by role. A learner's name appears only
         when a signed consent form is on file; otherwise the page reads
         <em>withheld</em>.</p>
      <p style="margin-bottom:12px">No section names. No personal mobile numbers. No photographs
         of identifiable learners without consent.</p>
      <p><a href="about.html#privacy">Read the rule</a></p>
    </aside>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">Accountability</div>
        <h2>Transparency at a glance</h2>
        <p>Which learner governments publish financial reports, how often, and how fresh
           their last filing is.</p>
      </div>
      <a class="more" href="transparency.html">Full table</a>
    </div>
    <div class="stats">
      <div class="stat"><b>{total_reports}</b><span>Reports published</span></div>
      <div class="stat"><b>{sum(1 for s in schools if s['finance']['reports'])}</b><span>Schools reporting</span></div>
      <div class="stat"><b>{len(schools)}</b><span>Schools registered</span></div>
      <div class="stat"><b>{regions}</b><span>Regions</span></div>
    </div>
  </div>
</section>
"""
    return page("SSLG.ph — every learner government, in one place", body, active="index.html",
                desc="A shared registry and publishing standard for Supreme Secondary Learner Governments.")


def build_directory(schools: list[dict]) -> str:
    regions = sorted({s["school"]["region"] for s in schools},
                     key=lambda r: list(REGION_NAMES).index(r) if r in REGION_NAMES else 99)
    options = "".join(
        f'<option value="{e(r)}">Region {e(r)} — {e(REGION_NAMES.get(r, ""))}</option>'
        for r in regions
    )
    rows = "".join(school_row(s) for s in schools)
    verified = sum(1 for s in schools if s["status"] == "verified")
    divisions = len({s["school"]["division"] for s in schools})
    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Directory</div>
    <h1 style="font-size:2.2rem;margin-bottom:10px">Learner governments</h1>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:22px">Every registered SSLG,
       with its division, cluster and filing status. Names of learners are not published
       here; see the privacy rule.</p>

    <div class="cluster-key">
      <span class="chip"><b>{len(schools)}</b> learner governments</span>
      <a class="chip" href="divisions.html"><b>{divisions}</b> divisions</a>
      <span class="chip"><b>{len(regions)}</b> regions</span>
      <span class="chip"><b>{verified}</b> adviser-verified</span>
      <span class="chip"><b>{sum(len(s['clubs']) for s in schools)}</b> clubs classified</span>
    </div>

    <div class="filters">
      <input type="search" placeholder="Search school, division or town" data-filter-search>
      <select data-filter-region><option value="">All regions</option>{options}</select>
      <span class="count" data-filter-count></span>
    </div>

    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>School</th><th>Division</th><th>Activities</th><th>Clubs</th><th>Updated</th><th>Status</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</section>
"""
    return page("Directory — SSLG.ph", body, active="schools.html")


def build_activities(schools: list[dict]) -> str:
    pairs = [(s, a) for s in schools for a in s["activities"] if a.get("date")]
    pairs.sort(key=lambda p: sort_key(p[1]["date"]), reverse=True)
    cards = "".join(activity_card(a, school=s, href=f"s/{e(s['slug'])}/activities.html")
                    for s, a in pairs)
    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">National feed</div>
    <h1 style="font-size:2.2rem;margin-bottom:10px">Activities</h1>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:28px">{len(pairs)} dated activity
       records across {len(schools)} learner governments. Records without a date in the source
       are held back until the date is confirmed.</p>
    <div class="grid g3">{cards}</div>
  </div>
</section>
"""
    return page("Activities — SSLG.ph", body, active="activities.html")


def build_documents(schools: list[dict]) -> str:
    rows = []
    for school in schools:
        for doc in school["documents"]:
            rows.append((sort_key(doc.get("date")), school, doc))
    rows.sort(key=lambda r: r[0], reverse=True)
    body_rows = ""
    for _, school, doc in rows:
        direction = "Issued" if doc.get("direction") == "issued" else "Received"
        body_rows += f"""
<tr>
  <td><strong>{e(doc['number'])}</strong>{f", s. {doc['series']}" if doc.get('series') else ""}
      <span class="sub">{e(doc['type'])}</span></td>
  <td>{e(doc['title'])}</td>
  <td><a href="s/{e(school['slug'])}/index.html">{e(school['school']['short'])}</a>
      <span class="sub">{e(school['school']['division'])}</span></td>
  <td><span class="badge plain">{direction}</span></td>
  <td>{fmt_date(doc.get('date'))}</td>
</tr>"""
    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Issuances</div>
    <h1 style="font-size:2.2rem;margin-bottom:10px">Documents</h1>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:28px">Memoranda and resolutions
       issued by learner governments, plus the external issuances they received. One index
       across every school.</p>
    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>Number</th><th>Title</th><th>School</th><th>Direction</th><th>Date</th></tr></thead>
        <tbody>{body_rows}</tbody>
      </table>
    </div>
  </div>
</section>
"""
    return page("Documents — SSLG.ph", body, active="documents.html")


def build_transparency(schools: list[dict]) -> str:
    rows = "".join(finance_row(school)
                   for school in sorted(schools, key=lambda s: s["school"]["name"]))
    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Accountability</div>
    <h1 style="font-size:2.2rem;margin-bottom:10px">Transparency</h1>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:28px">Publication of financial
       reports is voluntary and uneven. The table shows who publishes, how often, and when
       they last filed &mdash; which is itself the useful information.</p>
    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>School</th><th>Stated frequency</th><th>Reports</th><th>Last published</th><th>Status</th><th>Record updated</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="note" style="margin-top:22px">
      <strong>Why this page exists.</strong> A school that files nothing is not necessarily
      hiding anything &mdash; it may not know the standard. Publishing the comparison is what
      creates the pressure to adopt one.
    </div>
  </div>
</section>
"""
    return page("Transparency — SSLG.ph", body, active="transparency.html")


# ------------------------------------------------------------------ division pages
def build_divisions(schools: list[dict]) -> str:
    groups = division_groups(schools)
    rows = ""
    for name, members in groups.items():
        region = members[0]["school"]["region"]
        acts = sum(len(m["activities"]) for m in members)
        clubs = sum(len(m["clubs"]) for m in members)
        verified = sum(1 for m in members if m["status"] == "verified")
        updated = max((m.get("updated") or "" for m in members), default="")
        rows += f"""
<tr>
  <td><a href="divisions/{slugify(name)}.html"><strong>{e(name)}</strong></a>
      <span class="sub">{len(members)} learner government{'s' if len(members) != 1 else ''}</span></td>
  <td>Region {e(region)}<span class="sub">{e(REGION_NAMES.get(region, ''))}</span></td>
  <td class="num">{acts}</td>
  <td class="num">{clubs}</td>
  <td class="num">{verified} of {len(members)}</td>
  <td>{fmt_date(updated)}</td>
</tr>"""

    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Divisions</div>
    <h1 style="font-size:2.2rem;margin-bottom:10px">Schools by division</h1>
    <p style="color:var(--muted);max-width:64ch;margin-bottom:22px">Every division with at least
       one record, with its schools, activities and clubs rolled up. Nothing extra is filed for
       these pages: the division named on a school's record decides where it appears.</p>

    <div class="cluster-key">
      <span class="chip"><b>{len(groups)}</b> divisions</span>
      <span class="chip"><b>{len(schools)}</b> learner governments</span>
      <span class="chip"><b>{sum(len(s['activities']) for s in schools)}</b> activities</span>
      <span class="chip"><b>{sum(len(s['clubs']) for s in schools)}</b> clubs</span>
    </div>

    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>Division</th><th>Region</th><th>Activities</th><th>Clubs</th><th>Verified</th><th>Updated</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div class="note" style="margin-top:22px;max-width:820px">
      <strong>Generated, not maintained.</strong> A division page is a view over the school
      records, not a second set of files. Add a school to the registry and its division page
      either appears or updates on the next build &mdash; there is no division spreadsheet to
      keep in step.
    </div>
  </div>
</section>
"""
    return page("Divisions — SSLG.ph", body, active="divisions.html",
                desc="Every division with an SSLG record, rolled up from the school records.")


def build_division(name: str, members: list[dict]) -> str:
    members = sorted(members, key=lambda s: s["school"]["name"])
    region = members[0]["school"]["region"]
    acts = sum(len(m["activities"]) for m in members)
    clubs = sum(len(m["clubs"]) for m in members)
    docs = sum(len(m["documents"]) for m in members)
    reports = sum(len(m["finance"]["reports"]) for m in members)
    verified = sum(1 for m in members if m["status"] == "verified")
    updated = max((m.get("updated") or "" for m in members), default="")

    rows = "".join(school_row(m, root="../", link_division=False) for m in members)

    pairs = [(m, a) for m in members for a in m["activities"] if a.get("date")]
    pairs.sort(key=lambda pair: sort_key(pair[1]["date"]), reverse=True)
    cards = "".join(
        activity_card(a, school=m, root="../", href=f"../s/{e(m['slug'])}/activities.html")
        for m, a in pairs[:6]
    ) or '<div class="empty" style="grid-column:1/-1">No dated activities on file yet.</div>'

    cluster_counts = {k: sum(1 for m in members for c in m["clubs"] if c["cluster"] == k)
                      for k in "ABCD"}
    fin_rows = "".join(finance_row(m, root="../") for m in members)

    head = f"""
<section class="school-band division-band">
  <div class="wrap">
    <div class="eyebrow">Division roll-up</div>
    <h1>SDO {e(name)}</h1>
    <div class="meta">
      <span>Region <strong>{e(region)} &middot; {e(REGION_NAMES.get(region, ''))}</strong></span>
      <span><strong>{len(members)}</strong> learner government{'s' if len(members) != 1 else ''}</span>
      <span><strong>{verified}</strong> adviser-verified</span>
      <span>Updated <strong>{fmt_date(updated)}</strong></span>
    </div>
  </div>
</section>
<div class="wrap"><div class="crumbs"><a href="../index.html">SSLG.ph</a><span>/</span><a href="../divisions.html">Divisions</a><span>/</span>{e(name)}</div></div>
"""

    body = f"""
<section class="section">
  <div class="wrap">
    <div class="stats cols-3">
      <div class="stat"><b>{len(members)}</b><span>Schools</span></div>
      <div class="stat"><b>{acts}</b><span>Activity records</span></div>
      <div class="stat"><b>{clubs}</b><span>Clubs classified</span></div>
      <div class="stat"><b>{docs}</b><span>Issuances</span></div>
      <div class="stat"><b>{reports}</b><span>Finance reports</span></div>
      <div class="stat"><b>{verified} of {len(members)}</b><span>Verified</span></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">Schools</div>
        <h2>Learner governments in this division</h2>
        <p>Each row links to the school's own record. A <em>Demo record</em> badge means the
           adviser has not attested it yet.</p>
      </div>
      <a class="more" href="../schools.html">National directory</a>
    </div>
    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>School</th><th>Division</th><th>Activities</th><th>Clubs</th><th>Updated</th><th>Status</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">Latest</div>
        <h2>Recent activities</h2>
        <p>The newest records across every school in the division.</p>
      </div>
      <a class="more" href="../activities.html">All activities</a>
    </div>
    <div class="grid g3">{cards}</div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">Clubs</div>
        <h2>Clubs by cluster</h2>
        <p>Counts across the division. The cluster is operational; the category on the
           accreditation form is unchanged.</p>
      </div>
    </div>
    <div class="grid g4">
      {''.join(f'''<div class="callout"><h3>{CLUSTERS[c][0]}</h3>
        <p style="margin-bottom:8px">{CLUSTERS[c][1]}</p>
        <p style="font-family:var(--font-serif);font-size:1.75rem;font-weight:700;color:var(--navy);margin:0">{cluster_counts[c]}</p></div>''' for c in "ABCD")}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div>
        <div class="eyebrow">Accountability</div>
        <h2>Finance publication</h2>
        <p>Who publishes, how often, and when they last filed. Figures stay in the reports.</p>
      </div>
      <a class="more" href="../transparency.html">National view</a>
    </div>
    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>School</th><th>Stated frequency</th><th>Reports</th><th>Last published</th><th>Status</th><th>Record updated</th></tr></thead>
        <tbody>{fin_rows}</tbody>
      </table>
    </div>
    <div class="note" style="margin-top:22px;max-width:820px">
      <strong>Nothing extra to file.</strong> This page exists because the school records exist.
      A division coordinator does not maintain it, and a school does not submit a second report
      to appear here.
    </div>
  </div>
</section>
"""
    return page(f"SDO {name} — SSLG.ph", head + body, root="../", active="divisions.html",
                desc=f"Learner governments, activities, clubs and finance publication in SDO {name}.")


# ------------------------------------------------------------------ about
def build_about(schools: list[dict]) -> str:
    body = f"""
<section class="section">
  <div class="wrap narrow">
    <div class="eyebrow">About</div>
    <h1 style="font-size:2.2rem;margin-bottom:14px">What this is</h1>
    <p style="font-size:1.0625rem;color:var(--ink-soft)">A prototype of a national registry and
       publishing standard for Supreme Secondary Learner Governments. One record per school
       produces one public site; the same records produce the directory, the activity feed, the
       issuance index and the transparency table.</p>
    <p style="color:var(--ink-soft)">It is modelled on BetterGov.ph: a volunteer-run, open-source
       portal built on a shared schema and a public repository, where the value is the
       consistency of the data rather than the design of any one page.</p>
    <p style="color:var(--ink-soft)">Records arrive through a form that runs in the browser
       (<a href="submit.html">Submit</a>). It validates the fields, shows the JSON as it is
       built, and downloads one file. Nothing is uploaded and no account is required; the
       school sends the file to its division.</p>

    <h2 id="status" style="margin-top:40px;font-size:1.375rem">What is real in this prototype</h2>
    <div class="table-wrap" style="margin-top:16px">
      <table class="data">
        <thead><tr><th>Item</th><th>Status</th></tr></thead>
        <tbody>
          <tr><td>The {len(schools)}-school registry, directory, feed and transparency views</td><td>Working code, generated from JSON</td></tr>
          <tr><td>The division roll-up at <a href="divisions.html">Divisions</a></td><td>Generated from the same records; no extra fields, no division spreadsheet</td></tr>
          <tr><td>The submission form at <a href="submit.html">Submit</a></td><td>Working code. Validates, previews and downloads the record in the browser</td></tr>
          <tr><td>BSANHS record: activities, dates, memoranda, 20 clubs and clusters</td><td>Drawn from the school's own vault records</td></tr>
          <tr><td>The {len(schools) - 1} other school records</td><td>Synthetic, marked <em>Demo record</em></td></tr>
          <tr><td>Officer names</td><td>Withheld everywhere except one demo record, to show the consent rule</td></tr>
          <tr><td>Finance figures</td><td>Not shown. Only the fact and date of publication</td></tr>
          <tr><td>Photographs</td><td>Six real school photographs from the SSLG photo folder</td></tr>
        </tbody>
      </table>
    </div>

    <h2 id="privacy" style="margin-top:40px;font-size:1.375rem">Privacy rules</h2>
    <p style="color:var(--ink-soft)">The officers of an SSLG are learners, which puts this
       platform under the Data Privacy Act of 2012 and the DepEd data privacy manual in a way
       that a government directory of adult officials is not.</p>
    <ul style="color:var(--ink-soft);padding-left:20px">
      <li>Roles are public. Names are not.</li>
      <li>A name renders only when a signed consent form is recorded against it.</li>
      <li>No section names, no learner addresses, no personal mobile numbers.</li>
      <li>No photograph of an identifiable learner without consent; event and document images
          are preferred.</li>
      <li>A school can withdraw its record at any time, and the page goes down with it.</li>
    </ul>

    <h2 id="verification" style="margin-top:40px;font-size:1.375rem">Verification</h2>
    <p style="color:var(--ink-soft)">A record is published as <em>Verified</em> only after the
       adviser attests to it and the division confirms the school exists. Until then it carries
       a <em>Demo record</em> badge, which is visible on every page it touches. Without this
       step the platform would be a spoofing tool with a DepEd-shaped logo on it.</p>

    <h2 id="schema" style="margin-top:40px;font-size:1.375rem">The record</h2>
    <p style="color:var(--ink-soft)">One JSON file per school, six blocks:</p>
    <div class="table-wrap" style="margin-top:16px">
      <table class="data">
        <thead><tr><th>Block</th><th>Holds</th></tr></thead>
        <tbody>
          <tr><td><code>school</code></td><td>Name, school ID, division, region, cluster, address</td></tr>
          <tr><td><code>sslg</code></td><td>Term, adviser, officers, contact</td></tr>
          <tr><td><code>activities</code></td><td>ID, title, date, status, kind, summary, photo</td></tr>
          <tr><td><code>documents</code></td><td>Number, series, type, direction, title, date</td></tr>
          <tr><td><code>finance</code></td><td>Frequency, published reports</td></tr>
          <tr><td><code>clubs</code></td><td>Name and cluster</td></tr>
        </tbody>
      </table>
    </div>

    <h2 id="plan" style="margin-top:40px;font-size:1.375rem">Rollout</h2>
    <div class="table-wrap" style="margin-top:16px">
      <table class="data">
        <thead><tr><th>Phase</th><th>Scope</th><th>Test of success</th></tr></thead>
        <tbody>
          <tr><td>0</td><td>Schema, generator, BSANHS as record #1</td><td>This prototype</td></tr>
          <tr><td>1</td><td>Five schools in one division, records collected by form</td><td>Five verified records, no manual HTML</td></tr>
          <tr><td>2</td><td>Division endorsement, adviser attestation flow</td><td>A record can be verified without emailing you</td></tr>
          <tr><td>3</td><td>Cluster and regional federation roll-up</td><td>One screen per division, one per region</td></tr>
        </tbody>
      </table>
    </div>

    <div class="note" style="margin-top:36px">
      <strong>This build is a demonstration.</strong> The registry, the generator and the
      privacy rules are real. The {len(schools) - 1} synthetic school records exist to show what a populated
      directory looks like, and are labelled as such on every page.
    </div>
  </div>
</section>
"""
    return page("About — SSLG.ph", body, active="about.html")


# ------------------------------------------------------------------ submission
def build_submit(schools: list[dict]) -> str:
    region_options = "".join(
        f'<option value="{e(code)}">{e(code)} &mdash; {e(name)}</option>'
        for code, name in REGION_NAMES.items()
    )
    cluster_options = "".join(
        f'<option value="{key}">{key} &mdash; {e(name)}</option>'
        for key, (name, _) in CLUSTERS.items()
    )
    kind_options = "".join(
        f'<option>{e(k)}</option>'
        for k in ["Meeting", "Program", "Project", "Ceremony", "Competition",
                  "Outreach", "Drill", "Election", "Planning", "Training", "Other"]
    )
    status_options = "".join(
        f'<option value="{v}">{v.title()}</option>'
        for v in ["completed", "ongoing", "planned"]
    )
    doc_type_options = "".join(
        f'<option>{e(t)}</option>'
        for t in ["Memorandum", "Office Memorandum", "Resolution",
                  "Division Memorandum", "National Federation Memorandum", "Other"]
    )
    direction_options = '<option value="issued">Issued by this SSLG</option><option value="received">Received from a higher office</option>'
    frequency_options = "".join(
        f'<option{" selected" if f == "Quarterly" else ""}>{f}</option>'
        for f in ["Monthly", "Quarterly", "Semestral", "Annual"]
    )
    standard_roles = "\n".join([
        "President", "Vice President", "Secretary", "Treasurer", "Auditor",
        "Public Information Officer", "Business Manager", "Sergeant-at-Arms",
        "Grade 7 Representative", "Grade 8 Representative", "Grade 9 Representative",
        "Grade 10 Representative", "Grade 11 Representative", "Grade 12 Representative",
    ])

    body = f"""
<section class="form-shell">
  <div class="wrap">
    <div class="form-head">
      <div class="eyebrow">Submission</div>
      <h1>File a record</h1>
      <p>One form, one file. Fill this in and the page builds the JSON record that the registry
         reads &mdash; the same shape as every school already published here. Nothing is uploaded;
         the file is produced in your browser and you send it to your division.</p>
    </div>

    <div class="form-grid">
      <form id="record-form" novalidate autocomplete="off">

        <fieldset>
          <legend>School</legend>
          <div class="field">
            <label for="f-name">School name <span class="req">*</span></label>
            <input id="f-name" data-top="school.name" placeholder="Benigno S. Aquino National High School">
          </div>
          <div class="field-row">
            <div class="field">
              <label for="f-short">Short name <span class="req">*</span></label>
              <input id="f-short" data-top="school.short" placeholder="BSANHS">
              <span class="hint">Used in the directory and page titles.</span>
            </div>
            <div class="field">
              <label for="f-id">School ID <span class="req">*</span></label>
              <input id="f-id" data-top="school.school_id" inputmode="numeric" placeholder="300981">
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label for="f-division">Division <span class="req">*</span></label>
              <input id="f-division" data-top="school.division" placeholder="Tarlac Province">
            </div>
            <div class="field">
              <label for="f-region">Region <span class="req">*</span></label>
              <select id="f-region" data-top="school.region">
                <option value="">Select a region</option>
                {region_options}
              </select>
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label for="f-cluster">Federation cluster</label>
              <input id="f-cluster" data-top="school.cluster" placeholder="IV">
            </div>
            <div class="field">
              <label for="f-address">Town or city <span class="req">*</span></label>
              <input id="f-address" data-top="school.address" placeholder="Concepcion, Tarlac">
            </div>
          </div>
        </fieldset>

        <fieldset>
          <legend>Learner government</legend>
          <div class="field-row">
            <div class="field">
              <label for="f-term">School year <span class="req">*</span></label>
              <input id="f-term" data-top="sslg.term" placeholder="2026-2027">
            </div>
            <div class="field">
              <label for="f-adviser">Adviser position</label>
              <input id="f-adviser" data-top="sslg.adviser.position" value="SSLG Adviser">
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label for="f-contact">Contact email</label>
              <input id="f-contact" data-top="sslg.contact" type="email" placeholder="sslg@school.edu.ph">
              <span class="hint">A shared mailbox, not a learner's personal address.</span>
            </div>
            <div class="field">
              <label for="f-facebook">Facebook page</label>
              <input id="f-facebook" data-top="sslg.facebook" placeholder="facebook.com/…">
            </div>
          </div>
          <div class="field">
            <label for="f-roles">Officer roles, one per line</label>
            <textarea id="f-roles" data-top="sslg.roles" rows="6">{e(standard_roles)}</textarea>
            <span class="hint">Roles only. Names are never collected here &mdash; they are added
              later, by the adviser, against a signed consent form.</span>
          </div>
        </fieldset>

        <fieldset>
          <legend>Activities</legend>
          <p class="hint" style="margin:-4px 0 14px">The activity records that already exist in your
             ACRs and monitoring reports. Enter the ones filed this school year.</p>
          <div class="repeat-list" data-list="activities"></div>
          <button type="button" class="add-row" data-add="activities">+ Add an activity</button>
        </fieldset>

        <fieldset>
          <legend>Issuances</legend>
          <p class="hint" style="margin:-4px 0 14px">Memoranda and resolutions issued by the SSLG,
             plus external issuances it received.</p>
          <div class="repeat-list" data-list="documents"></div>
          <button type="button" class="add-row" data-add="documents">+ Add a document</button>
        </fieldset>

        <fieldset>
          <legend>Finance</legend>
          <div class="field">
            <label for="f-frequency">Stated publication frequency</label>
            <select id="f-frequency" data-top="finance.frequency">{frequency_options}</select>
          </div>
          <div class="repeat-list" data-list="reports"></div>
          <button type="button" class="add-row" data-add="reports">+ Add a published report</button>
          <p class="hint" style="margin-top:12px">Record the period and the date it was published.
             The figures stay in the report itself; this page never republishes them.</p>
        </fieldset>

        <fieldset>
          <legend>Clubs</legend>
          <p class="hint" style="margin:-4px 0 14px">Every recognized club and organization, with
             one cluster each. Assignment is by primary purpose, at accreditation.</p>
          <div class="repeat-list" data-list="clubs"></div>
          <button type="button" class="add-row" data-add="clubs">+ Add a club</button>
        </fieldset>

        <fieldset>
          <legend>Declaration</legend>
          <div class="field">
            <label style="display:flex;gap:9px;align-items:flex-start;text-transform:none;letter-spacing:0;font-family:var(--font-ui);font-size:.875rem;color:var(--ink-soft);font-weight:400">
              <input type="checkbox" data-top="attest" style="width:auto;margin-top:3px">
              <span>I am the SSLG adviser or an officer authorized by the adviser, and the
                information in this record is true and drawn from documents on file.</span>
            </label>
          </div>
          <p class="hint">A record submitted without this declaration is published as
             <em>Demo</em> and is not indexed as a verified school.</p>
        </fieldset>

      </form>

      <aside class="form-aside">
        <div class="preview">
          <div class="label">record.json &mdash; live</div>
          <pre id="preview">{{}}</pre>
        </div>
        <div class="form-actions">
          <button type="button" class="btn primary" id="download">Download the record</button>
          <button type="button" class="btn outline" id="copy">Copy JSON</button>
          <button type="button" class="btn outline" id="example">Load an example</button>
        </div>
        <div class="status-msg" id="status"></div>
        <div class="callout">
          <h3>What happens next</h3>
          <p>Send the file to your division's SSLG coordinator. The adviser attests to it, the
             division confirms the school exists, and the record's status changes from
             <em>Demo</em> to <em>Verified</em>. Until then it carries the amber badge.</p>
        </div>
        <div class="note">
          <strong>This page has no server.</strong> Everything you type stays in this tab. Closing
          it discards the draft &mdash; download the file first.
        </div>
      </aside>
    </div>
  </div>
</section>

<template id="tpl-activity">
  <div class="repeat-row" data-repeat="activity">
    <div class="row-head"><span>Activity</span><button type="button" data-remove>Remove</button></div>
    <div class="grid-3">
      <div class="field"><label>Title</label><input data-f="title" placeholder="Club Fair 2026"></div>
      <div class="field"><label>Date</label><input data-f="date" type="date"></div>
      <div class="field"><label>Kind</label><select data-f="kind">{kind_options}</select></div>
    </div>
    <div class="grid-3" style="margin-top:12px">
      <div class="field" style="grid-column:span 2"><label>Summary</label><input data-f="summary" placeholder="One sentence: what happened, who took part."></div>
      <div class="field"><label>Status</label><select data-f="status">{status_options}</select></div>
    </div>
  </div>
</template>

<template id="tpl-document">
  <div class="repeat-row" data-repeat="document">
    <div class="row-head"><span>Issuance</span><button type="button" data-remove>Remove</button></div>
    <div class="grid-3">
      <div class="field"><label>Number</label><input data-f="number" placeholder="001"></div>
      <div class="field"><label>Series</label><input data-f="series" inputmode="numeric" placeholder="2026"></div>
      <div class="field"><label>Type</label><select data-f="type">{doc_type_options}</select></div>
    </div>
    <div class="grid-3" style="margin-top:12px">
      <div class="field" style="grid-column:span 2"><label>Title</label><input data-f="title" placeholder="Establishment of LGCC Standing Committees"></div>
      <div class="field"><label>Date</label><input data-f="date" type="date"></div>
    </div>
    <div class="field" style="margin-top:12px"><label>Direction</label><select data-f="direction">{direction_options}</select></div>
  </div>
</template>

<template id="tpl-report">
  <div class="repeat-row" data-repeat="report">
    <div class="row-head"><span>Published report</span><button type="button" data-remove>Remove</button></div>
    <div class="grid-3">
      <div class="field"><label>Period</label><input data-f="period" placeholder="Quarter 1, SY 2026-2027"></div>
      <div class="field"><label>Published on</label><input data-f="published" type="date"></div>
      <div class="field"><label>Document</label><input data-f="type" value="Financial Report"></div>
    </div>
  </div>
</template>

<template id="tpl-club">
  <div class="repeat-row" data-repeat="club">
    <div class="row-head"><span>Club</span><button type="button" data-remove>Remove</button></div>
    <div class="grid-2">
      <div class="field"><label>Name</label><input data-f="name" placeholder="Mathematics Club"></div>
      <div class="field"><label>Cluster</label><select data-f="cluster">{cluster_options}</select></div>
    </div>
  </div>
</template>
"""
    return page("Submit a record — SSLG.ph", body, active="submit.html",
                desc="File an SSLG record as a single JSON document, in the browser.")


# ------------------------------------------------------------------ school pages
def build_school_home(school: dict) -> str:
    s = school["school"]
    acts = [a for a in school["activities"] if a.get("date")]
    acts.sort(key=lambda a: sort_key(a["date"]), reverse=True)
    cards = "".join(activity_card(a, school=school, root="../../", href="activities.html")
                    for a in acts[:4])
    clubs = school["clubs"]
    clusters = {c: [x for x in clubs if x["cluster"] == c] for c in "ABCD"}

    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="stats" style="margin-bottom:34px">
      <div class="stat"><b>{len(school['activities'])}</b><span>Activity records</span></div>
      <div class="stat"><b>{len(clubs)}</b><span>Recognized clubs</span></div>
      <div class="stat"><b>{len(school['documents'])}</b><span>Issuances</span></div>
      <div class="stat"><b>{len(school['finance']['reports'])}</b><span>Finance reports</span></div>
    </div>

    <div class="section-head">
      <div>
        <div class="eyebrow">Latest</div>
        <h2>Recent activities</h2>
      </div>
      <a class="more" href="activities.html">All {len(school['activities'])} records</a>
    </div>
    <div class="grid g4">{cards}</div>

    <div class="grid g2" style="margin-top:34px">
      <div class="callout">
        <h3>Learner government</h3>
        <p>School Year {e(school['sslg']['term'])} &middot; {len(school['sslg']['officers'])} officers
           &middot; {len(clubs)} recognized clubs in four clusters.</p>
        <p style="margin-top:10px"><a href="officers.html">Officers</a> &middot;
           <a href="clubs.html">Clubs</a></p>
      </div>
      <div class="callout">
        <h3>Record status</h3>
        <p>{record_badge(school)}</p>
        <p style="margin-top:8px">Last updated {fmt_date(school.get('updated'))}.
           {('Attested by the SSLG adviser on ' + fmt_date(school.get('verified_on')) + '.') if school.get('verified_on') else 'Not yet attested by the adviser.'}</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head">
      <div><div class="eyebrow">Clubs</div><h2>Four clusters</h2>
      <p>Every recognized club has one home, assigned at accreditation by primary purpose.</p></div>
      <a class="more" href="clubs.html">Full list</a>
    </div>
    <div class="grid g4">
      {''.join(f'''<div class="callout"><h3>{CLUSTERS[c][0]}</h3>
        <p style="margin-bottom:8px">{CLUSTERS[c][1]}</p>
        <p style="font-size:1.5rem;font-weight:700;color:var(--navy)">{len(clusters[c])}</p></div>''' for c in "ABCD")}
    </div>
  </div>
</section>
"""
    return school_page(school, "Overview", body, "index.html")


def build_school_officers(school: dict) -> str:
    rows = ""
    published = 0
    for off in school["sslg"]["officers"]:
        if off.get("name") and off.get("consent"):
            who = f'<span class="who">{e(off["name"])}</span>'
            published += 1
        else:
            who = '<span class="who withheld">Name withheld</span>'
        grade = (f' &middot; Grade {off["grade"]}'
                 if off.get("grade") and "grade" not in off["role"].lower() else "")
        rows += f'<div class="officer"><span class="role">{e(off["role"])}{grade}</span>{who}</div>'

    adviser = school["sslg"]["adviser"]
    if adviser.get("name") and adviser.get("consent"):
        adv = e(adviser["name"])
    else:
        adv = "Name withheld"

    total = len(school["sslg"]["officers"])
    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Officers</div>
    <h2 style="margin-bottom:8px">School Year {e(school['sslg']['term'])}</h2>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:26px">Roles are published.
       A learner's name appears only where a signed consent form is recorded.</p>

    <div class="stats" style="margin-bottom:30px">
      <div class="stat"><b>{total}</b><span>Officers</span></div>
      <div class="stat"><b>{published}</b><span>Names published</span></div>
      <div class="stat"><b>{published} of {total}</b><span>Consent on file</span></div>
      <div class="stat"><b>{fmt_date(school.get('verified_on'))}</b><span>Adviser attestation</span></div>
    </div>

    <div class="officers">{rows}</div>

    <div class="grid g2 start" style="margin-top:22px">
      <div class="callout">
        <h3>Adviser</h3>
        <p>{adv} &middot; {e(adviser.get('position', 'SSLG Adviser'))}</p>
      </div>
      <div class="callout">
        <h3>To publish a name</h3>
        <p>The school files a signed consent form for that learner, records
           <code>consent: true</code> against the role, and rebuilds. Nothing else changes.</p>
      </div>
    </div>

    <div class="note" style="margin-top:26px;max-width:860px">
      <strong>Why names are withheld.</strong> The officers of a learner government are minors.
      Publishing a roster with full names, grades and sections creates a searchable map of
      children, which is exactly what the Data Privacy Act exists to prevent. A school that
      collects consent can publish names; a school that has not, cannot.
    </div>
  </div>
</section>
"""
    return school_page(school, "Officers", body, "officers.html")


def build_school_activities(school: dict) -> str:
    acts = sorted(school["activities"], key=lambda a: sort_key(a["date"]), reverse=True)
    rows = ""
    for act in acts:
        rows += f"""
<tr>
  <td class="num">{fmt_date(act.get('date'))}</td>
  <td><strong>{e(act['title'])}</strong><span class="sub">{e(act.get('summary', ''))}</span></td>
  <td>{e(act.get('kind', '&mdash;'))}</td>
  <td>{status_badge(act['status'])}</td>
  <td class="num"><code>{e(act['id'])}</code></td>
</tr>"""
    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Records</div>
    <h2 style="margin-bottom:8px">{len(acts)} activities</h2>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:26px">Every activity the learner
       government has on file, with its record ID. Records without a confirmed date are kept
       but sorted last.</p>
    <div class="table-wrap">
      <table class="data">
        <thead><tr><th>Date</th><th>Activity</th><th>Kind</th><th>Status</th><th>Record</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</section>
"""
    return school_page(school, "Activities", body, "activities.html")


def build_school_documents(school: dict) -> str:
    issued = [d for d in school["documents"] if d.get("direction") == "issued"]
    received = [d for d in school["documents"] if d.get("direction") != "issued"]

    def table(items, empty):
        if not items:
            return f'<div class="empty">{empty}</div>'
        rows = ""
        for doc in sorted(items, key=lambda d: sort_key(d.get("date")), reverse=True):
            rows += f"""
<tr>
  <td><strong>{e(doc['number'])}</strong>{f", s. {doc['series']}" if doc.get('series') else ""}</td>
  <td>{e(doc['title'])}<span class="sub">{e(doc['type'])}</span></td>
  <td class="num">{fmt_date(doc.get('date'))}</td>
</tr>"""
        return f"""<div class="table-wrap"><table class="data">
<thead><tr><th>Number</th><th>Title</th><th>Date</th></tr></thead><tbody>{rows}</tbody></table></div>"""

    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Issuances</div>
    <h2 style="margin-bottom:24px">Documents</h2>

    <h3 style="font-size:1rem;margin-bottom:12px">Issued by this learner government</h3>
    {table(issued, "No issuances on file yet.")}

    <h3 style="font-size:1rem;margin:30px 0 12px">Received from higher offices</h3>
    {table(received, "No external issuances on file.")}

    <div class="note" style="margin-top:26px;max-width:760px">
      <strong>Publication standard.</strong> Only final issuances are published. Drafts,
      unnumbered memoranda and documents containing personal data stay in the school's own
      archive.
    </div>
  </div>
</section>
"""
    return school_page(school, "Documents", body, "documents.html")


def build_school_finance(school: dict) -> str:
    fin = school["finance"]
    last = max((r.get("published") for r in fin["reports"]), default=None)
    if fin["reports"]:
        rows = ""
        for rep in sorted(fin["reports"], key=lambda r: sort_key(r.get("published")), reverse=True):
            rows += f"""
<tr>
  <td><strong>{e(rep['period'])}</strong><span class="sub">{e(rep['type'])}</span></td>
  <td class="num">{fmt_date(rep.get('published'))}</td>
  <td><span class="badge completed">Published</span></td>
</tr>"""
        table = f"""<div class="table-wrap"><table class="data">
<thead><tr><th>Period</th><th>Published</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    else:
        table = '<div class="empty">No financial reports have been filed.</div>'

    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Accountability</div>
    <h2 style="margin-bottom:8px">Finance</h2>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:26px">The table records what was
       published and when. Figures are published in the report itself, not on this page.</p>

    <div class="stats" style="margin-bottom:26px">
      <div class="stat"><b>{len(fin['reports'])}</b><span>Reports published</span></div>
      <div class="stat"><b>{e(fin['frequency'])}</b><span>Stated frequency</span></div>
      <div class="stat"><b>{fmt_date(last)}</b><span>Last published</span></div>
      <div class="stat"><b>{fmt_date(school.get('updated'))}</b><span>Record updated</span></div>
    </div>

    {table}
    <div class="note" style="margin-top:26px;max-width:760px">
      <strong>Why only the dates.</strong> A transparency page that republishes numbers invites
      arguments about the numbers. A page that records <em>whether</em> a report was published,
      and when, is much harder to argue with &mdash; and it is the part that actually changes
      behaviour.
    </div>
  </div>
</section>
"""
    return school_page(school, "Finance", body, "finance.html")


def build_school_clubs(school: dict) -> str:
    clubs = school["clubs"]
    blocks = ""
    for key in "ABCD":
        items = [c for c in clubs if c["cluster"] == key]
        if not items:
            continue
        lis = "".join(f"<li>{e(c['name'])}</li>" for c in items)
        blocks += f"""
<div class="callout cluster-card">
  <div class="cluster-head">
    <span class="cluster-mark">{key}</span>
    <div>
      <h3>{CLUSTERS[key][0]}</h3>
      <p>{CLUSTERS[key][1]}</p>
    </div>
    <span class="n">{len(items)}</span>
  </div>
  <ul>{lis}</ul>
</div>"""

    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Clubs</div>
    <h2 style="margin-bottom:8px">{len(clubs)} recognized clubs and organizations</h2>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:22px">Grouped into four clusters
       for operations &mdash; fair booths, budget lines, monitoring reports. The cluster does not
       replace the category declared on the accreditation form.</p>

    <div class="cluster-key">
      {''.join(f'<span class="chip"><b>{c}</b> {CLUSTERS[c][0]} &mdash; {CLUSTERS[c][1]}</span>' for c in "ABCD")}
    </div>

    <div class="grid g2 start">{blocks}</div>

    <div class="note" style="max-width:760px;margin-top:26px">
      <strong>One club, one home.</strong> Assignment happens at accreditation, by primary
      purpose, and is recorded once. A club that wants to move clusters asks the Learner
      Government Coordinating Council, not the website.
    </div>
  </div>
</section>
"""
    return school_page(school, "Clubs", body, "clubs.html")


def build_school_photos(school: dict) -> str:
    photos = [a for a in school["activities"] if a.get("photo")]
    if photos:
        grid = "".join(
            f'<figure><img src="../../assets/photos/{e(a["photo"])}" alt="" loading="lazy">'
            f'<figcaption>{e(a["title"])} &middot; {fmt_date(a.get("date"))}</figcaption></figure>'
            for a in photos
        )
    else:
        grid = '<div class="empty" style="grid-column:1/-1">No photographs published for this record.</div>'

    body = f"""
<section class="section" style="border-bottom:0">
  <div class="wrap">
    <div class="eyebrow">Photos</div>
    <h2 style="margin-bottom:8px">Images from the record</h2>
    <p style="color:var(--muted);max-width:62ch;margin-bottom:26px">Each image is attached to the
       activity record it belongs to, never to a separate album that drifts out of date. Where
       no photograph exists, the record's own document cover stands in.</p>
    <div class="photo-grid">{grid}</div>
    <div class="note" style="margin-top:26px;max-width:860px">
      <strong>Consent rule.</strong> No class pictures, no section photos, no images of learners
      in distress. Event photographs are published only where the school has confirmed consent.
      The event images here come from the school's existing public site and must be re-confirmed
      before this build goes live &mdash; which is exactly the kind of check the platform is
      supposed to make routine.
    </div>
  </div>
</section>
"""
    return school_page(school, "Photos", body, "photos.html")


# ------------------------------------------------------------------ build
def main() -> None:
    schools: list[dict] = []
    problems: list[str] = []
    for path in sorted(DATA.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            problems.append(f"{path.name}: invalid JSON at line {err.lineno}: {err.msg}")
            continue
        problems.extend(validate_record(record, path))
        schools.append(record)

    if problems:
        print("The build stopped because a record is not valid:\n")
        for problem in problems:
            print("  -", problem)
        raise SystemExit(1)

    schools.sort(key=lambda s: s["school"]["name"])

    slugs: dict[str, str] = {}
    for school in schools:
        if school["slug"] in slugs:
            raise SystemExit(f"Two records share the slug '{school['slug']}'.")
        slugs[school["slug"]] = school["school"]["name"]

    divisions = division_groups(schools)
    written: dict[str, str] = {}
    for name in divisions:
        slug = slugify(name)
        if slug in written and written[slug] != name:
            raise SystemExit(
                f"Division names collide: '{written[slug]}' and '{name}' "
                f"both write to {slug}.html")
        written[slug] = name

    for index, school in enumerate(schools):
        school["_tone"] = index % 5

    if OUT.exists():
        try:
            shutil.rmtree(OUT)
        except PermissionError:
            # A preview server may hold the directory itself; clear what is inside instead.
            for child in OUT.iterdir():
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    (OUT / "assets").mkdir(parents=True)
    (OUT / "s").mkdir(parents=True)

    shutil.copy2(ASSETS / "style.css", OUT / "assets" / "style.css")
    shutil.copy2(ASSETS / "app.js", OUT / "assets" / "app.js")
    shutil.copy2(ASSETS / "submit.js", OUT / "assets" / "submit.js")

    PHOTO_DST.mkdir(parents=True, exist_ok=True)
    for src in PHOTO_SRC.glob("*.jpg"):
        shutil.copy2(src, PHOTO_DST / src.name)

    (OUT / "index.html").write_text(build_home(schools), encoding="utf-8")
    (OUT / "schools.html").write_text(build_directory(schools), encoding="utf-8")
    (OUT / "divisions.html").write_text(build_divisions(schools), encoding="utf-8")
    (OUT / "activities.html").write_text(build_activities(schools), encoding="utf-8")
    (OUT / "documents.html").write_text(build_documents(schools), encoding="utf-8")
    (OUT / "transparency.html").write_text(build_transparency(schools), encoding="utf-8")
    (OUT / "submit.html").write_text(build_submit(schools), encoding="utf-8")
    (OUT / "about.html").write_text(build_about(schools), encoding="utf-8")

    for school in schools:
        target = OUT / "s" / school["slug"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(build_school_home(school), encoding="utf-8")
        (target / "officers.html").write_text(build_school_officers(school), encoding="utf-8")
        (target / "activities.html").write_text(build_school_activities(school), encoding="utf-8")
        (target / "documents.html").write_text(build_school_documents(school), encoding="utf-8")
        (target / "finance.html").write_text(build_school_finance(school), encoding="utf-8")
        (target / "clubs.html").write_text(build_school_clubs(school), encoding="utf-8")
        (target / "photos.html").write_text(build_school_photos(school), encoding="utf-8")

    div_dir = OUT / "divisions"
    div_dir.mkdir(parents=True, exist_ok=True)
    for name, members in divisions.items():
        (div_dir / f"{slugify(name)}.html").write_text(
            build_division(name, members), encoding="utf-8")

    pages = len(list(OUT.rglob("*.html")))
    print(f"Built {pages} pages for {len(schools)} schools in {len(divisions)} divisions -> {OUT}")


if __name__ == "__main__":
    main()
