# SSLG Website on Cloudflare Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Google Sites shell with a static React site on Cloudflare Pages, forked from `WEBSITES/chembank`, whose galleries and document lists read the public SSLG Drive folders so new photos, albums, and reports appear without a site edit.

**Architecture:** Cloudflare Pages serves a Vite/React single-page app. Pages Functions under `/api/*` proxy the public Google Drive folders using a Drive API key held only as a Worker secret, cache every listing in Workers KV for 15 minutes, and expose three JSON endpoints (`/api/albums`, `/api/photos`, `/api/documents`). The browser never sees the key and never calls Google's API directly, so the key can be revoked and the folder allowlist can be changed in one file. Page copy lives in typed content modules committed to the repo; photos, albums, and documents live only in Drive.

**Tech Stack:** Vite 8 · React 19 · TypeScript · React Router 7 · Cloudflare Pages + Pages Functions · Workers KV · Google Drive API v3 · Vitest.

**Spec:** This plan supersedes the Google Sites update path in `docs/superpowers/plans/2026-11-08-sslg-site-update.md`; that document remains the source for the activity copy, Drive IDs, and flagged facts. No separate design spec exists.

## Global Constraints

- All site code lives in `C:\Users\Ma Christine\Downloads\WEBSITES\sslg`. Nothing is written into Drive, and no site code is added to the `SSLG MEMOS` vault except this plan.
- Drive stays read-only. Never upload, move, rename, or change permissions on anything in Drive.
- Never commit a Google credential. `GOOGLE_API_KEY` exists only as a Cloudflare secret and in a gitignored `.dev.vars` for local work.
- Do not invent dates, names, or outcomes. `date` is optional on every activity; no page renders a date that is not documented in the vault.
- Keep the published URLs: `/`, `/finance`, `/accomplishments`, `/transparency`, `/about-us`, `/feedback`. Add `/photos` and `/accomplishments/:slug`. Existing bookmarks keep working.
- Keep the published nav order: Home · Finance · Accomplishments · Transparency · About us · Feedback, with Photos inserted after Accomplishments.
- Free tier only: Cloudflare Pages, Pages Functions, KV, and the Drive API quota.
- Fork `chembank`'s proven skeleton (build, router, fonts, test setup). Do not fork its chemistry content, PWA, or theme toggle.
- The site is public and school-official. Officer names and roles are already published on the live site; everything else about students stays off the site.

## Why this shape

| Option | Photos update without a deploy | Design control | Key exposure | Verdict |
| --- | --- | --- | --- | --- |
| Google Sites + Drive iframes | Yes | None | None | Today's ceiling |
| Drive `embeddedfolderview` iframes on the new site | Yes | Low (Google-branded grid inside our page) | None | Fallback only |
| Browser calls Drive API directly | Yes | Full | Key ships to every visitor | Rejected |
| **Pages Function + KV cache + Drive API** | **Yes (≤15 min)** | **Full** | **Server-side only** | **Chosen** |
| R2 mirror synced by cron | Yes, after sync | Full | Server-side | Phase 2 if Drive quota or uptime becomes a problem |

What becomes automatic: new photos in an existing album, a brand-new album or term folder under the PIO root, new finance reports, minutes, notices, elections, proposals, memos, and every activity cover that comes from an album. What still needs one content edit and a deploy: the title and caption of a new activity, officer changes, and page copy.

## Drive map (public, read-only)

| Key | ID |
| --- | --- |
| PIO photo root | `1QbMxIfTuL9-qJ3T9YgfuYyErHexqxBiQ` |
| Records root | `1XU9s-pHPCk_zJQo7LSOjcmtGeIiI9JeM` |
| Finance reports | `1NhgG1fkfxch70E3hzb5YhTgCK0PWKcdV` |
| Minutes of the meeting | `1qm3Z6OmjxFa41OsjTPrBUJEl57-GSGH5` |
| Notice of meeting | `1SVzssvcj1IkEndY0Mp5Nv8WhDsaQUDl4` |
| Elections | `1hiqv7sFda_cGWVo7OtgJs5cpPS-buZ4L` |
| Project proposals | `15vGFBRfifPvEUkN5yo1iv87MQPAoaFHE` |
| School memorandums | `1xszCcvP83aaVus3xLQ4f1RDmjvWqLHUj` |
| General Plan of Action folder | `16_T5tmGrzwHF6X9lR1JxrNY8K1C9EYnN` |
| Accomplishment reports | `1_44iCUzUJAaBi0cc0a7DcpauUPpRJIxj` |
| Legal bases PDF | `1MthdcNxs_w_QoLuus-nVcAoi4xaACNKd` |
| Album — Teachers' Day | `1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz` |
| Album — LGCC Clean-Up | `1_0DykrJF1DVEzwo19m9mbgAp2HRi85ix` |
| Album — Earthquake Drill | `1UT4M9b8TrctZ-d-tGjAEPbLADbUo_ik8` |
| Album — Grade 7 Election | `1y2tKu7-5uoxBK-jQ2dN0sEIqCj2tL8av` |
| Album — Brigada Eskwela | `1p-60nKJtTiACOF1Kkj8OLCuEFlnhR1sn` |
| Album — Induction (empty) | `1iPxMcxI61C0pIZDc_2raj4IYfZAyxLL_` |
| Album — Club Fair (empty) | `1S6yMnWlYO_ilgiwc5akv32WAOYmI3rtf` |
| ACR — GPOA (cover page) | `1pdEWqxhVOBNwM71FUpsyVNdwUjCbezWJ` |
| ACR — Election of Registered Clubs (cover page) | `11NW0ZtYcFbPeRcNgpFwT26_IJUln8n1S` |

## File structure

```
WEBSITES/sslg/
  wrangler.toml                 Pages project name, KV binding
  functions/
    api/_drive.ts               Drive fetch, KV cache, allowlist
    api/albums.ts               GET /api/albums
    api/photos.ts               GET /api/photos?album=
    api/documents.ts            GET /api/documents?folder=
  shared/drive.ts               Types + thumbnail URL builders (browser + Worker)
  src/
    config.ts                   Site name, URL, Facebook, form URL
    content/{types,site,activities,officers,documents}.ts
    components/{SiteLayout,PageMeta,SectionHead,ActivityCard,PhotoGrid,AlbumViewer,DocumentList,SmartImage,EmptyState}.tsx
    lib/{api,useAlbums,format}.ts
    pages/{Home,Accomplishments,ActivityPage,Photos,Finance,Transparency,About,Feedback,NotFound}.tsx
    styles/{tokens,base,components,pages,responsive}.css
  scripts/generate-seo.mjs
  public/{_redirects,_headers,robots.txt,favicon.svg}
  tests/
```

Each file has one job: page components compose, `lib` owns fetching, `content` owns copy, `shared/drive.ts` owns URL construction, `functions/api/_drive.ts` owns Google access.

---

### Task 1: Fork the chembank shell into `WEBSITES/sslg` and deploy a smoke page

**Files:**
- Create: `WEBSITES/sslg/` (copy of chembank's skeleton)
- Create: `WEBSITES/sslg/wrangler.toml`
- Create: `WEBSITES/sslg/.gitignore`
- Modify: `WEBSITES/sslg/package.json`, `index.html`, `src/main.tsx`, `src/App.tsx`
- Create: `WEBSITES/sslg/src/pages/Home.tsx` (temporary smoke page)

**Interfaces:**
- Consumes: `chembank` at `C:\Users\Ma Christine\Downloads\WEBSITES\chembank`.
- Produces: a deployable Pages project named `sslg` at `https://sslg-2sr.pages.dev`, React Router mounted, fonts loaded, Vitest configured, git initialized.

- [ ] **Step 1: Copy only the skeleton**

```bash
cd "C:/Users/Ma Christine/Downloads/WEBSITES"
mkdir -p sslg/src/components sslg/src/styles sslg/src/pages sslg/public sslg/tests
cp chembank/package.json chembank/package-lock.json chembank/tsconfig.json chembank/vite.config.ts chembank/vitest.config.ts sslg/
cp chembank/index.html sslg/
cp chembank/.gitignore sslg/
cp chembank/src/main.tsx chembank/src/config.ts chembank/src/vite-env.d.ts sslg/src/
cp chembank/src/components/PageMeta.tsx sslg/src/components/
cp chembank/src/styles/tokens.css chembank/src/styles/base.css sslg/src/styles/
touch sslg/src/styles/components.css sslg/src/styles/pages.css sslg/src/styles/responsive.css
cp chembank/public/favicon.svg chembank/public/icon.svg chembank/public/_redirects chembank/public/_headers sslg/public/
cp chembank/tests/setup.ts sslg/tests/
```

Do not copy `src/data`, `src/pages`, `src/styles/components.css`, `src/styles/pages.css`, `src/styles/responsive.css` from chembank, or `content/`, `docs/`, `dist/`, `node_modules/`, `.github/`, `.git/`. The three empty stylesheets are written fresh in Task 2; chembank's versions carry chemistry-only rules.

- [ ] **Step 2: Replace package.json with the pruned manifest**

```json
{
  "name": "sslg",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "pages:dev": "npm run build && wrangler pages dev dist",
    "deploy": "npm run build && wrangler pages deploy dist --project-name sslg --branch main"
  },
  "dependencies": {
    "@fontsource/ibm-plex-mono": "^5.3.0",
    "@fontsource/ibm-plex-sans": "^5.3.0",
    "@fontsource/instrument-serif": "^5.3.0",
    "react": "^19.3.1",
    "react-dom": "^19.3.1",
    "react-router-dom": "^7.18.5"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.20260101.0",
    "@testing-library/jest-dom": "^7.0.1",
    "@testing-library/react": "^16.3.3",
    "@types/react": "^19.3.0",
    "@types/react-dom": "^19.3.0",
    "@vitejs/plugin-react": "^6.2.1",
    "jsdom": "^29.1.1",
    "typescript": "^7.0.2",
    "vite": "^8.3.6",
    "vitest": "^5.1.0",
    "wrangler": "^4.158.0"
  }
}
```

- [ ] **Step 3: Write wrangler.toml and remove the PWA plugin**

```toml
name = "sslg"
compatibility_date = "2026-11-08"
pages_build_output_dir = "dist"
```

In `vite.config.ts`, keep only the React plugin: `plugins: [react()]`, `build: { target: "es2022" }`.

In `tsconfig.json`, add `"shared"` to `include` so the root typecheck sees `shared/drive.ts` when tests import it:

```json
"include": ["src", "shared", "tests", "vite.config.ts", "vitest.config.ts"]
```

- [ ] **Step 4: Write the temporary App and Home**

`src/main.tsx`: drop `UpdatePrompt` and `initTheme`; import the five stylesheets and render `<BrowserRouter><App /></BrowserRouter>`.

`src/App.tsx`:

```tsx
import { Route, Routes } from "react-router-dom";
import Home from "./pages/Home";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
    </Routes>
  );
}
```

`src/pages/Home.tsx`:

```tsx
import { PageMeta } from "../components/PageMeta";

export default function Home() {
  return (
    <main style={{ padding: "4rem 1.5rem" }}>
      <PageMeta title="Home" description="Supreme Secondary Learner Government of Benigno S. Aquino National High School." />
      <h1>Benigno S. Aquino National High School</h1>
      <p>Supreme Secondary Learner Government — site migration in progress.</p>
    </main>
  );
}
```

Update `src/config.ts`:

```ts
export const SITE_URL = "https://sslg-2sr.pages.dev";
export const APP_NAME = "BSANHS SSLG";
export const SITE_DESCRIPTION =
  "Official website of the Supreme Secondary Learner Government of Benigno S. Aquino National High School.";
export const FACEBOOK_URL = "https://www.facebook.com/SSLGBSANHS";
export const FEEDBACK_FORM_URL =
  "https://docs.google.com/forms/d/e/1FAIpQLSc7Zpvp_lFYk--GfG4YjbdckcEJ-0hRvskEjJ1YMByPSq_0bg/viewform";
```

In `PageMeta.tsx`, change the suffix from `ChemBank` to `APP_NAME`.

- [ ] **Step 5: Install, build, and typecheck**

```bash
cd "C:/Users/Ma Christine/Downloads/WEBSITES/sslg"
npm install
npm run build
```

Expected: `dist/index.html`, `dist/assets/*.js`, no TypeScript errors.

- [ ] **Step 6: Deploy the smoke page**

```bash
npx wrangler pages deploy dist --project-name sslg --branch main
```

If wrangler asks to create the project, accept. Expected: `Deployment complete` and `https://sslg-2sr.pages.dev`.

- [ ] **Step 7: Verify and commit**

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://sslg-2sr.pages.dev
curl -s https://sslg-2sr.pages.dev | grep -o "Benigno S. Aquino National High School" | head -1
git init && git add -A && git commit -m "chore: fork Cloudflare Pages shell from chembank"
```

Expected: `200`, the school name printed, one commit.

---

### Task 2: Design system, masthead, navigation, footer

**Files:**
- Modify: `src/styles/tokens.css`, `base.css`, `components.css`, `pages.css`, `responsive.css`
- Create: `src/components/SiteLayout.tsx`, `src/components/SectionHead.tsx`
- Modify: `src/main.tsx`, `src/App.tsx`
- Replace: `public/favicon.svg`, `public/icon.svg`
- Test: `tests/layout.test.tsx`

**Interfaces:**
- Produces: `<SiteLayout />` as the router layout with `<Outlet />`; `<SectionHead eyebrow title lead />`; CSS variables consumed by every later task.

- [ ] **Step 1: Replace the token block**

```css
:root {
  --paper: #f5f0e4;
  --paper-2: #ece4d2;
  --surface: #fffdf6;
  --ink: #14213a;
  --ink-2: #3c4a63;
  --muted: #6b7280;
  --navy: #0f2440;
  --navy-2: #1a3557;
  --gold: #b8862f;
  --gold-soft: #e8d3a4;
  --brick: #8a3324;
  --rule: #d8cdb6;
  --shadow: 0 1px 0 rgba(20, 33, 58, 0.06), 0 12px 28px -20px rgba(20, 33, 58, 0.45);
  --radius: 4px;
  --font-display: "Instrument Serif", Georgia, serif;
  --font-ui: "IBM Plex Sans", system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, monospace;
  --page-max: 1160px;
  --measure: 66ch;
  --gutter: clamp(1rem, 4vw, 2.75rem);
  --ease: cubic-bezier(0.22, 0.61, 0.36, 1);
}
```

Remove the dark-theme block. Design direction: an official school record, not a product landing page — parchment ground, navy masthead rule, serif display, numbered section labels, tabular document lists, photo grids with square corners and thin rules.

- [ ] **Step 1b: Replace the chemistry favicon and icon**

The forked artwork is chembank's hexagon and benzene chevron. Replace both files wholesale; `index.html` already points at them.

`public/favicon.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="SSLG">
  <rect width="64" height="64" fill="#0f2440"/>
  <rect x="5" y="5" width="54" height="54" fill="none" stroke="#b8862f" stroke-width="1.5" opacity="0.85"/>
  <path d="M13 43.5C18 41.6 26 41.2 31 43V20.8C26 19 18 19.4 13 21.2Z" fill="#f5f0e4"/>
  <path d="M51 43.5C46 41.6 38 41.2 33 43V20.8C38 19 46 19.4 51 21.2Z" fill="#f5f0e4"/>
  <path d="M32 20.4V43.2" stroke="#b8862f" stroke-width="1.6"/>
</svg>
```

`public/icon.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="SSLG">
  <rect width="64" height="64" rx="14" fill="#0f2440"/>
  <path d="M11 45C17 42.6 26.5 42.2 32 44.4V19.6C26.5 17.4 17 17.8 11 20.2Z" fill="#f5f0e4"/>
  <path d="M53 45C47 42.6 37.5 42.2 32 44.4V19.6C37.5 17.4 47 17.8 53 20.2Z" fill="#f5f0e4"/>
  <path d="M32 19V44.4" stroke="#b8862f" stroke-width="1.8"/>
</svg>
```

An open book on the site's navy, ruled in gold: legible at 16px, no letterforms that depend on installed fonts. Verify in the browser tab before committing.

- [ ] **Step 2: Build SiteLayout**

```tsx
import { NavLink, Outlet } from "react-router-dom";
import { APP_NAME, FACEBOOK_URL } from "../config";

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
  return (
    <div className="site">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="masthead">
        <div className="masthead-top">
          <span>S.Y. 2026–2027</span>
          <span>Benigno S. Aquino National High School</span>
        </div>
        <div className="masthead-main">
          <NavLink to="/" className="wordmark">
            <span className="wordmark-mark">SSLG</span>
            <span className="wordmark-sub">Supreme Secondary Learner Government</span>
          </NavLink>
          <nav className="site-nav" aria-label="Primary">
            {NAV.map(([to, label]) => (
              <NavLink key={to} to={to} end={to === "/"}>{label}</NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main id="main" className="site-main"><Outlet /></main>
      <footer className="site-footer">
        <p>Benigno S. Aquino National High School Supreme Secondary Learner Government</p>
        <p><a href={FACEBOOK_URL} rel="noreferrer">facebook.com/bsanhssslg</a></p>
        <p className="footer-note">{APP_NAME} · Public records and activity reports</p>
      </footer>
    </div>
  );
}
```

Below 820px the nav wraps; give `.site-nav a` a 44px tap target. The mobile menu is the wrapped nav, not a drawer — seven short labels fit on two rows on a 390px screen.

`SectionHead.tsx`:

```tsx
export function SectionHead({ eyebrow, title, lead }: { eyebrow: string; title: string; lead?: string }) {
  return (
    <header className="section-head">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {lead && <p className="lead">{lead}</p>}
    </header>
  );
}
```

- [ ] **Step 3: Wire the layout into the router**

```tsx
<Route element={<SiteLayout />}>
  <Route index element={<Home />} />
  <Route path="finance" element={<Finance />} />
  {/* remaining routes added in later tasks */}
</Route>
```

For this task, add only the index route; the other pages arrive in Tasks 5–8.

- [ ] **Step 4: Test nav order and skip link**

```tsx
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SiteLayout } from "../src/components/SiteLayout";

test("keeps the published nav order with Photos after Accomplishments", () => {
  render(
    <MemoryRouter>
      <Routes>
        <Route element={<SiteLayout />}>
          <Route index element={<p>home</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
  const nav = screen.getByRole("navigation", { name: "Primary" });
  expect(within(nav).getAllByRole("link").map((a) => a.textContent)).toEqual([
    "Home", "Finance", "Accomplishments", "Photos", "Transparency", "About us", "Feedback",
  ]);
  expect(screen.getByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main");
});
```

- [ ] **Step 5: Run and commit**

```bash
npm test -- tests/layout.test.tsx
git add -A && git commit -m "feat: add SSLG masthead, navigation, and design tokens"
```

Expected: 1 passing test.

---

### Task 3: Typed content layer with the published copy

**Files:**
- Create: `src/content/types.ts`, `site.ts`, `activities.ts`, `officers.ts`, `documents.ts`
- Test: `tests/content.test.ts`

**Interfaces:**
- Produces: `Activity`, `Officer`, `DocumentGroup` types; `ACTIVITIES` (10 entries, ordered newest first); `OFFICERS`; `DOCUMENT_GROUPS`; `HOME` copy. Later tasks import these and never hardcode copy.

- [ ] **Step 1: Define types**

```ts
export type Cover =
  | { kind: "album"; album: string }
  | { kind: "doc"; fileId: string }
  | { kind: "none" };

export interface Activity {
  slug: string;
  title: string;
  caption: string;
  cover: Cover;
  album?: string;
  date?: string;        // ISO date only when documented in the vault
  reportUrl?: string;   // Drive file or folder with the accomplishment report
  featured?: boolean;
}

export interface Officer {
  name: string;
  role: string;
  group: "executive" | "grade" | "school";
}

export interface DocumentGroup {
  key: "minutes" | "notices" | "elections" | "proposals" | "memorandums" | "finance";
  label: string;
  blurb: string;
}
```

- [ ] **Step 2: Write `activities.ts`**

Order is editorial, newest first. Do not add dates that are not in the vault.

| slug | title | caption | cover | album / report |
| --- | --- | --- | --- | --- |
| `world-teachers-day-2026` | World Teachers' Day 2026 | To honor the dedication and service of teachers, this celebration recognized their contributions to learners and the school community through a programme led by the SSLG and LGCC. | album | `1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz` |
| `lgcc-clean-up-2026` | LGCC Clean-Up Drive – Project ECOLEAD | To promote environmental stewardship and maintain a clean learning environment, the LGCC and SSLG led a school-wide clean-up drive under Project ECOLEAD. | album | `1_0DykrJF1DVEzwo19m9mbgAp2HRi85ix` |
| `earthquake-drill-2026` | National Simultaneous Earthquake Drill 2026 | To strengthen disaster preparedness and safety awareness, SSLG officers and Red Cross Youth members joined the 2026 National Simultaneous Earthquake Drill. | album | `1UT4M9b8TrctZ-d-tGjAEPbLADbUo_ik8` |
| `election-registered-clubs-2026` | Election of Registered School Clubs and Organizations | To promote democratic participation and student leadership, this activity elected the officers of registered school clubs and organizations. | doc `11NW0ZtYcFbPeRcNgpFwT26_IJUln8n1S` | report = ACR-004 |
| `gpoa-crafting-2026` | Crafting of the SSLG General Plan of Action | To set the direction of student-led programmes for the school year, the SSLG crafted its General Plan of Action with the guidance of the LGCC and advisers. | doc `1pdEWqxhVOBNwM71FUpsyVNdwUjCbezWJ` | report = ACR-005 |
| `brigada-eskwela-2026` | Brigada Eskwela 2026 | To prepare the school facilities for the opening of classes, the SSLG, LGCC, and registered clubs and organizations took part in Brigada Eskwela. | album | `1p-60nKJtTiACOF1Kkj8OLCuEFlnhR1sn` |
| `club-organizations-membership-drive-2026` | Club and Organizations Membership Drive | To foster enhanced student engagement and dedication, this project helped the students pick what fits their interests and goals that will also help them feel more involved in their community. | album | `1S6yMnWlYO_ilgiwc5akv32WAOYmI3rtf` |
| `grade-7-representatives-election-2026` | Grade 7 Representatives Election for the S.Y 2026-2027 | To promote student leadership, this project facilitated the election of Grade 7 Representatives who now serve as the official spokespeople of their year level within the Supreme Secondary Learner Government (SSLG). | album | `1y2tKu7-5uoxBK-jQ2dN0sEIqCj2tL8av` |
| `induction-ceremony-2026` | Onto the Next Leaders Induction Ceremony | To instill a sense of responsibility, leadership, and commitment among the officers, this event formally introduced and recognized the newly elected student leaders. | album | `1iPxMcxI61C0pIZDc_2raj4IYfZAyxLL_` |
| `project-tinig` | Project Tinig | To strengthen transparency, accountability, and student participation by establishing an online platform where students can access SSLG reports, announcements, financial summaries, and submit feedback or concerns, ensuring that every voice is heard. | none | — |

Set `reportUrl` with these Drive IDs (file view URLs): Teachers' Day `1KiYs31znp_3EKYMNV0hxJCQvcK90mtws`; LGCC `10EnbVjEL94AXwWm4IeW5QRCi29Z9tJy5`; Election of Registered Clubs `11NW0ZtYcFbPeRcNgpFwT26_IJUln8n1S`; GPOA `1pdEWqxhVOBNwM71FUpsyVNdwUjCbezWJ`; Brigada `16KFJZmhSiTPeEV0JIO8ttj894RZBbuQQ`; Club Drive `1ZRyWYuL4w1oZcgo0V5HU-vr0JMq6g-4Y`; Grade 7 `168M9PVEHlju8RL0DRNUwljBU9BPS0pGa`; Induction `1omiyOdHtxgngsb7WMcpNGTaZsaMBgrYE`. Earthquake Drill has no report file in Drive; omit `reportUrl`. 

`project-tinig` is a standing project, not an accomplishment report; set `featured: true` on `world-teachers-day-2026` only. The two typos in the published copy are corrected here: `=formally` → `formally`, and `who now serves` → `who now serve`.

- [ ] **Step 3: Write `officers.ts`** with the 27 published names, in this order (add `import type { Officer } from "./types";` at the top):

```ts
export const OFFICERS = [
  { name: "Hon. Rhian Jade L. Castro", role: "SSLG President", group: "executive" },
  { name: "Hon. Aaron Y. Hernandez", role: "SSLG Vice President", group: "executive" },
  { name: "Hon. Micaella Sabelle R. Monloy", role: "SSLG Secretary", group: "executive" },
  { name: "Hon. Sophia Elise C. Aguas", role: "SSLG Public Information Officer", group: "executive" },
  { name: "Hon. Samantha Joy C. De Venecia", role: "SSLG Treasurer", group: "executive" },
  { name: "Hon. Diyah Marowe T. Hipolito", role: "SSLG Auditor", group: "executive" },
  { name: "Hon. Ian Kendrick M. Lapuz", role: "SSLG Protocol Officer", group: "executive" },
  { name: "Hon. Rajon Landolf F. Lobo", role: "SSLG Grade 12 Chairperson", group: "grade" },
  { name: "Hon. Yuan B. Cutiongco", role: "SSLG Grade 12 Representative", group: "grade" },
  { name: "Hon. Blu Enno U. Sampang", role: "SSLG Grade 11 Chairperson", group: "grade" },
  { name: "Hon. Godswill Jobel D. Noe", role: "SSLG Grade 11 Representative", group: "grade" },
  { name: "Hon. Akio Nathan C. Manlapaz", role: "SSLG Grade 10 Chairperson", group: "grade" },
  { name: "Hon. Rommel S. Dizon, Jr.", role: "SSLG Grade 10 Representative", group: "grade" },
  { name: "Hon. Vince Yael P. Garin", role: "SSLG Grade 9 Chairperson", group: "grade" },
  { name: "Hon. Juliana Bea Q. De Guzman", role: "SSLG Grade 9 Representative", group: "grade" },
  { name: "Hon. Josh Edan D. Porlucas", role: "SSLG Grade 8 Chairperson", group: "grade" },
  { name: "Hon. Zyrene Gale W. Tinio", role: "SSLG Grade 8 Representative", group: "grade" },
  { name: "Hon. Chloe Danielle L. David", role: "SSLG Grade 7 Chairperson", group: "grade" },
  { name: "Hon. Kean Albert J. Pineda", role: "SSLG Grade 7 Representative", group: "grade" },
  { name: "Dr. Amparo M. Munoz", role: "Principal IV", group: "school" },
  { name: "Hon. Gilbert Policarpio", role: "Head Teacher VI", group: "school" },
  { name: "Hon. Aaron Khristian Banag", role: "SSLG Adviser", group: "school" },
  { name: "Hon. Christopher Kabilangan", role: "SSLG Co-Adviser", group: "school" },
  { name: "Hon. Jayvee Zarate", role: "SSLG Co-Adviser", group: "school" },
  { name: "Hon. Mary Joy Santos", role: "SSLG Co-Adviser", group: "school" },
  { name: "Hon. Ma Theresa Gatchalian", role: "SSLG Co-Adviser", group: "school" },
  { name: "Hon. Mira Narciso", role: "SSLG Co-Adviser", group: "school" },
] satisfies Officer[];
```

The live page's `Grade 1 1`, `Grade 1 1`, `Grade 1 0` splits are Grade 11 and Grade 10; they are written correctly here. The live Finance page says "Samantha C. De Venecia"; use the About-page spelling above and flag the difference to the adviser.

- [ ] **Step 4: Write `documents.ts` and `site.ts`**

```ts
export const DOCUMENT_GROUPS: DocumentGroup[] = [
  { key: "minutes", label: "Minutes of the Meeting", blurb: "Signed minutes of every SSLG meeting." },
  { key: "notices", label: "Notice of Meeting", blurb: "Call and agenda for each meeting." },
  { key: "elections", label: "Elections", blurb: "Election materials and results." },
  { key: "proposals", label: "Project Proposals", blurb: "Approved activity proposals (AP-SSLG series)." },
  { key: "memorandums", label: "School Memorandums", blurb: "School, Division, and DepEd issuances." },
  { key: "finance", label: "Financial Reports", blurb: "Latest financial reports, prepared by the Treasurer." },
];
```

`site.ts` exports the mandate paragraph, the five objectives, and the three duties printed on the live About page. Use these strings:

```ts
export const MANDATE =
  "The SSLG shall be the highest student governing body in the school, be the forefront of learners' rights and welfare; model of learners' excellence; and representation of good character and deep sense of good moral values.";

export const OBJECTIVES = [
  "Be the forefront of learners' rights and welfare",
  "Model of the learners' excellence",
  "Representation of good character and deep sense of moral values",
  "Empower learners to strive for excellence in academics, leadership, and academic responsibility",
  "Encourage learners to be proactive members of the society",
];

export const DUTIES = [
  "To support and promote the ideals, principles, thrusts, and objectives of the SSLG, the School, and the Department of Education",
  "To represent learners in school matters deemed as necessary",
  "To serve as a representative of learners in voicing their opinions, suggestions, and grievances",
];
```

Only `necessarry` → `necessary` and the stray `a` before `proactive` are changed.

- [ ] **Step 5: Test content invariants**

```ts
test("slugs are unique and every activity has copy", () => {
  const slugs = ACTIVITIES.map((a) => a.slug);
  expect(new Set(slugs).size).toBe(slugs.length);
  for (const a of ACTIVITIES) {
    expect(a.title.length).toBeGreaterThan(3);
    expect(a.caption.length).toBeGreaterThan(30);
    expect(a.caption).not.toMatch(/=formally|who now serves/);
  }
});
test("album covers reference a known album id", () => {
  for (const a of ACTIVITIES.filter((x) => x.cover.kind === "album")) {
    expect(a.album).toMatch(/^[A-Za-z0-9_-]{20,}$/);
  }
});
```

- [ ] **Step 6: Run and commit**

```bash
npm test -- tests/content.test.ts
git add -A && git commit -m "feat: add typed SSLG content with published copy"
```

---

### Task 4: Drive API proxy with KV cache

**Files:**
- Create: `shared/drive.ts`
- Create: `functions/api/_drive.ts`, `albums.ts`, `photos.ts`, `documents.ts`
- Create: `functions/tsconfig.json`
- Modify: `wrangler.toml`, `.gitignore`
- Test: `tests/drive.test.ts`

**Interfaces:**
- Produces:
  - `GET /api/albums` → `{ years: Year[], fetchedAt: string }`
  - `GET /api/photos?album=<id>` → `{ album: {id,name}, photos: Photo[], fetchedAt }`
  - `GET /api/documents?folder=<key>` → `{ folders: Folder[], files: DocFile[], fetchedAt }`
  - `shared/drive.ts`: `imageThumb(id, mime, width)`, `docThumb(id)`, `folderKey` union.
- Consumes: `GOOGLE_API_KEY` secret, `CACHE` KV binding.

- [ ] **Step 1: Write shared URL builders**

```ts
export interface Photo { id: string; name: string; width?: number; height?: number; thumb: string; full: string; }

const isHeic = (mime: string) => /heic|heif/i.test(mime);

export function imageThumb(id: string, mime: string, width = 800): string {
  return isHeic(mime)
    ? `https://drive.google.com/thumbnail?id=${id}&sz=w${width}`
    : `https://lh3.googleusercontent.com/d/${id}=w${width}`;
}
export function imageFull(id: string, mime: string): string {
  return isHeic(mime)
    ? `https://drive.google.com/thumbnail?id=${id}&sz=w2000`
    : `https://lh3.googleusercontent.com/d/${id}=w2000`;
}
export function docThumb(id: string): string {
  return `https://drive.google.com/thumbnail?id=${id}&sz=w600`;
}
```

HEIC is served through Drive's converter; `lh3` refuses those files.

- [ ] **Step 2: Write the Drive client**

```ts
/// <reference types="@cloudflare/workers-types" />

export interface Env {
  GOOGLE_API_KEY: string;
  CACHE: KVNamespace;
}

export const PIO_ROOT = "1QbMxIfTuL9-qJ3T9YgfuYyErHexqxBiQ";

export const FOLDERS = {
  finance: "1NhgG1fkfxch70E3hzb5YhTgCK0PWKcdV",
  minutes: "1qm3Z6OmjxFa41OsjTPrBUJEl57-GSGH5",
  notices: "1SVzssvcj1IkEndY0Mp5Nv8WhDsaQUDl4",
  elections: "1hiqv7sFda_cGWVo7OtgJs5cpPS-buZ4L",
  proposals: "15vGFBRfifPvEUkN5yo1iv87MQPAoaFHE",
  memorandums: "1xszCcvP83aaVus3xLQ4f1RDmjvWqLHUj",
} as const;

export type FolderKey = keyof typeof FOLDERS;

export const FOLDER_MIME = "application/vnd.google-apps.folder";
const FIELDS =
  "files(id,name,mimeType,modifiedTime,size,imageMediaMetadata(width,height))";

export interface DriveFile {
  id: string; name: string; mimeType: string;
  modifiedTime?: string; size?: string;
  imageMediaMetadata?: { width?: number; height?: number };
}

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=60, s-maxage=300, stale-while-revalidate=86400",
    },
  });
}

export async function driveList(env: Env, folderId: string, extra = ""): Promise<DriveFile[]> {
  const url = new URL("https://www.googleapis.com/drive/v3/files");
  url.searchParams.set("q", `'${folderId}' in parents and trashed = false${extra}`);
  url.searchParams.set("fields", FIELDS);
  url.searchParams.set("pageSize", "1000");
  url.searchParams.set("orderBy", "name_natural");
  url.searchParams.set("key", env.GOOGLE_API_KEY);
  const res = await fetch(url.toString(), { cf: { cacheTtl: 300, cacheEverything: true } });
  if (!res.ok) throw new Error(`Drive ${res.status} for ${folderId}`);
  const body = (await res.json()) as { files?: DriveFile[] };
  return body.files ?? [];
}

export async function cached<T>(env: Env, key: string, ttl: number, load: () => Promise<T>): Promise<T> {
  const hit = await env.CACHE.get(key, "json");
  if (hit) return hit as T;
  const value = await load();
  await env.CACHE.put(key, JSON.stringify(value), { expirationTtl: ttl });
  return value;
}
```

If `env.GOOGLE_API_KEY` is missing, `json({ error: "drive-not-configured" }, 503)` must be returned by each endpoint, never a stack trace.

- [ ] **Step 3: Write `/api/albums` with automatic discovery**

```ts
import type { PagesFunction } from "@cloudflare/workers-types";
import { cached, driveList, json, PIO_ROOT, type Env, type DriveFile } from "./_drive";
import { imageThumb } from "../../shared/drive";

const FOLDER_MIME = "application/vnd.google-apps.folder";

export interface Album { id: string; name: string; count: number; cover: string | null; }
export interface Term { id: string; name: string; albums: Album[]; }
export interface Year { id: string; name: string; terms: Term[]; }

export const onRequestGet: PagesFunction<Env> = async ({ env }) => {
  if (!env.GOOGLE_API_KEY) return json({ error: "drive-not-configured" }, 503);
  try {
    const years = await cached(env, "albums:v2", 900, async () => {
      const yearFolders = await driveList(env, PIO_ROOT, ` and mimeType = '${FOLDER_MIME}'`);
      const out: Year[] = [];
      for (const year of yearFolders) {
        const termFolders = await driveList(env, year.id, ` and mimeType = '${FOLDER_MIME}'`);
        const terms: Term[] = [];
        for (const term of termFolders) {
          const albumFolders = await driveList(env, term.id, ` and mimeType = '${FOLDER_MIME}'`);
          const albums: Album[] = [];
          for (const album of albumFolders) {
            const photos = await driveList(env, album.id, ` and mimeType contains 'image/'`);
            const first = photos.find((p: DriveFile) => /image\/(jpeg|png|heic|heif)/i.test(p.mimeType));
            albums.push({
              id: album.id,
              name: album.name,
              count: photos.length,
              cover: first ? imageThumb(first.id, first.mimeType, 1200) : null,
            });
          }
          terms.push({ id: term.id, name: term.name, albums: albums.filter((a) => a.count > 0) });
        }
        out.push({ id: year.id, name: year.name, terms: terms.filter((t) => t.albums.length > 0) });
      }
      return out;
    });
    return json({ years, fetchedAt: new Date().toISOString() });
  } catch (error) {
    console.error("albums", error);
    return json({ error: "drive-unavailable" }, 502);
  }
};
```

- [ ] **Step 4: Write `/api/photos` restricted to discovered albums**

```ts
import type { PagesFunction } from "@cloudflare/workers-types";
import {
  cached, driveList, json, FOLDER_MIME, PIO_ROOT,
  type DriveFile, type Env,
} from "./_drive";
import { imageThumb, imageFull } from "../../shared/drive";

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  if (!env.GOOGLE_API_KEY) return json({ error: "drive-not-configured" }, 503);
  const album = new URL(request.url).searchParams.get("album") ?? "";
  if (!/^[A-Za-z0-9_-]{20,}$/.test(album)) return json({ error: "bad-album" }, 400);

  const tree = await cached(env, "album-ids:v2", 900, async () => {
    const years = await driveList(env, PIO_ROOT, ` and mimeType = '${FOLDER_MIME}'`);
    const ids: Record<string, string> = {};
    for (const year of years) {
      for (const term of await driveList(env, year.id, ` and mimeType = '${FOLDER_MIME}'`)) {
        for (const folder of await driveList(env, term.id, ` and mimeType = '${FOLDER_MIME}'`)) {
          ids[folder.id] = folder.name;
        }
      }
    }
    return ids;
  });

  const name = tree[album];
  if (!name) return json({ error: "unknown-album" }, 404);

  try {
    const photos = await cached(env, `photos:${album}:v2`, 900, async () => {
      const files = await driveList(env, album, ` and mimeType contains 'image/'`);
      return files
        .filter((f) => /image\//.test(f.mimeType))
        .map((f) => ({
          id: f.id,
          name: f.name,
          mime: f.mimeType,
          width: f.imageMediaMetadata?.width,
          height: f.imageMediaMetadata?.height,
          thumb: imageThumb(f.id, f.mimeType, 800),
          full: imageFull(f.id, f.mimeType),
        }));
    });
    return json({ album: { id: album, name }, photos, fetchedAt: new Date().toISOString() });
  } catch (error) {
    console.error("photos", error);
    return json({ error: "drive-unavailable" }, 502);
  }
};
```

The allowlist is the reason a leaked request cannot enumerate arbitrary Drive folders: only IDs discovered under the PIO root are served.

- [ ] **Step 5: Write `/api/documents`**

```ts
import type { PagesFunction } from "@cloudflare/workers-types";
import {
  cached, driveList, json, FOLDERS, FOLDER_MIME,
  type Env, type FolderKey,
} from "./_drive";
import { docThumb } from "../../shared/drive";

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  if (!env.GOOGLE_API_KEY) return json({ error: "drive-not-configured" }, 503);
  const key = new URL(request.url).searchParams.get("folder") ?? "";
  if (!(key in FOLDERS)) return json({ error: "unknown-folder" }, 400);

  try {
    const data = await cached(env, `docs:${key}:v2`, 900, async () => {
      const items = await driveList(env, FOLDERS[key as FolderKey]);
      return {
        folders: items.filter((f) => f.mimeType === FOLDER_MIME).map((f) => ({
          id: f.id, name: f.name,
          url: `https://drive.google.com/drive/folders/${f.id}`,
        })),
        files: items.filter((f) => f.mimeType !== FOLDER_MIME).map((f) => ({
          id: f.id, name: f.name, mime: f.mimeType, modified: f.modifiedTime ?? null,
          thumb: docThumb(f.id),
          view: `https://drive.google.com/file/d/${f.id}/view`,
        })),
      };
    });
    return json({ ...data, fetchedAt: new Date().toISOString() });
  } catch (error) {
    console.error("documents", error);
    return json({ error: "drive-unavailable" }, 502);
  }
};
```

- [ ] **Step 6: Create KV, the secret, and local vars**

```bash
cd "C:/Users/Ma Christine/Downloads/WEBSITES/sslg"
npx wrangler kv namespace create SSLG_CACHE
```

Paste the printed `id` into `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "CACHE"
id = "<printed id>"
```

Create the Google key once: Google Cloud Console → new project `sslg-site` → APIs & Services → Library → enable **Google Drive API** → Credentials → Create credentials → API key → edit the key → API restrictions → restrict to Google Drive API. Application restrictions must stay **None** because the Worker has no fixed IP; the allowlist, KV cache, and Cloudflare rate limiting are the guard instead.

```bash
npx wrangler pages secret put GOOGLE_API_KEY --project-name sslg
printf 'GOOGLE_API_KEY=...\n' > .dev.vars
printf '\n.dev.vars\n.wrangler/\n' >> .gitignore
```

- [ ] **Step 7: Declare Worker types and test locally**

`functions/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noEmit": true,
    "types": ["@cloudflare/workers-types"]
  },
  "include": ["**/*.ts", "../shared/*.ts"]
}
```

Add the Worker typecheck to the build script now that `functions/` exists:

```json
"build": "tsc --noEmit && tsc -p functions --noEmit && vite build"
```

```bash
npm run build
npx wrangler pages dev dist
```

Then, in a second terminal:

```bash
curl -s "http://localhost:8788/api/albums" | head -c 300
curl -s "http://localhost:8788/api/photos?album=1yVIUPC5q0G8EsRahOUxbHG_EvSByCXlz" | head -c 300
curl -s "http://localhost:8788/api/documents?folder=finance" | head -c 300
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8788/api/documents?folder=../../etc"
```

Expected: JSON with real album names, one photo object, two finance files; `400` for the traversal attempt. With `GOOGLE_API_KEY` removed from `.dev.vars`, the same calls return `503`.

- [ ] **Step 8: Unit-test the pure helpers and commit**

```ts
import { imageThumb, imageFull, docThumb } from "../shared/drive";

test("uses Drive conversion for HEIC and lh3 for JPEG", () => {
  expect(imageThumb("abc", "image/heic")).toContain("drive.google.com/thumbnail");
  expect(imageThumb("abc", "image/jpeg")).toBe("https://lh3.googleusercontent.com/d/abc=w800");
  expect(imageFull("abc", "image/png")).toContain("=w2000");
  expect(docThumb("abc")).toContain("sz=w600");
});
```

```bash
npm test -- tests/drive.test.ts
git add -A && git commit -m "feat: proxy public Drive folders through cached Pages Functions"
```

---

### Task 5: Photos page with album groups and lightbox

**Files:**
- Create: `src/lib/api.ts`, `src/lib/useAlbums.ts`, `src/components/PhotoGrid.tsx`, `src/components/AlbumViewer.tsx`, `src/components/SmartImage.tsx`, `src/pages/Photos.tsx`
- Modify: `src/App.tsx`
- Test: `tests/photo-grid.test.tsx`

**Interfaces:**
- Consumes: `GET /api/albums`, `GET /api/photos?album=`.
- Produces: `<PhotoGrid photos />` with an accessible lightbox; `<SmartImage src alt ratio />`; `<AlbumViewer albumId name />` shared with the activity detail page in Task 6.

- [ ] **Step 1: Write the fetch helpers**

```ts
export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, { signal, headers: { accept: "application/json" } });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return (await res.json()) as T;
}
```

`useAlbums.ts` keeps one module-level promise so Photos and every activity card share a single request:

```ts
let pending: Promise<AlbumsResponse> | null = null;
export function loadAlbums(): Promise<AlbumsResponse> {
  pending ??= getJson<AlbumsResponse>("/api/albums");
  return pending;
}
export function useAlbums() {
  const [state, setState] = useState<{ data: AlbumsResponse | null; error: string | null }>({ data: null, error: null });
  useEffect(() => {
    let alive = true;
    loadAlbums().then((data) => alive && setState({ data, error: null }))
      .catch(() => alive && setState({ data: null, error: "Photos are unavailable right now." }));
    return () => { alive = false; };
  }, []);
  return state;
}
```

- [ ] **Step 2: Build SmartImage and PhotoGrid**

`SmartImage` renders a 4:3 skeleton until `onLoad`, then fades in; on error it shows a ruled placeholder with the alt text so a broken Drive permission never leaves a blank square. PhotoGrid uses `loading="lazy"`, `decoding="async"`, and a `srcset` built from `imageThumb(id, mime, 400 | 800 | 1600)` using the `mime` field returned by `/api/photos`.

Lightbox: a fixed overlay with `role="dialog"` and `aria-modal="true"`, not a native `<dialog>` (jsdom does not implement `showModal`, and the test must exercise it). On open, focus moves to the close button and `Escape` closes; arrow keys step photos; closing restores focus to the thumbnail that opened it. Caption is the filename with the extension removed and underscores replaced by spaces; counter reads `3 / 53`.

- [ ] **Step 3: Compose the page**

```tsx
export default function Photos() {
  const { data, error } = useAlbums();
  const [open, setOpen] = useState<{ id: string; name: string } | null>(null);
  return (
    <div className="page">
      <PageMeta title="Photos" description="Photo albums from SSLG and LGCC activities." path="/photos" />
      <SectionHead eyebrow="Photo record" title="Photos" lead="Albums from the SSLG and LGCC. Photos are added by the PIO; this page reads the public Drive albums directly." />
      {error && <EmptyState title="Albums are unavailable" body={error} />}
      {data?.years.map((year) => (
        <section key={year.id} className="album-year">
          <h2 className="album-year-title">{year.name}</h2>
          {year.terms.map((term) => (
            <div key={term.id} className="album-term">
              <h3>{term.name}</h3>
              <div className="album-grid">
                {term.albums.map((album) => (
                  <button key={album.id} className="album-card" onClick={() => setOpen({ id: album.id, name: album.name })}>
                    {album.cover && <img src={album.cover} alt="" loading="lazy" />}
                    <span className="album-name">{album.name}</span>
                    <span className="album-count">{album.count} photos</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </section>
      ))}
      {open && <AlbumViewer albumId={open.id} name={open.name} onClose={() => setOpen(null)} />}
    </div>
  );
}
```

`AlbumViewer` fetches once per album, caches the response in a module map, shows a loading rule while it waits, an empty state for a folder that emptied, and `PhotoGrid` when photos arrive. It is a full-width inline panel below the album grid, with a "Close album" control, so every album keeps one URL and no routing work is needed.

- [ ] **Step 4: Test the grid and lightbox**

```tsx
import { fireEvent, render, screen } from "@testing-library/react";

test("opens the lightbox on click and closes on Escape", () => {
  render(<PhotoGrid photos={[{ id: "1", name: "IMG_0012.JPG", mime: "image/jpeg", thumb: "/a.jpg", full: "/b.jpg" }]} />);
  fireEvent.click(screen.getByRole("button", { name: /IMG_0012/i }));
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  fireEvent.keyDown(document, { key: "Escape" });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});
```

- [ ] **Step 5: Run, build, deploy, and commit**

```bash
npm test -- tests/photo-grid.test.tsx
npm run build && npx wrangler pages deploy dist --project-name sslg --branch main
git add -A && git commit -m "feat: add Drive-backed Photos page with lightbox"
```

Expected: `/photos` lists the five non-empty albums under `S.Y. 2026-2027 → TERM 1`, Teachers' Day opens 1 photo, Brigada 53, Grade 7 12.

---

### Task 6: Accomplishments list and activity detail

**Files:**
- Create: `src/components/ActivityCard.tsx`, `src/pages/Accomplishments.tsx`, `src/pages/ActivityPage.tsx`
- Modify: `src/App.tsx`
- Test: `tests/activities.test.tsx`

**Interfaces:**
- Consumes: `ACTIVITIES`, `useAlbums()` for album-derived covers.
- Produces: routes `/accomplishments` and `/accomplishments/:slug` (404 inside the layout for unknown slugs).

- [ ] **Step 1: Build the card**

`ActivityCard` shows a 4:3 cover, the title in display serif, the caption clamped to four lines, and a "Read report" link when `reportUrl` exists. Cover resolution order:

1. `cover.kind === "album"` → find `album.id` in the albums tree from `useAlbums()`; use `album.cover`.
2. `cover.kind === "doc"` → `docThumb(fileId)`.
3. `none` → a ruled placeholder with the first letters of the title.

If the album is missing or empty, fall back to the placeholder; never hotlink a `lh3` ID that is not in the tree.

- [ ] **Step 2: Compose the list**

Header "ACCOMPLISHMENTS", lead "Activity reports from the SSLG and LGCC, newest first." A three-column grid at ≥1000px, two at ≥680px, one below. `project-tinig` renders in its own "Standing project" strip above the grid, without a cover.

- [ ] **Step 3: Compose the detail page**

```tsx
const { slug } = useParams();
const activity = ACTIVITIES.find((a) => a.slug === slug);
if (!activity) return <NotFound />;
```

Layout: title, caption, optional date, a link to the Drive album (`https://drive.google.com/drive/folders/<album>`), the report button, and the album itself rendered with `<AlbumViewer albumId={activity.album} name={activity.title} onClose={() => navigate("/accomplishments")} />` when `activity.album` is set (`import { useNavigate } from "react-router-dom"` and `const navigate = useNavigate()`). This is where a reader lands from the Home "Latest" card.

- [ ] **Step 4: Test routing and 404**

```tsx
test("unknown slug renders the not-found page", () => {
  render(
    <MemoryRouter initialEntries={["/accomplishments/not-a-real-activity"]}>
      <Routes><Route path="accomplishments/:slug" element={<ActivityPage />} /></Routes>
    </MemoryRouter>,
  );
  expect(screen.getByRole("heading", { name: /not found/i })).toBeInTheDocument();
});
```

- [ ] **Step 5: Run, deploy, commit**

```bash
npm test -- tests/activities.test.tsx
npm run build && npx wrangler pages deploy dist --project-name sslg --branch main
git add -A && git commit -m "feat: add accomplishments index and activity pages"
```

---

### Task 7: Finance and Transparency pages from Drive

**Files:**
- Create: `src/components/DocumentList.tsx`, `src/pages/Finance.tsx`, `src/pages/Transparency.tsx`
- Modify: `src/App.tsx`
- Test: `tests/documents.test.tsx`

**Interfaces:**
- Consumes: `GET /api/documents?folder=`.
- Produces: `DocumentList` (loading, empty, error states), two routes.

- [ ] **Step 1: Build DocumentList**

Each row: 56px thumbnail, filename in mono, modified date (`en-PH`, day-month-year) when present, and the whole row links to `view`. Show a "PDF" or "DOCX" tag from the extension. Empty state: "No documents in this folder yet." Error state: "Records are unavailable right now." with a retry button.

- [ ] **Step 2: Finance page**

Header "FINANCE"; lead "Latest financial reports published by the SSLG Treasurer."; one `DocumentList` on `folder=finance`; then the italic line `Prepared By: Samantha Joy C. De Venecia (SSLG Treasurer)`. Keep the existing page name and route.

- [ ] **Step 3: Transparency page**

Header "TRANSPARENCY". First a feature block for the General Plan of Action. Add the folder to the allowlist in `functions/api/_drive.ts`:

```ts
gpoa: "16_T5tmGrzwHF6X9lR1JxrNY8K1C9EYnN",
```

Then list it with `DocumentList`. After that, one section per `DOCUMENT_GROUPS` entry, each with `DocumentList`. For `memorandums`, render the four subfolders as links above the file list. Last, a "Legal bases" block linking the PDF `1MthdcNxs_w_QoLuus-nVcAoi4xaACNKd` and a "More documents" link to the records root `1XU9s-pHPCk_zJQo7LSOjcmtGeIiI9JeM`.

- [ ] **Step 4: Test states**

```tsx
test("shows the empty state when the folder has no files", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ files: [], folders: [] }) }));
  render(<DocumentList folder="finance" />);
  expect(await screen.findByText(/no documents/i)).toBeInTheDocument();
});
```

- [ ] **Step 5: Run, deploy, commit**

```bash
npm test -- tests/documents.test.tsx
npm run build && npx wrangler pages deploy dist --project-name sslg --branch main
git add -A && git commit -m "feat: drive finance and transparency pages from public folders"
```

---

### Task 8: Home, About us, Feedback, 404

**Files:**
- Create: `src/pages/Home.tsx`, `About.tsx`, `Feedback.tsx`, `NotFound.tsx`
- Modify: `src/App.tsx`

**Interfaces:**
- Consumes: `ACTIVITIES`, `OFFICERS`, `useAlbums()`.
- Produces: the four remaining routes.

- [ ] **Step 1: Home**

Order: masthead hero (school name, "Supreme Secondary Learner Government", mandate sentence, two buttons: "Accomplishments" and "Transparency"); featured latest activity (the first `featured` entry, large cover, title, caption, "Read more"); a three-card "Recent activity" row (`ACTIVITIES.slice(0, 3)`); a two-column "About us" strip with 3 executive officers and a link; a "Records" strip linking Finance, Transparency, Photos.

No carousel, no auto-rotating hero: a school record should be readable and stable.

- [ ] **Step 2: About us**

Sections: Executive Officers (7), Grade-Level Representatives (12, grouped by grade in descending order), School Leadership (8), then "Objectives of the SSLG" (5 bullets) and "Duties and Obligations" (3 bullets) from `site.ts`. Use a two-column grid of name/role rows; no photos (none are published).

- [ ] **Step 3: Feedback**

Header, one paragraph explaining the form, and a responsive iframe:

```tsx
<iframe
  src={`${FEEDBACK_FORM_URL}?embedded=true`}
  title="SSLG feedback form"
  className="feedback-frame"
  loading="lazy"
  referrerPolicy="no-referrer"
/>
```

Minimum height 900px, full width, with a fallback link below for blocked embeds.

- [ ] **Step 4: 404**

Inside the layout: "Page not found", one line, links to Home and Accomplishments. Set `noindex` via `PageMeta` by passing no `path`.

- [ ] **Step 5: Build, deploy, commit**

```bash
npm run build && npx wrangler pages deploy dist --project-name sslg --branch main
git add -A && git commit -m "feat: add home, about, feedback, and not-found pages"
```

Check in a browser: Home → Latest card → activity page → album; About lists all 27 names; Feedback form loads; `/nope` renders the 404 without losing the masthead.

---

### Task 9: SEO, headers, redirects, and metadata

**Files:**
- Create: `scripts/generate-seo.mjs`
- Modify: `public/_redirects`, `public/_headers`, `index.html`, `src/components/PageMeta.tsx`
- Create: `public/robots.txt`

**Interfaces:**
- Consumes: `SITE_URL` from `src/config.ts`, `ACTIVITIES` slugs from source.
- Produces: `dist/sitemap.xml` at build, per-route titles/canonicals, security headers.

- [ ] **Step 1: Write the SEO generator and add it to the build**

Fork chembank's script pattern: read `SITE_URL`, emit a sitemap with `/`, `/finance`, `/accomplishments`, `/photos`, `/transparency`, `/about-us`, `/feedback`, plus `/accomplishments/<slug>` for every activity. Escape XML. Fail the build if `SITE_URL` is missing. Then set:

```json
"build": "tsc --noEmit && tsc -p functions --noEmit && vite build && node scripts/generate-seo.mjs"
```

- [ ] **Step 2: Write headers and redirects**

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

Do not add a Content-Security-Policy yet; the Google Form embed and Google image hosts need an exact `frame-src`/`img-src` list. That is a Phase 2 item after the pages are stable.

- [ ] **Step 3: Update index.html metadata**

Title `BSANHS SSLG — Supreme Secondary Learner Government`, description from `SITE_DESCRIPTION`, `theme-color #0f2440`, OG title/description/url for `https://sslg-2sr.pages.dev/`, canonical, and `<html lang="en">`. Keep the `<noscript>` line explaining that photos and records need JavaScript, with a link to the static Facebook page.

- [ ] **Step 4: Verify**

```bash
npm run build
grep -c "<url>" dist/sitemap.xml
grep -o "accomplishments/world-teachers-day-2026" dist/sitemap.xml
head -5 dist/_headers
git add -A && git commit -m "feat: add sitemap, social metadata, and security headers"
```

Expected: 15+ URLs including every activity slug.

---

### Task 10: End-to-end verification and cutover

**Files:**
- Create: `docs/sslg-cloudflare-runbook.md` (in the vault, not the repo)
- Modify: this plan's checklist as items complete

**Interfaces:**
- Consumes: every prior task.
- Produces: a verified live site and a documented rollback.

- [ ] **Step 1: Run the local checks**

```bash
cd "C:/Users/Ma Christine/Downloads/WEBSITES/sslg"
npm test
npm run build
npx wrangler pages deploy dist --project-name sslg --branch main
```

Expected: all tests pass; deploy prints the deployment URL.

- [ ] **Step 2: Verify live, unauthenticated**

```bash
for p in / /finance /accomplishments /photos /transparency /about-us /feedback; do
  printf "%s %s\n" "$(curl -s -o /dev/null -w '%{http_code}' https://sslg-2sr.pages.dev$p)" "$p"
done
curl -s https://sslg-2sr.pages.dev/api/albums | grep -o '"name":"[^"]*"' | head -8
```

Expected: seven `200`s; real album names, no API key anywhere in the responses.

- [ ] **Step 3: Verify the automation promise without writing to Drive**

Ask the PIO to add one photo to the Teachers' Day album (or wait for the next real upload). After 15 minutes, reload `/photos` without deploying: the count and the album cover change. This account must not upload anything; the folders belong to the PIO.

- [ ] **Step 4: Verify on a phone and without sign-in**

Open the site in a private window and on a phone: nav wraps without horizontal scroll, album grids are two columns, the lightbox works by tap, the Finance PDFs open in Drive without a Google sign-in prompt.

- [ ] **Step 5: Cut over**

1. Keep the Google Sites site live as the archive.
2. Put one link at the top of the Google Sites Home page: "Our new website: https://sslg-2sr.pages.dev" (manual, one edit).
3. Announce the new address on `facebook.com/SSLGBSANHS` and in the SSLG group chat.
4. After 30 days with no missing content, leave Sites published but unlinked, or unpublish it. Do not delete the Drive folders.
5. If a custom domain is available, add it in Cloudflare Pages → Custom domains, then change `SITE_URL` in `src/config.ts`, rebuild, and redeploy.

- [ ] **Step 6: Record rollback**

Cloudflare Pages → Deployments → previous deployment → "Rollback". The Drive data is untouched, so a rollback never loses content. If the Drive key is compromised, delete it in Google Cloud Console and issue a new one; the site shows the empty state until the secret is updated.

- [ ] **Step 7: Write the vault runbook**

`docs/sslg-cloudflare-runbook.md`: how the PIO adds photos, how a new album appears, how to publish a new activity (edit `src/content/activities.ts`, commit, push, or run `npm run deploy`), how to check the Drive key, the 15-minute cache, and the rollback step.

---

## Flagged items to confirm with the adviser

| # | Item | Why it matters | Default used here |
| --- | --- | --- | --- |
| 1 | Official school colours and logo | The palette above is provisional (navy/gold/parchment) | Ship provisional, swap tokens later; no logo is invented |
| 2 | Custom domain | `sslg-2sr.pages.dev` is free but not memorable | Use pages.dev now; add a domain if one exists |
| 3 | Treasurer's full name | Live Finance says "Samantha C. De Venecia"; About says "Samantha Joy C. De Venecia" | About-page spelling |
| 4 | Club Fair name | ACR-003 says Club Fair; the site says Club and Organizations Membership Drive | Keep the published name |
| 5 | Activity dates | Most events have no documented date on the site | No dates rendered; `date` stays optional |
| 6 | GPOA document | The transparency page links a file whose ID is not in the records listing | List the GPOA folder; confirm the exact file with the adviser |
| 7 | Legal bases PDF | The live page embeds one PDF and links another | Link `1MthdcNxs_…`; verify it matches the OUOPS 2023-03 issuance |
| 8 | Empty albums | Induction and Club Fair have zero photos | Albums endpoint hides empty folders automatically |
| 9 | Grade 7 HEIC photos | HEIC needs conversion for some browsers | Drive thumbnail conversion is used; verify on an iPhone |

## Phase 2 (not in this plan)

- GitHub repo + Cloudflare Pages Git integration, so a content edit in the GitHub web editor deploys without a laptop.
- A small admin page behind Cloudflare Access (email OTP) to add activity copy without touching code.
- R2 mirror plus a nightly sync if Drive quotas or outages become a problem.
- Cloudflare Web Analytics and a monthly link check.
- Move officer and activity data into D1 if the adviser wants non-technical editing.
