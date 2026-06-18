#!/usr/bin/env python3
"""
drip.py — generates a fixed number of pages per run, in priority order,
across ALL data files. Designed to run on a daily cron so the site grows
organically instead of dumping thousands of pages overnight.

It walks data files in a defined ORDER, finds pages that don't yet exist
in output/, and generates up to DAILY_LIMIT of them. English pages use the
normal pipeline; lang_*.json pages use the multilingual pipeline.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python drip.py [limit]

    limit (optional) overrides DAILY_LIMIT for this run.

Cron-friendly: when everything is generated, it exits cleanly with a message.
"""

import os
import sys
import json
import glob

# Reuse the two generators' internals
import generate as gen_en
import generate_multilingual as gen_ml

# ──────────────────────────────────────────────────────────
DAILY_LIMIT = 350  # pages per run
OUTPUT_DIR = "output"
TEMPLATE_PATH = "templates/page_template.html"

# Order pages get rolled out. Highest-priority money pages first,
# then immigrant, then multilingual. Within each, P1 before P2 before P3.
FILE_ORDER = [
    # money — hand built (highest quality, ship first)
    "data/workflow1_divorce.json",
    "data/workflow2_grief.json",
    "data/workflow3_anxiety.json",
    "data/workflow5_affordability.json",
    "data/workflow4_lifestage.json",
    "data/workflow6_stories.json",
    # money — auto, by priority
    "data/auto_p1.json",
    "data/auto_p2.json",
    "data/auto_p3.json",
    # immigrant, by priority
    "data/imm_p1.json",
    "data/imm_p2.json",
    "data/imm_p3.json",
    # multilingual (native content) — Spanish first, it's the biggest
    "data/lang_spanish.json",
    "data/lang_chinese.json",
    "data/lang_russian.json",
    "data/lang_portuguese.json",
    "data/lang_polish.json",
    "data/lang_arabic.json",
]


def page_exists(slug):
    return os.path.exists(os.path.join(OUTPUT_DIR, f"{slug}.html"))


def main():
    limit = DAILY_LIMIT
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()

    generated = 0
    print(f"Drip run — target {limit} pages this run.\n")

    for data_file in FILE_ORDER:
        if generated >= limit:
            break
        if not os.path.exists(data_file):
            continue

        with open(data_file, encoding="utf-8") as fh:
            data = json.load(fh)

        is_multilingual = os.path.basename(data_file).startswith("lang_")
        pending = [p for p in data["pages"] if not page_exists(p["slug"])]
        if not pending:
            continue

        print(f"[{data_file}] {len(pending)} pending")

        for page_def in pending:
            if generated >= limit:
                break
            if is_multilingual:
                status, info = gen_ml.generate_one(template, page_def)
            else:
                status, info = gen_en.generate_one(template, page_def)

            if status == "ok":
                generated += 1
                print(f"  [OK]   {info}")
            elif status == "skip":
                print(f"  [SKIP] {info}")
            else:
                print(f"  [ERR]  {info}")

    # rebuild sitemap with whatever exists now
    try:
        import build_sitemap
        build_sitemap.main()
    except Exception as e:
        print(f"(sitemap step skipped: {e})")

    total_pages = sum(
        len(json.load(open(f, encoding="utf-8"))["pages"])
        for f in FILE_ORDER if os.path.exists(f)
    )
    done = len(glob.glob(os.path.join(OUTPUT_DIR, "*.html")))
    remaining = max(0, total_pages - done)

    print(f"\nThis run: {generated} new pages.")
    print(f"Total live: ~{done} / {total_pages}.  Remaining: ~{remaining}.")
    if remaining == 0:
        print("All pages generated. Drip complete.")


if __name__ == "__main__":
    main()
