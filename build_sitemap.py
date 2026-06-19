#!/usr/bin/env python3
"""
build_sitemap.py — walks output/ recursively and builds sitemap.xml
from the nested hub/subhub folder structure with clean URLs.

Run after generating pages (the drip and other workflows already call this
automatically). Can also be run standalone anytime: python build_sitemap.py
"""
import os
import glob
from datetime import date
from config import SITE_URL

OUTPUT_DIR = "output"

# Files that should never appear in the sitemap (previews, error logs, etc).
EXCLUDE_PREFIXES = ("_",)


def url_for(path):
    rel = os.path.relpath(path, OUTPUT_DIR)
    rel = rel.replace(os.sep, "/")
    if rel == "index.html":
        return f"{SITE_URL}/"
    if rel.endswith("/index.html"):
        return f"{SITE_URL}/{rel[:-len('index.html')]}"  # keeps trailing slash
    if rel.endswith(".html"):
        return f"{SITE_URL}/{rel[:-len('.html')]}"  # clean URL, no .html
    return f"{SITE_URL}/{rel}"


def should_include(path):
    name = os.path.basename(path)
    return not name.startswith(EXCLUDE_PREFIXES)


def main():
    files = [
        f for f in glob.glob(os.path.join(OUTPUT_DIR, "**", "*.html"), recursive=True)
        if should_include(f)
    ]
    today = date.today().isoformat()
    urls = sorted({url_for(f) for f in files})

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        # hubs/home get higher priority than deep spoke pages
        depth = u.replace(SITE_URL, "").strip("/").count("/")
        priority = "1.0" if u == f"{SITE_URL}/" else ("0.9" if depth <= 1 else "0.7")
        lines += ["  <url>", f"    <loc>{u}</loc>", f"    <lastmod>{today}</lastmod>",
                  "    <changefreq>monthly</changefreq>", f"    <priority>{priority}</priority>", "  </url>"]
    lines.append("</urlset>")

    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"sitemap.xml written with {len(urls)} URLs")


if __name__ == "__main__":
    main()
