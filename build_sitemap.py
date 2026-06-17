#!/usr/bin/env python3
"""
Build sitemap.xml from all generated HTML files in output/.
Run after generating pages:  python build_sitemap.py
"""
import os
import glob
from datetime import date

SITE_URL = "https://therapyfor.us"
OUTPUT_DIR = "output"

def main():
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.html")))
    today = date.today().isoformat()

    urls = [f"{SITE_URL}/"]  # homepage
    for f in files:
        slug = os.path.splitext(os.path.basename(f))[0]
        urls.append(f"{SITE_URL}/{slug}")

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{u}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("    <priority>0.8</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"sitemap.xml written with {len(urls)} URLs")

if __name__ == "__main__":
    main()
