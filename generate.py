#!/usr/bin/env python3
"""
TherapyFor.us page generator
Generates 800-1000 word landing pages from a keyword JSON file.
Two Haiku calls per page (content + SEO), run concurrently.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python generate.py data/workflow1_divorce.json

Output goes to output/<slug>.html
"""

import os
import sys
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic

# ─── CONFIG ──────────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"
SITE_URL = "https://therapyfor.us"
AFFILIATE_LINK = "https://betterhelp.com/YOUR_AFFILIATE_LINK"  # <-- swap this
TEMPLATE_PATH = "templates/page_template.html"
OUTPUT_DIR = "output"
MAX_WORKERS = 4          # concurrent pages; keep low to respect rate limits
PScript_DELAY = 0.4      # seconds between page submissions

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ─── CALL 1: PAGE CONTENT ────────────────────────────────
CONTENT_SYSTEM = """You are an expert mental health content writer for TherapyFor.us, a site that helps people find online therapy through BetterHelp. You write with deep empathy and emotional intelligence — never clinical, never salesy, never preachy.

Your writing meets people at their lowest moment and makes them feel seen, then gently opens a door to help.

CRITICAL RULES:
- Never diagnose or make medical claims
- Never exaggerate symptoms or use fear
- Warm, human, plain language — like a wise friend, not a brochure
- Vary sentence length. Short punches. Then longer, flowing thoughts.
- No clichés like "you are not alone" more than once
- American spelling and context (US audience)

You output ONLY valid JSON, no markdown, no preamble."""

CONTENT_PROMPT = """Write a landing page for the search term: "{keyword}"
Angle: {angle}

Return ONLY this JSON structure (no markdown fences):
{{
  "h1": "Emotional headline that mirrors the search. Wrap 3-6 words in <em></em> for emphasis. Max 14 words.",
  "hero_sub": "2 sentences of pure empathy under the headline. Make them feel understood in 10 seconds.",
  "stat1_num": "A realistic statistic number relevant to this topic, e.g. '40%' or '1 in 3'",
  "stat1_label": "Short label under stat1, max 4 words",
  "stat2_num": "Another realistic stat number",
  "stat2_label": "Short label under stat2, max 4 words",
  "section1_h2": "Heading for the empathy section",
  "section1_body": "2 paragraphs naming their specific pain. Wrap each in <p></p>. Make them feel seen.",
  "pull_quote": "A single powerful first-person quote that captures how someone in this situation feels. No quotation marks inside.",
  "section1_body2": "1 paragraph continuing the empathy, wrapped in <p></p>.",
  "section2_h2": "Heading for the 'why this is hard / what helps' section",
  "section2_body": "2 paragraphs about why this struggle is real and that help exists. Wrap each in <p></p>.",
  "info_box": "2-3 sentences of hopeful, factual context about how therapy helps this specific situation.",
  "story_text": "A 90-word first-person story snippet from someone who went through this and found help via therapy. Emotional, specific, real-feeling.",
  "story_name": "A realistic first name and age, e.g. 'Sarah, 38'",
  "story_meta": "One line of context, e.g. 'Started therapy after her divorce'",
  "faqs": [
    {{"q": "A real objection question someone has before starting therapy for this", "a": "A reassuring 2-3 sentence answer"}},
    {{"q": "Another objection", "a": "Answer"}},
    {{"q": "A cost/practical question", "a": "Answer mentioning weekly pricing and 20% off first month"}},
    {{"q": "A 'will it even work' question", "a": "Answer"}},
    {{"q": "A 'what if I don't like my therapist' question", "a": "Answer about switching anytime free"}}
  ]
}}

Total word count across all fields should be 800-1000 words. Write like every word matters."""

# ─── CALL 2: SEO PACKAGE ─────────────────────────────────
SEO_SYSTEM = """You are an SEO specialist. You output ONLY valid JSON, no markdown, no preamble."""

SEO_PROMPT = """For a landing page targeting the search term "{keyword}" on the site TherapyFor.us (online therapy via BetterHelp), generate:

Return ONLY this JSON (no markdown fences):
{{
  "meta_title": "55-60 char SEO title. Include the keyword naturally. Add a benefit or emotional hook. End with | TherapyFor.us if it fits.",
  "meta_description": "150-160 char meta description. Empathetic, includes keyword, has a soft call to action.",
  "eyebrow": "A short 2-5 word category label for the top of the page, e.g. 'Therapy After Divorce'"
}}"""


def call_content(keyword, angle):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2500,
        system=CONTENT_SYSTEM,
        messages=[{"role": "user", "content": CONTENT_PROMPT.format(keyword=keyword, angle=angle)}],
    )
    return parse_json(msg.content[0].text)


def call_seo(keyword):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=SEO_SYSTEM,
        messages=[{"role": "user", "content": SEO_PROMPT.format(keyword=keyword)}],
    )
    return parse_json(msg.content[0].text)


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def build_schema(meta_title, meta_desc, canonical, faqs):
    faq_entities = [
        {
            "@type": "Question",
            "name": f["q"],
            "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
        }
        for f in faqs
    ]
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "name": meta_title,
        "description": meta_desc,
        "url": canonical,
        "mainEntity": faq_entities,
    }
    return json.dumps(schema, indent=2)


def build_faq_html(faqs):
    out = []
    for f in faqs:
        out.append(
            f'<div class="faq-item"><div class="faq-q">{f["q"]}</div>'
            f'<div class="faq-a">{f["a"]}</div></div>'
        )
    return "\n".join(out)


def render_page(template, content, seo, slug):
    canonical = f"{SITE_URL}/{slug}"
    schema = build_schema(seo["meta_title"], seo["meta_description"], canonical, content["faqs"])
    faq_html = build_faq_html(content["faqs"])

    replacements = {
        "{{META_TITLE}}": seo["meta_title"],
        "{{META_DESCRIPTION}}": seo["meta_description"],
        "{{CANONICAL_URL}}": canonical,
        "{{SCHEMA_JSON}}": schema,
        "{{AFFILIATE_LINK}}": AFFILIATE_LINK,
        "{{EYEBROW}}": seo["eyebrow"],
        "{{H1}}": content["h1"],
        "{{HERO_SUB}}": content["hero_sub"],
        "{{STAT1_NUM}}": content["stat1_num"],
        "{{STAT1_LABEL}}": content["stat1_label"],
        "{{STAT2_NUM}}": content["stat2_num"],
        "{{STAT2_LABEL}}": content["stat2_label"],
        "{{SECTION1_H2}}": content["section1_h2"],
        "{{SECTION1_BODY}}": content["section1_body"],
        "{{PULL_QUOTE}}": content["pull_quote"],
        "{{SECTION1_BODY2}}": content["section1_body2"],
        "{{SECTION2_H2}}": content["section2_h2"],
        "{{SECTION2_BODY}}": content["section2_body"],
        "{{INFO_BOX}}": content["info_box"],
        "{{STORY_TEXT}}": content["story_text"],
        "{{STORY_NAME}}": content["story_name"],
        "{{STORY_META}}": content["story_meta"],
        "{{FAQ_ITEMS}}": faq_html,
    }
    page = template
    for k, v in replacements.items():
        page = page.replace(k, str(v))
    return page


def generate_one(template, page_def):
    keyword = page_def["keyword"]
    slug = page_def["slug"]
    angle = page_def.get("angle", "")
    try:
        # two calls in parallel
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_content = ex.submit(call_content, keyword, angle)
            f_seo = ex.submit(call_seo, keyword)
            content = f_content.result()
            seo = f_seo.result()

        html = render_page(template, content, seo, slug)
        out_path = os.path.join(OUTPUT_DIR, f"{slug}.html")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(html)
        return ("ok", slug)
    except Exception as e:
        return ("err", f"{slug}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate.py data/workflowX.json")
        sys.exit(1)

    data_path = sys.argv[1]
    with open(data_path, encoding="utf-8") as fh:
        data = json.load(fh)

    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pages = data["pages"]
    print(f"Generating {len(pages)} pages for cluster: {data['cluster_title']}\n")

    ok, err = 0, 0
    futures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for p in pages:
            futures.append(pool.submit(generate_one, template, p))
            time.sleep(PScript_DELAY)
        for fut in futures:
            status, info = fut.result()
            if status == "ok":
                ok += 1
                print(f"  [OK]  {info}")
            else:
                err += 1
                print(f"  [ERR] {info}")

    print(f"\nDone. {ok} pages generated, {err} errors.")
    print(f"Output: {os.path.abspath(OUTPUT_DIR)}/")


if __name__ == "__main__":
    main()
