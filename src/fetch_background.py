"""Fetches free stock video clips from Pexels for the background montage.

HALAL-ONLY visuals: nature, sky, ocean, mountains, desert, light, mosque
architecture, Islamic geometric patterns, calligraphy. Never faces of prophets,
never music-video / inappropriate footage. Requires a free PEXELS_API_KEY.

If no key / no results, returns [] and the renderer falls back to an animated
gradient in the channel's colours.
"""
import os
import json
import urllib.request
import urllib.parse
from pathlib import Path


# Halal visual search terms per content type (several for variety)
TYPE_QUERIES = {
    "quran":         ["light rays sky", "open book pages", "sunrise clouds", "calm ocean", "stars night sky"],
    "hadith":        ["mosque architecture", "islamic pattern", "desert dunes", "candle light", "calligraphy ink"],
    "dua":           ["hands prayer light", "sunset horizon", "rain window", "starry sky", "calm sea sunrise"],
    "akhlaq":        ["green forest light", "flowing river", "mountain sunrise", "blooming flower", "gentle rain"],
    "prophet_story": ["desert caravan", "ancient ruins", "night sky stars", "mountains fog", "sea waves"],
    "islamic_story": ["old city architecture", "desert sunset", "ancient manuscript", "lantern light", "stone fortress"],
    "did_you_know":  ["mosque dome", "islamic geometry", "milky way galaxy", "old manuscript", "architecture arch"],
}
DEFAULT_QUERIES = [
    "nature landscape", "sky clouds", "ocean waves", "mountains sunrise",
    "islamic pattern", "mosque architecture", "starry night", "light rays",
]

_HEADERS_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) MuslimWorldBot/1.0"


def _search_pexels(query: str, api_key: str, limit: int = 8,
                   orientation: str = "portrait") -> list[str]:
    """Returns up to `limit` video file URLs for the query in the given orientation."""
    params = urllib.parse.urlencode({
        "query": query,
        "orientation": orientation,
        "size": "medium",
        "per_page": 15,
    })
    url = f"https://api.pexels.com/videos/search?{params}"
    req = urllib.request.Request(url, headers={
        "Authorization": api_key,
        "User-Agent": _HEADERS_UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Pexels search failed ('{query}'): {e}")
        return []

    portrait = orientation == "portrait"
    urls = []
    for video in data.get("videos", []):
        if portrait:
            candidates = [f for f in video.get("video_files", [])
                          if f.get("height", 0) >= 1280 and f.get("width", 1) < f.get("height", 1)]
        else:
            candidates = [f for f in video.get("video_files", [])
                          if f.get("height", 0) >= 720 and f.get("width", 1) > f.get("height", 1)]
        if candidates:
            best = min(candidates, key=lambda f: f["height"])  # smallest HD = fast DL
            urls.append(best["link"])
        if len(urls) >= limit:
            break
    return urls


def _download(url: str, output_path: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _HEADERS_UA})
        with urllib.request.urlopen(req, timeout=60) as resp, open(output_path, "wb") as f:
            f.write(resp.read())
        return output_path
    except Exception as e:
        print(f"Download failed: {e}")
        return None


def fetch_background_clips(theme: str, output_dir: str, count: int = 5,
                          tags: list[str] = None, orientation: str = "portrait") -> list[str]:
    """
    Downloads up to `count` distinct halal clips for the theme/content-type.
    `theme` is a content_type key (quran/hadith/...) or any label; falls back to
    DEFAULT_QUERIES. `tags` (visual_tags from the generator) are tried first.
    Returns a list of local file paths (possibly empty).
    """
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []

    queries = list(TYPE_QUERIES.get(theme, DEFAULT_QUERIES))
    if tags:
        queries = list(tags[:3]) + queries  # generator's specific halal terms first

    seen, urls = set(), []
    for q in queries:
        for u in _search_pexels(q, api_key, orientation=orientation):
            if u not in seen:
                seen.add(u)
                urls.append(u)
        if len(urls) >= count:
            break

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    paths = []
    for i, u in enumerate(urls[:count]):
        dest = str(Path(output_dir) / f"clip_{i}.mp4")
        if _download(u, dest):
            paths.append(dest)
    if paths:
        print(f"{len(paths)} background clips downloaded")
    return paths


if __name__ == "__main__":
    clips = fetch_background_clips("quran", "/tmp/bgclips", count=5)
    print("Clips:", clips)
