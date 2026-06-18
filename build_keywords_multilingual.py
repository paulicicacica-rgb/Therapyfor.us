#!/usr/bin/env python3
"""
build_keywords_multilingual.py — generates therapy pages in 10 languages,
each written natively for that language community in the US.

For each language it combines core situations + immigrant-specific angles,
producing 80-120 pages per language. The generator writes the actual page
content IN that language (handled by generate_multilingual.py).

Output: one JSON per language, e.g. data/lang_spanish.json
Each page entry carries a "lang" field the generator uses to write natively.

Usage:  python build_keywords_multilingual.py
"""

import json
import os
import re

OUTPUT_DIR = "data"
SLUG_MAX = 80


def slugify(text):
    text = text.lower()
    # keep basic latin only for slugs; transliterate-ish by stripping accents handled upstream
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:SLUG_MAX].strip("-")


# ──────────────────────────────────────────────────────────
# LANGUAGES — code, name, native name, slug prefix, RTL flag,
# and the keyword phrasing IN that language.
# Each language has its own native keyword list so slugs and
# search intent match how that community actually searches.
# ──────────────────────────────────────────────────────────
LANGUAGES = {
    "spanish": {
        "name": "Spanish", "native": "Español", "rtl": False,
        "keywords": [
            ("terapia en español", "therapy in Spanish for the US Latino community"),
            ("terapia online en español sin seguro", "affordable Spanish therapy without insurance"),
            ("terapia para la ansiedad en español", "anxiety therapy in Spanish"),
            ("terapia para la depresión en español", "depression therapy in Spanish"),
            ("terapia después del divorcio", "therapy after divorce in Spanish"),
            ("terapia para inmigrantes latinos", "therapy for Latino immigrants"),
            ("terapia para la soledad del inmigrante", "immigrant loneliness therapy"),
            ("terapia para el estrés de adaptación", "acculturative stress therapy"),
            ("psicólogo que hable español", "finding a Spanish-speaking therapist"),
            ("terapia para madres latinas", "therapy for Latina mothers"),
            ("terapia para el duelo en español", "grief therapy in Spanish"),
            ("terapia de pareja en español", "couples therapy in Spanish"),
            ("cómo encontrar terapia barata en español", "how to find affordable Spanish therapy"),
            ("terapia para ataques de pánico en español", "panic attack therapy in Spanish"),
            ("terapia para la nostalgia de casa", "homesickness therapy"),
            ("por qué me siento solo en Estados Unidos", "why do I feel alone in America"),
            ("terapia para latinos sin papeles", "therapy for undocumented Latinos, confidential"),
            ("terapia para el agotamiento emocional", "emotional burnout therapy"),
            ("terapia para la culpa del inmigrante", "immigrant guilt therapy"),
            ("hablar con alguien en español sobre mis problemas", "talking to someone in Spanish"),
        ],
    },
    "portuguese": {
        "name": "Portuguese", "native": "Português", "rtl": False,
        "keywords": [
            ("terapia em português", "therapy in Portuguese for Brazilians in the US"),
            ("terapia online em português sem seguro", "affordable Portuguese therapy"),
            ("terapia para ansiedade em português", "anxiety therapy in Portuguese"),
            ("terapia para depressão em português", "depression therapy in Portuguese"),
            ("terapia para imigrantes brasileiros", "therapy for Brazilian immigrants"),
            ("terapia para solidão do imigrante", "immigrant loneliness"),
            ("psicólogo que fale português", "finding a Portuguese-speaking therapist"),
            ("terapia depois do divórcio", "therapy after divorce"),
            ("terapia para saudade de casa", "homesickness and saudade therapy"),
            ("terapia para mães brasileiras", "therapy for Brazilian mothers"),
            ("por que me sinto sozinho nos Estados Unidos", "why do I feel alone in America"),
            ("terapia para o estresse de adaptação", "acculturative stress"),
            ("terapia para luto em português", "grief therapy in Portuguese"),
            ("terapia de casal em português", "couples therapy in Portuguese"),
            ("terapia para esgotamento emocional", "emotional burnout therapy"),
        ],
    },
    "polish": {
        "name": "Polish", "native": "Polski", "rtl": False,
        "keywords": [
            ("terapia po polsku", "therapy in Polish for the US Polish community"),
            ("terapia online po polsku", "online Polish therapy"),
            ("terapia na lęk po polsku", "anxiety therapy in Polish"),
            ("terapia na depresję po polsku", "depression therapy in Polish"),
            ("terapia dla polskich imigrantów", "therapy for Polish immigrants"),
            ("psycholog mówiący po polsku", "finding a Polish-speaking therapist"),
            ("terapia po rozwodzie", "therapy after divorce"),
            ("terapia na samotność imigranta", "immigrant loneliness"),
            ("terapia na tęsknotę za domem", "homesickness therapy"),
            ("dlaczego czuję się samotny w Ameryce", "why do I feel alone in America"),
            ("terapia dla polskich matek", "therapy for Polish mothers"),
            ("terapia na stres adaptacyjny", "acculturative stress"),
            ("terapia na wypalenie emocjonalne", "emotional burnout"),
            ("terapia w żałobie po polsku", "grief therapy in Polish"),
        ],
    },
    "russian": {
        "name": "Russian", "native": "Русский", "rtl": False,
        "keywords": [
            ("терапия на русском", "therapy in Russian for US Russian speakers"),
            ("онлайн терапия на русском", "online Russian therapy"),
            ("терапия от тревоги на русском", "anxiety therapy in Russian"),
            ("терапия от депрессии на русском", "depression therapy in Russian"),
            ("терапия для русских иммигрантов", "therapy for Russian-speaking immigrants"),
            ("психолог говорящий по-русски", "finding a Russian-speaking therapist"),
            ("терапия после развода", "therapy after divorce"),
            ("терапия от одиночества иммигранта", "immigrant loneliness"),
            ("почему мне так одиноко в Америке", "why do I feel alone in America"),
            ("терапия от тоски по дому", "homesickness therapy"),
            ("терапия для русских мам", "therapy for Russian-speaking mothers"),
            ("терапия от эмоционального выгорания", "emotional burnout"),
            ("терапия горя на русском", "grief therapy in Russian"),
        ],
    },
    "arabic": {
        "name": "Arabic", "native": "العربية", "rtl": True,
        "keywords": [
            ("علاج نفسي بالعربية", "therapy in Arabic for US Arabic speakers"),
            ("علاج نفسي اونلاين بالعربية", "online Arabic therapy"),
            ("علاج القلق بالعربية", "anxiety therapy in Arabic"),
            ("علاج الاكتئاب بالعربية", "depression therapy in Arabic"),
            ("علاج نفسي للمهاجرين العرب", "therapy for Arab immigrants"),
            ("معالج نفسي يتحدث العربية", "finding an Arabic-speaking therapist"),
            ("علاج نفسي بعد الطلاق", "therapy after divorce"),
            ("علاج الشعور بالوحدة للمهاجرين", "immigrant loneliness"),
            ("لماذا أشعر بالوحدة في أمريكا", "why do I feel alone in America"),
            ("علاج الحنين إلى الوطن", "homesickness therapy"),
            ("علاج نفسي للأمهات العربيات", "therapy for Arab mothers"),
            ("علاج الإرهاق العاطفي", "emotional burnout"),
            ("علاج الحزن والفقدان بالعربية", "grief therapy in Arabic"),
        ],
    },
    "chinese": {
        "name": "Chinese", "native": "中文", "rtl": False,
        "keywords": [
            ("中文心理咨询", "therapy in Chinese for US Chinese speakers"),
            ("在线中文心理治疗", "online Chinese therapy"),
            ("中文焦虑症治疗", "anxiety therapy in Chinese"),
            ("中文抑郁症治疗", "depression therapy in Chinese"),
            ("华人移民心理咨询", "therapy for Chinese immigrants"),
            ("会说中文的心理医生", "finding a Chinese-speaking therapist"),
            ("离婚后的心理咨询", "therapy after divorce"),
            ("移民孤独感心理咨询", "immigrant loneliness"),
            ("为什么我在美国感到孤独", "why do I feel alone in America"),
            ("思乡之情的心理治疗", "homesickness therapy"),
            ("华人母亲心理咨询", "therapy for Chinese mothers"),
            ("情绪倦怠心理治疗", "emotional burnout"),
            ("中文哀伤辅导", "grief therapy in Chinese"),
        ],
    },
    # ─── CUT FOR NOW (smaller US footprint) — uncomment any to re-add ───
    # To bring a language back, just remove the leading "# DISABLED: " note
    # and restore its block here. The structure is identical to the above.
    #
    # vietnamese, korean, hindi, tagalog were here.
    # Their full keyword blocks are preserved in _cut_languages_backup.txt
}

# Shared situation expanders applied to each language (in English angle;
# the generator translates content into the target language).
# We add native-prefixed variants to scale each language to 80-100+ pages.
SITUATION_EXPANDERS_EN = [
    ("anxiety", "anxiety"), ("depression", "depression"), ("loneliness", "loneliness"),
    ("homesickness", "homesickness"), ("divorce", "after divorce"),
    ("grief", "grief and loss"), ("burnout", "emotional burnout"),
    ("panic attacks", "panic attacks"), ("stress", "chronic stress"),
    ("trauma", "trauma"), ("low self esteem", "low self-esteem"),
    ("relationship problems", "relationship difficulties"),
    ("parenting stress", "parenting stress"), ("work stress", "work stress"),
    ("insomnia", "anxiety-driven sleeplessness"),
    ("identity", "cultural identity struggles"),
    ("family pressure", "family expectation and pressure"),
    ("isolation", "social isolation"),
    ("breakup", "after a painful breakup"),
    ("acculturative stress", "the exhaustion of adapting to a new country"),
    ("immigrant guilt", "guilt over family left behind"),
    ("postpartum depression", "depression after childbirth"),
    ("anger", "anger and irritability"),
    ("overthinking", "constant overthinking and worry"),
    ("perfectionism", "perfectionism and never feeling enough"),
    ("financial stress", "money worries and financial pressure"),
    ("social anxiety", "social anxiety and fear of judgment"),
    ("emotional numbness", "feeling numb and disconnected"),
]


def build():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = []
    grand_total = 0

    for code, meta in LANGUAGES.items():
        seen = set()
        pages = []

        def add(keyword, angle):
            # slug: prefix with language code to guarantee uniqueness across langs
            base = slugify(keyword)
            if not base:
                # for non-latin scripts slugify returns empty; build from angle instead
                base = slugify(angle)
            slug = f"{code}-{base}" if base else None
            if not slug or slug in seen:
                return
            seen.add(slug)
            pages.append({
                "keyword": keyword,
                "slug": slug,
                "angle": angle,
                "lang": code,
                "lang_name": meta["name"],
                "native_name": meta["native"],
                "rtl": meta["rtl"],
            })

        # native keyword list (these are the hero terms per language)
        for kw, angle in meta["keywords"]:
            add(kw, angle)

        # expand: English-keyed situational pages, content written in target lang.
        # These ensure every language reaches good page volume even if the native
        # list is short. Keyword stays descriptive; slug carries lang prefix.
        lang_name = meta["name"]
        for sit_slug, sit_angle in SITUATION_EXPANDERS_EN:
            add(f"{lang_name} therapy for {sit_slug}",
                f"{sit_angle}, written natively in {lang_name}")
            add(f"{lang_name} speaking therapist for {sit_slug}",
                f"{sit_angle}; finding a {lang_name}-speaking therapist")
            add(f"online {lang_name} therapy for {sit_slug}",
                f"{sit_angle}; online and confidential, in {lang_name}")

        data = {
            "workflow": f"lang_{code}",
            "cluster_title": f"{meta['name']} ({meta['native']}) — {len(pages)} pages",
            "language": code,
            "pages": pages,
        }
        fname = f"lang_{code}.json"
        with open(os.path.join(OUTPUT_DIR, fname), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        report.append(f"  {fname:22s} {len(pages):>4d} pages  — {meta['name']} ({meta['native']})")
        grand_total += len(pages)

    txt = ("TherapyFor.us — Multilingual keyword universe\n"
           "=============================================\n\n"
           + "\n".join(report)
           + f"\n\n  {'TOTAL':22s} {grand_total:>4d} pages across {len(LANGUAGES)} languages\n\n"
           "Each language file is generated with generate_multilingual.py\n"
           "(writes page content natively in the target language).\n")
    with open(os.path.join(OUTPUT_DIR, "_multilingual_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    build()
