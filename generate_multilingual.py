#!/usr/bin/env python3
"""
generate_multilingual.py — like generate.py, but writes every page's content
natively in the target language (Spanish, Arabic, Chinese, etc.).

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python generate_multilingual.py data/lang_spanish.json

Output: output/<slug>.html  (slug already carries the lang prefix)
Adds dir="rtl" + lang attribute automatically for Arabic and other RTL langs.
"""

import os
import sys
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"
SITE_URL = "https://therapyfor.us"
AFFILIATE_LINK = "https://betterhelp.com/YOUR_AFFILIATE_LINK"  # <-- swap this
TEMPLATE_PATH = "templates/page_template.html"
OUTPUT_DIR = "output"
MAX_WORKERS = 4
SUBMIT_DELAY = 0.4

_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not _api_key:
    raise SystemExit("ERROR: ANTHROPIC_API_KEY is not set. Add it as a GitHub secret / env var.")
client = Anthropic(api_key=_api_key)

# RTL language codes
RTL_LANGS = {"arabic", "hebrew", "farsi", "urdu"}

CONTENT_SYSTEM = """You are an expert mental health content writer who writes with deep empathy and emotional intelligence in MANY languages. You write natively — never translated-sounding — in the target language, using the natural idiom, warmth, and rhythm a native speaker expects.

You write for TherapyFor.us, a site helping people find online therapy through BetterHelp.

CRITICAL RULES:
- Write ALL content fields entirely in the requested target language. Do not mix in English.
- Never diagnose or make medical claims.
- Warm, human, plain language — like a wise friend, not a brochure.
- Culturally sensitive to the specific community you're writing for.
- The brand name "BetterHelp" and "TherapyFor.us" stay in Latin script.
- Keep "988" as the US crisis number but explain it in the target language.

You output ONLY valid JSON, no markdown, no preamble. The JSON KEYS stay in English; the VALUES are in the target language."""

CONTENT_PROMPT = """Target language: {lang_name}
Write a landing page for the search term: "{keyword}"
Angle: {angle}

Write ALL values entirely in {lang_name}. Return ONLY this JSON (keys in English, values in {lang_name}, no markdown fences):
{{
  "h1": "Emotional headline mirroring the search. Wrap 3-6 words in <em></em>. Max 14 words.",
  "hero_sub": "2 sentences of pure empathy. Make them feel understood instantly.",
  "stat1_num": "A realistic statistic number, e.g. '40%' or '1 de 3'",
  "stat1_label": "Short label, max 4 words",
  "stat2_num": "Another realistic stat number",
  "stat2_label": "Short label, max 4 words",
  "section1_h2": "Heading for the empathy section",
  "section1_body": "2 paragraphs naming their specific pain, each wrapped in <p></p>.",
  "pull_quote": "A single powerful first-person quote capturing how they feel. No quotation marks inside.",
  "section1_body2": "1 paragraph continuing the empathy, wrapped in <p></p>.",
  "section2_h2": "Heading for the 'what helps' section",
  "section2_body": "2 paragraphs about why this is real and that help exists, each wrapped in <p></p>.",
  "info_box": "2-3 sentences of hopeful, factual context about how therapy helps.",
  "story_text": "A 90-word first-person story from someone in this community who found help via therapy. Specific and real-feeling.",
  "story_name": "A realistic first name and age natural to this community, e.g. 'María, 38'",
  "story_meta": "One line of context",
  "faqs": [
    {{"q": "A real objection question", "a": "A reassuring 2-3 sentence answer"}},
    {{"q": "Another objection", "a": "Answer"}},
    {{"q": "A cost question", "a": "Answer mentioning weekly pricing and 20% off first month"}},
    {{"q": "A 'will it work' question", "a": "Answer"}},
    {{"q": "A 'what if I don't like my therapist' question", "a": "Answer about switching free"}}
  ]
}}

Total 800-1000 words across all fields. Write like every word matters, fully in {lang_name}."""

SEO_SYSTEM = """You are a multilingual SEO specialist. You output ONLY valid JSON, no markdown, no preamble. Values are in the requested target language except where noted."""

SEO_PROMPT = """Target language: {lang_name}
For a page targeting "{keyword}" on TherapyFor.us (online therapy via BetterHelp), generate (values in {lang_name}):
{{
  "meta_title": "55-60 char SEO title in {lang_name}. Include the keyword. End with | TherapyFor.us",
  "meta_description": "150-160 char meta description in {lang_name}, empathetic, with soft call to action.",
  "eyebrow": "A short 2-5 word category label in {lang_name}"
}}"""


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def call_content(keyword, angle, lang_name):
    msg = client.messages.create(
        model=MODEL, max_tokens=2800, system=CONTENT_SYSTEM,
        messages=[{"role": "user", "content": CONTENT_PROMPT.format(keyword=keyword, angle=angle, lang_name=lang_name)}],
    )
    return parse_json(msg.content[0].text)


def call_seo(keyword, lang_name):
    msg = client.messages.create(
        model=MODEL, max_tokens=700, system=SEO_SYSTEM,
        messages=[{"role": "user", "content": SEO_PROMPT.format(keyword=keyword, lang_name=lang_name)}],
    )
    return parse_json(msg.content[0].text)


def build_schema(meta_title, meta_desc, canonical, faqs):
    ents = [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "name": meta_title,
                       "description": meta_desc, "url": canonical, "mainEntity": ents}, indent=2, ensure_ascii=False)


def build_faq_html(faqs):
    return "\n".join(f'<div class="faq-item"><div class="faq-q">{f["q"]}</div><div class="faq-a">{f["a"]}</div></div>' for f in faqs)


def render_page(template, content, seo, slug, lang_code, rtl):
    canonical = f"{SITE_URL}/{slug}"
    schema = build_schema(seo["meta_title"], seo["meta_description"], canonical, content["faqs"])
    faq_html = build_faq_html(content["faqs"])

    repl = {
        "{{META_TITLE}}": seo["meta_title"], "{{META_DESCRIPTION}}": seo["meta_description"],
        "{{CANONICAL_URL}}": canonical, "{{SCHEMA_JSON}}": schema, "{{AFFILIATE_LINK}}": AFFILIATE_LINK,
        "{{EYEBROW}}": seo["eyebrow"], "{{H1}}": content["h1"], "{{HERO_SUB}}": content["hero_sub"],
        "{{STAT1_NUM}}": content["stat1_num"], "{{STAT1_LABEL}}": content["stat1_label"],
        "{{STAT2_NUM}}": content["stat2_num"], "{{STAT2_LABEL}}": content["stat2_label"],
        "{{SECTION1_H2}}": content["section1_h2"], "{{SECTION1_BODY}}": content["section1_body"],
        "{{PULL_QUOTE}}": content["pull_quote"], "{{SECTION1_BODY2}}": content["section1_body2"],
        "{{SECTION2_H2}}": content["section2_h2"], "{{SECTION2_BODY}}": content["section2_body"],
        "{{INFO_BOX}}": content["info_box"], "{{STORY_TEXT}}": content["story_text"],
        "{{STORY_NAME}}": content["story_name"], "{{STORY_META}}": content["story_meta"],
        "{{FAQ_ITEMS}}": faq_html,
    }
    page = template
    for k, v in repl.items():
        page = page.replace(k, str(v))

    # set lang + dir on <html>
    lang_attr = lang_code
    if rtl:
        page = page.replace('<html lang="en">', f'<html lang="{lang_attr}" dir="rtl">')
    else:
        page = page.replace('<html lang="en">', f'<html lang="{lang_attr}">')
    return page


def generate_one(template, page_def):
    keyword = page_def["keyword"]
    slug = page_def["slug"]
    angle = page_def.get("angle", "")
    lang_code = page_def.get("lang", "en")
    lang_name = page_def.get("lang_name", "English")
    rtl = page_def.get("rtl", False) or lang_code in RTL_LANGS
    out_path = os.path.join(OUTPUT_DIR, f"{slug}.html")

    if os.path.exists(out_path):
        return ("skip", slug)

    try:
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_c = ex.submit(call_content, keyword, angle, lang_name)
            f_s = ex.submit(call_seo, keyword, lang_name)
            content = f_c.result()
            seo = f_s.result()
        html = render_page(template, content, seo, slug, lang_code, rtl)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        return ("ok", slug)
    except Exception as e:
        return ("err", f"{slug}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_multilingual.py data/lang_spanish.json")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as fh:
        data = json.load(fh)
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pages = data["pages"]
    print(f"Generating {len(pages)} pages for: {data['cluster_title']}\n")

    ok, err, skip = 0, 0, 0
    futures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for p in pages:
            futures.append(pool.submit(generate_one, template, p))
            time.sleep(SUBMIT_DELAY)
        for fut in futures:
            status, info = fut.result()
            if status == "ok":
                ok += 1; print(f"  [OK]   {info}")
            elif status == "skip":
                skip += 1; print(f"  [SKIP] {info}")
            else:
                err += 1; print(f"  [ERR]  {info}")

    print(f"\nDone. {ok} generated, {skip} skipped, {err} errors.")


if __name__ == "__main__":
    main()
