"""Tiny Chrome DevTools Protocol client for the separate Muslim World Chrome.

Playwright's connect_over_cdp fails on Chrome 157 ("Browser context management
is not supported"), so the bot talks raw CDP over the page websocket.
The browser itself is started by scripts/open_tiktok_browser.sh on port 9341.
"""
import itertools
import json
import subprocess
import time
import urllib.request
from pathlib import Path

import websocket

PORT = 9341
BASE = f"http://127.0.0.1:{PORT}"
LAUNCHER = Path(__file__).resolve().parent / "open_tiktok_browser.sh"


def ensure_browser() -> None:
    subprocess.run([str(LAUNCHER)], check=True, timeout=40)


def _get(path: str, method: str = "GET"):
    req = urllib.request.Request(BASE + path, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


class Page:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=True)
        self._ids = itertools.count(1)

    @classmethod
    def open(cls, url: str, match: str | None = None) -> "Page":
        """Reuse a tab whose URL contains `match`, else open a new one."""
        ensure_browser()
        old = [t for t in _get("/json/list") if t["type"] == "page" and match and match in t["url"]]
        tab = _get(f"/json/new?{url}", method="PUT")   # always a fresh tab
        for t in old:                                   # stale tabs may hang in dialogs
            try:
                _get(f"/json/close/{t['id']}")
            except Exception:
                pass
        p = cls(tab["webSocketDebuggerUrl"])
        p.call("Page.enable")
        p.call("DOM.enable")
        p.call("Runtime.enable")
        return p

    def call(self, method: str, **params):
        i = next(self._ids)
        self.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("method") == "Page.javascriptDialogOpening":
                # 'Leave site?' / alerts would block navigation forever
                self.ws.send(json.dumps({"id": next(self._ids), "method": "Page.handleJavaScriptDialog",
                                         "params": {"accept": True}}))
                continue
            if msg.get("id") == i:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def js(self, expr: str):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError(f"JS error: {r['exceptionDetails'].get('text')} in {expr[:80]}")
        return r["result"].get("value")

    def goto(self, url: str, wait: float = 6.0) -> None:
        self.js("window.onbeforeunload = null")
        try:
            self.call("Page.handleJavaScriptDialog", accept=True)  # one may already be open
        except RuntimeError:
            pass
        self.call("Page.navigate", url=url)
        time.sleep(wait)

    def wait_for(self, expr: str, timeout: float = 60, every: float = 1.0):
        end = time.time() + timeout
        while time.time() < end:
            v = self.js(expr)
            if v:
                return v
            time.sleep(every)
        return None

    def set_files(self, selector: str, files: list[str]) -> None:
        root = self.call("DOM.getDocument", depth=-1, pierce=True)["root"]["nodeId"]
        node = self.call("DOM.querySelector", nodeId=root, selector=selector)["nodeId"]
        if not node:
            raise RuntimeError(f"no element for {selector}")
        self.call("DOM.setFileInputFiles", nodeId=node, files=files)

    def click_xy(self, x: float, y: float) -> None:
        for t in ("mousePressed", "mouseReleased"):
            self.call("Input.dispatchMouseEvent", type=t, x=x, y=y, button="left", clickCount=1)

    def insert_text(self, text: str) -> None:
        self.call("Input.insertText", text=text)

    def key(self, key: str, code: str, vk: int, modifiers: int = 0) -> None:
        for t in ("rawKeyDown", "keyUp"):
            self.call("Input.dispatchKeyEvent", type=t, key=key, code=code,
                      windowsVirtualKeyCode=vk, modifiers=modifiers)

    def screenshot(self, path: str) -> None:
        import base64
        data = self.call("Page.captureScreenshot", format="jpeg", quality=60)["data"]
        Path(path).write_bytes(base64.b64decode(data))

    def account(self) -> str | None:
        return self.js("fetch('/passport/web/account/info/',{credentials:'include'})"
                       ".then(r=>r.json()).then(j=>j.data&&j.data.username).catch(()=>null)")
