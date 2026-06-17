# TherapyFor.us — Page Generator

Generates 800–1000 word emotional landing pages for BetterHelp affiliate traffic.
Each page = 2 Haiku calls (content + SEO), run concurrently. Design = Version A (Slate & Amber).

## What's here

```
generate.py              Main generator. Run per keyword file.
build_sitemap.py         Builds sitemap.xml from generated pages.
templates/
  page_template.html     The Version A page, with {{placeholders}}.
data/
  workflow1_divorce.json First cluster, 20 pages, ready to run.
api/
  sarah.js               Vercel serverless backend for the Sarah widget.
output/                  Generated .html pages land here.
requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Generate a cluster

```bash
python generate.py data/workflow1_divorce.json
python build_sitemap.py
```

Pages appear in `output/`. Each is a standalone HTML file named by slug.

## Before you deploy — 3 edits

1. In `generate.py`, set `AFFILIATE_LINK` to your real MaxBounty link (top of file).
2. In `generate.py`, set `SITE_URL` if not therapyfor.us.
3. In Vercel, add `ANTHROPIC_API_KEY` as an environment variable (for Sarah).

## Adding more clusters

Copy `data/workflow1_divorce.json`, change the `pages` array. Each entry:

```json
{ "keyword": "the exact search term", "slug": "url-slug", "angle": "one line steering the emotional angle" }
```

Then `python generate.py data/yourfile.json`.

The 6 money workflows to build out:
1. Divorce & relationships (started — 20 of ~180)
2. Grief & loss (~120)
3. Anxiety, depression & symptoms (~250)
4. Life stage & identity (~200)
5. Affordability & access (~100)
6. Stories + hubs (~90)

## Cost

Haiku, 2 calls per page, ~2.5k tokens total. Roughly **$0.002–0.004 per page**.
940 money pages ≈ **$3–4 total**.

## Rate limits

`MAX_WORKERS = 4` in generate.py controls concurrency. If you hit rate limits,
lower it. For very large runs, run one cluster at a time.

## Deploy (Vercel)

- Put generated HTML + sitemap.xml at project root (or a /public folder).
- Put `api/sarah.js` in the `api/` folder so it becomes `/api/sarah`.
- Add `ANTHROPIC_API_KEY` in Vercel env vars.
- The Sarah widget on every page calls `/api/sarah` — key stays server-side.

## How Sarah works

Each page has the widget baked in. It auto-opens after 20 seconds, listens with
empathy, and after 2–3 exchanges drops a BetterHelp CTA button. The system prompt
lives in the page (`SYSTEM` const) and the key never touches the browser — all
calls route through `/api/sarah`.

## Safety / quality notes

- Every page has the 988 crisis line in the footer block. Keep it.
- Content is written non-clinical, no diagnosis, no symptom exaggeration — keep that bar.
- Spot-check the first 5–10 generated pages before running the full batch.
