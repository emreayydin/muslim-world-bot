"""Muslim World: Sammlung taeglich kostenlos auffuellen (laeuft auf GitHub).

Schreiben/Pruefen ueber Gratis-Kontingente mit Wechsel (ki_kern.py: Groq,
Mistral, Gemini). Strenger als bei den anderen Kanaelen: die KI darf hier NUR
Inhalte liefern,
die auf Koranversen beruhen (quran, dua, akhlaq, prophet_story). Jede
angegebene Stelle wird bei api.alquran.cloud nachgeschlagen; gibt es sie
nicht, fliegt der Eintrag raus. Der echte Verstext geht dann mit in die
Gegenpruefung, damit Uebersetzung und Aussage zum Vers passen muessen.
Hadithe und Geschichte schreibt weiter nur der Claude-Agent - deren
Nummern lassen sich nicht automatisch nachpruefen.

    python scripts/content_bank_nachfuellen.py            # auffuellen
    python scripts/content_bank_nachfuellen.py --anzahl 3 # kleiner Test
"""
import argparse
import json
import os
import random
import re
import sys
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "scripts"))

import ki_kern as g  # noqa: E402
import local_content  # noqa: E402

NEU_DATEI = WURZEL / "src" / "content_bank_neu.py"
ZIEL = int(os.environ.get("BANK_ZIEL", "45"))
PRO_LAUF = int(os.environ.get("PRO_LAUF", "10"))
PRO_AUFRUF = 5
MAX_RUNDEN = 12
TYPEN = {"dua": 4, "quran": 3, "akhlaq": 2, "prophet_story": 2}
QUELLE = re.compile(r"^Qur'an (\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?$")

AUFTRAG = """You write entries for the English YouTube Shorts channel "Muslim World":
calm, respectful Islamic reminders. Only use verses you know precisely - every
reference is looked up automatically and checked against the real verse text.

Write {anzahl} new entries of type "{typ}". {typ_regel}

HARD RULES
- Every entry is based ONLY on Qur'an verses. No hadith, no history, no
  stories that are not in the Qur'an itself.
- "source" is exactly one reference in the form "Qur'an S:A" or "Qur'an S:A-B"
  (at most 8 verses). It must be the verse that actually says what you write.
- "translation": a faithful paraphrase of that verse in plain English, at most
  220 characters. Never add words the verse does not contain.
- Do not invent details. No numbers, names or events that are not in the verse.
- No music, no instruments, no narrator character.

These topics and verses were already used - do not repeat them:
{schon}

Fields per entry:
- content_type: "{typ}"
- title: at most 60 characters, honest, inviting. Style that works on the
  channel: "The Dua to Say When You Feel Hopeless", "This Verse Tells You
  Where True Trust Belongs".
- hook: one sentence, at most 60 characters.
- body: 55 to 80 words, spoken English, gentle and concrete.
- translation, source as above
- tags: 4 lowercase tags

Answer ONLY with a JSON array of these objects inside a ```json block."""

TYP_REGEL = {
    "dua": "A dua that appears word for word in the Qur'an, with when to say it.",
    "quran": "One verse and what it means for daily life.",
    "akhlaq": "Good character as the Qur'an itself teaches it.",
    "prophet_story": "A moment from a prophet's life exactly as the Qur'an tells it.",
}


def vers_text(s, a, b):
    """Echte englische Uebersetzung (Sahih International) oder None, wenn es die Stelle nicht gibt."""
    teile = []
    for ayah in range(a, (b or a) + 1):
        try:
            with urllib.request.urlopen(
                    f"https://api.alquran.cloud/v1/ayah/{s}:{ayah}/en.sahih", timeout=30) as r:
                daten = json.loads(r.read())
        except Exception:  # noqa: BLE001 - 404 oder Netz: Stelle gilt als unbelegt
            return None
        if daten.get("code") != 200:
            return None
        teile.append(f"{s}:{ayah} {daten['data']['text']}")
    return "\n".join(teile)


def gueltig(e, bekannt):
    for k in ("content_type", "title", "hook", "body", "translation", "source", "tags"):
        if not e.get(k):
            return f"Feld {k} fehlt", None
    if e["title"].lower() in bekannt:
        return "Titel schon bekannt", None
    if len(e["title"]) > 75 or len(e["translation"]) > 260:
        return "zu lang", None
    woerter = len(str(e["body"]).split())
    if not 40 <= woerter <= 110:
        return f"Text {woerter} Woerter", None
    m = QUELLE.match(str(e["source"]).strip())
    if not m:
        return f"Quelle nicht im Format Qur'an S:A ({e['source']})", None
    s, a, b = int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None
    if b is not None and not (a < b <= a + 7):
        return "Versbereich ungueltig", None
    text = vers_text(s, a, b)
    if not text:
        return "Vers existiert nicht", None
    return None, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anzahl", type=int)
    args = ap.parse_args()

    gepostet = {e["title"].lower() for e in json.loads((WURZEL / "history.json").read_text())}
    frisch = [e for e in local_content.ENTRIES if e["title"].lower() not in gepostet]
    fehlend = args.anzahl if args.anzahl is not None else min(PRO_LAUF, max(0, ZIEL - len(frisch)))
    print(f"Frische Eintraege: {len(frisch)}, Ziel {ZIEL}, fehlen {fehlend}")
    if not fehlend:
        return

    try:
        from content_bank_neu import NEU
    except ImportError:
        NEU = []
    bekannt = gepostet | {e["title"].lower() for e in local_content.ENTRIES}
    quellen = sorted({e.get("source", "") for e in local_content.ENTRIES})
    schon = sorted(bekannt)[-150:] + [f"verse {q}" for q in quellen if q.startswith("Qur")]
    neu, verworfen = [], 0
    for runde in range(MAX_RUNDEN):
        if len(neu) >= fehlend:
            break
        typ = random.choices(list(TYPEN), weights=list(TYPEN.values()))[0]
        print(f"Runde {runde + 1}: {typ}")
        for e in g.erzeugen(AUFTRAG.format(anzahl=PRO_AUFRUF, typ=typ, typ_regel=TYP_REGEL[typ],
                                           schon="\n".join(f"- {t}" for t in schon))):
            if len(neu) >= fehlend:
                break
            e["content_type"] = typ
            grund, vers = gueltig(e, bekannt)
            if grund:
                verworfen += 1
                print(f"  verworfen ({grund}): {e.get('title')}")
                continue
            ok, warum = g.pruefen(
                {k: e[k] for k in ("title", "hook", "body", "translation", "source")},
                "This is Islamic content. The translation must faithfully match the real verse "
                "text given below, and every statement in the body must be supported by that "
                "verse. General encouragement that follows from the verse is fine; any added "
                "fact, name, event or number that is not in the verse means ok=false.",
                zusatz=f"REAL VERSE TEXT (Sahih International):\n{vers}\n")
            if not ok:
                verworfen += 1
                print(f"  Pruefung nein: {e['title']} - {warum}")
                continue
            print(f"  + {e['title']} ({e['source']})")
            neu.append({k: e[k] for k in ("content_type", "title", "hook", "body",
                                          "translation", "source", "tags")})
            bekannt.add(e["title"].lower())
            schon.append(e["title"].lower())
            schon.append(f"verse {e['source']}")

    if neu:
        g.schreibe_modul(NEU_DATEI, "NEU", list(NEU) + neu,
                         "Automatisch geschriebene, gegen den Korantext gepruefte Eintraege "
                         "(scripts/content_bank_nachfuellen.py). Nicht von Hand ordnen.")
    print(f"Ergebnis: {len(neu)} neu, {verworfen} verworfen, "
          f"noch fehlend {max(0, fehlend - len(neu))}")


if __name__ == "__main__":
    main()
