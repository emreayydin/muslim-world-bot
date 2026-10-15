# Muslim World — Islamic YouTube Bot 🌙

Automatically creates authentic, respectful Islamic **Shorts** (6/day) and
**long-form** videos (3/week) in English, and uploads them to YouTube — fully
automated via GitHub Actions. Modelled on the "Faktastisch" trivia bot pipeline.

## What it makes

**Shorts (9:16, 30–60s)** — up to 6 per day (6 slots/day at 0,4,8,12,16,20 UTC),
rotating through 7 content types so each airs evenly across the week. On long-video
days (Tue/Thu/Sun) the 20:00 slot is skipped so the day stays within YouTube's free
10k/day upload quota → **5 shorts + 1 long** those days, **6 shorts** otherwise
(39 shorts + 3 long per week, the free-tier maximum):

| Type | Content |
|---|---|
| `quran` | A Qur'an verse explained |
| `hadith` | An authentic hadith of the day |
| `dua` | A supplication with its meaning |
| `akhlaq` | A character / good-manners reminder |
| `prophet_story` | A short story of a prophet |
| `islamic_story` | A story of the companions / righteous people / Islamic history |
| `did_you_know` | A "did you know?" fact about Islam |

**Long-form (16:9, ~8–12 min)** — Tue/Thu/Sun: list-style educational videos
(Names of Allah, Seerah, stories of the prophets, duas, akhlaq, wisdom from a surah).

## Content safety (important)

Uploads are **fully automatic and public**, so the generator is deliberately
conservative:

- Only Qur'an, Sahih hadith (Bukhari, Muslim, …) and recognised scholarship.
- **Every** piece carries an exact source, shown on screen and in the description.
- No controversial fatwas, no sectarian/school-of-law disputes, no politics.
- The prompt forbids fabricating any verse, hadith or reference number.
- Halal visuals only (nature, sky, mosques, calligraphy, patterns) — never faces
  of prophets.

Die Standardausgabe kommt aus einer lokalen, quellenmarkierten Faktenbank.
Dadurch ist kein Anthropic-Schlüssel erforderlich. Wenn später bewusst ein
LLM aktiviert wird, sollten die ersten Ausgaben trotzdem gegengeprüft werden.

## Architecture

```
Lokale Quellenbank → generate content JSON (with mandatory source)
edge-tts        → English neural voice + word timing for captions
Pexels + ffmpeg → halal montage (fast cuts + Ken-Burns) + Pillow captions/source
YouTube API     → upload (Short or long-form)
GitHub Actions  → 6 shorts/day + 3 long/week, anti-repeat history.json
```

## Setup

### 1. Dependencies
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# ffmpeg:  macOS: brew install ffmpeg   |   Ubuntu: sudo apt install ffmpeg
```

### 2. Keys
- **Pexels (free):** https://www.pexels.com/api/ → API key
- Copy `.env.example` → `.env` and add Pexels only if you want stock visuals.
- **No Anthropic key is required.** Content generation uses the local source bank.

### 3. YouTube API (one-time, needs your login)
1. [Google Cloud Console](https://console.cloud.google.com) → new project
2. Enable **YouTube Data API v3**
3. Create **OAuth client ID** (type: Desktop app) → download as
   `src/client_secrets.json`
4. Authenticate once:
   ```bash
   cd src && python upload_youtube.py
   ```
   Browser opens → authorise the "Muslim World" channel → `youtube_token.json`
   is written and its JSON printed for the GitHub secret.

### 4. GitHub secrets
`Settings → Secrets and variables → Actions`:

| Secret | Value |
|---|---|
| `PEXELS_API_KEY` | your Pexels key |
| `YOUTUBE_TOKEN_JSON` | contents of `youtube_token.json` |

## Local use

```bash
cd src

# Render only, no upload (also works without API keys via the sample):
python render_video.py                 # quick pipeline smoke test → /tmp/test_video.mp4

# Generate a real Short but do not upload:
python main.py --type quran --dry-run

# Long-form, no upload:
python main_long.py --topic "The Beautiful Names of Allah (Asma ul Husna)" --dry-run
```

## Cost
Die lokale Quellenbank, edge-tts, ffmpeg und GitHub Actions sind kostenlos.
Pexels ist optional; YouTube benötigt weiterhin OAuth, aber keinen Anthropic-Schlüssel.

## Maintenance
YouTube OAuth token expires ~6 months → re-run `python upload_youtube.py`, update
the `YOUTUBE_TOKEN_JSON` secret.
