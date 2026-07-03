"""Generates authentic Islamic short-video content via the Claude API.

Six content types rotate through the channel (one per daily slot):
  quran         - a Qur'an verse explained
  hadith        - an authentic (sahih) hadith of the day
  dua           - a supplication with meaning
  akhlaq        - a character / good-manners reminder
  prophet_story - a short story from the life of a prophet
  islamic_story - a story of the companions / righteous people / Islamic history
  did_you_know  - a "did you know?" fact about Islam / Islamic history

Non-negotiable rules baked into every prompt (from the channel policy):
  - Only authentic sources: Qur'an, Sahih hadith (Bukhari, Muslim, etc.),
    recognised scholars. ALWAYS cite the exact source.
  - No controversial fatwas, no sectarian polemics, no divisive topics.
    Where schools of law differ, stay neutral or pick a different topic.
  - Respectful to everyone. No hatred, no politics.
  - Because uploads are fully automatic, the model must be CONSERVATIVE:
    only well-established, universally-accepted content, and it must NEVER
    fabricate a hadith, a reference or a verse number.
"""
import anthropic
import json
import random

# Rotation order — 7 types cycle across the 6 daily slots (see main.py)
CONTENT_TYPES = [
    "quran", "hadith", "dua", "akhlaq", "prophet_story", "islamic_story", "did_you_know",
]

# Human-readable badge shown on screen per type
TYPE_BADGES = {
    "quran":         "QUR'AN",
    "hadith":        "HADITH",
    "dua":           "DUA",
    "akhlaq":        "CHARACTER",
    "prophet_story": "PROPHETS",
    "islamic_story": "STORY",
    "did_you_know":  "DID YOU KNOW",
}

# Type-specific instructions appended to the shared rules
TYPE_GUIDANCE = {
    "quran": (
        "Pick ONE well-known Qur'anic verse and explain its meaning simply.\n"
        "- Give the exact reference as Surah name + number:verse (e.g. Al-Baqarah 2:255).\n"
        "- Put the Arabic of the verse in \"arabic\", a simple transliteration in\n"
        "  \"transliteration\", and the English meaning in \"translation\".\n"
        "- The body explains the verse in 2-4 short sentences: context + a practical lesson.\n"
        "- Choose a famous verse you are 100% certain about. Never invent a verse number."
    ),
    "hadith": (
        "Pick ONE short, authentic (sahih) and widely-known hadith.\n"
        "- ONLY use hadith you are certain are authentic and famous (e.g. the 40 Nawawi,\n"
        "  or well-known narrations in Bukhari / Muslim). If unsure, choose a different one.\n"
        "- Source must be exact: collection + number (e.g. Sahih al-Bukhari 6018,\n"
        "  Sahih Muslim 2699, or Riyad as-Salihin / 40 Hadith Nawawi number).\n"
        "- NEVER fabricate a hadith or a number. Accuracy is more important than novelty.\n"
        "- \"arabic\" may hold the Arabic text if you are certain of it, else leave it empty.\n"
        "- The body: state the hadith's meaning, then one practical takeaway."
    ),
    "dua": (
        "Pick ONE authentic supplication (dua) from the Qur'an or Sunnah.\n"
        "- Give the exact source (e.g. Al-Baqarah 2:201, or Sahih al-Bukhari 6389).\n"
        "- \"arabic\" = the Arabic dua, \"transliteration\" = simple Latin script,\n"
        "  \"translation\" = the English meaning.\n"
        "- The body: when/why to say it and the comfort or benefit it brings."
    ),
    "akhlaq": (
        "Give ONE reminder about good character / manners (akhlaq) in Islam.\n"
        "- Anchor it in a verse or an authentic hadith and cite the exact source.\n"
        "- Topics: honesty, patience, kindness to parents, controlling anger, gratitude,\n"
        "  keeping promises, good speech, humility, generosity. Keep it universal.\n"
        "- The body: the value, why it matters, and one concrete way to practise it today."
    ),
    "prophet_story": (
        "Tell ONE short, moving episode from the life of a prophet (e.g. Ibrahim, Musa,\n"
        "Yusuf, Nuh, Muhammad peace be upon them), grounded in the Qur'an / authentic sources.\n"
        "- Cite the relevant Surah reference where the story is told.\n"
        "- IMPORTANT: never describe the physical face/appearance of any prophet.\n"
        "- The body: set the scene, the turning point, and the timeless lesson."
    ),
    "islamic_story": (
        "Tell ONE short, moving TRUE story from Islamic tradition — NOT a prophet\n"
        "(that is the prophet_story type). Draw from: the companions (Sahaba) such as\n"
        "Abu Bakr, Umar, Bilal, Khadijah, Aisha, the righteous predecessors, or a\n"
        "well-documented episode from early Islamic history.\n"
        "- Use only authentic, well-attested accounts. Avoid weak or fabricated tales.\n"
        "- Cite the source (e.g. Sahih al-Bukhari, or a recognised historical work).\n"
        "- The body: set the scene, the turning point, and one timeless lesson for today."
    ),
    "did_you_know": (
        "Share ONE surprising, TRUE and respectful fact about Islam, the Qur'an, Islamic\n"
        "history, science in the Qur'an, or Muslim contributions to civilisation.\n"
        "- It must be historically / factually accurate and verifiable. No exaggeration.\n"
        "- Cite a source (a verse, a hadith, or a well-known historical fact).\n"
        "- Avoid anything sectarian or politically charged."
    ),
}

SHARED_RULES = """You write content for an English-language Islamic YouTube Shorts channel called "Muslim World".
Your goal: authentic, respectful, valuable reminders that inspire Muslims and correctly introduce Islam to non-Muslims.

NON-NEGOTIABLE RULES:
- Sources: only the Qur'an, Sahih hadith (Bukhari, Muslim, etc.) and recognised scholarship. ALWAYS cite the exact source.
- NEVER fabricate a verse, a hadith, or a reference number. If you are not certain, choose a different, famous, well-attested item. Accuracy outranks novelty — these videos publish automatically with no human check.
- No controversial fatwas, no sectarian or school-of-law disputes, no politics, no hatred. Stay on universally accepted ground.
- Respectful and warm in tone. Never describe the face of any prophet.
- Language: English. Address the viewer directly ("you"). Simple, spoken sentences.

HOOK (first 2-3 seconds decide everything):
- Maximum 9 words, emotionally compelling, opens a curiosity gap.
- Never start with "Did you know" (except the did_you_know type may hint at it).

BODY:
- Maximum 120 words, short spoken sentences, no warm-up — start immediately.
- Warm, sincere, reflective tone. End on an uplifting note."""

PROMPT_TEMPLATE = """{shared}

CONTENT TYPE: {content_type}
{guidance}
{avoid}
Respond with ONLY a JSON object (no markdown, no explanation). Use single quotes (') inside text values, never double quotes. No line breaks inside values:
{{
  "content_type": "{content_type}",
  "title": "Clickable but respectful title, max 70 chars (no clickbait, nothing haram)",
  "hook": "Compelling hook, max 9 words",
  "body": "Spoken script, max 120 words",
  "arabic": "Arabic text if applicable (verse/dua/hadith), else empty string",
  "transliteration": "Simple Latin transliteration if applicable, else empty string",
  "translation": "English meaning of the Arabic if applicable, else empty string",
  "source": "EXACT source, e.g. Qur'an 2:255 or Sahih al-Bukhari 6018 — required, never empty",
  "cta": "Short warm call to follow/comment, e.g. Follow for a daily reminder",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "visual_tags": ["halal English stock-video search term", "term2", "term3"]
}}

"visual_tags" must be HALAL b-roll search terms only: nature, sky, stars, ocean, mountains, desert, forest, rain, light rays, mosque architecture, Islamic geometric patterns, calligraphy, candle, prayer beads. Never faces of prophets, never anything inappropriate."""


def generate_content(content_type: str = None, avoid: list[str] = None,
                     attempts: int = 3) -> dict:
    """Generates one piece of Islamic short content as a validated dict."""
    if content_type is None:
        content_type = random.choice(CONTENT_TYPES)
    if content_type not in TYPE_GUIDANCE:
        raise ValueError(f"Unknown content_type: {content_type}")

    from history import avoid_block
    prompt = PROMPT_TEMPLATE.format(
        shared=SHARED_RULES,
        content_type=content_type,
        guidance=TYPE_GUIDANCE[content_type],
        avoid=avoid_block(avoid or []),
    )

    client = anthropic.Anthropic()
    last_err = None
    for attempt in range(attempts):
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            data = json.loads(raw.strip())
            if not data.get("body"):
                raise ValueError("No body text generated")
            if not data.get("source"):
                raise ValueError("Missing mandatory source citation")
            data.setdefault("content_type", content_type)
            return data
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            print(f"Invalid response (attempt {attempt + 1}/{attempts}): {e} — retrying...")

    raise RuntimeError(f"Could not produce valid content after {attempts} attempts: {last_err}")


if __name__ == "__main__":
    import sys
    ctype = sys.argv[1] if len(sys.argv) > 1 else None
    item = generate_content(ctype)
    print(json.dumps(item, ensure_ascii=False, indent=2))
