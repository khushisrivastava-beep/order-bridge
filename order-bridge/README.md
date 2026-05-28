# Order Bridge Analysis

Daily order bridge dashboard for leadership — D-1 vs D-2 (short-term) and D-1 vs D-8 (weekly trend).

## Project structure

```
order-bridge/
├── public/
│   ├── index.html          # Single-page app — host this on Vercel
│   └── data/
│       ├── d2.json         # D-1 vs D-2 data (auto-generated)
│       └── d8.json         # D-1 vs D-8 data (auto-generated)
├── scripts/
│   └── generate.py         # Run this with each new CSV to refresh data
├── data/
│   └── latest.csv          # Commit your daily CSV here
├── .github/workflows/
│   └── daily.yml           # GitHub Actions — auto-refresh on schedule
└── vercel.json
```

## Daily update workflow

### Option A — Commit CSV to repo (simplest)
1. Replace `data/latest.csv` with today's CSV
2. `git add data/latest.csv && git commit -m "data: YYYY-MM-DD" && git push`
3. GitHub Action runs automatically → updates JSON → Vercel redeploys

### Option B — Manual trigger with URL
1. Go to **Actions → Daily Data Refresh → Run workflow**
2. Paste a direct download URL to your CSV
3. Action downloads, generates JSON, commits, Vercel redeploys (~2 min end-to-end)

### Option C — Run locally and push JSON
```bash
python scripts/generate.py /path/to/your/file.csv
git add public/data/ && git commit -m "data: YYYY-MM-DD" && git push
```

## First-time Vercel setup

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) → **New Project** → Import your GitHub repo
3. **Framework preset:** Other
4. **Output directory:** `public`
5. Click **Deploy** — your URL is ready in ~30 seconds

That's it. Leadership bookmarks the URL once and it auto-refreshes daily.

## Local development

Open `public/index.html` via a local server (required for `fetch()` to work):
```bash
cd public && python3 -m http.server 8000
# then open http://localhost:8000
```
