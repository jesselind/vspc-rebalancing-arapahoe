## CEI Frontend (Static-First Next.js)

This app provides:

- Precinct -> assigned VSPC lookup
- Read-only CSV report viewing and downloads
- PDF map viewing with loading feedback
- Rate-limited feedback email (mailto opened after `/api/feedback`)
- Rate-limited CSV/PDF downloads via `/api/download`

## Getting Started

Install dependencies with your preferred package manager, then sync static assets from the project root:

```bash
npm run sync:assets
```

Start the app:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Asset Sync

`npm run sync:assets` copies:

- `../output/*.csv` -> `content/data/`
- `../maps/*.pdf` -> `content/maps/`

Run this command whenever source CSV/PDF outputs change.

## Playwright E2E

Install Playwright browsers:

```bash
npx playwright install
```

Run tests:

```bash
npm run test:e2e
```

## Security Notes

- App is read-only in MVP
- Baseline security headers are set in `next.config.ts` (add CSP in Cloudflare when ready)
- CSV/PDF files live under `content/` (not `public/`); direct `/data/` and `/maps/` URLs return 404
- Downloads, map PDF, and contact email use edge rate limits (per IP); tune with env:
  - `RATE_LIMIT_WINDOW_SECONDS` (default `60`) — CSV download window
  - `RATE_LIMIT_DOWNLOAD_MAX` (default `10`) — CSV downloads per IP per window
  - `RATE_LIMIT_MAP_PDF_WINDOW_SECONDS` (default `60`) — map PDF window
  - `RATE_LIMIT_MAP_PDF_MAX` (default `2`) — map PDF open/download combined per IP per window
  - `RATE_LIMIT_FEEDBACK_MAX` (default `1`) — feedback requests per IP per window
- On Cloudflare, add WAF rate limiting on `/api/download`, `/api/map-pdf`, and `/api/feedback` as defense in depth
- County map PDF is proxied from GitHub via `/api/map-pdf` (inline view and download; avoids bundling the file in the Worker)
- Do not commit `.dev.vars` or API tokens; set runtime env in the dashboard only if needed

## Deploy on Cloudflare Workers

Git-connected build (dashboard: **Workers & Pages** → import repo):

| Setting | Value |
| --- | --- |
| Path | `web` |
| Build command | `npm run build:cf` |
| Deploy command | `npx wrangler deploy` |

`wrangler.jsonc` `name` and `services[].service` must match the Worker name in the dashboard (e.g. `cei`). Renaming the Worker in the dashboard requires updating both fields.

Data for production is the committed copy under `web/content/`; `prebuild` sync from `../output` and `../maps` is for local refresh only.
