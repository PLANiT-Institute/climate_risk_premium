# CRP Dashboard (Vercel)

Production dashboard for the Climate Risk Premium model of Samcheok Blue Power (2,100 MW).

## What This App Shows

- Scenario-level financial outputs: NPV, IRR, DSCR, LLCR
- Credit outcomes: rating migration (AAA-D), spread, counterfactual CRP
- Physical-risk channel (PLANiT): wildfire, drought, water risk conversion logic
- Transition-risk channel: policy dispatch effects + enhanced 11th Basic Plan stress

## Data Source Priority

1. Supabase (`scenario_results`, `cashflow_yearly`, `credit_ratings`) when configured
2. Local frozen JSON under `src/data/` as fallback

This behavior is implemented in `src/lib/queries/*`.

## Local Development

```bash
cd crp-dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build Check

```bash
cd crp-dashboard
npm run build
```

## Vercel Deployment

- Framework: Next.js (`vercel.json`)
- Vercel project **Root Directory**: `crp-dashboard`
- Region: `icn1`
- Security headers are applied globally
- Optional ISR revalidation endpoint: `POST /api/revalidate`

### Required Environment Variables (if Supabase is used)

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_SITE_URL` (recommended, for metadata base URL)
- `REVALIDATE_SECRET` (optional, for revalidate endpoint)

If Supabase variables are absent, the dashboard automatically falls back to local JSON.

## Project Structure

- `src/app/`: route pages
- `src/components/`: chart, table, map, layout components
- `src/lib/queries/`: data loading strategy (Supabase-first, local fallback)
- `src/data/`: frozen scenario/cashflow/rating JSON snapshots
- `archive/`: deprecated or unused assets

## Syncing Model Results

From repository root:

```bash
python scripts/regenerate_dashboard_data.py
```

This refreshes CSV outputs and dashboard JSON snapshots.
