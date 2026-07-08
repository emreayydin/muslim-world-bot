"""Generates a long-form Islamic educational script (16:9 video) via Claude.

List-style, safe, non-sectarian topics (Seerah, Names of Allah, stories of the
prophets, duas, akhlaq, wisdom from a surah). Every point carries a source.
"""
import anthropic
import json
import random


LONG_TOPICS = [
    "The Beautiful Names of Allah (Asma ul Husna)",
    "Stories of the Prophets and their lessons",
    "Lessons from the Seerah (life of Prophet Muhammad, peace be upon him)",
    "Powerful duas from the Qur'an and Sunnah",
    "Good character and manners in Islam (Akhlaq)",
    "Timeless wisdom from Surah Al-Kahf",
    "The Companions of the Prophet (the Sahaba)",
    "The signs of Allah in His creation",
    "The virtues of patience, gratitude and charity",
    "Common questions about Islam, answered simply",
    # Story-driven Islamic history topics
    "Incredible true stories of the Companions (Sahaba)",
    "Inspiring stories of the righteous predecessors (the Salaf)",
    "Powerful moments from early Islamic history",
    "The remarkable lives of the women around the Prophet ﷺ",
    "Stories of faith and courage from Islamic history",
]

SHARED_RULES = """You write scripts for an English-language Islamic educational YouTube channel called "Muslim World".

NON-NEGOTIABLE RULES:
- Sources: only the Qur'an, Sahih hadith (Bukhari, Muslim, etc.) and recognised scholarship. ALWAYS cite the exact source per point.
- NEVER fabricate a verse, a hadith, or a reference number. If unsure, use a different, famous, well-attested item. Accuracy outranks novelty — this publishes automatically.
- No controversial fatwas, no sectarian or school-of-law disputes, no politics, no hatred. Stay on universally accepted ground.
- Respectful and warm. Never describe the face of any prophet.
- Language: English, addressing the viewer directly. Clear, warm, reflective."""

PROMPT_TEMPLATE = """{shared}

Write a script for a calm, educational list-style video on the topic: {topic}
{avoid}
Rules:
- Exactly 10 points/lessons, each genuinely valuable and true.
- Each point: 90-130 words, told warmly and vividly, with a practical takeaway.
- Each point MUST include an exact source (a verse, a hadith reference, or a well-known historical fact).
- Intro: a warm, inviting opening (max 45 words).
- Outro: a reflective question + a gentle invitation to subscribe (max 40 words).
- Build meaningfully; keep the most moving point for last.

IMPORTANT for valid JSON: NEVER use double quotes (") inside text values — use single (') or none. No line breaks inside values.

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "title": "Respectful, inviting title (max 70 chars, no clickbait)",
  "topic": "Short topic (1-4 words)",
  "intro": "Intro text",
  "hook_visual": "halal English AI-image prompt for the intro",
  "facts": [
    {{"headline": "Short headline (max 40 chars)", "text": "90-130 words", "source": "CONCISE citation only, e.g. Qur'an 2:255 or Sahih al-Bukhari 6018 (max ~30 chars)", "image_prompt": "halal English AI-image prompt"}}
  ],
  "outro": "Outro text",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "visual_tags": ["halal stock term","term2","term3"],
  "category": "{topic}"
}}

The "facts" list must have exactly 10 entries. "visual_tags" must be HALAL only: nature, sky, ocean, mountains, desert, mosque architecture, islamic patterns, calligraphy, light.
"image_prompt"/"hook_visual" = STRICTLY HALAL AI-image prompts: only serene scenes (nature, sky, stars, desert, ocean, mountains, mosque architecture, arabesque/geometric patterns, soft divine light, lanterns, prayer beads, old manuscripts without readable text). ABSOLUTELY NO people, NO faces, NO figures, NEVER any depiction of God, prophets, the Prophet Muhammad, companions, or the Kaaba interior. No text in the image. Reverent, cinematic, peaceful."""


def generate_compilation(topic: str = None, avoid: list[str] = None,
                         attempts: int = 3) -> dict:
    if topic is None:
        topic = random.choice(LONG_TOPICS)

    from history import avoid_block
    prompt = PROMPT_TEMPLATE.format(
        shared=SHARED_RULES, topic=topic, avoid=avoid_block(avoid or []))

    client = anthropic.Anthropic()
    last_err = None
    for attempt in range(attempts):
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            data = json.loads(raw.strip())
            if not data.get("facts"):
                raise ValueError("No points generated")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            print(f"Invalid response (attempt {attempt + 1}/{attempts}): {e} — retrying...")

    raise RuntimeError(f"Could not produce a valid script after {attempts} attempts: {last_err}")


if __name__ == "__main__":
    comp = generate_compilation()
    print(f"Title: {comp['title']}")
    print(f"Points: {len(comp['facts'])}")
    for i, f in enumerate(comp["facts"], 1):
        print(f"  {i}. {f['headline']}  ({f.get('source', '')})")
