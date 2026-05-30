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
- Baseline security headers are set in `next.config.ts` (configure CSP at Cloudflare if needed)
- CSV/PDF files live under `content/` (not `public/`); direct `/data/` and `/maps/` URLs return 404
- Downloads and contact email use edge rate limits (`/api/download`, `/api/feedback`); tune with env:
  - `RATE_LIMIT_WINDOW_SECONDS` (default `60`)
  - `RATE_LIMIT_DOWNLOAD_MAX` (default `30`)
  - `RATE_LIMIT_FEEDBACK_MAX` (default `8`)
- On Cloudflare, also add WAF rate limiting rules for `/api/download` and `/api/feedback` as defense in depth
- PDF viewer loads the map only from `/api/download?asset=map`

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
