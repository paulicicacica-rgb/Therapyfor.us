#!/usr/bin/env python3
"""
fix_canonicals.py — sitewide canonical/schema URL fix for TherapyFor.us.

THE BUG: config.py's SITE_URL was set to "https://therapyfor.us" (no www),
but the live site is actually served at "https://www.therapyfor.us" (with
www). Every page's <link rel="canonical">, the JSON-LD schema "url" field,
and the sitemap were all generated from the wrong (non-www) value, baked in
at generation time. Changing config.py only fixes pages generated AFTER the
fix — every already-built page in output/ still has the old, wrong URLs
hardcoded in its HTML.

WHAT THIS SCRIPT DOES:
  Walks every .html file under output/, and for each one:
    1. Rewrites <link rel="canonical" href="https://therapyfor.us/..."> to
       the www version.
    2. Rewrites the "url": "https://therapyfor.us/..." field inside the
       embedded JSON-LD <script type="application/ld+json"> schema block.
    3. Rewrites any other bare https://therapyfor.us occurrences (og:url,
       twitter:url, absolute internal links) to the www version, EXCEPT
       it leaves alone any URL that's already correct or points to a
       genuinely different external domain.
  Does NOT touch http vs https, trailing slashes, or anything else — this
  is a narrow, single-purpose fix for exactly this bug, on purpose, so it's
  safe to run sitewide without risking unrelated side effects.

SAFE TO RE-RUN: idempotent. Running it twice does nothing the second time,
because after the first run there are no more "https://therapyfor.us"
(non-www) strings left to replace.

USAGE:
    python3 fix_canonicals.py                  # fixes output/ in place
    python3 fix_canonicals.py --dry-run         # shows what WOULD change, no writes
    python3 fix_canonicals.py --dir output      # specify a different folder
"""

import argparse
import os
import re
import sys

OLD = "https://therapyfor.us"
NEW = "https://www.therapyfor.us"

# Matches the old domain only when NOT already preceded by "www."
# (a negative lookbehind), so we never double up to www.www.therapyfor.us
# if the script is somehow run twice or mixed content already has www.
PATTERN = re.compile(r"(?<!www\.)" + re.escape(OLD))


def find_html_files(root):
    matches = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(".html"):
                matches.append(os.path.join(dirpath, fname))
    return matches


def fix_file(path, dry_run=False):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        original = f.read()

    occurrences = len(PATTERN.findall(original))
    if occurrences == 0:
        return 0

    fixed = PATTERN.sub(NEW, original)

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(fixed)

    return occurrences


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="output", help="root folder to walk (default: output)")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing files")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"ERROR: directory '{args.dir}' not found. Run this from the repo root.", file=sys.stderr)
        sys.exit(1)

    files = find_html_files(args.dir)
    print(f"Scanning {len(files)} HTML file(s) under '{args.dir}/'...\n")

    changed_files = 0
    total_occurrences = 0

    for path in sorted(files):
        n = fix_file(path, dry_run=args.dry_run)
        if n > 0:
            changed_files += 1
            total_occurrences += n
            verb = "Would fix" if args.dry_run else "Fixed"
            print(f"  {verb} {n:3d} occurrence(s) — {path}")

    print("\n--- Summary ---")
    print(f"Files scanned:     {len(files)}")
    print(f"Files changed:     {changed_files}")
    print(f"Total replacements:{total_occurrences:5d}")
    if args.dry_run:
        print("\n(dry run — no files were actually modified. Re-run without --dry-run to apply.)")


if __name__ == "__main__":
    main()
