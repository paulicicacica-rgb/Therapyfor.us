#!/usr/bin/env python3
"""
TherapyFor.us — dead page audit.

Answers one question per URL: is this page actually there and good,
or is it dead — and if dead, WHY (never generated / generated but broken /
generated but thin / orphaned with no sitemap entry).

WHAT THIS CHECKS, for every URL in the sitemap(s):
  1. HTTP status (404 / 500 / redirect / 200)
  2. If 200: page size and a thin-content heuristic (word count, whether it
     has real body content vs just nav/footer boilerplate)
  3. Cross-check against the repo file tree (if REPO_ROOT is a local
     checkout) to see whether a source file for that URL actually exists
     on disk — this is what tells "never generated" apart from
     "generated but the live deploy is serving something else."
  4. Language mismatch heuristic: flags pages where the URL/lang prefix
     says one language (e.g. /es/) but the visible CTA/button text still
     contains English strings from a fixed list (the exact "Talk to
     Someone Today" type leftover bug you found).

OUTPUT: dead_pages_report.csv with one row per URL and a clear "verdict"
column, plus a console summary count by verdict.

USAGE:
    python3 audit_dead_pages.py --sitemap https://therapyfor.us/sitemap.xml
    python3 audit_dead_pages.py --sitemap https://therapyfor.us/sitemap.xml --repo-root /path/to/local/checkout
    python3 audit_dead_pages.py --url-list urls.txt          # if you'd rather paste URLs directly
"""

import argparse
import csv
import os
import re
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree import ElementTree as ET

# ----- config you may want to tweak -----
THIN_WORD_THRESHOLD = 150          # below this many visible words => "thin"
REQUEST_TIMEOUT = 12
MAX_WORKERS = 12
RETRY_ON_TIMEOUT = 2

# English leftover strings that should NEVER appear on a non-English page's
# primary CTA. Extend this list as you find more.
ENGLISH_CTA_LEAKS = [
    "Talk to Someone Today",
    "Talk to someone today",
    "Find someone to talk to",
    "Get matched",
    "Free consultation",
]

# language prefixes you actually use — maps URL prefix to expected lang
LANG_PREFIXES = {
    "/es/": "es", "/pt-br/": "pt", "/pl/": "pl", "/ru/": "ru", "/ro/": "ro",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (dead-page-audit)"})
    last_err = None
    for attempt in range(RETRY_ON_TIMEOUT + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                return resp.status, body, None
        except urllib.error.HTTPError as e:
            return e.code, "", str(e)
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            time.sleep(1.5)
    return 0, "", last_err


def strip_tags(html):
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def get_lang_prefix(url):
    for prefix, lang in LANG_PREFIXES.items():
        if prefix in url:
            return lang
    return "en"


def check_english_leak(url, html):
    lang = get_lang_prefix(url)
    if lang == "en":
        return False, ""
    for leak in ENGLISH_CTA_LEAKS:
        if leak in html:
            return True, leak
    return False, ""


def load_sitemap_urls(sitemap_url):
    """Handles both a plain sitemap and a sitemap index (sitemap of sitemaps)."""
    status, body, err = fetch(sitemap_url)
    if status != 200:
        print(f"Could not fetch sitemap {sitemap_url}: status={status} err={err}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        print(f"Could not parse sitemap XML: {e}", file=sys.stderr)
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []

    # Is this a sitemap index?
    sub_sitemaps = root.findall("sm:sitemap/sm:loc", ns)
    if sub_sitemaps:
        for loc in sub_sitemaps:
            urls.extend(load_sitemap_urls(loc.text.strip()))
        return urls

    for loc in root.findall("sm:url/sm:loc", ns):
        urls.append(loc.text.strip())
    return urls


def repo_file_for_url(url, repo_root):
    """Best-effort guess at where this URL's source file would live in the
    repo, for static-site / Next.js-style export structures. Adjust the
    candidate paths list if your repo uses a different convention."""
    from urllib.parse import urlparse
    path = urlparse(url).path.strip("/")
    if path == "":
        path = "index"
    candidates = [
        os.path.join(repo_root, path, "index.html"),
        os.path.join(repo_root, path + ".html"),
        os.path.join(repo_root, "pages", path + ".js"),
        os.path.join(repo_root, "pages", path + ".tsx"),
        os.path.join(repo_root, "app", path, "page.tsx"),
        os.path.join(repo_root, "app", path, "page.js"),
        os.path.join(repo_root, "content", path + ".md"),
        os.path.join(repo_root, "content", path + ".mdx"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def classify(url, status, html, err, repo_root):
    """Returns (verdict, detail)."""
    if status in (404, 410):
        if repo_root:
            src = repo_file_for_url(url, repo_root)
            if src:
                return "BROKEN_LIVE_404_BUT_SOURCE_EXISTS", f"source file present at {src}, but live site 404s — likely a deploy/build/routing issue"
            else:
                return "NEVER_GENERATED_404", "no source file found in repo and live site 404s — page was listed in sitemap but never built"
        return "DEAD_404", "live site returns 404/410"

    if status in (301, 302, 307, 308):
        return "REDIRECT", f"redirects (status {status}) — check if sitemap should point at the final URL instead"

    if status == 0 or status >= 500:
        return "SERVER_ERROR_OR_TIMEOUT", err or f"status {status}"

    if status == 403:
        return "BLOCKED_403", "server returned 403 — could be a real access restriction, or the site's bot/WAF protection blocking this checker; verify manually before assuming it's broken for real visitors"

    if status in (401, 429):
        return "BLOCKED_OR_RATE_LIMITED", f"status {status} — site may be rate-limiting or blocking automated requests; re-run slower or from a different IP/User-Agent"

    if status == 200:
        text = strip_tags(html)
        word_count = len(text.split())

        leak, leaked_string = check_english_leak(url, html)

        if word_count < THIN_WORD_THRESHOLD:
            detail = f"only ~{word_count} visible words — looks thin/boilerplate-only, may be an auto-generated shell with no real content"
            if leak:
                detail += f"; ALSO has English CTA leak: '{leaked_string}'"
            return "THIN_OR_EMPTY", detail

        if leak:
            return "LIVE_BUT_ENGLISH_CTA_LEAK", f"page has real content (~{word_count} words) but CTA leaks English string: '{leaked_string}'"

        return "OK", f"~{word_count} words, looks like a real page"

    return "UNKNOWN", f"unexpected status {status}"


def audit(urls, repo_root):
    results = []

    def worker(url):
        status, html, err = fetch(url)
        verdict, detail = classify(url, status, html, err, repo_root)
        return {"url": url, "status": status, "verdict": verdict, "detail": detail}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(worker, u): u for u in urls}
        for i, fut in enumerate(as_completed(futures), 1):
            row = fut.result()
            results.append(row)
            print(f"[{i}/{len(urls)}] {row['verdict']:32s} {row['url']}")

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sitemap", help="sitemap.xml URL to crawl")
    parser.add_argument("--url-list", help="path to a plain text file, one URL per line")
    parser.add_argument("--repo-root", default=None, help="local path to a checked-out copy of the repo, to distinguish 'never generated' from 'broken deploy'")
    parser.add_argument("--out", default="dead_pages_report.csv")
    args = parser.parse_args()

    if not args.sitemap and not args.url_list:
        print("Provide --sitemap or --url-list", file=sys.stderr)
        sys.exit(1)

    if args.sitemap:
        urls = load_sitemap_urls(args.sitemap)
    else:
        with open(args.url_list, encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

    urls = sorted(set(urls))
    print(f"Loaded {len(urls)} URLs to check.\n")

    results = audit(urls, args.repo_root)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "status", "verdict", "detail"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print("\n--- Summary ---")
    counts = {}
    for row in results:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    for verdict, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {verdict:32s} {count}")

    print(f"\nFull detail written to {args.out}")


if __name__ == "__main__":
    main()
