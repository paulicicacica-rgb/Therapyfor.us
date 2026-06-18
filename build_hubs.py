#!/usr/bin/env python3
"""
build_hubs.py — generates the hub index pages and the homepage.

A hub page (e.g. /anxiety/) is the authority anchor that links down to every
spoke in its cluster, and the homepage links to every hub. This is the top of
the pyramid that makes the internal-linking structure complete.

Run AFTER pages have been generated (or anytime — it reads the data files, not
the html). Re-run to refresh hub pages as more spokes get added.

Usage:  python build_hubs.py
Writes: output/index.html, output/<hub>/index.html, output/<hub>/<sub>/index.html
"""

import os
import json
import glob
import collections
from taxonomy import hub_for, HUBS, DEFAULT_HUB
import sitestructure
from config import AFFILIATE_LINK, SITE_URL

# ── shared head/style (mirrors the page template, lighter) ──
HEAD = """<!DOCTYPE html>
<html lang="{lang}"{dir}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400;1,600&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
 :root{{--navy:#1a1f3a;--navy2:#222845;--navy3:#2b3252;--rule:#353c5e;--green:#6a9d7f;--green-bright:#7fb393;--gold:#c9a55c;--cream:#faf8f2;--text:#d9dce8;--text-soft:#9298b0;--text-muted:#626885;--white:#f5f6fb;}}
 *{{margin:0;padding:0;box-sizing:border-box;}}
 body{{font-family:'Inter',sans-serif;background:var(--navy);color:var(--text);line-height:1.7;}}
 nav{{background:var(--cream);padding:20px 48px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}}
 .logo{{font-family:'Playfair Display',serif;font-size:26px;font-weight:600;color:var(--navy);}}
 .logo span{{color:var(--green);}}
 .nav-cta{{background:var(--green);color:#fff;padding:10px 20px;border-radius:7px;font-size:14px;font-weight:600;text-decoration:none;}}
 .breadcrumb{{padding:14px 48px;font-size:13px;color:var(--text-muted);border-bottom:1px solid var(--rule);}}
 .breadcrumb a{{color:var(--green-bright);text-decoration:none;}}
 .breadcrumb span{{margin:0 8px;}}
 .hero{{padding:72px 48px 48px;max-width:860px;}}
 .eyebrow{{display:inline-block;background:var(--green);color:#fff;font-size:12px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;padding:7px 18px;border-radius:20px;margin-bottom:28px;}}
 h1{{font-family:'Playfair Display',serif;font-size:clamp(34px,5vw,56px);font-weight:600;line-height:1.15;color:var(--white);margin-bottom:22px;}}
 .lead{{font-size:18px;color:var(--text-soft);max-width:600px;font-weight:300;margin-bottom:32px;}}
 .btn-main{{background:var(--green);color:#fff;padding:13px 28px;border-radius:7px;font-size:15px;font-weight:600;text-decoration:none;display:inline-block;}}
 .wrap{{max-width:1000px;margin:0 auto;padding:48px;}}
 h2{{font-family:'Playfair Display',serif;font-size:28px;font-weight:600;color:var(--white);margin:8px 0 24px;}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:40px;}}
 .grid a{{display:block;padding:16px 18px;background:var(--navy2);border:1px solid var(--rule);border-radius:8px;color:var(--text);text-decoration:none;font-size:14px;transition:all .2s;}}
 .grid a:hover{{border-color:var(--green);color:var(--white);}}
 .subhubs{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:36px;}}
 .subhubs a{{padding:8px 16px;background:var(--navy3);border:1px solid var(--rule);border-radius:20px;color:var(--green-bright);text-decoration:none;font-size:13px;font-weight:500;}}
 footer{{background:var(--navy2);border-top:1px solid var(--rule);padding:36px 48px;font-size:13px;color:var(--text-muted);line-height:1.8;margin-top:40px;}}
 footer a{{color:var(--text-muted);text-decoration:underline;}}
 @media(max-width:640px){{nav,.hero,.wrap,.breadcrumb,footer{{padding-left:20px;padding-right:20px;}}}}
</style>
</head>
<body>
<nav><div class="logo">Therapy<span>For</span></div><a href="{affiliate}" class="nav-cta">Talk to Someone Today</a></nav>
"""

FOOTER = """<footer>
TherapyFor.us &nbsp;·&nbsp; Helping people access mental health support<br>
We may earn a commission if you sign up through our links, at no extra cost to you.<br>
<a href="/about">About</a> &nbsp;·&nbsp; <a href="/editorial-standards">Editorial Standards</a> &nbsp;·&nbsp; <a href="/privacy">Privacy</a> &nbsp;·&nbsp; <a href="/contact">Contact</a>
</footer>
</body></html>"""


def card(title, url):
    label = title[0].upper() + title[1:] if title else title
    if len(label) > 70:
        label = label[:67] + "…"
    return f'<a href="{url}">{label}</a>'


def build():
    index, hub_members = get_full_index()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ---- HOMEPAGE ----
    hub_cards = []
    for hub in HUBS:
        n = len(hub_members.get(hub["slug"], []))
        if n == 0:
            continue
        hub_cards.append(f'<a href="/{hub["slug"]}/"><strong>{hub["title"]}</strong><br><span style="color:var(--text-muted);font-size:13px;">{n} resources</span></a>')

    home = HEAD.format(
        lang="en", dir="", title="TherapyFor.us — Find Online Therapy & Mental Health Support",
        desc="Honest, compassionate guides to online therapy. Find support for anxiety, depression, divorce, grief and more — and get matched with a licensed therapist.",
        canonical=f"{SITE_URL}/", affiliate=AFFILIATE_LINK,
    )
    home += f"""
<div class="hero">
  <span class="eyebrow">Online Therapy, Made Human</span>
  <h1>Whatever you're carrying, you don't have to carry it alone.</h1>
  <p class="lead">TherapyFor.us is an honest guide to online therapy and mental health support. Find help for what you're going through — and get matched with a licensed therapist in under 48 hours.</p>
  <a href="{AFFILIATE_LINK}" class="btn-main">Talk to Someone Today</a>
</div>
<div class="wrap">
  <h2>Find support for what you're going through</h2>
  <div class="grid">
    {''.join(hub_cards)}
  </div>
</div>
"""
    home += FOOTER
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(home)

    # ---- HUB PAGES ----
    made = 1
    for hub in HUBS:
        members = hub_members.get(hub["slug"], [])
        if not members:
            continue
        is_lang = "match_lang" in hub
        lang = hub.get("lang", "en")
        rtl = hub["slug"] == "arabi"
        dir_attr = ' dir="rtl"' if rtl else ""

        # group members by subhub
        by_sub = collections.defaultdict(list)
        for title, url, sub in members:
            by_sub[sub].append((title, url))

        # subhub pills
        sub_pills = ""
        if len([s for s in by_sub if s]) > 1:
            pills = [f'<a href="/{hub["slug"]}/{s}/">{s.replace("-"," ").title()}</a>'
                     for s in by_sub if s]
            sub_pills = f'<div class="subhubs">{"".join(pills)}</div>'

        # all spoke cards
        cards = "\n    ".join(card(t, u) for t, u, _s in sorted(members, key=lambda x: x[0]))

        page = HEAD.format(
            lang=lang, dir=dir_attr, title=f"{hub['title']} | TherapyFor.us",
            desc=hub["intent"], canonical=f"{SITE_URL}/{hub['slug']}/", affiliate=AFFILIATE_LINK,
        )
        page += f"""
<div class="breadcrumb"><a href="/">Home</a><span>›</span>{hub['title']}</div>
<div class="hero">
  <span class="eyebrow">{hub['title']}</span>
  <h1>{hub['title']}</h1>
  <p class="lead">{hub['intent']}. Browse {len(members)} resources below, or talk to someone today.</p>
  <a href="{AFFILIATE_LINK}" class="btn-main">Talk to Someone Today</a>
</div>
<div class="wrap">
  {sub_pills}
  <h2>All {hub['title'].lower()} resources</h2>
  <div class="grid">
    {cards}
  </div>
</div>
"""
        page += FOOTER
        folder = os.path.join(OUTPUT_DIR, hub["slug"])
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page)
        made += 1

        # ---- SUBHUB PAGES ----
        for sub, items in by_sub.items():
            if not sub:
                continue
            sub_label = sub.replace("-", " ").title()
            cards = "\n    ".join(card(t, u) for t, u in sorted(items, key=lambda x: x[0]))
            sp = HEAD.format(
                lang=lang, dir=dir_attr,
                title=f"{sub_label} — {hub['title']} | TherapyFor.us",
                desc=f"{sub_label}: {hub['intent']}",
                canonical=f"{SITE_URL}/{hub['slug']}/{sub}/", affiliate=AFFILIATE_LINK,
            )
            sp += f"""
<div class="breadcrumb"><a href="/">Home</a><span>›</span><a href="/{hub['slug']}/">{hub['title']}</a><span>›</span>{sub_label}</div>
<div class="hero">
  <span class="eyebrow">{hub['title']}</span>
  <h1>{sub_label}</h1>
  <p class="lead">{len(items)} resources on {sub_label.lower()}.</p>
  <a href="{AFFILIATE_LINK}" class="btn-main">Talk to Someone Today</a>
</div>
<div class="wrap">
  <div class="grid">
    {cards}
  </div>
</div>
"""
            sp += FOOTER
            subfolder = os.path.join(OUTPUT_DIR, hub["slug"], sub)
            os.makedirs(subfolder, exist_ok=True)
            with open(os.path.join(subfolder, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(sp)
            made += 1

    print(f"Built {made} hub/subhub/home pages.")


def get_full_index():
    """Like sitestructure index but also tracks subhub per member."""
    index = {}
    hub_members = collections.defaultdict(list)
    for f in glob.glob("data/*.json"):
        if f.endswith(".txt"):
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for p in data.get("pages", []):
            hub, sub = hub_for(p)
            url = sitestructure.page_url(p["slug"], hub, sub)
            index[p["slug"]] = url
            hub_members[hub["slug"]].append((p["keyword"], url, sub))
    return index, hub_members


if __name__ == "__main__":
    build()
