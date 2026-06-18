#!/usr/bin/env python3
"""
build_keywords_immigrants.py — generates the immigrant-focused page universe
for TherapyFor.us, ranked by priority, written into batched JSON files.

Combines:
  - NATIONALITIES (the core moat — nobody else targets these)
  - SITUATIONS (immigrant-specific emotional triggers)
  - PROFESSIONS (immigrant working life)
  - CITIES (where diaspora communities concentrate)
  - FEELINGS (the immigrant 2am searches)

Priority tiers:
  P1 = nationality core + immigrant feelings (run first)
  P2 = nationality + situation/profession combos
  P3 = city-level and deep long-tail

Usage:  python build_keywords_immigrants.py
Writes: data/imm_p1.json, imm_p2.json, imm_p3.json, _immigrant_report.txt
"""

import json
import os
import re

OUTPUT_DIR = "data"
SLUG_MAX = 75


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:SLUG_MAX].strip("-")


def make_page(keyword, angle):
    return {"keyword": keyword, "slug": slugify(keyword), "angle": angle}


# ──────────────────────────────────────────────────────────
# NATIONALITIES — grouped by region, with a short context note
# ──────────────────────────────────────────────────────────
NATIONALITIES = [
    # Latin America (largest US immigrant volume)
    ("Mexican", "the largest US immigrant community, deep family ties left behind"),
    ("Salvadoran", "fleeing violence, sending money home, family separation"),
    ("Guatemalan", "indigenous roots, language barriers, hard labor"),
    ("Honduran", "escaping instability, building from nothing"),
    ("Colombian", "leaving behind a vivid culture, starting over"),
    ("Venezuelan", "fleeing collapse, grief for a country that changed"),
    ("Cuban", "exile, the ache of a homeland you can't easily return to"),
    ("Dominican", "tight community, pressure to provide"),
    ("Peruvian", "leaving family and tradition behind"),
    ("Ecuadorian", "hard work, sending support home, isolation"),
    ("Brazilian", "language isolation, vibrant culture left behind"),
    ("Argentine", "economic flight, cultural adjustment"),
    ("Bolivian", "indigenous identity, distance from family"),
    ("Nicaraguan", "political flight, rebuilding safety"),
    ("Chilean", "starting fresh far from home"),
    # Europe
    ("Romanian", "leaving family behind in Europe, building quietly in the US"),
    ("Polish", "strong work ethic, tight diaspora, homesickness"),
    ("Ukrainian", "displacement, war trauma, grief for home"),
    ("Russian", "cultural distance, political complexity"),
    ("Albanian", "tight family structures, honor and pressure"),
    ("Bulgarian", "quiet adjustment, distance from family"),
    ("Portuguese", "close-knit community, generational immigration"),
    ("Italian", "family-centered culture, identity across generations"),
    ("Greek", "diaspora pride, distance from homeland"),
    ("Irish", "generational ties, the pull of home"),
    ("German", "precision culture meeting American chaos"),
    ("French", "cultural difference, language and identity"),
    ("Spanish", "leaving a Mediterranean life behind"),
    ("Serbian", "history carried abroad, tight community"),
    ("Bosnian", "war legacy, refugee history, resilience"),
    # Asia
    ("Indian", "high-skill migration, H1B stress, family expectation"),
    ("Filipino", "caregiving and nursing, sending money home, sacrifice"),
    ("Chinese", "academic and family pressure, cultural distance"),
    ("Vietnamese", "refugee legacy, generational expectation"),
    ("Korean", "intense pressure to succeed, church community"),
    ("Pakistani", "faith, family honor, identity navigation"),
    ("Bangladeshi", "hard labor, sending support home"),
    ("Indonesian", "religious community, cultural adjustment"),
    ("Japanese", "precision and restraint meeting a loud culture"),
    ("Sri Lankan", "distance from family, professional migration"),
    ("Nepali", "recent growth community, hard work, isolation"),
    ("Thai", "small tight community, cultural distance"),
    ("Cambodian", "refugee legacy, intergenerational trauma"),
    # Africa & Middle East
    ("Nigerian", "high achievement pressure, vibrant diaspora"),
    ("Ghanaian", "family expectation, tight community"),
    ("Ethiopian", "refugee and migration history, strong community"),
    ("Somali", "refugee resettlement, faith, displacement"),
    ("Kenyan", "professional migration, family back home"),
    ("Egyptian", "faith and culture, identity navigation"),
    ("Moroccan", "language and faith, distance from family"),
    ("Lebanese", "diaspora resilience, war legacy"),
    ("Iranian", "exile, political complexity, cultural pride"),
    ("Syrian", "war trauma, refugee experience, profound loss"),
    ("Iraqi", "displacement, trauma, rebuilding safety"),
    ("Afghan", "refugee flight, trauma, starting over"),
    # Caribbean
    ("Haitian", "hardship, language barriers, resilience"),
    ("Jamaican", "vibrant culture, family back home"),
    ("Trinidadian", "tight diaspora, cultural pride"),
]

# Immigrant-specific situations
IMM_SITUATIONS = [
    ("loneliness", "the specific isolation of being far from everyone who knows you"),
    ("homesickness", "missing home so deeply it physically aches"),
    ("anxiety", "the constant low hum of uncertainty as an immigrant"),
    ("depression", "the quiet depression that creeps in after arriving"),
    ("acculturative stress", "the exhaustion of adapting to a whole new world"),
    ("culture shock", "the disorientation of everything being different"),
    ("isolation", "feeling cut off from both home and here"),
    ("identity loss", "not knowing who you are between two cultures"),
    ("family separation", "the grief of leaving family across an ocean"),
    ("immigration stress", "the weight of visas, status, and uncertainty"),
    ("burnout", "working endlessly to build a life with no rest"),
    ("guilt", "survivor guilt for leaving others behind"),
]

# Professions immigrants commonly work
IMM_PROFESSIONS = [
    ("nurses", "frontline caregiving far from home, emotional exhaustion"),
    ("doctors", "high pressure, re-credentialing, isolation"),
    ("caregivers", "caring for others while carrying your own grief"),
    ("engineers", "H1B and visa pressure, performance expectation"),
    ("construction workers", "hard physical labor, isolation, sending money home"),
    ("delivery drivers", "long hours, isolation, invisible work"),
    ("truck drivers", "isolation of the road, distance from family"),
    ("restaurant workers", "long shifts, low pay, exhaustion"),
    ("cleaners", "invisible labor, dignity, isolation"),
    ("students", "studying far from home, pressure and loneliness"),
    ("IT workers", "visa stress, performance pressure, isolation"),
    ("warehouse workers", "physical toll, anonymity, long shifts"),
    ("domestic workers", "isolation in someone else's home"),
    ("taxi drivers", "long solitary hours, distance from family"),
]

# Cities with major diaspora concentrations
CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Miami",
    "Dallas", "Atlanta", "Boston", "Seattle", "San Francisco",
    "Washington DC", "Phoenix", "Philadelphia", "San Diego", "Denver",
]

# Immigrant "2am" feeling searches
IMM_FEELINGS = [
    ("why do I feel so lonely after moving to America", "the loneliness nobody warned them about"),
    ("why do I cry when I call home", "the ache that surfaces hearing family's voices"),
    ("I feel invisible in America", "feeling unseen in a new country"),
    ("I feel like I made a mistake moving abroad", "the doubt and regret that creeps in"),
    ("I feel like two different people since I moved", "the split identity of living between cultures"),
    ("why do I feel guilty for leaving my country", "the guilt of those left behind"),
    ("I miss home so much I can't function", "homesickness that takes over daily life"),
    ("I feel like I don't belong anywhere anymore", "belonging to neither home nor here"),
    ("nobody here understands what I left behind", "carrying an invisible history"),
    ("I feel alone even with people around me", "isolation in a crowd of strangers"),
    ("why is starting over so much harder than I expected", "the exhaustion of rebuilding a life"),
    ("I feel ashamed that I'm struggling after moving", "the shame of not thriving as expected"),
    ("I can't talk to my family about how hard it is", "protecting family from your own pain"),
    ("I feel stuck between two worlds", "the in-between of immigrant identity"),
]


def build():
    pages = {1: [], 2: [], 3: []}
    seen = set()

    def add(tier, keyword, angle):
        slug = slugify(keyword)
        if slug in seen or not slug:
            return
        seen.add(slug)
        pages[tier].append(make_page(keyword, angle))

    # ── P1: nationality core + immigrant feelings ──
    for nat, ctx in NATIONALITIES:
        add(1, f"therapy for {nat} immigrants", ctx)
        add(1, f"therapy for {nat} immigrants in America", ctx)

    for kw, angle in IMM_FEELINGS:
        add(1, kw, angle)

    # General immigrant situation pages
    for sit, angle in IMM_SITUATIONS:
        add(1, f"therapy for immigrant {sit}", angle)
        add(1, f"therapy for immigrants with {sit}", angle)

    # ── P2: nationality + situation combos ──
    TOP_SITS = IMM_SITUATIONS[:6]  # loneliness, homesickness, anxiety, depression, acculturative stress, culture shock
    for nat, ctx in NATIONALITIES:
        for sit, s_angle in TOP_SITS:
            add(2, f"therapy for {nat} immigrants with {sit}",
                f"{ctx}; {s_angle}")

    # Profession pages (general immigrant)
    for prof, angle in IMM_PROFESSIONS:
        add(2, f"therapy for immigrant {prof}", angle)

    # ── P3: city-level + nationality-profession deep combos ──
    # Top nationalities get city pages
    TOP_NATS = NATIONALITIES[:24]
    for nat, ctx in TOP_NATS:
        for city in CITIES[:10]:
            add(3, f"therapy for {nat} immigrants in {city}",
                f"{ctx}; concentrated diaspora in {city}")

    # Nationality + profession (the deepest long tail)
    TOP_PROFS = IMM_PROFESSIONS[:8]
    for nat, ctx in NATIONALITIES[:30]:
        for prof, p_angle in TOP_PROFS:
            add(3, f"therapy for {nat} {prof} in America",
                f"{ctx}; {p_angle}")

    # Immigrant situation + city (general, no nationality)
    for sit, s_angle in IMM_SITUATIONS[:8]:
        for city in CITIES[:10]:
            add(3, f"therapy for immigrant {sit} in {city}",
                f"{s_angle}; in {city}")

    return pages


def write_files(pages):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = {
        1: ("imm_p1.json", "Immigrant P1 — Nationality core + immigrant feelings"),
        2: ("imm_p2.json", "Immigrant P2 — Nationality + situation/profession"),
        3: ("imm_p3.json", "Immigrant P3 — City-level + deep long-tail"),
    }
    report = []
    total = 0
    for tier, (fname, title) in files.items():
        data = {
            "workflow": fname.replace(".json", ""),
            "cluster_title": title,
            "pages": pages[tier],
        }
        with open(os.path.join(OUTPUT_DIR, fname), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        report.append(f"  {fname:18s} {len(pages[tier]):>4d} pages  — {title}")
        total += len(pages[tier])

    txt = ("TherapyFor.us — Immigrant keyword universe\n"
           "==========================================\n\n"
           + "\n".join(report)
           + f"\n\n  {'TOTAL':18s} {total:>4d} pages\n\n"
           "Run order: imm_p1 first, then imm_p2, then imm_p3.\n")
    with open(os.path.join(OUTPUT_DIR, "_immigrant_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    write_files(build())
