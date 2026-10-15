"""Browser tests (UI redesign plan R0): the real app served by uvicorn in this process on a free port, driven by
Playwright's Chromium. Each test still gets its own empty state (the autouse fixture in ../conftest.py), which
the server reads, so a test can seed records in-process and see them in the browser.

Skipped, with the reason, when Playwright or a Chromium is not available. MF_CHROMIUM points at a Chromium
binary; otherwise Playwright's own install is used."""

import os
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="pip install -e '.[ui]' for the browser tests")
uvicorn = pytest.importorskip("uvicorn")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the seeding helpers of tests/test_apply.py

SIZES = {"desktop": (1440, 900), "phone": (390, 844)}


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
        self.page = self.ctx.new_page()
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e} @ {(e.stack or '').splitlines()[1:3]}"))
        self.page.on("console", lambda m: m.type == "error" and self.errors.append(f"console: {m.text}"))
        self.base = base_url
        self.page.goto(f"{base_url}/#/client")
        self.page.wait_for_function("document.querySelector('#nav a') && document.querySelector('#client option')")

    def go(self, route):
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
