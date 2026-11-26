# SSLG Website Design Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the SSLG site on Cloudflare Pages so it carries the published Google Sites identity — full-bleed navy hero with gold beams, mint content bands, Gentium headings, white action bars — and finishes all seven pages with the current published content.

**Architecture:** The existing Vite/React app and its Drive proxy stay. This plan replaces the provisional parchment design system with the measured Google Sites system, adds the official seals, portraits and artwork as local assets, and composes every route from four primitives: `Band`, `PageHero`/`HomeHero`, `SectionTitle` and `CtaBar`. Content stays in typed modules; albums, photos and document files still come from `/api/*` with KV caching.

**Tech Stack:** Vite 8 · React 19 · TypeScript · React Router 7 · Cloudflare Pages Functions · Workers KV · Google Drive API v3 · Fontsource (Gentium Book Plus, Montserrat, IBM Plex Sans/Mono) · Vitest + jsdom.

**Spec:** The design analysis in this file is the spec. This plan **supersedes Tasks 5–10** of `docs/superpowers/plans/2026-11-08-cloudflare-migration.md`; that plan's Drive contracts, security constraints and deploy commands remain in force. Design guidance comes from Jakub Krehel's `skills` repository (`build-design`, `better-ui`, `better-layout`, `better-typography`, `better-colors`, `better-accessibility`, `better-interface`, `interface-review`) and motion vocabulary from `uiverse-io/galaxy` (MIT).

---

## Global Constraints

- All site code lives in `C:\Users\Ma Christine\Downloads\WEBSITES\sslg`. The only files written into the vault are plans and reports.
- Drive stays read-only. Never upload, move, rename, or change permissions on anything in Drive.
- Never commit a Google credential. `GOOGLE_API_KEY` exists only as a Cloudflare secret and in a gitignored `.dev.vars`.
- **No Google API key exists in this session.** Every Drive-backed page must therefore have a designed, tested loading, empty and error state, and a static Drive-folder fallback link. Live Drive counts and KV hits remain owner-verified.
- Do not invent dates, names, amounts or outcomes. Every string rendered must exist in the published site or in the vault.
- Keep the published routes: `/`, `/finance`, `/accomplishments`, `/transparency`, `/about-us`, `/feedback`; add `/photos` and `/accomplishments/:slug`. Keep nav order Home · Finance · Accomplishments · **Photos** · Transparency · About us · Feedback.
- **Visual identity is fixed by the live Google Sites.** Navy `#02133e`, title-band gradient `#141953 → #02133e`, raised panel `#08205d`, mint `#d0e0e3`, ink `#0a1c3d`, paper `#f9f9f9`, gold beams `#b98a4a → #e8c98f`, gold accent `#c9a227`. Gentium headings, heavy grotesque wordmark, white bars. Do not introduce a second brand, a light theme, or a different palette.
- All color reaches components through semantic tokens in `tokens.css`; no raw hex in component CSS.
- Type floors: body and controls 16px, captions 14px, labels 13px. Line-height ≥1.5 for body, 1.2–1.3 for headings, 0.92 only for the four-line hero wordmark. Long-form measure ≤68ch.
- Contrast: body and control text ≥4.5:1; large text ≥3:1; focus ring and control edges ≥3:1. Measured pairs are listed in Task 1.
- Every pointer interaction has a keyboard path. Every motion is inside `@media (prefers-reduced-motion: no-preference)`. Hover effects are inside `@media (hover: hover)`.
- No new runtime dependencies except the three font packages. No CSS framework, no icon library, no animation library, no external images at runtime other than Drive thumbnails and the Google Form iframe.
- Portraits are the school's already-published images. Reuse them unchanged except for CSS framing; add no student data that is not already published.
- Uiverse Galaxy code is MIT; adapted snippets carry a source comment and a line in `docs/CREDITS.md`.
- Deploy with `npm run deploy` (it passes `--branch main`). Verify with `.superpowers/shots/cdp-shot.mjs` at 1440 and 390; Windows Chrome crops rather than reflows, so the CDP override is mandatory for narrow widths.

---

## Source analysis (measured from the live site on 2026-11-08)

| Property | Measured value | Source |
| --- | --- | --- |
| Content column | 1152px at 1440 viewport (144px margins) | `home-1440.json`, screenshots |
| Home hero | ~1180px tall at 1440 (≈100vh), transparent header overlay | `home-1440.png` |
| Subpage title band | ~204px (title band top → white rule) | `accomplishments-1440.png` |
| Transparent header | 66px, seal 40px + “BSANHS” serif, nav 16px white | `home-1440.png` |
| Hero lockup | 2 seals 84px stacked, 1px white rule, 4-line wordmark ~300×220 | `assets/lockup-zoom.jpg` |
| Hero wordmark | Montserrat-class heavy grotesque, solid white, 4 lines, tight leading | `assets/img2.png` |
| School line / year | Gentium caps, ~13px, letterspaced | `assets/lockup-zoom.jpg` |
| H1 | Gentium Basic 700, 45.33px / 62.56px (1.38), `#f9f9f9` | page audits |
| H2 | Gentium Basic 700, 24px / 36px | page audits |
| H3 | Gentium Basic 700, 18.67px / 22.4px | About audit |
| Body / captions | sans (Roboto), 13–14px on Google Sites | screenshots |
| Title band | vertical gradient `#141953` → `#02133e`, white rule at bottom | sampled |
| Mint band | `#d0e0e3` | sampled |
| Raised navy band | `#08205d` | sampled |
| Footer | `#02133e`, seal + full name + white Facebook bar | screenshot |
| White bars | paper `#f9f9f9`, navy 13px caps, 36px tall | screenshots |
| Gold beams | warm `#b98a4a` → `#e8c98f`, two crossing diagonals | sampled |
| Destination art | 3 transparent PNG illustrations (award, folder, clipboard) | `assets/img5–7.png` |
| Portraits | 27 × 1080px, baked nameplates, graded blue background | `assets/about/p02–p28.jpg` |
| Feedback | Google Form, 2 pages, same form ID as `FEEDBACK_FORM_URL` | `feedback-1440.png` |

### Measured contrast pairs (WCAG 2.2)

| Pair | Ratio | Verdict |
| --- | --- | --- |
| `#f9f9f9` on `#02133e` | 17.12:1 | AA/AAA |
| `#d0e0e3` on `#02133e` | 13.26:1 | AA/AAA |
| `#08205d` on `#d0e0e3` | 11.24:1 | AA/AAA |
| `#ffffff` on `#08205d` | 15.27:1 | AA/AAA |
| `#0a1c3d` on `#d0e0e3` | 12.40:1 | AA/AAA |
| `#c9a227` on `#02133e` | 7.45:1 | AA |
| `#b98a4a` on `#02133e` | 5.83:1 | AA |

### Deliberate deviations from Google Sites (quality, not taste)

| Google Sites | This build | Why |
| --- | --- | --- |
| Hero lockup is a 1280px raster with baked type | HTML + CSS lockup using the two official seals | Crisp at every density, readable on mobile, ~1.6MB lighter |
| Hero background is a raster | CSS beams and glows | Scales to any viewport, no asset decode cost |
| Card captions centered at 13px | Left-aligned 15px, measure capped | Centered multi-line body text is slow to read and fails the measure rule |
| Body copy ~13px | 16px | WCAG 1.4.4 / size floor |
| Nav wraps to 2–3 rows at 390px, or hides behind a search icon | 44px menu button + disclosure panel | Predictable keyboard path, no clipped labels at 320px |
| Six repeated stock “READ HERE” document images | One CSS document plate per card, Drive thumbnails when available | Repetition reads as placeholder; a plate is lighter and consistent |
| Finance shows a raw Drive URL as a link | “Open the report” action bar + folder fallback | Raw URLs are not a control |
| No Photos page | `/photos` with albums and a lightbox | Already promised in the migration plan; photos live in Drive |
| Title-case `Read More` bars | Sentence-case labels; uppercase only for 13px section labels | Screen text reads naturally; caps stay a label style |
| Portraits include baked names/roles | Baked nameplate cropped away; HTML name/role below | The published text is authoritative and must be selectable |

### Uiverse Galaxy shortlist (MIT, adapted — not copied wholesale)

| Source | Take | Used on |
| --- | --- | --- |
| `Buttons/Codecite_angry-bullfrog-58.html` | Top inner shine + inset bottom light on a solid fill | `.btn--primary` (hero, About, Finance) |
| `Buttons/neerajbaniwal_hungry-mule-59.html` | A single specular sweep across text/background, run on hover only | `.cta-bar::after` (white bars) |
| `Cards/gharsh11032000_rare-bobcat-17.html` | 1.03 lift + top scrim on hover, `cubic-bezier(.23,1,.32,1)` | `.activity-card` |
| `loaders/abrahamcalsin_serious-turkey-52.html` | Eight-dot pulse spinner | `.loader` for albums/documents |

Every one is re-authored against our tokens, gated by `(hover: hover)` and `prefers-reduced-motion: no-preference`, and credited in `docs/CREDITS.md`.

---

## Asset inventory (copy once in Task 2)

| Destination | Source | Treatment |
| --- | --- | --- |
| `public/brand/seal-sslg.png` | `.superpowers/shots/gsites/assets/img0.png` | 200×200, copy as-is |
| `public/brand/seal-school.png` | crop `(95, 250, 356, 520)` of `assets/img2.png` | 261×270, trim alpha |
| `public/brand/officers/<slug>.webp` | `assets/about/p02.jpg` … `p28.jpg` | 720px, WebP q82, order = officer order |
| `public/media/inkantations-2026.webp` | `assets/img3.jpg` | 1080px, WebP q82 |
| `public/media/induction-2026.webp` | `assets/img4.jpg` | 1280px, WebP q82 |
| `public/media/destination-accomplishments.webp` | `assets/img5.png` | 480px, WebP alpha |
| `public/media/destination-transparency.webp` | `assets/img6.png` | 480px, WebP alpha |
| `public/media/destination-finance.webp` | `assets/img7.png` | 480px, WebP alpha |
| `public/og.png` | lockup bbox `(102, 297, 1267, 825)` of `img2.png` on navy | 1200×630 |

The source files live in `WEBSITES/sslg/.superpowers/shots/gsites/assets/` at plan time. They are git-ignored scratch; Task 2 copies them into `public/` and commits the result. Do not re-download from `sitesv-images-rt` URLs — they expire.

---

## File structure

```
src/
  components/
    SiteLayout.tsx        masthead, mobile disclosure, main, footer
    Hero.tsx              HomeHero + PageHero + Beams
    Band.tsx              Band, SectionTitle, CtaBar, Rail
    ActivityCard.tsx
    SmartImage.tsx        skeleton, fade-in, ruled error fallback
    PhotoGrid.tsx         thumbnail grid + lightbox
    AlbumViewer.tsx       inline album panel (skeleton/empty/error/grid)
    DocumentList.tsx      file rows (skeleton/empty/error/fallback link)
    DocumentPlate.tsx     CSS document card art
    Stat.tsx
    EmptyState.tsx
  lib/
    api.ts                getJson
    useAlbums.ts          module-cached album tree
    useDocuments.ts       per-folder cached list
    format.ts             date + filename helpers
  content/
    types.ts              Cover gains `image`; Officer gains `photo`; DocumentGroup gains `folderUrl`
    activities.ts         11 entries, INKantations featured
    officers.ts           27 officers + derived photo paths
    documents.ts          6 groups + folder URLs
    finance.ts            report + 3 stats
    site.ts               mandate, objectives, duties, about intro, legal bases
  pages/
    Home.tsx  Accomplishments.tsx  ActivityPage.tsx  Photos.tsx
    Finance.tsx  Transparency.tsx  About.tsx  Feedback.tsx  NotFound.tsx
  styles/
    tokens.css            semantic tokens only
    base.css              fonts, reset, type scale, focus, motion
    components.css        shell, hero, bands, cards, bars
    pages.css             page-specific composition
    responsive.css        container queries and narrow-width rules
public/
  brand/  media/  og.png  _redirects  _headers  robots.txt
docs/
  CREDITS.md              Uiverse attribution
```

---

### Task 1: Replace the design system with the SSLG identity

**Files:**
- Modify: `package.json` (fonts)
- Rewrite: `src/styles/tokens.css`, `base.css`, `components.css`, `pages.css`, `responsive.css`
- Create: `src/components/Band.tsx`
- Modify: `index.html` (`theme-color`)
- Test: `tests/design.test.tsx`

**Interfaces:**
- Produces: `Band`, `SectionTitle`, `CtaBar` and the full token set every later task uses.

- [ ] **Step 1: Swap the fonts**

```bash
cd "C:/Users/Ma Christine/Downloads/WEBSITES/sslg"
npm uninstall @fontsource/instrument-serif
npm install @fontsource/gentium-book-plus@^5.3.0 @fontsource/montserrat@^5.3.0
```

Remove the Instrument Serif import from `base.css`. `@fontsource/gentium-book-plus` ships `latin-400.css` and `latin-700.css`; `@fontsource/montserrat` ships `latin-800.css`.

- [ ] **Step 2: Write `tokens.css` exactly**

```css
:root {
  /* Primitives — navy */
  --navy-950: #02133e;
  --navy-900: #061a4a;
  --navy-850: #141953;
  --navy-800: #08205d;
  --navy-700: #0d2a6e;
  --navy-line: #1b3570;

  /* Primitives — mint */
  --mint-100: #d0e0e3;
  --mint-200: #bfd2d6;

  /* Primitives — gold */
  --gold-300: #e8c98f;
  --gold-500: #c9a227;
  --gold-600: #b98a4a;

  /* Neutrals */
  --paper: #f9f9f9;
  --white: #ffffff;
  --ink: #0a1c3d;
  --ink-soft: #2b4166;

  /* Semantic — surfaces and text */
  --bg-page: var(--navy-950);
  --bg-title: var(--navy-850);
  --bg-panel: var(--navy-800);
  --bg-band: var(--mint-100);
  --bg-bar: var(--paper);
  --text-dark: var(--paper);
  --text-light: var(--ink);
  --link-underline-dark: color-mix(in srgb, var(--gold-300) 70%, transparent);
  --link-underline-light: color-mix(in srgb, var(--navy-950) 55%, transparent);
  --text-muted-dark: #b9c6dd;
  --text-muted-light: #3a4f70;
  --border-dark: rgba(249, 249, 249, 0.16);
  --border-light: rgba(10, 28, 61, 0.16);
  --accent: var(--gold-500);
  --accent-soft: var(--gold-300);
  --focus-on-dark: var(--gold-300);
  --focus-on-light: var(--navy-950);
  --on-accent: var(--navy-950);

  /* Type */
  --font-display: "Gentium Book Plus", Gentium, Georgia, serif;
  --font-wordmark: "Montserrat", "Archivo Black", system-ui, sans-serif;
  --font-ui: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, "Cascadia Mono", monospace;

  --text-xs: 0.8125rem;   /* 13 */
  --text-sm: 0.875rem;    /* 14 */
  --text-base: 1rem;      /* 16 */
  --text-lg: 1.125rem;    /* 18 */
  --text-xl: 1.375rem;    /* 22 */
  --text-h3: 1.1667rem;   /* 18.67 */
  --text-h2: clamp(1.375rem, 1.6vw, 1.5rem);
  --text-h1: clamp(2rem, 3.2vw, 2.833rem); /* 32 → 45.33 */
  --text-wordmark: clamp(2.25rem, 4vw, 3.25rem);

  /* Space — 4px base */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;
  --space-8: 4rem;
  --space-9: 6rem;

  /* Layout */
  --page-max: 1152px;
  --gutter: clamp(1.25rem, 5vw, 1.5rem);
  --measure: 68ch;
  --header-h: 72px;
  --hero-min: clamp(560px, calc(100svh - var(--header-h)), 980px);
  --title-h: clamp(200px, 18vw, 240px);
  --radius-sm: 3px;
  --radius-md: 8px;
  --shadow-panel: 0 18px 40px -24px rgba(2, 19, 62, 0.7);
  --ease-out: cubic-bezier(0.2, 0, 0, 1);
  --ease-card: cubic-bezier(0.23, 1, 0.32, 1);
}
```

- [ ] **Step 3: Rewrite `base.css`**

Keep the reset, `sr-only`, link reset and reduced-motion block from the current file. Replace fonts, body ground, type scale and focus:

```css
@import "@fontsource/gentium-book-plus/latin-400.css";
@import "@fontsource/gentium-book-plus/latin-700.css";
@import "@fontsource/montserrat/latin-800.css";
@import "@fontsource/ibm-plex-sans/latin-400.css";
@import "@fontsource/ibm-plex-sans/latin-500.css";
@import "@fontsource/ibm-plex-sans/latin-600.css";
@import "@fontsource/ibm-plex-mono/latin-500.css";

html {
  color-scheme: light;
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
  scroll-padding-block-start: calc(var(--header-h) + var(--space-4));
}
@media (prefers-reduced-motion: no-preference) {
  html { scroll-behavior: smooth; }
}

body {
  margin: 0;
  min-height: 100vh;
  background: var(--bg-page);
  color: var(--text-dark);
  font-family: var(--font-ui);
  font-size: var(--text-base);
  line-height: 1.6;
  font-synthesis-weight: none;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: clip;
}

h1, h2, h3 {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.005em;
  text-wrap: balance;
}
h1 { font-size: var(--text-h1); line-height: 1.2; }
h2 { font-size: var(--text-h2); line-height: 1.3; }
h3 { font-size: var(--text-h3); line-height: 1.3; }

p { margin: 0; text-wrap: pretty; }

a {
  color: inherit;
  text-decoration-line: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  text-decoration-color: var(--link-underline-dark);
}

/* Gold is invisible on mint and paper; flip the underline, not the text. */
.band--mint a,
.band--paper a {
  text-decoration-color: var(--link-underline-light);
}

:where(a, button, input, select, textarea, summary, [tabindex]):focus-visible {
  outline: 2px solid var(--focus-on-dark);
  outline-offset: 3px;
}

/* Light bands flip the ring. */
.band--mint :where(a, button, input, select, textarea, summary, [tabindex]):focus-visible,
.band--paper :where(a, button, input, select, textarea, summary, [tabindex]):focus-visible {
  outline-color: var(--focus-on-light);
}

::selection { background: var(--gold-300); color: var(--on-accent); }

.skip-link {
  position: fixed;
  inset-block-start: var(--space-3);
  inset-inline-start: var(--space-3);
  z-index: 100;
  transform: translateY(-200%);
  padding: 0.7rem 1rem;
  background: var(--bg-bar);
  color: var(--on-accent);
  font-size: var(--text-base);
  font-weight: 600;
  text-decoration-color: var(--link-underline-light);
  border-radius: var(--radius-sm);
  transition: transform 150ms var(--ease-out);
}
.skip-link:focus { transform: translateY(0); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 4: Write `Band.tsx`**

```tsx
import type { ReactNode } from "react";

type Variant = "navy" | "mint" | "deep" | "paper";

export function Band({
  variant = "navy",
  className = "",
  id,
  children,
}: {
  variant?: Variant;
  className?: string;
  id?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className={`band band--${variant} ${className}`.trim()}>
      <div className="band__inner">{children}</div>
    </section>
  );
}

export function SectionTitle({
  title,
  lead,
  as: Heading = "h2",
}: {
  title: string;
  lead?: string;
  as?: "h2" | "h3";
}) {
  return (
    <header className="section-title">
      <Heading>{title}</Heading>
      {lead ? <p>{lead}</p> : null}
    </header>
  );
}

export function CtaBar({
  href,
  children,
  external = false,
}: {
  href: string;
  children: ReactNode;
  external?: boolean;
}) {
  return (
    <a
      className="cta-bar"
      href={href}
      {...(external ? { target: "_blank", rel: "noreferrer" } : {})}
    >
      <span>{children}</span>
    </a>
  );
}
```

`CtaBar` must stay an `<a>` — for internal routes the page passes `href`; React Router does not intercept these bars, which is acceptable because a full load is rare and the routes are static. If a later task needs client-side navigation, wrap with `useNavigate`; do not turn it into a `<div>`.

- [ ] **Step 5: Write the shell CSS in `components.css`**

```css
.site { display: flex; flex-direction: column; min-height: 100svh; background: var(--bg-page); }
.site-main { flex: 1 0 auto; }

.band { padding-block: clamp(2.5rem, 5vw, 4.5rem); }
.band--navy { background: var(--bg-panel); color: var(--text-dark); }
.band--deep { background: var(--bg-page); color: var(--text-dark); }
.band--mint { background: var(--bg-band); color: var(--text-light); }
.band--paper { background: var(--bg-bar); color: var(--text-light); }
.band__inner {
  width: 100%;
  max-width: var(--page-max);
  margin-inline: auto;
  padding-inline: var(--gutter);
}

.section-title { display: grid; gap: var(--space-1); margin-block-end: clamp(1.5rem, 3vw, 2.5rem); }
.section-title h2, .section-title h3 { color: inherit; }
.section-title p {
  max-width: var(--measure);
  color: var(--text-muted-dark);
  font-size: var(--text-sm);
}
.band--mint .section-title p, .band--paper .section-title p { color: var(--text-muted-light); }

.cta-bar {
  --bar-h: 48px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: var(--bar-h);
  padding-inline: var(--space-5);
  overflow: hidden;
  background: var(--bg-bar);
  color: var(--on-accent);
  font-size: var(--text-base);
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: 0.01em;
  text-align: center;
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: background-color 180ms var(--ease-out), color 180ms var(--ease-out);
}
.cta-bar > span { position: relative; z-index: 1; }
/* Adapted from uiverse.io by neerajbaniwal (MIT) */
.cta-bar::after {
  content: "";
  position: absolute;
  inset-block: 0;
  inset-inline-start: -60%;
  width: 40%;
  background: linear-gradient(100deg, transparent, color-mix(in srgb, var(--white) 85%, transparent), transparent);
  transform: skewX(-18deg);
  opacity: 0;
}
@media (hover: hover) and (prefers-reduced-motion: no-preference) {
  .cta-bar:hover::after {
    animation: bar-sweep 700ms var(--ease-out);
  }
}
@keyframes bar-sweep {
  from { inset-inline-start: -60%; opacity: 0; }
  20% { opacity: 0.9; }
  to { inset-inline-start: 120%; opacity: 0; }
}
@media (hover: hover) {
  .cta-bar:hover { background: var(--gold-300); color: var(--navy-950); }
}
```

`letter-spacing` stays small because the published bars use sentence case in this build, not caps.

- [ ] **Step 6: Set the theme color**

In `index.html`, change `theme-color` to `#02133e` and `color-scheme` to `light` (the page is dark, but form controls inside the mint bands should stay light). Keep `meta name="color-scheme" content="light"`; set `theme-color` only.

- [ ] **Step 7: Test the primitives**

```tsx
// tests/design.test.tsx
import { render, screen } from "@testing-library/react";
import { Band, CtaBar, SectionTitle } from "../src/components/Band";

test("a band exposes its variant, title and lead", () => {
  render(
    <Band variant="mint">
      <SectionTitle title="Latest" lead="Stay updated." />
    </Band>,
  );
  const band = screen.getByRole("region", { name: "" });
  expect(band.className).toContain("band--mint");
  expect(screen.getByRole("heading", { level: 2, name: "Latest" })).toBeInTheDocument();
  expect(screen.getByText("Stay updated.")).toBeInTheDocument();
});

test("a CTA bar is a link with one accessible name", () => {
  render(<CtaBar href="/accomplishments">Read more accomplishment reports</CtaBar>);
  const link = screen.getByRole("link", { name: "Read more accomplishment reports" });
  expect(link).toHaveAttribute("href", "/accomplishments");
  expect(link.className).toContain("cta-bar");
});
```

The `region` role requires a name; if the test cannot find it, query `.band` with `container.querySelector` instead — do not add `aria-label` to every band. Use `container` from `render`.

- [ ] **Step 8: Run and commit**

```bash
npm test -- tests/design.test.tsx
npm run build
git add -A
git commit -m "feat: replace parchment tokens with the SSLG navy and mint design system"
```

---

### Task 2: Official assets, hero, masthead and footer

**Files:**
- Create: `public/brand/*`, `public/media/*`, `public/og.png`
- Create: `src/components/Hero.tsx`
- Rewrite: `src/components/SiteLayout.tsx`, `src/styles/components.css` (shell section only)
- Modify: `index.html`
- Test: `tests/layout.test.tsx` (rewrite)

**Interfaces:**
- Produces: `<HomeHero />`, `<PageHero title lead />`, `<SiteLayout />` with a mobile disclosure; asset paths used by every page.

- [ ] **Step 1: Prepare the assets**

Run from the repo root. `PIL` is available on this machine; if it is not, stop and report rather than substituting different artwork.

```bash
python -X utf8 - <<'PY'
from PIL import Image
import os, shutil
src = '.superpowers/shots/gsites/assets'
os.makedirs('public/brand/officers', exist_ok=True)
os.makedirs('public/media', exist_ok=True)

shutil.copyfile(f'{src}/img0.png', 'public/brand/seal-sslg.png')

hero = Image.open(f'{src}/img2.png').convert('RGBA')
hero.crop((95, 250, 356, 520)).save('public/brand/seal-school.png')

def slug(name):
    import re
    s = re.sub(r'^hon\.\s*', '', name.strip().lower())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

names = [
 "Hon. Rhian Jade L. Castro","Hon. Aaron Y. Hernandez","Hon. Micaella Sabelle R. Monloy",
 "Hon. Sophia Elise C. Aguas","Hon. Samantha Joy C. De Venecia","Hon. Diyah Marowe T. Hipolito",
 "Hon. Ian Kendrick M. Lapuz","Hon. Rajon Landolf F. Lobo","Hon. Yuan B. Cutiongco",
 "Hon. Blu Enno U. Sampang","Hon. Godswill Jobel D. Noe","Hon. Akio Nathan C. Manlapaz",
 "Hon. Rommel S. Dizon, Jr.","Hon. Vince Yael P. Garin","Hon. Juliana Bea Q. De Guzman",
 "Hon. Josh Edan D. Porlucas","Hon. Zyrene Gale W. Tinio","Hon. Chloe Danielle L. David",
 "Hon. Kean Albert J. Pineda","Dr. Amparo M. Munoz","Hon. Gilbert Policarpio",
 "Hon. Aaron Khristian Banag","Hon. Christopher Kabilangan","Hon. Jayvee Zarate",
 "Hon. Mary Joy Santos","Hon. Ma Theresa Gatchalian","Hon. Mira Narciso",
]
for i, name in enumerate(names, start=2):
    im = Image.open(f'{src}/about/p{i:02d}.jpg').convert('RGB')
    im.thumbnail((720, 720), Image.LANCZOS)
    im.save(f'public/brand/officers/{slug(name)}.webp', 'WEBP', quality=82, method=6)

def webp(src_path, out, max_w):
    im = Image.open(src_path).convert('RGBA')
    im.thumbnail((max_w, max_w), Image.LANCZOS)
    im.save(out, 'WEBP', quality=82, method=6, lossless=False)

webp(f'{src}/img3.jpg', 'public/media/inkantations-2026.webp', 1080)
webp(f'{src}/img4.jpg', 'public/media/induction-2026.webp', 1280)
webp(f'{src}/img5.png', 'public/media/destination-accomplishments.webp', 480)
webp(f'{src}/img6.png', 'public/media/destination-transparency.webp', 480)
webp(f'{src}/img7.png', 'public/media/destination-finance.webp', 480)

lock = hero.crop((102, 297, 1267, 825))
og = Image.new('RGBA', (1200, 630), (2, 19, 62, 255))
scale = 500 / lock.height
lock = lock.resize((int(lock.width * scale), 500), Image.LANCZOS)
og.alpha_composite(lock, ((1200 - lock.width) // 2, (630 - lock.height) // 2))
og.convert('RGB').save('public/og.png', optimize=True)
print('assets ready:', len(os.listdir('public/brand/officers')), 'portraits')
PY
rm -f public/favicon.svg public/icon.svg
```

Expected: 27 portraits, 5 media files, 2 seals, `og.png`.

- [ ] **Step 2: Point the document at the seal and OG image**

In `index.html`:

```html
<link rel="icon" type="image/png" href="/brand/seal-sslg.png" />
<link rel="apple-touch-icon" href="/brand/seal-sslg.png" />
<meta property="og:image" content="https://sslg-2sr.pages.dev/og.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="Supreme Secondary Learner Government wordmark with the BSANHS and SSLG seals" />
<meta property="og:locale" content="en_PH" />
```

- [ ] **Step 3: Build the hero**

`src/components/Hero.tsx`:

```tsx
import type { ReactNode } from "react";

export function Beams() {
  return (
    <div className="beams" aria-hidden="true">
      <span className="beam beam--a" />
      <span className="beam beam--b" />
      <span className="beam-glow beam-glow--a" />
      <span className="beam-glow beam-glow--b" />
    </div>
  );
}

export function HomeHero() {
  return (
    <section className="hero hero--home" aria-labelledby="hero-title">
      <Beams />
      <div className="hero__lockup">
        <div className="hero__seals">
          <img src="/brand/seal-school.png" alt="" width="84" height="84" />
          <img src="/brand/seal-sslg.png" alt="" width="84" height="84" />
        </div>
        <span className="hero__rule" aria-hidden="true" />
        <div className="hero__type">
          <p className="hero__school">Benigno S. Aquino National High School</p>
          <h1 id="hero-title" className="hero__wordmark">
            Supreme<br />Secondary<br />Learner<br />Government
          </h1>
          <p className="hero__year">School Year 2026–2027</p>
        </div>
      </div>
      <a className="hero__scroll" href="#latest" aria-label="Skip to the latest news">
        <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false">
          <path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </a>
    </section>
  );
}

export function PageHero({
  title,
  lead,
  children,
}: {
  title: string;
  lead?: string;
  children?: ReactNode;
}) {
  return (
    <section className="hero hero--page" aria-labelledby="page-title">
      <Beams />
      <div className="hero__page-inner">
        <h1 id="page-title">{title}</h1>
        {lead ? <p className="hero__lead">{lead}</p> : null}
        {children}
      </div>
    </section>
  );
}
```

Rules: Home has exactly one `h1` (the wordmark). Every subpage’s `PageHero` is its only `h1`. Never render two `PageHero`s on one page.

- [ ] **Step 4: Style the hero**

```css
.beams {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(55% 65% at 72% 34%, rgba(43, 84, 178, 0.55), transparent 62%),
    radial-gradient(45% 55% at 16% 84%, rgba(26, 63, 150, 0.42), transparent 68%),
    linear-gradient(180deg, #091449 0%, var(--navy-950) 58%, var(--navy-950) 100%);
}
.beam {
  position: absolute;
  inset-inline: -20%;
  height: 1.5px;
  background: linear-gradient(90deg, transparent 4%, rgba(185, 138, 74, 0.1) 22%, var(--gold-300) 48%, rgba(232, 201, 143, 0.15) 72%, transparent 96%);
  opacity: 0.85;
}
.beam--a { inset-block-start: 24%; transform: rotate(-13deg); }
.beam--b { inset-block-start: 79%; transform: rotate(8deg); }
.beam-glow {
  position: absolute;
  inset-inline: -20%;
  height: 160px;
  filter: blur(34px);
  background: radial-gradient(50% 50% at 50% 50%, rgba(201, 162, 39, 0.28), transparent 72%);
}
.beam-glow--a { inset-block-start: 18%; }
.beam-glow--b { inset-block-start: 74%; }

.hero { position: relative; isolation: isolate; display: grid; place-items: center; overflow: hidden; background: var(--navy-950); color: var(--text-dark); }
.hero--home { min-height: var(--hero-min); padding-block: var(--space-8) var(--space-9); }
.hero--page {
  min-height: var(--title-h);
  padding-block: calc(var(--header-h) * 0.15) var(--space-6);
  border-block-end: 1px solid rgba(249, 249, 249, 0.55);
  background: linear-gradient(180deg, var(--bg-title) 0%, var(--navy-950) 100%);
}
.hero__page-inner { width: 100%; max-width: var(--page-max); padding-inline: var(--gutter); text-align: center; }
.hero--page h1 { font-size: var(--text-h1); line-height: 1.2; letter-spacing: 0.055em; text-transform: uppercase; }
.hero__lead { max-width: 58ch; margin: var(--space-3) auto 0; color: var(--text-muted-dark); font-size: var(--text-base); }

.hero__lockup {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: auto 1px auto;
  gap: clamp(1.25rem, 3vw, 2.25rem);
  align-items: center;
  padding-inline: var(--gutter);
}
.hero__seals { display: grid; gap: var(--space-3); justify-items: center; }
.hero__seals img { width: clamp(56px, 5.8vw, 84px); height: auto; }
.hero__rule { width: 1px; align-self: stretch; background: rgba(249, 249, 249, 0.85); }
.hero__type { display: grid; gap: var(--space-2); }
.hero__school,
.hero__year {
  font-family: var(--font-display);
  font-size: clamp(0.7rem, 0.9vw, 0.8125rem);
  line-height: 1.3;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.hero__wordmark {
  font-family: var(--font-wordmark);
  font-size: var(--text-wordmark);
  font-weight: 800;
  line-height: 0.92;
  letter-spacing: -0.005em;
  text-transform: uppercase;
  color: var(--white);
}
.hero__year { color: var(--text-muted-dark); }

.hero__scroll {
  position: absolute;
  inset-block-end: var(--space-5);
  inset-inline-start: 50%;
  translate: -50% 0;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  color: var(--paper);
  border-radius: 50%;
  opacity: 0.85;
}
@media (prefers-reduced-motion: no-preference) {
  .hero__scroll svg { animation: nudge 2.4s var(--ease-out) infinite; }
}
@keyframes nudge {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(4px); }
}
```

At ≤560px, turn `.hero__lockup` into one column with the seals in a row and the rule hidden:

```css
@media (max-width: 560px) {
  .hero__lockup { grid-template-columns: 1fr; justify-items: start; gap: var(--space-5); }
  .hero__seals { grid-auto-flow: column; gap: var(--space-4); }
  .hero__rule { display: none; }
}
```

- [ ] **Step 5: Rewrite `SiteLayout`**

```tsx
import { useEffect, useId, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { FACEBOOK_URL } from "../config";

const NAV = [
  ["/", "Home"],
  ["/finance", "Finance"],
  ["/accomplishments", "Accomplishments"],
  ["/photos", "Photos"],
  ["/transparency", "Transparency"],
  ["/about-us", "About us"],
  ["/feedback", "Feedback"],
] as const;

export function SiteLayout() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const menuId = useId();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const { pathname } = useLocation();

  useEffect(() => setOpen(false), [pathname]);

  useEffect(() => {
    const sentinel = document.getElementById("top-sentinel");
    if (!sentinel) return;
    const observer = new IntersectionObserver(([entry]) => setScrolled(!entry.isIntersecting), { threshold: 0 });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="site">
      <a className="skip-link" href="#main">Skip to content</a>
      <div id="top-sentinel" aria-hidden="true" />
      <header className="masthead" data-scrolled={scrolled}>
        <div className="masthead__inner">
          <NavLink to="/" className="brand" aria-label="BSANHS SSLG, home">
            <img src="/brand/seal-sslg.png" alt="" width="40" height="40" />
            <span className="brand__name">BSANHS</span>
          </NavLink>
          <nav className="site-nav" aria-label="Primary" data-open={open} id={menuId}>
            {NAV.map(([to, label]) => (
              <NavLink key={to} to={to} end={to === "/"}>{label}</NavLink>
            ))}
          </nav>
          <button
            ref={buttonRef}
            type="button"
            className="menu-toggle"
            aria-expanded={open}
            aria-controls={menuId}
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            <span aria-hidden="true">{open ? "×" : "☰"}</span>
          </button>
        </div>
      </header>
      <main id="main" className="site-main" tabIndex={-1}><Outlet /></main>
      <footer className="site-footer">
        <div className="site-footer__inner">
          <p className="site-footer__name">
            <img src="/brand/seal-sslg.png" alt="" width="48" height="48" />
            <span>Benigno S. Aquino National High School Supreme Secondary Learner Government</span>
          </p>
          <a className="cta-bar site-footer__fb" href={FACEBOOK_URL} target="_blank" rel="noreferrer">
            <span>facebook.com/SSLGBSANHS</span>
          </a>
          <p className="site-footer__note">S.Y. 2026–2027 · Official website</p>
        </div>
      </footer>
    </div>
  );
}
```

Keyboard: Escape closes the panel and returns focus to the toggle. Add:

```tsx
useEffect(() => {
  if (!open) return;
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      setOpen(false);
      buttonRef.current?.focus();
    }
  };
  document.addEventListener("keydown", onKey);
  return () => document.removeEventListener("keydown", onKey);
}, [open]);
```

- [ ] **Step 6: Style the masthead and footer**

```css
#top-sentinel { position: absolute; inset-block-start: 0; height: 1px; width: 1px; }
.masthead {
  position: sticky;
  inset-block-start: 0;
  z-index: 50;
  background: transparent;
  transition: background-color 200ms var(--ease-out), box-shadow 200ms var(--ease-out);
}
.masthead[data-scrolled="true"] {
  background: rgba(2, 19, 62, 0.94);
  box-shadow: 0 1px 0 var(--border-dark);
  backdrop-filter: blur(10px);
}
.masthead__inner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  width: 100%;
  max-width: var(--page-max);
  min-height: var(--header-h);
  margin-inline: auto;
  padding-inline: var(--gutter);
}
.brand { display: inline-flex; align-items: center; gap: var(--space-3); text-decoration: none; }
.brand img { width: 40px; height: 40px; }
.brand__name {
  font-family: var(--font-display);
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: var(--text-dark);
}
.site-nav { display: flex; align-items: center; gap: var(--space-1); margin-inline-start: auto; }
.site-nav a {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding-inline: var(--space-3);
  color: var(--text-dark);
  font-size: 0.9375rem;
  font-weight: 500;
  text-decoration: none;
  border-block-end: 2px solid transparent;
  transition: color 150ms var(--ease-out), border-color 150ms var(--ease-out);
}
@media (hover: hover) { .site-nav a:hover { border-block-end-color: var(--gold-300); } }
.site-nav a[aria-current="page"] { border-block-end-color: var(--gold-300); }
.menu-toggle {
  display: none;
  width: 44px;
  height: 44px;
  margin-inline-start: auto;
  background: transparent;
  color: var(--text-dark);
  border: 1px solid var(--border-dark);
  border-radius: var(--radius-sm);
  font-size: 1.25rem;
}

@media (max-width: 899.98px) {
  .menu-toggle { display: grid; place-items: center; }
  .site-nav {
    position: absolute;
    inset-block-start: 100%;
    inset-inline: 0;
    display: none;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    padding: var(--space-2) var(--gutter) var(--space-4);
    background: var(--navy-900);
    box-shadow: var(--shadow-panel);
  }
  .site-nav[data-open="true"] { display: flex; }
  .site-nav a { min-height: 48px; padding-inline: 0; border-block-end: 1px solid var(--border-dark); }
}

.site-footer { background: var(--navy-950); color: var(--text-dark); border-block-start: 1px solid var(--border-dark); }
.site-footer__inner {
  display: grid;
  justify-items: center;
  gap: var(--space-4);
  width: 100%;
  max-width: var(--page-max);
  margin-inline: auto;
  padding: var(--space-7) var(--gutter) var(--space-6);
  text-align: center;
}
.site-footer__name { display: flex; align-items: center; gap: var(--space-3); max-width: 62ch; font-size: var(--text-base); }
.site-footer__name img { width: 48px; height: 48px; }
.site-footer__fb { width: min(100%, 560px); }
.site-footer__note { color: var(--text-muted-dark); font-size: var(--text-xs); letter-spacing: 0.08em; text-transform: uppercase; }
```

- [ ] **Step 7: Rewrite the layout test**

```tsx
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SiteLayout } from "../src/components/SiteLayout";

function renderLayout() {
  return render(
    <MemoryRouter>
      <Routes>
        <Route element={<SiteLayout />}>
          <Route index element={<p>home</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

test("keeps the published nav order with Photos after Accomplishments", () => {
  renderLayout();
  const nav = screen.getByRole("navigation", { name: "Primary" });
  expect(within(nav).getAllByRole("link").map((a) => a.textContent)).toEqual([
    "Home", "Finance", "Accomplishments", "Photos", "Transparency", "About us", "Feedback",
  ]);
});

test("exposes one skip link, one main and the current page", () => {
  renderLayout();
  expect(screen.getByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main");
  expect(screen.getByRole("main")).toHaveAttribute("id", "main");
  expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute("aria-current", "page");
});

test("the menu toggle announces and closes on Escape", () => {
  renderLayout();
  const toggle = screen.getByRole("button", { name: "Open menu" });
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  fireEvent.click(toggle);
  expect(screen.getByRole("button", { name: "Close menu" })).toHaveAttribute("aria-expanded", "true");
  fireEvent.keyDown(document, { key: "Escape" });
  expect(screen.getByRole("button", { name: "Open menu" })).toHaveAttribute("aria-expanded", "false");
});

test("the footer names the government and links Facebook", () => {
  renderLayout();
  expect(screen.getByText(/Benigno S\. Aquino National High School Supreme Secondary Learner Government/i)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /facebook\.com\/SSLGBSANHS/i })).toHaveAttribute("href", "https://www.facebook.com/SSLGBSANHS");
});
```

jsdom has no `IntersectionObserver`; add a stub to `tests/setup.ts`:

```ts
class IO {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-expect-error test stub
globalThis.IntersectionObserver = IO;
```

- [ ] **Step 8: Build, deploy, compare**

```bash
npm test -- tests/layout.test.tsx tests/design.test.tsx
npm run build && npm run deploy
node .superpowers/shots/cdp-shot.mjs https://sslg-2sr.pages.dev 1440 900 .superpowers/shots/build-home-1440.png viewport
node .superpowers/shots/cdp-shot.mjs https://sslg-2sr.pages.dev 390 844 .superpowers/shots/build-home-390.png viewport
```

Home is still the smoke page at this point; confirm the masthead/footer render and `scrollWidth === 390`. Then commit:

```bash
git add -A && git commit -m "feat: add official seals, hero beams, masthead and footer"
```

---

### Task 3: Refresh the content layer to the published site

**Files:**
- Modify: `src/content/types.ts`, `activities.ts`, `officers.ts`, `documents.ts`, `site.ts`, `src/config.ts`
- Create: `src/content/finance.ts`
- Modify: `tests/content.test.ts`

**Interfaces:**
- Produces: `Cover` with `image`, `Officer.photo`, `DocumentGroup.folderUrl`, `FINANCE`, `ABOUT_INTRO`, `LEGAL_BASES`, `ACCOMPLISHMENT_REPORTS_URL`.

- [ ] **Step 1: Extend the types**

```ts
export type Cover =
  | { kind: "album"; album: string }
  | { kind: "doc"; fileId: string }
  | { kind: "image"; src: string; alt?: string }
  | { kind: "none" };

export interface Officer {
  name: string;
  role: string;
  group: "executive" | "grade" | "school";
  photo: string;
}

export interface DocumentGroup {
  key: "minutes" | "notices" | "elections" | "proposals" | "memorandums" | "finance";
  label: string;
  blurb: string;
  folderUrl: string;
}
```

- [ ] **Step 2: Add INKantations and the induction artwork**

Insert at the top of `ACTIVITIES`:

```ts
{
  slug: "inkantations-2026",
  title: "INKantations: Melodramatic Essay Writing Contest",
  caption:
    "To celebrate the power of the written word, the SSLG invites learners to pen dramatically tragic, wildly theatrical essays in this spooky-season showcase of creativity and flair.",
  cover: {
    kind: "image",
    src: "/media/inkantations-2026.webp",
    alt: "INKantations poster: Melodramatic Essay Writing Contest",
  },
  featured: true,
},
```

Remove `featured: true` from `world-teachers-day-2026`. On `induction-ceremony-2026`, change the cover to:

```ts
cover: {
  kind: "image",
  src: "/media/induction-2026.webp",
  alt: "SSLG officers at the Onto the Next Leaders induction ceremony",
},
```

Keep its `album` and `reportUrl` — the detail page still loads the album.

- [ ] **Step 3: Add officer photos**

In `officers.ts`:

```ts
import type { Officer } from "./types";

const photo = (name: string) =>
  `/brand/officers/${name
    .replace(/^Hon\.\s*/, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")}.webp`;

const roster = [
  // the existing 27 entries, unchanged
] satisfies Omit<Officer, "photo">[];

export const OFFICERS: Officer[] = roster.map((officer) => ({
  ...officer,
  photo: photo(officer.name),
}));
```

The photo function must match the Python slug function exactly: `Hon.` stripped, lowercase, non-alphanumerics to `-`, trimmed.

- [ ] **Step 4: Add folder URLs and the finance module**

`documents.ts` gains:

```ts
folderUrl: "https://drive.google.com/drive/folders/<id>",
```

with IDs `minutes 1qm3Z6OmjxFa41OsjTPrBUJEl57-GSGH5`, `notices 1SVzssvcj1IkEndY0Mp5Nv8WhDsaQUDl4`, `elections 1hiqv7sFda_cGWVo7OtgJs5cpPS-buZ4L`, `proposals 15vGFBRfifPvEUkN5yo1iv87MQPAoaFHE`, `memorandums 1xszCcvP83aaVus3xLQ4f1RDmjvWqLHUj`, `finance 1NhgG1fkfxch70E3hzb5YhTgCK0PWKcdV`.

`src/content/finance.ts`:

```ts
export const FINANCE_REPORT = {
  title: "SSLG Financial Report",
  date: "November 8, 2026",
  folderUrl: "https://drive.google.com/drive/folders/1NhgG1fkfxch70E3hzb5YhTgCK0PWKcdV",
  preparedBy: "Samantha C. De Venecia",
  preparedRole: "SSLG Treasurer",
};

export const FINANCE_STATS = [
  { key: "funds", value: "₱13,327.90", label: "Current Funds", note: "as of November 8, 2026" },
  { key: "ppas", value: "26", label: "Proposed PPAs", note: "from the SSLG GPOA (up for approval)" },
  { key: "projects", value: "10", label: "Projects accomplished", note: "as of July 28, 2026" },
] as const;
```

- [ ] **Step 5: Add About and legal copy**

`site.ts` gains:

```ts
export const ABOUT_INTRO =
  "The highest student governing body of Benigno S. Aquino National High School. Forefront of learners' rights and welfare, model of learners' excellence, and representation of good character and deep sense of moral values.";

export const LEGAL_BASES = {
  heading: "Legal bases of the Supreme Secondary Learner Government",
  issuance: "OUOPS No. 2023-03-Memorandum",
  title: "Interim Guidelines of the Learner Government Program (LGP) for School Year 2023–2024",
  url: "https://drive.google.com/file/d/1MthdcNxs_w_QoLuus-nVcAoi4xaACNKd/view",
};

export const GPOA = {
  title: "General Plan of Action",
  body:
    "The General Plan of Action serves as the official document that outlines the specific programs, projects, and activities the student council officers plan to carry out for the school year, along with their objectives, timelines, and persons responsible for each activity.",
  folderUrl: "https://drive.google.com/drive/folders/16_T5tmGrzwHF6X9lR1JxrNY8K1C9EYnN",
};
```

`config.ts` gains:

```ts
export const ACCOMPLISHMENT_REPORTS_URL =
  "https://drive.google.com/drive/folders/1_44iCUzUJAaBi0cc0a7DcpauUPpRJIxj";
export const RECORDS_ROOT_URL =
  "https://drive.google.com/drive/folders/1XU9s-pHPCk_zJQo7LSOjcmtGeIiI9JeM";
```

- [ ] **Step 6: Update the content tests**

```ts
expect(ACTIVITIES).toHaveLength(11);
expect(ACTIVITIES.filter((a) => a.featured).map((a) => a.slug)).toEqual(["inkantations-2026"]);
expect(ACTIVITIES.filter((a) => a.cover.kind === "image").map((a) => a.slug)).toEqual([
  "inkantations-2026", "induction-ceremony-2026",
]);
for (const a of ACTIVITIES.filter((x) => x.cover.kind === "image")) {
  expect(a.cover.kind === "image" && a.cover.src).toMatch(/^\/media\/[a-z0-9-]+\.webp$/);
}
expect(new Set(OFFICERS.map((o) => o.photo)).size).toBe(27);
for (const o of OFFICERS) expect(o.photo).toMatch(/^\/brand\/officers\/[a-z0-9-]+\.webp$/);
expect(FINANCE_STATS.map((s) => s.value)).toEqual(["₱13,327.90", "26", "10"]);
expect(FINANCE_REPORT.preparedBy).toBe("Samantha C. De Venecia");
expect(DOCUMENT_GROUPS.every((g) => g.folderUrl.startsWith("https://drive.google.com/drive/folders/"))).toBe(true);
expect(LEGAL_BASES.url).toContain("1MthdcNxs_w_QoLuus-nVcAoi4xaACNKd");
```

Also verify on disk that every `officer.photo` exists:

```ts
import { existsSync } from "node:fs";
import { join } from "node:path";
for (const o of OFFICERS) {
  expect(existsSync(join(process.cwd(), "public", o.photo))).toBe(true);
}
```

- [ ] **Step 7: Run and commit**

```bash
npm test -- tests/content.test.ts
git add -A && git commit -m "feat: add INKantations, finance figures, portraits and legal bases"
```

---

### Task 4: Compose the Home page

**Files:**
- Rewrite: `src/pages/Home.tsx`
- Modify: `src/styles/pages.css`, `src/App.tsx` (no route change yet)
- Test: `tests/pages.test.tsx` (Home block)

**Interfaces:**
- Consumes: `HomeHero`, `Band`, `SectionTitle`, `CtaBar`, `ACTIVITIES`, `ABOUT_INTRO`, `MANDATE`.

- [ ] **Step 1: Compose the page**

Order and copy:

1. `HomeHero`.
2. `Band variant="deep"` with `id="latest"`:
   `<SectionTitle title="Latest" lead="Stay Updated with Current SSLG Affairs Here" />`
   then a two-column latest block: 16:9 `SmartImage` of the featured activity on the left, and on the right the `<h2>` title, caption, and `CtaBar href={`/accomplishments/${featured.slug}`}>Read more</CtaBar>`.
   Use `ACTIVITIES.find((a) => a.featured) ?? ACTIVITIES[0]`.
3. `Band variant="mint"`: `SectionTitle title="About us" lead="Get to know your student leaders here"`, then a three-column block:
   - figure: `/media/induction-2026.webp`, caption “Onto the Next Leaders Induction Ceremony”;
   - “The Supreme Secondary Learner Government” (`h3`), `ABOUT_INTRO`, `CtaBar href="/about-us">Read more</CtaBar>`;
   - “Our Mandate” (`h3`), `MANDATE`, `CtaBar href="/about-us#mandate">Read more</CtaBar>`.
4. `Band variant="navy"`: three destination articles, each with the transparent artwork, a label, and a white `CtaBar`: Accomplishments → `/accomplishments`; Transparency → `/transparency`; Financial Reports → `/finance`.
5. No footer here — the layout owns it.

`<PageMeta title="Home" description="Official website of the Supreme Secondary Learner Government of Benigno S. Aquino National High School." path="/" />` stays first.

Use `<figure>` and `<figcaption>` for the induction photo. The caption is 14px, muted, left-aligned.

- [ ] **Step 2: Style the home blocks**

```css
.home-latest { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: clamp(1.5rem, 4vw, 3rem); align-items: center; }
.home-latest__media { aspect-ratio: 4 / 3; overflow: hidden; border-radius: var(--radius-sm); }
.home-latest__media img { width: 100%; height: 100%; object-fit: cover; }
.home-latest h2 { font-size: clamp(1.75rem, 2.6vw, 2.5rem); color: var(--text-dark); }
.home-latest p { max-width: 52ch; margin-block: var(--space-3) var(--space-5); color: var(--text-muted-dark); }
.home-latest .cta-bar { max-width: 320px; }

.home-about { display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: clamp(1.5rem, 4vw, 3rem); align-items: start; }
.home-about figure { margin: 0; }
.home-about img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border-radius: var(--radius-sm); }
.home-about figcaption { margin-block-start: var(--space-2); color: var(--text-muted-light); font-size: var(--text-sm); }
.home-about h3 { color: var(--text-light); }
.home-about p { margin-block: var(--space-3) var(--space-5); color: var(--ink-soft); }
.home-about .cta-bar { background: var(--navy-950); color: var(--paper); }
@media (hover: hover) { .home-about .cta-bar:hover { background: var(--navy-700); color: var(--paper); } }

.home-destinations { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: clamp(1.25rem, 3vw, 2.5rem); align-items: end; }
.home-destinations article { display: grid; gap: var(--space-4); justify-items: center; text-align: center; }
.home-destinations img { width: min(100%, 220px); height: auto; }
.home-destinations .cta-bar { width: 100%; }

@media (max-width: 899.98px) {
  .home-latest, .home-about { grid-template-columns: 1fr; }
  .home-about figure { max-width: 560px; }
}
@media (max-width: 639.98px) {
  .home-destinations { grid-template-columns: 1fr; }
  .home-destinations img { width: 160px; }
}
```

- [ ] **Step 3: Test Home**

```tsx
test("Home names the government once and features INKantations", () => {
  render(<MemoryRouter><Home /></MemoryRouter>);
  expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/Supreme Secondary Learner Government/i);
  expect(screen.getByRole("link", { name: /Read more/i, hidden: false })).toBeInTheDocument();
  expect(screen.getAllByText(/INKantations/i).length).toBeGreaterThan(0);
  expect(screen.getByRole("link", { name: /facebook\.com\/SSLGBSANHS/i })).toBeInTheDocument();
});
```

`Home` alone has no footer; assert the footer in the layout test instead. Remove that last assertion here.

- [ ] **Step 4: Build, deploy, view**

```bash
npm test -- tests/pages.test.tsx
npm run build && npm run deploy
node .superpowers/shots/cdp-shot.mjs https://sslg-2sr.pages.dev 1440 900 .superpowers/shots/build-home-1440.png full
node .superpowers/shots/cdp-shot.mjs https://sslg-2sr.pages.dev 390 844 .superpowers/shots/build-home-390.png full
```

Compare against `.superpowers/shots/gsites/home-1440.png`: hero height, lockup size, mint band, three destination cards, white bars. Record differences that are deviations from Task 1’s table.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: compose the home page with hero, latest, about and destinations"
```

---

### Task 5: Media layer and the Photos page

**Files:**
- Create: `src/lib/api.ts`, `src/lib/useAlbums.ts`, `src/components/SmartImage.tsx`, `src/components/PhotoGrid.tsx`, `src/components/AlbumViewer.tsx`, `src/components/EmptyState.tsx`, `src/pages/Photos.tsx`
- Modify: `src/App.tsx`, `src/styles/components.css`, `src/styles/pages.css`
- Test: `tests/photo-grid.test.tsx`

**Interfaces:**
- Consumes: `GET /api/albums`, `GET /api/photos?album=`, `shared/drive` types.
- Produces: `useAlbums()`, `<SmartImage src alt ratio />`, `<PhotoGrid photos />`, `<AlbumViewer albumId name onClose />`, route `/photos`.

- [ ] **Step 1: Write the fetch helpers**

```ts
// src/lib/api.ts
export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, { signal, headers: { accept: "application/json" } });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return (await res.json()) as T;
}
```

```ts
// src/lib/useAlbums.ts
import { useEffect, useState } from "react";
import type { AlbumsResponse } from "../../shared/drive";
import { getJson } from "./api";

let pending: Promise<AlbumsResponse> | null = null;
export function loadAlbums() {
  pending ??= getJson<AlbumsResponse>("/api/albums");
  return pending;
}

export function useAlbums() {
  const [state, setState] = useState<{ data: AlbumsResponse | null; error: string | null }>({ data: null, error: null });
  useEffect(() => {
    let alive = true;
    loadAlbums()
      .then((data) => alive && setState({ data, error: null }))
      .catch(() => alive && setState({ data: null, error: "Albums are unavailable right now." }));
    return () => { alive = false; };
  }, []);
  return state;
}
```

- [ ] **Step 2: SmartImage**

Props: `src`, `alt`, `ratio = "4 / 3"`, `sizes`, `priority = false`. Renders a wrapper with `aspect-ratio`, a shimmering skeleton until `onLoad`, then the image with `opacity: 1`. On error, replace with a ruled plate containing the alt text and a small “Image unavailable” label; never leave an empty box. `loading={priority ? "eager" : "lazy"}`, `decoding="async"`, `fetchPriority={priority ? "high" : "auto"}`.

- [ ] **Step 3: PhotoGrid and lightbox**

- Grid: `ul` with `li > button` (the button covers the thumbnail), accessible name = the cleaned filename, `aria-haspopup="dialog"`.
- Lightbox: fixed overlay, `role="dialog"`, `aria-modal="true"`, `aria-labelledby` the filename. On open: save the trigger, focus the close button. Escape closes; ArrowLeft/ArrowRight step; Tab is trapped by cycling between the close, previous and next controls. On close: restore focus to the trigger.
- Counter: `3 / 53` with `aria-live="polite"`.
- Image: `full` URL, `alt` = cleaned filename.
- Use `overscroll-behavior: contain` on the overlay.

Test:

```tsx
test("opens the lightbox, steps, and restores focus on Escape", () => {
  render(<PhotoGrid photos={[
    { id: "1", name: "IMG_0012.JPG", mime: "image/jpeg", thumb: "/a.jpg", full: "/b.jpg" },
    { id: "2", name: "IMG_0013.JPG", mime: "image/jpeg", thumb: "/c.jpg", full: "/d.jpg" },
  ]} />);
  const trigger = screen.getByRole("button", { name: /IMG 0012/i });
  trigger.focus();
  fireEvent.click(trigger);
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  expect(screen.getByText("1 / 2")).toBeInTheDocument();
  fireEvent.keyDown(document, { key: "ArrowRight" });
  expect(screen.getByText("2 / 2")).toBeInTheDocument();
  fireEvent.keyDown(document, { key: "Escape" });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(document.activeElement).toBe(trigger);
});
```

- [ ] **Step 4: AlbumViewer**

Inline panel below the album grid. States: skeleton (eight-dot loader with `role="status"` and text “Loading photos…”), error with a retry button and an “Open in Drive” link (`https://drive.google.com/drive/folders/<id>`), empty (“This album has no photos yet.”), grid. Close button returns focus to the album card that opened it. Cache responses in a module `Map<string, PhotosResponse>`.

- [ ] **Step 5: Photos page**

```tsx
<PageMeta title="Photos" description="Photo albums from SSLG and LGCC activities." path="/photos" />
<PageHero title="Photos" lead="Albums from the SSLG and LGCC. Photos are added by the PIO; this page reads the public Drive albums directly." />
<Band variant="deep">
  {loading && <Loading />}
  {error && <EmptyState title="Albums are unavailable" body={error} action={{ href: PIO_FOLDER_URL, label: "Open the Drive folder" }} />}
  {data?.years.map((year) => (
    <section key={year.id} className="album-year">
      <h2>{year.name}</h2>
      {year.terms.map((term) => (
        <div key={term.id} className="album-term">
          <h3>{term.name}</h3>
          <ul className="album-grid">
            {term.albums.map((album) => (
              <li key={album.id}>
                <button type="button" className="album-card" aria-haspopup="dialog" onClick={() => setOpen(album)}>
                  <SmartImage src={album.cover ?? "/media/placeholder-album.webp"} alt="" ratio="4 / 3" />
                  <span className="album-card__name">{album.name}</span>
                  <span className="album-card__count">{album.count} photos</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  ))}
</Band>
```

Add a static `/media/placeholder-album.webp`? Do not create new art: when `cover` is null, render a CSS plate with the album initials instead of an image. Replace the `SmartImage` branch with `album.cover ? <SmartImage …/> : <DocumentPlate label={album.name} />`.

`PIO_FOLDER_URL` is `https://drive.google.com/drive/folders/1QbMxIfTuL9-qJ3T9YgfuYyErHexqxBiQ`; add it to `config.ts`.

- [ ] **Step 6: Album grid styles**

Three columns ≥896px, two ≥560px, one below; 4:3 covers; card is a button with no default border; name 18px Gentium 700 on navy; count 13px muted. Add a 1px inset outline on covers (`outline: 1px solid rgba(0,0,0,.12); outline-offset: -1px;`) so light photos keep an edge on navy.

- [ ] **Step 7: Wire the route, run, commit**

```tsx
<Route path="photos" element={<Photos />} />
```

```bash
npm test -- tests/photo-grid.test.tsx
npm run build && git add -A && git commit -m "feat: add Drive-backed photo albums with an accessible lightbox"
```

Deploy and open `/photos`. Without the API key it must show the empty/error state with the Drive link — that is the expected live result until the owner sets the secret.

---

### Task 6: Accomplishments and activity detail

**Files:**
- Create: `src/components/ActivityCard.tsx`, `src/pages/Accomplishments.tsx`, `src/pages/ActivityPage.tsx`, `src/pages/NotFound.tsx`
- Modify: `src/App.tsx`, `src/styles/pages.css`
- Test: `tests/pages.test.tsx` (Accomplishments block)

> **Execution ruling (forward dependency):** Task 6 Step 3 renders `<NotFound />` for an unknown slug, but the original plan created `NotFound.tsx` in Task 8. To avoid a forward dependency, Task 6 creates `src/pages/NotFound.tsx` to the Task 8 Step 3 spec (PageHero title="Page not found" lead="That page is not part of the SSLG record."; Band variant="deep" with links to Home and Accomplishments; PageMeta title="Page not found" with **no** `path` so it stays noindex). Task 8 then REUSES this component (it does not recreate it) and only wires the catch-all route + adds the 404 test.

**Interfaces:**
- Consumes: `ACTIVITIES`, `useAlbums()`, `docThumb`, `AlbumViewer`, `ACCOMPLISHMENT_REPORTS_URL`.
- Produces: routes `/accomplishments`, `/accomplishments/:slug`.

- [ ] **Step 1: ActivityCard**

Cover resolution: `image` → `SmartImage`; `album` → find in `useAlbums()` and use `album.cover`, else plate; `doc` → `docThumb(fileId)`; `none` → plate with the title’s initials (or “TINIG” for `project-tinig`).

Card structure:

```tsx
<article className="activity-card">
  <div className="activity-card__media">{cover}</div>
  <div className="activity-card__body">
    <h3><Link to={`/accomplishments/${activity.slug}`}>{activity.title}</Link></h3>
    <p>{activity.caption}</p>
  </div>
  {activity.reportUrl && (
    <a className="activity-card__report" href={activity.reportUrl} target="_blank" rel="noreferrer">
      Read the report<span className="sr-only"> for {activity.title}</span>
    </a>
  )}
</article>
```

The title link covers the card with `::after { position:absolute; inset:0 }`; the report link sits above it with `position: relative; z-index: 1`. Two distinct tab stops, no nested anchors.

- [ ] **Step 2: Accomplishments page**

`PageHero title="Accomplishments"`. Then `Band variant="navy"` with the grid (3 ≥1000px, 2 ≥680px, 1 below) in content order. `project-tinig` is not separated; it renders in the same grid with its plate. End with `CtaBar href={ACCOMPLISHMENT_REPORTS_URL} external>Read more accomplishment reports</CtaBar>`, inside `Band variant="deep"` so the bar sits on navy.

- [ ] **Step 3: Activity detail**

`PageHero title={activity.title}` (title case, no uppercase transform) with a lead: the caption. Then `Band variant="mint"` containing: date (only if set), the album viewer when `album` is set, a `CtaBar` to the report when `reportUrl` exists, and a text link back to `/accomplishments` (“All accomplishments”).

Unknown slug: render `<NotFound />` inside the same layout.

- [ ] **Step 4: Test**

```tsx
test("accomplishments render every title and link to detail pages", () => {
  render(<MemoryRouter><Accomplishments /></MemoryRouter>);
  expect(screen.getByRole("heading", { level: 1, name: "Accomplishments" })).toBeInTheDocument();
  expect(screen.getAllByRole("link", { name: /INKantations/i }).length).toBeGreaterThan(0);
  expect(screen.getByRole("link", { name: /Read more accomplishment reports/i })).toHaveAttribute("href", expect.stringContaining("1_44iCUzUJAaBi0cc0a7DcpauUPpRJIxj"));
});

test("an unknown activity slug renders not found", () => { /* memory router at /accomplishments/nope */ });
```

- [ ] **Step 5: Card styles + Galaxy lift**

```css
.activity-card { position: relative; display: flex; flex-direction: column; gap: var(--space-4); }
.activity-card__media { overflow: hidden; border-radius: var(--radius-sm); background: var(--navy-900); }
.activity-card__media img { width: 100%; height: 100%; object-fit: cover; transition: transform 450ms var(--ease-card); }
.activity-card h3 { font-size: clamp(1.125rem, 1.6vw, 1.375rem); line-height: 1.3; color: var(--text-dark); }
.activity-card h3 a { text-decoration: none; }
.activity-card h3 a::after { content: ""; position: absolute; inset: 0; }
.activity-card p { color: var(--text-muted-dark); font-size: var(--text-sm); line-height: 1.6; }
.activity-card__report { position: relative; z-index: 1; align-self: start; color: var(--gold-300); font-size: var(--text-sm); font-weight: 500; }
/* Adapted from uiverse.io by gharsh11032000 (MIT) */
@media (hover: hover) and (prefers-reduced-motion: no-preference) {
  .activity-card:hover .activity-card__media img { transform: scale(1.03); }
  .activity-card:hover h3 a { color: var(--gold-300); }
}
```

Focus indication for the stretched link: the `a:focus-visible` ring draws around the inline title, not the card; add `.activity-card:focus-within { outline: 2px solid var(--gold-300); outline-offset: 6px; }` and keep the title’s own ring.

- [ ] **Step 6: Run, deploy, commit**

```bash
npm test -- tests/pages.test.tsx
npm run build && npm run deploy
node .superpowers/shots/cdp-shot.mjs https://sslg-2sr.pages.dev/accomplishments 1440 900 .superpowers/shots/build-acc-1440.png full
git add -A && git commit -m "feat: add accomplishments index and activity detail pages"
```

---

### Task 7: Transparency and Finance with document browsing

**Files:**
- Create: `src/lib/useDocuments.ts`, `src/components/DocumentList.tsx`, `src/components/DocumentPlate.tsx`, `src/components/Stat.tsx`, `src/pages/Transparency.tsx`, `src/pages/Finance.tsx`
- Modify: `src/App.tsx`, `src/styles/pages.css`
- Test: `tests/documents.test.tsx`

**Interfaces:**
- Consumes: `GET /api/documents?folder=`, `DOCUMENT_GROUPS`, `FINANCE_*`, `GPOA`, `LEGAL_BASES`.
- Produces: routes `/transparency`, `/finance`; `<DocumentList folder fallbackUrl />`.

- [ ] **Step 1: DocumentList**

Props `folder: FolderKey`, `fallbackUrl: string`. Module cache `Map<FolderKey, Promise<DocumentsResponse>>` plus a `reload` that deletes the entry. Rows: 56px `docThumb` (or plate), filename (14px, breaks on long names), `modified` date in `en-PH` (day-month-year) when present, and a type tag from the extension. The whole row is an `<a>` to `view`, `target="_blank"`. Errors: message + “Retry” button + “Open the Drive folder” link. Empty: “No documents in this folder yet.” plus the folder link. Loading: eight-dot loader with `role="status"` and text.

- [ ] **Step 2: DocumentPlate**

A pure-CSS sheet: 4:5 white card, 3 grey rules, a gold tab, the label in 13px caps at the bottom, and an optional navy “Read here” pill. Used for all six cards and for the album/doc fallback. No image request.

- [ ] **Step 3: Transparency**

`PageHero title="Transparency"`. Then:

1. `Band variant="navy"` with the GPOA feature: 2 columns — `DocumentPlate` large, and `h2` + `GPOA.body` + `CtaBar href={GPOA.folderUrl} external>Open the plan</CtaBar>`.
2. `Band variant="deep"` with a tablist of the six groups. Each card = `<button role="tab" aria-selected aria-controls>` containing a `DocumentPlate` and the label. Roving tabindex: selected = 0, others = -1; ArrowLeft/Right/Home/End move selection and focus. Below, one `<div role="tabpanel" aria-labelledby>` rendering `<h2>{group.label}</h2>`, the blurb, and `<DocumentList folder={group.key} fallbackUrl={group.folderUrl} />`.
3. `Band variant="mint"` with the legal bases: `h2` `LEGAL_BASES.heading`, `p` issuance, `a` title.
4. `Band variant="deep"` with `CtaBar href={RECORDS_ROOT_URL} external>Read more documents here</CtaBar>`.

Default tab: `minutes`.

- [ ] **Step 4: Finance**

`PageHero title="Finance"`. Then:

1. `Band variant="mint"` with a 2-column report block: document plate (label “Financial Report”), and on the right `h2` “Latest Financial Reports”, `p` “SSLG Financial Report (November 8, 2026)”, `CtaBar href={FINANCE_REPORT.folderUrl} external>Open the November 8 finance folder</CtaBar>`, and the italic line “Prepared by Samantha C. De Venecia (SSLG Treasurer)”.

> **Final-review ruling (CTA label fidelity):** the original label “Open the November 8 report” links to the finance *folder* (a Drive folder that holds the published reports), not a single report file, and that phrase appears nowhere on the published page. Relabelled “Open the November 8 finance folder” so the destination (a folder) matches the words and the November 8 report date is still named. Cost if wrong: a one-line label change.

> **Execution ruling (byline fidelity, carries the Task 3 ruling):** render the byline from the content layer — `Prepared by {FINANCE_REPORT.preparedBy} ({FINANCE_REPORT.preparedRole})` — which is exactly “Samantha C. De Venecia (SSLG Treasurer)”, the name printed on the published financial report. Do NOT hardcode the roster/About spelling “Samantha Joy C. De Venecia” here; that spelling belongs to the About roster only. The original plan note (Owner follow-up #2) proposed using the About spelling on both pages but flagged it for owner confirmation; pending that confirmation, the Finance page quotes its own source document faithfully.
2. `Band variant="mint"` (continuous) with three `Stat` tiles separated by 1px rules: value 40px Gentium 700 tabular-nums, label 13px caps 600, note 13px italic muted. Stack on mobile.
3. `Band variant="deep"` with `h2` “Financial reports” and `<DocumentList folder="finance" fallbackUrl={FINANCE_REPORT.folderUrl} />`.

- [ ] **Step 5: Tests**

```tsx
test("a document folder with no files shows the empty state and fallback", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ folders: [], files: [], fetchedAt: "" }) }));
  render(<DocumentList folder="finance" fallbackUrl="https://drive.google.com/drive/folders/x" />);
  expect(await screen.findByText(/no documents in this folder yet/i)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /open the drive folder/i })).toBeInTheDocument();
});

test("transparency switches tabs by keyboard", () => {
  render(<MemoryRouter><Transparency /></MemoryRouter>);
  const tab = screen.getByRole("tab", { name: "Elections" });
  tab.focus();
  fireEvent.keyDown(tab, { key: "ArrowRight" });
  expect(screen.getByRole("tab", { name: "Project Proposals" })).toHaveAttribute("aria-selected", "true");
});

test("finance prints the published figures", () => {
  render(<MemoryRouter><Finance /></MemoryRouter>);
  expect(screen.getByText("₱13,327.90")).toBeInTheDocument();
  expect(screen.getByText("26")).toBeInTheDocument();
  expect(screen.getByText("10")).toBeInTheDocument();
  expect(screen.getByText(/Samantha C\. De Venecia/)).toBeInTheDocument();
});
```

Stub `fetch` globally in these tests to return `{ files: [], folders: [] }` so the lists settle.

- [ ] **Step 6: Styles, run, commit**

Stat and plate styles go in `pages.css`; tab styles in `components.css`. The tab cards form a 3×2 grid ≥900px, 2 columns ≥560px, 1 below; the selected card gets a gold 2px inset ring and a `aria-selected` style change (not color alone: also show a “Viewing” label).

```bash
npm test -- tests/documents.test.tsx
npm run build && npm run deploy
git add -A && git commit -m "feat: add transparency document browser and finance report page"
```

---

### Task 8: About us, Feedback and the 404

**Files:**
- Create: `src/pages/About.tsx`, `src/pages/Feedback.tsx`
- Reuse: `src/pages/NotFound.tsx` (created in Task 6 per the execution ruling — do NOT recreate it; verify it matches the Step 3 spec)
- Modify: `src/App.tsx`, `src/styles/pages.css`
- Test: `tests/pages.test.tsx` (remaining blocks)

**Interfaces:**
- Consumes: `OFFICERS`, `OBJECTIVES`, `DUTIES`, `ABOUT_INTRO`, `MANDATE`, `FEEDBACK_FORM_URL`.
- Produces: routes `/about-us`, `/feedback`, catch-all.

- [ ] **Step 1: About page**

`PageHero title="About us"`. Then three bands, each with its own `SectionTitle` and a portrait grid:

1. `Band variant="navy"` — “Executive Officers”, 7 cards.
2. `Band variant="deep"` — “Grade-Level Representatives”, 12 cards in listed order (Grade 12 → Grade 7).
3. `Band variant="navy"` — “School Leadership”, 8 cards.
4. `Band variant="mint" id="mandate"` — `h2` “Duties, Responsibilities, and Obligations of the Supreme Secondary Learner Government”, `h3` “Objectives of the SSLG” + ordered list of 5, `h3` “Duties and Obligations of the SSLG” + unordered list of 3, then `MANDATE` in a bordered aside.

Officer card:

```tsx
<figure className="officer">
  <span className="officer__frame">
    <img src={officer.photo} alt={`Portrait of ${officer.name}`} width="720" height="720" loading="lazy" decoding="async" />
  </span>
  <figcaption>
    <span className="officer__name">{officer.name}</span>
    <span className="officer__role">{officer.role}</span>
  </figcaption>
</figure>
```

The frame crops the baked nameplate without editing the file:

```css
.officer__frame { display: block; aspect-ratio: 4 / 5; overflow: hidden; background: var(--navy-800); border-radius: var(--radius-sm); }
.officer__frame img { width: 132%; margin-inline-start: -16%; height: auto; }
```

The official photo is square; 132% width makes its height 132% of the frame, so the bottom nameplate falls below the crop while faces stay centered. Verify visually on one portrait at 1440 and 390 before applying to all.

- [ ] **Step 2: Feedback page**

`PageHero title="Feedback"`. `Band variant="mint"` with a white card: `h2` “Share feedback with the SSLG”, a 68ch paragraph explaining that responses go to the official form and that the anonymous option exists, the iframe below, and a fallback line.

```tsx
<iframe
  className="feedback-frame"
  src={`${FEEDBACK_FORM_URL}?embedded=true`}
  title="BSANHS SSLG feedback form"
  loading="lazy"
  referrerPolicy="no-referrer"
/>
<p className="feedback-fallback">
  Form not loading? <a href={FEEDBACK_FORM_URL}>Open it in a new tab</a>.
</p>
```

`min-height: 900px`, width 100%, border 0, white background. Do not wrap the iframe in a link.

- [ ] **Step 3: NotFound (reuse from Task 6)**

`NotFound.tsx` was created in Task 6 (execution ruling). Verify it matches this spec — `PageHero title="Page not found" lead="That page is not part of the SSLG record."`, `Band variant="deep"` with links to Home and Accomplishments, and `<PageMeta title="Page not found" description="…" />` with **no** `path` so it stays `noindex` — and adjust only if it drifted. Catch-all route: `<Route path="*" element={<NotFound />} />` inside the layout (wired in Step 4).

- [ ] **Step 4: Wire all routes**

```tsx
<Route element={<SiteLayout />}>
  <Route index element={<Home />} />
  <Route path="finance" element={<Finance />} />
  <Route path="accomplishments" element={<Accomplishments />} />
  <Route path="accomplishments/:slug" element={<ActivityPage />} />
  <Route path="photos" element={<Photos />} />
  <Route path="transparency" element={<Transparency />} />
  <Route path="about-us" element={<About />} />
  <Route path="feedback" element={<Feedback />} />
  <Route path="*" element={<NotFound />} />
</Route>
```

- [ ] **Step 5: Tests**

```tsx
test("About lists all 27 officers and the objectives", () => {
  render(<MemoryRouter><About /></MemoryRouter>);
  expect(screen.getAllByRole("img", { name: /^Portrait of /i })).toHaveLength(27);
  for (const name of ["Hon. Rhian Jade L. Castro", "Dr. Amparo M. Munoz", "Hon. Mira Narciso"]) {
    expect(screen.getByText(name)).toBeInTheDocument();
  }
  expect(screen.getByRole("heading", { level: 2, name: /Duties, Responsibilities/i })).toBeInTheDocument();
});

test("Feedback embeds the form with a fallback link", () => {
  render(<MemoryRouter><Feedback /></MemoryRouter>);
  expect(screen.getByTitle("BSANHS SSLG feedback form")).toHaveAttribute("src", expect.stringContaining("?embedded=true"));
  expect(screen.getByRole("link", { name: /open it in a new tab/i })).toHaveAttribute("href", expect.stringContaining("docs.google.com/forms"));
});

test("the 404 keeps the layout and offers a way home", () => {
  render(<MemoryRouter><NotFound /></MemoryRouter>);
  expect(screen.getByRole("heading", { level: 1, name: /page not found/i })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /home/i })).toBeInTheDocument();
});
```

- [ ] **Step 6: Run, deploy, compare About**

```bash
npm test -- tests/pages.test.tsx
npm run build && npm run deploy
node .superpowers/shots/cdp-shot.mjs https://sslg-2sr.pages.dev/about-us 1440 900 .superpowers/shots/build-about-1440.png full
node .superpowers/shots/cdp-shot.mjs https://sslg-2sr.pages.dev/feedback 390 844 .superpowers/shots/build-feedback-390.png full
git add -A && git commit -m "feat: add about, feedback and not-found pages"
```

---

### Task 9: SEO, accessibility, responsive audit and cutover

**Files:**
- Create: `scripts/generate-seo.mjs`, `public/robots.txt`, `docs/CREDITS.md`
- Modify: `public/_redirects`, `public/_headers`, `package.json`, `src/components/PageMeta.tsx`
- Test: manual + scripted checks

**Interfaces:**
- Produces: `dist/sitemap.xml`, security headers, per-page metadata, a verified live site.

- [ ] **Step 1: Sitemap**

Read `SITE_URL` from `src/config.ts` (or duplicate the literal and assert it matches). Emit `/`, `/finance`, `/accomplishments`, `/photos`, `/transparency`, `/about-us`, `/feedback` and every `/accomplishments/<slug>`. Escape XML. Fail if `SITE_URL` is empty.

Add to the build: `"build": "tsc --noEmit && tsc -p functions --noEmit && vite build && node scripts/generate-seo.mjs"`.

- [ ] **Step 2: Redirects and headers**

`public/_redirects`:

```
/home        /            301
/about       /about-us    301
/*           /index.html 200
```

`public/_headers`:

```
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  X-Frame-Options: SAMEORIGIN
/api/*
  Cache-Control: public, max-age=60, s-maxage=300, stale-while-revalidate=86400
```

Add a Content-Security-Policy only after verifying the form and image hosts:

```
Content-Security-Policy: default-src 'self'; img-src 'self' https://lh3.googleusercontent.com https://drive.google.com data:; frame-src https://docs.google.com; style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self'; connect-src 'self'
```

Apply it on the first deployment, then test every page in a private window; revert the header if the Google Form needs another host.

- [ ] **Step 3: Metadata per route**

Every page passes `path`. `PageMeta` sets `og:image` once (it is static). Add `og:image`, `og:image:alt` to the effect only if missing. Confirm `/404` stays `noindex,follow` with no canonical.

- [ ] **Step 4: Credits**

`docs/CREDITS.md`:

```md
# Credits

- Design guidance: Jakub Krehel, https://github.com/jakubkrehel/skills
- UI motion patterns adapted from Uiverse (MIT):
  - Button shine — https://uiverse.io/Codecite/angry-bullfrog-58
  - Text/bar sweep — https://uiverse.io/neerajbaniwal/hungry-mule-59
  - Card hover lift — https://uiverse.io/gharsh11032000/rare-bobcat-17
  - Dot loader — https://uiverse.io/abrahamcalsin/serious-turkey-52
- School and SSLG seals, officer portraits and activity artwork are published by
  Benigno S. Aquino National High School and its Supreme Secondary Learner Government.
```

- [ ] **Step 5: Run the design review**

Apply `better-interface` to the rendered build, in its order: accessibility → layout → writing → typography → colors → UI. Then run `interface-review` against the full range of this plan's commits. Report every finding with `path:line`, before/after and severity; fix every HIGH before deploying. At minimum verify:

- Keyboard-only pass on all seven pages: skip link, menu toggle, tabs, lightbox, forms, footer.
- 320px and 200% zoom with no horizontal scroll and no clipped controls.
- Focus visible on every stop; no focus hidden under the sticky header (`scroll-padding-block-start`).
- Reduced-motion replay: no beams animation, no nudge, no sweep, no card zoom; static cues remain.
- Contrast spot checks with the measured pairs in this plan.
- `lang="en"`, one `h1` per page, ordered headings, every image with correct `alt` (decorative seals empty).
- All times and figures use `tabular-nums` where they change.

- [ ] **Step 6: Live checks**

```bash
for p in / /finance /accomplishments /photos /transparency /about-us /feedback /nope; do
  printf "%s %s\n" "$(curl -s -o /dev/null -w '%{http_code}' https://sslg-2sr.pages.dev$p)" "$p"
done
curl -s https://sslg-2sr.pages.dev/sitemap.xml | grep -c "<url>"
curl -s -o /dev/null -w "%{http_code}\n" "https://sslg-2sr.pages.dev/api/documents?folder=../../etc"
```

Expected: eight 200s (the SPA serves `/nope` and React renders 404), 18 sitemap URLs (7 pages + 11 activities), `400` for traversal. Confirm `/api/*` still returns `503 drive-not-configured` until the secret is set.

- [ ] **Step 7: Deploy and record**

```bash
npm run deploy
git add -A && git commit -m "feat: add sitemap, headers, credits and finish the design audit"
```

Record the deployment URL, the known unproven items (Drive data, KV hit, real photo counts), and the owner steps in the plan ledger. Do not claim Drive data was verified.

---

## Owner-only follow-ups (cannot be done in this session)

1. Create a Google Cloud project, enable the Drive API, create an API key restricted to the Drive API, and run `npx wrangler pages secret put GOOGLE_API_KEY --project-name sslg`, then redeploy. Verify `/api/albums` returns real album names, `/api/photos` returns counts, `/api/documents?folder=finance` returns files, and the second call is served from KV.
2. Confirm the Treasurer byline. The published financial report prints “Samantha C. De Venecia” while the About roster lists “Hon. Samantha Joy C. De Venecia”. Per the Task 3/Task 7 execution rulings, the Finance page quotes the report (“Samantha C. De Venecia”, from `FINANCE_REPORT.preparedBy`) and the About page keeps the roster spelling. Confirm whether the owner wants these unified to one spelling on both pages.
3. Confirm the Facebook destination: the published bar says `facebook.com/bsanhssslg` but links to `facebook.com/SSLGBSANHS`. This plan labels `facebook.com/SSLGBSANHS`.
4. Confirm the GPOA folder is the correct public folder (`16_T5tmGrzwHF6X9lR1JxrNY8K1C9EYnN`).
5. Confirm the portraits and activity artwork may be republished (they are already public on the Google Sites).
6. After 30 days with no missing content, retire or unlink the Google Sites page. Keep the Drive folders.

## Verification statement to carry into the ledger

Anything not observed in a browser is `Not verified`. In this session the Drive-backed states will be verified against mocks and against the live `503`; they are not evidence of real album, photo or document data.
