#!/usr/bin/env python3
"""
taxonomy.py — the site's information architecture.

Defines the HUBS (top-level authority pages) and the rules that assign every
generated page to exactly one hub. This is what turns a flat pile of pages into
a hub-and-spoke topical authority structure with clean URLs like:

    /anxiety/therapy-for-high-functioning-anxiety
    /divorce/therapy-after-divorce
    /espanol/terapia-para-la-ansiedad
    /immigrants/therapy-for-romanian-immigrants

Each hub has: slug (the folder), title, a short intent, and a list of
match rules (substrings / regexes) used to route pages into it.

Routing is FIRST-MATCH-WINS, top to bottom, so order matters: put the most
specific hubs first, the catch-alls last.
"""

import re

# ──────────────────────────────────────────────────────────
# HUBS — the spine of the site. Folder = slug.
# ──────────────────────────────────────────────────────────
HUBS = [
    # ---- Language hubs (route by lang code first, before topic) ----
    {"slug": "espanol", "lang": "spanish", "title": "Terapia en Español",
     "intent": "Spanish-language mental health hub for the US Latino community",
     "match_lang": "spanish"},
    {"slug": "portugues", "lang": "portuguese", "title": "Terapia em Português",
     "intent": "Portuguese-language mental health hub", "match_lang": "portuguese"},
    {"slug": "polski", "lang": "polish", "title": "Terapia po polsku",
     "intent": "Polish-language mental health hub", "match_lang": "polish"},
    {"slug": "russkiy", "lang": "russian", "title": "Терапия на русском",
     "intent": "Russian-language mental health hub", "match_lang": "russian"},
    {"slug": "arabi", "lang": "arabic", "title": "العلاج النفسي بالعربية",
     "intent": "Arabic-language mental health hub", "match_lang": "arabic"},
    {"slug": "zhongwen", "lang": "chinese", "title": "中文心理咨询",
     "intent": "Chinese-language mental health hub", "match_lang": "chinese"},

    # ---- Immigrant hub (route by 'immigrant' before topic) ----
    {"slug": "immigrants", "title": "Therapy for Immigrants in America",
     "intent": "Mental health support for immigrants and diaspora communities",
     "match_any": ["immigrant", "immigrants", "moved to america", "moving abroad",
                   "moved abroad", "in america", "left my country", "call home",
                   "two worlds", "two cultures", "belong anywhere", "left behind",
                   "starting over"]},

    # ---- Topic hubs (the core money structure) ----
    {"slug": "divorce", "title": "Therapy After Divorce & Breakups",
     "intent": "Support through divorce, separation, breakups and betrayal",
     "match_any": ["divorce", "breakup", "break up", "separation", "cheated",
                   "infidelity", "toxic relationship", "left by", "ex moved on",
                   "anxious attachment", "codependency", "wrong partner",
                   "gray divorce", "marriage ended"]},

    {"slug": "grief", "title": "Grief & Loss Counseling",
     "intent": "Support through bereavement, loss and grief",
     "match_any": ["grief", "losing a", "lost my", "loss of", "death", "died",
                   "miscarriage", "suicide loss", "bereavement", "passed away",
                   "after a death", "mourning", "widow"]},

    {"slug": "anxiety", "title": "Therapy for Anxiety",
     "intent": "Support for anxiety, panic, worry and overthinking",
     "match_any": ["anxiety", "anxious", "panic", "worry", "worrying",
                   "overthinking", "overthink", "intrusive thought",
                   "can't stop", "racing", "on edge", "nervous"]},

    {"slug": "depression", "title": "Therapy for Depression",
     "intent": "Support for depression, low mood and emptiness",
     "match_any": ["depression", "depressed", "empty inside", "numb",
                   "can't get out of bed", "pointless", "hopeless", "sad for no",
                   "feel sad", "low mood", "don't feel like myself",
                   "feel like a failure", "feel like a burden", "exhaustion and low"]},

    {"slug": "burnout", "title": "Therapy for Burnout & Stress",
     "intent": "Support for burnout, chronic stress and overwhelm",
     "match_any": ["burnout", "burnt out", "stress", "stressed", "overwhelm",
                   "exhaust", "depleted", "running on empty", "tired all the time"]},

    {"slug": "trauma", "title": "Therapy for Trauma & PTSD",
     "intent": "Support for trauma, PTSD and childhood wounds",
     "match_any": ["trauma", "ptsd", "abuse", "childhood trauma", "narcissist",
                   "generational trauma", "survived"]},

    {"slug": "relationships", "title": "Relationship & Family Therapy",
     "intent": "Support for relationships, family and boundaries",
     "match_any": ["couples", "relationship problem", "communication",
                   "boundaries", "family", "estrangement", "people pleas",
                   "people-pleas", "parent", "marriage"]},

    {"slug": "identity", "title": "Self-Esteem & Identity",
     "intent": "Support for self-esteem, identity, life stage and purpose",
     "match_any": ["self esteem", "self-esteem", "imposter", "perfectionism",
                   "perfectionist", "identity", "midlife", "empty nest",
                   "retirement", "lgbtq", "loneliness", "lonely", "stuck in life",
                   "stuck and", "feel stuck", "low self"]},

    {"slug": "parenting", "title": "Therapy for Parents & Mothers",
     "intent": "Support for mothers, fathers and parenting stress",
     "match_any": ["mom", "moms", "mother", "postpartum", "new mom",
                   "single mom", "dads", "father", "parenting"]},

    {"slug": "mens-health", "title": "Men's Mental Health",
     "intent": "Mental health support specifically for men",
     "match_any": ["for men", "men who", "men with", "male "]},

    {"slug": "affordable-therapy", "title": "Affordable Therapy & Access",
     "intent": "How to access affordable therapy, with or without insurance",
     "match_any": ["affordable", "without insurance", "can't afford", "cost",
                   "cheap", "low income", "worth it", "vs in person",
                   "vs in-person", "from home", "financial aid", "weekly pay",
                   "how much", "no time", "no monthly"]},

    {"slug": "guides", "title": "Guides to Online Therapy",
     "intent": "Explainer and guide content about therapy and BetterHelp",
     "match_any": ["guide", "how online therapy works", "signs you need",
                   "find the right therapist", "first therapy session",
                   "betterhelp review", "how to start therapy",
                   "benefits of", "what to expect", "complete guide"]},

    # ---- Stories get their own hub ----
    {"slug": "stories", "title": "Real Stories",
     "intent": "First-person stories of finding help",
     "match_any": ["story", "this is what helped", "didn't speak", "fell apart",
                   "couldn't get out of bed", "nobody knew what to say",
                   "the strong one", "i had everything"]},
]

# Catch-all hub for anything unmatched (should be rare)
DEFAULT_HUB = {"slug": "support", "title": "Mental Health Support",
               "intent": "General mental health support and therapy"}


def hub_for(page):
    """Return (hub, subhub_slug_or_None) the page belongs to. First match wins."""
    lang = page.get("lang")
    keyword = page.get("keyword", "").lower()
    angle = page.get("angle", "").lower()
    haystack = f"{keyword} {angle}"

    # 1) language pages route to their language hub first
    if lang:
        for hub in HUBS:
            if hub.get("match_lang") == lang:
                return hub, _lang_subhub(haystack)

    # 2) topic / immigrant routing by keyword match
    for hub in HUBS:
        if "match_lang" in hub:
            continue
        for term in hub.get("match_any", []):
            if term in haystack:
                sub = _immigrant_subhub(haystack) if hub["slug"] == "immigrants" else None
                return hub, sub

    return DEFAULT_HUB, None


# Sub-hub routing for the big immigrant cluster — breaks 1000+ pages into
# topical sub-folders so no single folder is a flat dump.
IMM_SUB_RULES = [
    ("loneliness", ["lonely", "loneliness", "alone", "isolat"]),
    ("homesickness", ["homesick", "miss home", "call home", "nostalgia", "saudade"]),
    ("anxiety", ["anxiety", "anxious", "panic", "worry"]),
    ("depression", ["depression", "depressed", "empty", "numb"]),
    ("adjustment", ["acculturat", "culture shock", "adapting", "adjustment",
                    "two worlds", "two cultures", "belong", "identity", "stuck"]),
    ("family", ["family separation", "guilt", "left behind", "left my country"]),
    ("work", ["nurse", "doctor", "caregiver", "engineer", "construction",
              "delivery", "truck", "restaurant", "cleaner", "student",
              "warehouse", "domestic", "taxi", "worker", "burnout"]),
]

def _immigrant_subhub(haystack):
    for sub, terms in IMM_SUB_RULES:
        for t in terms:
            if t in haystack:
                return sub
    return "general"


# Sub-hub routing inside each language hub, so /espanol isn't a flat dump either.
LANG_SUB_RULES = [
    ("ansiedad", ["anxiety", "anxious", "panic", "ansied", "тревог", "焦虑",
                  "قلق", "lęk", "ansiedade"]),
    ("depresion", ["depression", "depres", "uppression", "抑郁", "اكتئاب",
                   "депресс"]),
    ("inmigrantes", ["immigrant", "imigrant", "inmigrant", "иммигрант",
                     "移民", "مهاجر", "imigr"]),
    ("relaciones", ["divorce", "divorcio", "divórcio", "развод", "离婚",
                    "طلاق", "rozwod", "couple", "pareja", "casal"]),
    ("duelo", ["grief", "duelo", "luto", "горе", "حزن", "żałob", "哀伤"]),
]

def _lang_subhub(haystack):
    for sub, terms in LANG_SUB_RULES:
        for t in terms:
            if t in haystack:
                return sub
    return "general"


def all_hub_slugs():
    return [h["slug"] for h in HUBS] + [DEFAULT_HUB["slug"]]


if __name__ == "__main__":
    # quick self-test: route every page in data/ and report distribution
    import json, glob, collections
    counts = collections.Counter()
    subcounts = collections.Counter()
    for f in glob.glob("data/*.json"):
        if f.endswith(".txt"):
            continue
        data = json.load(open(f, encoding="utf-8"))
        for p in data.get("pages", []):
            h, sub = hub_for(p)
            counts[h["slug"]] += 1
            key = f"{h['slug']}/{sub}" if sub else h["slug"]
            subcounts[key] += 1
    print("HUB distribution:\n")
    total = 0
    for slug, n in counts.most_common():
        total += n
        print(f"  {slug:20s} {n:>4d}")
    print(f"\n  TOTAL {total} pages routed\n")
    print("Largest sub-folders (no single folder should be a flat dump):\n")
    for key, n in subcounts.most_common(15):
        print(f"  {key:34s} {n:>4d}")
