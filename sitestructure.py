#!/usr/bin/env python3
"""
sitestructure.py — shared helpers that turn flat pages into a hub-and-spoke site.

Used by generate.py and generate_multilingual.py to:
  - place each page in its hub/subhub folder
  - build breadcrumb HTML
  - build internal "related links" (siblings in the same hub) + a hub link

The internal-link graph is what creates topical authority: every spoke links to
several siblings and up to its hub; the hub links down to its spokes.
"""

import os
import json
import glob
import random
from taxonomy import hub_for, HUBS, DEFAULT_HUB

SITE_URL = "https://therapyfor.us"

# Build a global index of every page -> its url + hub, once, lazily.
_INDEX = None


def _build_index():
    """Scan all data files, route every page, return dict keyed by slug."""
    index = {}
    hub_members = {}  # hub_slug -> list of (title, url)
    for f in glob.glob("data/*.json"):
        if f.endswith(".txt"):
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for p in data.get("pages", []):
            hub, sub = hub_for(p)
            url = page_url(p["slug"], hub, sub)
            title = p["keyword"]
            index[p["slug"]] = {
                "title": title, "url": url,
                "hub": hub["slug"], "sub": sub,
                "hub_title": hub["title"],
            }
            hub_members.setdefault(hub["slug"], []).append((title, url))
    return index, hub_members


def get_index():
    global _INDEX
    if _INDEX is None:
        _INDEX = _build_index()
    return _INDEX


def page_url(slug, hub, sub):
    """Clean URL path for a page within its hub/subhub."""
    if sub:
        return f"/{hub['slug']}/{sub}/{slug}"
    return f"/{hub['slug']}/{slug}"


def output_path(output_dir, slug, hub, sub):
    """Filesystem path mirroring the URL."""
    parts = [output_dir, hub["slug"]]
    if sub:
        parts.append(sub)
    folder = os.path.join(*parts)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{slug}.html")


def breadcrumb_html(hub, sub, page_title):
    """Build breadcrumb: Home > Hub > [Sub] > Page"""
    crumbs = [f'<a href="/">Home</a>']
    crumbs.append(f'<span>›</span><a href="/{hub["slug"]}/">{hub["title"]}</a>')
    if sub:
        sub_label = sub.replace("-", " ").title()
        crumbs.append(f'<span>›</span><a href="/{hub["slug"]}/{sub}/">{sub_label}</a>')
    short = page_title if len(page_title) <= 50 else page_title[:47] + "…"
    crumbs.append(f'<span>›</span>{short}')
    return "".join(crumbs)


def related_links_html(current_slug, hub_slug, n=6):
    """Pick n sibling pages in the same hub, return as link cards."""
    index, hub_members = get_index()
    members = [m for m in hub_members.get(hub_slug, []) if m[1] != index.get(current_slug, {}).get("url")]
    # stable-ish but varied selection
    if len(members) > n:
        random.seed(current_slug)  # deterministic per page
        members = random.sample(members, n)
    cards = []
    for title, url in members:
        label = title if len(title) <= 60 else title[:57] + "…"
        # Capitalize first letter for display
        label = label[0].upper() + label[1:] if label else label
        cards.append(f'<a href="{url}">{label}</a>')
    return "\n        ".join(cards)


def hub_link_html(hub):
    """A single prominent link up to the hub page."""
    return f'Explore more: <a href="/{hub["slug"]}/">{hub["title"]} →</a>'
