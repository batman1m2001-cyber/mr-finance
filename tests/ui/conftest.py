"""Browser tests (UI redesign plan R0): the real app served by uvicorn in this process on a free port, driven by
Playwright's Chromium. Each test still gets its own empty state (the autouse fixture in ../conftest.py), which
the server reads, so a test can seed records in-process and see them in the browser.

Sign-in is on here, with the demo accounts listed (BRD-RULE-SEC-01): a page signs in as the account of the
route's role before it opens it (``Page.as_role``), the way a person would.

Skipped, with the reason, when Playwright or a Chromium is not available. MF_CHROMIUM points at a Chromium
binary; otherwise Playwright's own install is used."""

import json
import os
import re
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="pip install -e '.[ui]' for the browser tests")
uvicorn = pytest.importorskip("uvicorn")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the seeding helpers of tests/test_apply.py

SIZES = {"desktop": (1440, 900), "phone": (390, 844)}
_FUNCTION = re.compile(r"^\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|\w+\s*=>)")


def _wait_for_function(self, expression, arg=None, timeout=None, polling=None):
    """``Page.wait_for_function`` polled from here with ``evaluate``: the app's Content-Security-Policy has no
    ``unsafe-eval`` (BRD-NFR-07), and Playwright's in-page polling compiles the predicate with ``eval``, which the
    page then refuses. ``evaluate`` goes through DevTools, which the policy does not cover. The policy stays on, so
    these tests also see any violation by the app itself."""
    fn = expression if _FUNCTION.match(expression) else f"() => ({expression})"
    check = f"(a) => !!(({fn})(a))"
    deadline = time.monotonic() + (30_000 if timeout is None else timeout) / 1000
    while True:
        try:
            if self.evaluate(check, arg):
                return True
        except sync_api.Error as e:  # the page is navigating: not yet
            if "context was destroyed" not in str(e) and "navigat" not in str(e):
                raise
        if time.monotonic() > deadline:
            raise sync_api.TimeoutError(f"wait_for_function timed out: {expression}")
        self.wait_for_timeout(polling if isinstance(polling, (int, float)) else 50)


sync_api.Page.wait_for_function = _wait_for_function
ACCOUNTS = {
    "client": "C01",
    "rm": "rm01",
    "cio": "cio",
    "compliance": "compliance",
    "admin": "admin",
    "specialist": "sp_global",
}


@pytest.fixture(autouse=True)
def sign_in_on(monkeypatch):
    monkeypatch.setenv("MF_AUTH", "on")
    monkeypatch.setenv("MF_DEMO_ACCOUNTS", "on")


def pytest_collection_modifyitems(items):
    for item in items:  # `pytest -m "not ui"` skips the browser tests (about a minute)
        if "tests/ui/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.ui)


@pytest.fixture(scope="session")
def base_url():
    from operonx.app import Application

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    config = uvicorn.Config(Application.find(".").asgi(), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(300):
        if server.started:
            break
        time.sleep(0.05)
    else:
        pytest.fail("the app did not start")
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(5)


@pytest.fixture(scope="session")
def browser():
    with sync_api.sync_playwright() as p:
        exe = os.environ.get("MF_CHROMIUM") or next(
            (str(x) for x in sorted(Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux/chrome"))), None
        )
        try:
            b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        except Exception as exc:  # no browser on this machine
            pytest.skip(f"no Chromium: {exc}".splitlines()[0])
        yield b
        b.close()


def api(base, path, body=None, who="C01"):
    """A request to the app as ``who`` (a session issued in-process: the server shares this process's state)."""
    from people import auth

    data = None if body is None else json.dumps(body).encode()
    headers = {"content-type": "application/json", "cookie": f"{auth.COOKIE}={auth.issue(who)}"}
    return json.load(urllib.request.urlopen(urllib.request.Request(base + path, data=data, headers=headers)))


def in_thread(fn, *args):
    """Run a seeding helper beside Playwright's loop (its graphs call asyncio.run); returns its result."""
    out = {}

    def run():
        try:
            out["value"] = fn(*args)
        except BaseException as exc:  # re-raised in the test
            out["error"] = exc

    t = threading.Thread(target=run)
    t.start()
    t.join()
    if "error" in out:
        raise out["error"]
    return out["value"]


class Page:
    """A page that records errors and waits for the shell to say a route has rendered (`mf:page`)."""

    def __init__(self, browser, base_url, size="desktop", reduced=False, theme="light"):
        w, h = SIZES[size]
        self.ctx = browser.new_context(
            viewport={"width": w, "height": h}, reduced_motion="reduce" if reduced else None, color_scheme=theme
        )
        # the app opens dark unless the person chose light (mf.theme), whatever the system's scheme: say which
        self.ctx.add_init_script(f"try {{ localStorage.setItem('mf.theme', '{theme}'); }} catch (_) {{}}")
        self.page = self.ctx.new_page()
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e} @ {(e.stack or '').splitlines()[1:3]}"))
        self.page.on("console", lambda m: m.type == "error" and self.errors.append(f"console: {m.text}"))
        self.page.on("response", lambda r: r.status in (401, 403) and self.errors.append(f"{r.status} {r.url}"))
        self.base = base_url
        self.role = None
        self.as_role("client")

    def as_role(self, role, route=None):
        """Sign in as the demo account of ``role`` (the session cookie is the context's) and open its home."""
        r = self.ctx.request.post(f"{self.base}/api/auth/demo", data={"id": ACCOUNTS[role]})
        assert r.ok, r.text()
        self.role = role
        self.page.goto(f"{self.base}/?as={role}{route or '#/' + role}")  # the query makes it a new document
        self.page.wait_for_function("document.querySelector('#nav a') && document.querySelector('#client option')")

    def go(self, route):
        role = route.split("/")[1] if route.startswith("#/") else None
        if role in ACCOUNTS and role != self.role:
            self.as_role(role, route)
        ok = self.page.evaluate(
            """(r) => new Promise((done) => {
                 window.addEventListener('mf:page', () => done(true), {once: true});
                 setTimeout(() => done(false), 15000);
                 if (location.hash !== r) location.hash = r;
                 else window.dispatchEvent(new HashChangeEvent('hashchange'));
               })""",
            route,
        )
        if not ok:
            self.errors.append(f"{route}: did not finish rendering in 15 s")
        self.page.wait_for_function("!document.querySelector('#page:not([hidden]) .skeleton')")
        self.page.wait_for_timeout(150)

    def problems(self):
        """Errors so far, an error panel on the page, and horizontal scroll."""
        out = list(self.errors)
        bad = self.page.evaluate(
            """() => [...document.querySelectorAll('[role=alert]')]
                 .filter(e => e.offsetParent && /Không tải được/.test(e.textContent))
                 .map(e => e.textContent.trim().slice(0, 120))"""
        )
        out += [f"error panel: {t}" for t in bad]
        sw, iw = self.page.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        if sw > iw:
            out.append(f"horizontal scroll: {sw} > {iw}")
        return out

    def close(self):
        self.ctx.close()


@pytest.fixture
def open_page(browser, base_url):
    pages = []

    def make(size="desktop", reduced=False, theme="light"):
        pages.append(Page(browser, base_url, size, reduced, theme))
        return pages[-1]

    yield make
    for p in pages:
        p.close()
