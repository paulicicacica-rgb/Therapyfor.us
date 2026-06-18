#!/usr/bin/env python3
"""
build_keywords.py — programmatically generates the full keyword universe
for TherapyFor.us, ranked by priority, and writes them into batched
JSON files the generator can consume.

It combines:
  - SEED templates (proven money phrases)
  - MODIFIERS (situations, people, professions, states, feelings)
into thousands of valid long-tail combinations, then DEDUPES and RANKS them.

Priority tiers:
  P1 = highest-volume proven money terms (run these first)
  P2 = strong long-tail with clear intent
  P3 = deep long-tail / scale volume

Usage:
    python build_keywords.py
Writes:
    data/auto_p1.json   (top ~500 priority pages)
    data/auto_p2.json
    data/auto_p3.json
    data/_keyword_report.txt  (summary)
"""

import json
import os
import re

OUTPUT_DIR = "data"
SLUG_MAX = 70

# ──────────────────────────────────────────────────────────
# SLUG HELPERS
# ──────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:SLUG_MAX].strip("-")


def make_page(keyword, angle, priority):
    return {
        "keyword": keyword,
        "slug": slugify(keyword),
        "angle": angle,
        "priority": priority,
    }


# ──────────────────────────────────────────────────────────
# MODIFIER POOLS
# ──────────────────────────────────────────────────────────

# Life situations — the core emotional triggers
SITUATIONS = [
    ("after divorce", "the emotional aftermath of divorce and rebuilding"),
    ("after a breakup", "a devastating breakup that still hurts"),
    ("after being cheated on", "betrayal trauma and rebuilding trust"),
    ("after separation", "the limbo before divorce is final"),
    ("after a toxic relationship", "healing from an emotionally draining partner"),
    ("after losing a parent", "the weight of losing a mother or father"),
    ("after losing a spouse", "widowhood and a lost shared future"),
    ("after a miscarriage", "the often silent grief of pregnancy loss"),
    ("after losing your job", "identity collapse when a career disappears"),
    ("after a death", "raw grief and the search for a way through"),
    ("for anxiety", "living with constant low-grade anxiety"),
    ("for depression", "the heaviness and numbness of depression"),
    ("for panic attacks", "the terror of panic and fear of the next one"),
    ("for burnout", "completely depleted, running on empty"),
    ("for loneliness", "deep chronic loneliness even around people"),
    ("for stress", "chronic stress that never lets up"),
    ("for grief", "carrying loss that others underestimate"),
    ("for trauma", "old wounds showing up in present life"),
    ("for low self esteem", "never feeling like enough"),
    ("for overthinking", "the racing mind that won't switch off"),
    ("for social anxiety", "the dread of being perceived"),
    ("for health anxiety", "constant fear about the body and illness"),
    ("for intrusive thoughts", "disturbing unwanted thoughts and the shame around them"),
    ("for perfectionism", "the exhausting pursuit of perfect"),
    ("for people pleasing", "saying yes to everyone and disappearing"),
    ("for anger issues", "anger that's really pain in disguise"),
    ("for postpartum depression", "the darkness after birth nobody warned about"),
    ("for empty nest", "kids leaving and not knowing who you are"),
    ("for midlife crisis", "questioning everything at 40-50"),
    ("for codependency", "unhealthy reliance and lost boundaries"),
]

# People / identity groups
PEOPLE = [
    ("new moms", "the overwhelm and identity shift of new motherhood"),
    ("single moms", "carrying everything alone with no backup"),
    ("single dads", "fathers raising kids alone, unspoken strain"),
    ("men", "men who were never taught to talk about feelings"),
    ("women", "women carrying invisible emotional load"),
    ("students", "academic pressure, isolation, uncertain futures"),
    ("college students", "the mental health crush of college years"),
    ("teenagers", "navigating adolescence and overwhelming feelings"),
    ("young adults", "the quarter-life crisis and pressure to have it together"),
    ("seniors", "isolation, loss, and change in later life"),
    ("couples", "relationship strain and communication breakdown"),
    ("parents", "the relentless pressure of raising kids"),
    ("nurses", "frontline burnout and emotional exhaustion"),
    ("teachers", "underpaid, overstretched, emotionally drained"),
    ("first responders", "trauma exposure and the cost of the job"),
    ("entrepreneurs", "the isolation and pressure of building something"),
    ("remote workers", "isolation and blurred boundaries working from home"),
    ("healthcare workers", "compassion fatigue and burnout"),
    ("veterans", "carrying service experiences into civilian life"),
    ("caregivers", "the burnout of caring for others endlessly"),
    ("introverts", "navigating a world built for extroverts"),
    ("perfectionists", "never resting, never satisfied"),
    ("overthinkers", "a mind that won't stop running"),
    ("adult children of narcissists", "unraveling a childhood around someone else's needs"),
    ("people pleasers", "losing yourself in everyone else's needs"),
    ("workaholics", "using work to avoid feeling"),
    ("highly sensitive people", "feeling everything more intensely"),
    ("immigrants", "the loneliness and stress of building a life in a new country"),
    ("expats", "isolation and identity strain living abroad"),
    ("freelancers", "income uncertainty and isolation of self-employment"),
    ("shift workers", "disrupted sleep and life out of sync with everyone"),
    ("truck drivers", "isolation and stress of long-haul life"),
    ("lawyers", "high-pressure profession and burnout"),
    ("doctors", "the emotional toll and exhaustion of medicine"),
    ("small business owners", "carrying the weight of a business alone"),
    ("retirees", "loss of purpose and structure after work ends"),
    ("divorced dads", "fathers grieving reduced access to their kids"),
    ("widows", "rebuilding after losing a spouse"),
    ("empty nesters", "the quiet house and lost identity"),
    ("grad students", "academic pressure and uncertain futures"),
    ("athletes", "performance pressure and identity tied to results"),
]

# US states for affordability local pages
STATES = [
    "California","Texas","Florida","New York","Illinois","Pennsylvania",
    "Ohio","Georgia","North Carolina","Michigan","New Jersey","Virginia",
    "Washington","Arizona","Massachusetts","Tennessee","Indiana","Missouri",
    "Maryland","Wisconsin","Colorado","Minnesota","South Carolina","Alabama",
    "Louisiana","Kentucky","Oregon","Oklahoma","Connecticut","Nevada",
]

# Feeling-state / "2am diary" searches
FEELINGS = [
    ("why do I feel anxious all the time", "constant unexplained anxiety"),
    ("why do I cry for no reason", "unexplained tears and emotional overflow"),
    ("why do I feel empty inside", "emotional emptiness and numbness"),
    ("why can't I stop overthinking", "the mind that won't switch off"),
    ("why do I feel disconnected from everyone", "feeling alone even around people"),
    ("why do I feel worse at night", "how low mood intensifies after dark"),
    ("why am I so tired all the time emotionally", "emotional exhaustion and depletion"),
    ("why do I feel like a failure", "the crushing sense of falling behind"),
    ("why am I so angry all the time", "irritability masking deeper pain"),
    ("why do I feel numb", "emotional flatness, feeling nothing"),
    ("I feel like I'm failing at life", "the sense of falling behind everyone"),
    ("I can't get out of bed lately", "the heaviness of depression"),
    ("everything feels pointless lately", "loss of meaning and motivation"),
    ("I feel like a burden to everyone", "the painful belief you weigh others down"),
    ("I don't feel like myself anymore", "the loss of identity"),
    ("I feel alone even when I'm with people", "isolation in a crowd"),
    ("I can't stop worrying about everything", "chronic relentless worry"),
    ("I feel stuck and I don't know why", "paralysis and lack of momentum"),
    ("I feel sad for no reason", "low mood without an obvious cause"),
    ("I can't switch my brain off at night", "racing thoughts and sleeplessness"),
]

# Cost / access angle
ACCESS = [
    ("affordable therapy without insurance", "wanting help but fearing the cost"),
    ("online therapy without insurance", "therapy when insurance won't cover it"),
    ("therapy when you can't afford it", "the gap between needing and affording help"),
    ("cheap online therapy that actually works", "skepticism about budget therapy quality"),
    ("how much does online therapy cost", "the practical cost question"),
    ("is online therapy worth it", "does it actually work or waste money"),
    ("online therapy vs in person", "weighing the two options"),
    ("therapy from home", "privacy and convenience of remote therapy"),
    ("therapy for busy people with no time", "fitting therapy into a packed life"),
    ("weekly pay therapy no monthly commitment", "flexibility without being locked in"),
]

# Therapy "guide / hub" intent
HUBS = [
    ("online therapy complete guide", "master hub — everything before starting"),
    ("how online therapy works", "explainer for first-timers"),
    ("signs you need therapy", "gentle checklist for the unsure"),
    ("how to find the right therapist", "practical guide to matching"),
    ("what to expect from your first therapy session", "demystifying the first appointment"),
    ("BetterHelp review honest", "balanced review — pros, cons, cost, fit"),
    ("benefits of talking to a therapist", "what therapy actually does for you"),
    ("how to start therapy when you're scared", "overcoming the fear of the first step"),
]


# ──────────────────────────────────────────────────────────
# BUILD THE UNIVERSE
# ──────────────────────────────────────────────────────────
def build():
    pages = []
    seen_slugs = set()

    def add(keyword, angle, priority):
        slug = slugify(keyword)
        if slug in seen_slugs or not slug:
            return
        seen_slugs.add(slug)
        pages.append(make_page(keyword, angle, priority))

    # ---- P1: highest-value proven money terms ----
    # Core "therapy [situation]" — these are the bread and butter
    for phrase, angle in SITUATIONS:
        add(f"therapy {phrase}", angle, 1)

    # Feelings (the 2am searches) — high intent, low competition
    for kw, angle in FEELINGS:
        add(kw, angle, 1)

    # Access / affordability core
    for kw, angle in ACCESS:
        add(kw, angle, 1)

    # Hubs
    for kw, angle in HUBS:
        add(kw, angle, 1)

    # People + top situations (the highest-converting combos)
    TOP_SITUATIONS_FOR_PEOPLE = [
        ("with anxiety", "carrying anxiety while holding everything together"),
        ("with depression", "depression beneath a functioning surface"),
        ("with burnout", "depleted past exhaustion"),
        ("who feel overwhelmed", "drowning in responsibility"),
        ("who feel alone", "isolation specific to this group"),
        ("with stress", "chronic stress wearing this group down"),
    ]
    for person, p_angle in PEOPLE:
        for suffix, s_angle in TOP_SITUATIONS_FOR_PEOPLE:
            add(f"therapy for {person} {suffix}",
                f"{p_angle}; {s_angle}", 1)

    # ---- P2: strong long-tail ----
    # "counseling [situation]" variant (different searchers than 'therapy')
    for phrase, angle in SITUATIONS:
        add(f"counseling {phrase}", angle, 2)

    # "online therapy [situation]"
    for phrase, angle in SITUATIONS:
        add(f"online therapy {phrase}", angle, 2)

    # People (plain) — therapy for [group]
    for person, angle in PEOPLE:
        add(f"therapy for {person}", angle, 2)

    # Affordability per state (local long tail)
    for state in STATES:
        add(f"affordable therapy without insurance in {state}",
            f"accessing affordable therapy in {state} without insurance", 2)

    # ---- P3: scale long-tail ----
    # "help for [situation]" framing
    for phrase, angle in SITUATIONS:
        kw = phrase.replace("for ", "").replace("after ", "after ")
        add(f"help {phrase}", angle, 3)

    # Online therapy per state
    for state in STATES:
        add(f"online therapy in {state} without insurance",
            f"online therapy options in {state}", 3)

    # People + more situations (deeper combos)
    MORE_SITUATIONS_FOR_PEOPLE = [
        ("after divorce", "this group navigating divorce"),
        ("after a breakup", "this group after a breakup"),
        ("with low self esteem", "this group struggling with self-worth"),
        ("who can't sleep", "this group with anxiety-driven insomnia"),
        ("who feel stuck", "this group feeling paralyzed"),
        ("with anger issues", "this group with anger masking pain"),
        ("with trauma", "this group carrying old wounds"),
        ("who overthink everything", "this group with relentless rumination"),
    ]
    for person, p_angle in PEOPLE:
        for suffix, s_angle in MORE_SITUATIONS_FOR_PEOPLE:
            add(f"therapy for {person} {suffix}",
                f"{p_angle}; {s_angle}", 3)

    return pages


# ──────────────────────────────────────────────────────────
# WRITE BATCHED FILES
# ──────────────────────────────────────────────────────────
def write_files(pages):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tiers = {1: [], 2: [], 3: []}
    for p in pages:
        tiers[p["priority"]].append(p)

    files = {
        1: ("auto_p1.json", "Priority 1 — Highest-value money terms"),
        2: ("auto_p2.json", "Priority 2 — Strong long-tail"),
        3: ("auto_p3.json", "Priority 3 — Scale long-tail"),
    }

    report = []
    total = 0
    for tier, (fname, title) in files.items():
        tier_pages = tiers[tier]
        # strip the priority key before writing (generator doesn't need it)
        clean = [{"keyword": p["keyword"], "slug": p["slug"], "angle": p["angle"]}
                 for p in tier_pages]
        data = {
            "workflow": fname.replace(".json", ""),
            "cluster_title": title,
            "pages": clean,
        }
        with open(os.path.join(OUTPUT_DIR, fname), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        report.append(f"  {fname:20s} {len(clean):>4d} pages  — {title}")
        total += len(clean)

    report_text = (
        "TherapyFor.us — Auto-generated keyword universe\n"
        "================================================\n\n"
        + "\n".join(report)
        + f"\n\n  {'TOTAL':20s} {total:>4d} pages\n\n"
        "Run order: auto_p1 first (most important ~500), then p2, then p3.\n"
    )
    with open(os.path.join(OUTPUT_DIR, "_keyword_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(report_text)

    print(report_text)


if __name__ == "__main__":
    pages = build()
    write_files(pages)
