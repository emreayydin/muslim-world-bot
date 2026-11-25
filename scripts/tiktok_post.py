"""Post a finished story Short to TikTok @muslimworld0 via TikTok Studio.

Drives the separate Muslim World Chrome (scripts/open_tiktok_browser.sh, port
9341) over raw CDP. Never touches any other TikTok account: it aborts unless
the logged-in user is EXPECTED_USER. Always switches on TikTok's
"AI-generated content" label (the stories are AI animation).

    venv/bin/python scripts/tiktok_post.py video.mp4 "caption" [--dry-run]

--dry-run fills in everything, saves a screenshot and discards the draft.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Page  # noqa: E402

EXPECTED_USER = "muslimworld0"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload"
SHOT = Path(__file__).resolve().parent.parent / "logs" / "tiktok_last.jpg"

# click the first visible button/element whose own text matches exactly
CLICK_TEXT = """((txt, scope) => {
  const root = scope ? [...document.querySelectorAll('[role=dialog],[class*=modal],[class*=Modal]')]
      .find(d => d.innerText && d.innerText.includes(scope)) : document;
  if (!root) return false;
  const el = [...root.querySelectorAll('button,[role=button]')]
      .find(e => e.innerText && e.innerText.trim() === txt && e.offsetParent !== null);
  if (!el) return false; el.click(); return true;
})(%r, %r)"""

SWITCH = """((label) => {
  for (const e of document.querySelectorAll('[role=switch],input[type=checkbox]')) {
    let c = e; for (let i = 0; i < 6 && c; i++) { c = c.parentElement;
      if (c && c.innerText && c.innerText.trim().length > 3) break; }
    if (c && c.innerText.includes(label)) {
      const on = (e.getAttribute('aria-checked') ?? String(e.checked)) === 'true';
      return on ? 'on' : (e.click(), 'clicked');
    }
  }
  return 'missing';
})(%r)"""


class TikTokError(RuntimeError):
    pass


def _dismiss_popups(p: Page) -> None:
    p.js(CLICK_TEXT % ("Verstanden", ""))
    p.js(CLICK_TEXT % ("Abbrechen", "Automatische Inhaltsprüfungen"))
    p.js(CLICK_TEXT % ("Got it", ""))


def _discard(p: Page) -> None:
    if p.js(CLICK_TEXT % ("Verwerfen", "")):
        time.sleep(1.5)
        p.js(CLICK_TEXT % ("Verwerfen", "verwerfen?"))
        time.sleep(2)


def post(video: str, caption: str, dry_run: bool = False) -> bool:
    video = str(Path(video).resolve())
    p = Page.open(UPLOAD_URL, "tiktokstudio")
    time.sleep(8)
    user = p.account()
    if user != EXPECTED_USER:
        raise TikTokError(f"wrong TikTok account logged in: {user!r} (expected {EXPECTED_USER})")
    # leftover draft from an earlier run -> discard it (TikTok asks twice)
    _discard(p)

    p.set_files("input[type=file]", [video])
    if not p.wait_for("[...document.querySelectorAll('button')].some(b=>b.innerText.trim()==='Veröffentlichen')", 120):
        raise TikTokError("upload form did not appear")
    # wait until the upload itself is finished: no 'verbleibend' (time left)
    # for 3 polls in a row - TikTok only fills in its default description then
    calm, end = 0, time.time() + 600
    while calm < 3 and time.time() < end:
        busy = p.js("document.body.innerText.includes('verbleibend') || "
                    "/\\d+(\\.\\d+)?%/.test((document.querySelector('[class*=progress],[class*=Progress]')"
                    "?.closest('div')?.innerText) || '')")
        calm = 0 if busy else calm + 1
        time.sleep(2)
    if calm < 3:
        raise TikTokError("video upload did not finish within 10 minutes")
    time.sleep(3)
    _dismiss_popups(p)

    # caption: replace TikTok's default (the file name) with ours
    for attempt in range(3):
        p.js("document.querySelector('.public-DraftEditor-content').focus()")
        p.call("Input.dispatchKeyEvent", type="rawKeyDown", key="a", code="KeyA",
               windowsVirtualKeyCode=65, modifiers=4, commands=["selectAll"])
        p.call("Input.dispatchKeyEvent", type="keyUp", key="a", code="KeyA",
               windowsVirtualKeyCode=65, modifiers=4)
        p.key("Backspace", "Backspace", 8)
        time.sleep(0.5)
        left = (p.js("document.querySelector('.public-DraftEditor-content').innerText") or "").strip()
        for _ in range(len(left) + 5 if left else 0):   # fallback: delete char by char
            p.key("Backspace", "Backspace", 8)
            p.key("Delete", "Delete", 46)
        time.sleep(0.5)
        p.insert_text(caption)
        time.sleep(1.5)
        p.key("Escape", "Escape", 27)           # close hashtag suggestions
        got = (p.js("document.querySelector('.public-DraftEditor-content').innerText") or "").strip()
        if " ".join(got.split()) == " ".join(caption.split()):
            break
        time.sleep(2)
    else:
        raise TikTokError(f"caption not set correctly: {got[-80:]!r}")

    # AI label (under 'Mehr anzeigen')
    p.js(CLICK_TEXT.replace("button,[role=button]", "button,[role=button],div,span") % ("Mehr anzeigen", ""))
    time.sleep(1.5)
    state = p.js(SWITCH % "KI-generierter Inhalt")
    time.sleep(1.5)
    p.js(CLICK_TEXT % ("Aktivieren", "KI-generierten"))   # TikTok asks to confirm
    time.sleep(1.5)
    if state == "missing":
        raise TikTokError("AI-content switch not found")
    if p.js(SWITCH % "KI-generierter Inhalt") != "on":
        raise TikTokError("AI-content label could not be switched on")
    _dismiss_popups(p)
    SHOT.parent.mkdir(exist_ok=True)
    p.screenshot(str(SHOT))

    # NOT 'post now': videos posted instantly from the automated browser got ~0 views (18.11.2026),
    # scheduled ones ~700. So schedule 25-50 min ahead via TikTok's own scheduler.
    import datetime as dt, random
    t = dt.datetime.now() + dt.timedelta(minutes=random.randint(25, 50))
    t = t.replace(second=0, microsecond=0) + dt.timedelta(minutes=(-t.minute) % 5)
    datum, zeit = t.strftime("%Y-%m-%d"), t.strftime("%H:%M")
    if not p.js(CLICK_TEXT.replace("button,[role=button]", "label,span,div") % ("Zeitplan", "")):
        raise TikTokError("schedule option not found")
    time.sleep(2.5)
    if p.js("document.body.innerText.includes('für eine geplante Veröffentlichung gespeichert')"):
        raise TikTokError("TikTok asks once for permission to store scheduled videos - click 'Erlauben' in Studio by hand")
    FIELD = """((re) => { const i=[...document.querySelectorAll('input[type=text]')].find(x=>new RegExp(re).test(x.value));
      if(!i) return null; i.scrollIntoView({block:'center'}); const q=i.getBoundingClientRect(); return [q.x+q.width/2,q.y+q.height/2]; })(%r)"""
    OPT = """((sel, txt) => { const e=[...document.querySelectorAll(sel)].find(x=>x.innerText.trim()===txt);
      if(!e) return false; e.scrollIntoView({block:'center'}); e.click(); return true; })(%r, %r)"""
    xy = p.js(FIELD % r"^\d{4}-\d{2}-\d{2}$")
    if not xy: raise TikTokError("date field missing")
    p.click_xy(*xy); time.sleep(0.8)
    if not p.js(OPT % (".calendar-wrapper span, .calendar-wrapper div", str(t.day))):
        raise TikTokError("calendar day not clickable")
    time.sleep(0.8)
    xy = p.js(FIELD % r"^\d{2}:\d{2}$")
    if not xy: raise TikTokError("time field missing")
    p.click_xy(*xy); time.sleep(0.8)
    p.js(OPT % (".tiktok-timepicker-option-text.tiktok-timepicker-left", f"{t.hour:02d}")); time.sleep(0.6)
    p.js(OPT % (".tiktok-timepicker-option-text.tiktok-timepicker-right", f"{t.minute:02d}")); time.sleep(0.6)
    p.click_xy(1000, 60); time.sleep(0.6)
    werte = p.js("[...document.querySelectorAll('input[type=text]')].map(i=>i.value)") or []
    if datum not in werte or zeit not in werte:
        raise TikTokError(f"schedule not set: {werte} instead of {datum} {zeit}")
    p.screenshot(str(SHOT))
    if dry_run:
        _discard(p)
        print(f"dry run ok - would schedule {datum} {zeit}")
        return True
    for versuch in range(9):   # content check still running -> dialog: cancel, wait, schedule again (never 'post now')
        if not p.js(CLICK_TEXT % ("Planen", "")):
            raise TikTokError("schedule button not clickable")
        time.sleep(4)
        if not p.js("!![...document.querySelectorAll('[role=dialog],.TUXModal')].find(d=>d.offsetParent!==null)"):
            break
        p.js(CLICK_TEXT % ("Abbrechen", ""))
        time.sleep(30)
    else:
        raise TikTokError("content check did not finish")
    ok = p.wait_for("location.href.includes('/tiktokstudio/content')", 120, 2)
    p.screenshot(str(SHOT))
    if not ok:
        raise TikTokError("no confirmation after publishing (see logs/tiktok_last.jpg)")
    print(f"scheduled on TikTok for {datum} {zeit}")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("caption")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    post(a.video, a.caption, a.dry_run)
