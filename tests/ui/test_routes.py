"""Every menu route of every role renders in the browser — no page error, no error panel, no horizontal scroll,
the Copilot button present — on a desktop and a phone, light and dark (R7), with one approved event so the
news-impact pages have content."""

import pytest
from conftest import in_thread
from test_apply import MARKET, approved

ROLES = ("client", "rm", "cio", "admin")


def routes(p):
    """Every nav and sub-nav link, read from the shell itself (so a new page is covered without editing this)."""
    out = []
    for role in ROLES:
        p.go(f"#/{role}")
        for nav in p.page.eval_on_selector_all("#nav a", "as => as.map(a => a.getAttribute('href'))"):
            p.go(nav)
            subs = p.page.eval_on_selector_all("#subnav:not([hidden]) a", "as => as.map(a => a.getAttribute('href'))")
            out += subs or [nav]
    return out


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_every_route_renders_without_errors(open_page, size, theme):
    in_thread(approved, *MARKET)
    p = open_page(size, theme=theme)
    assert p.page.evaluate("document.documentElement.dataset.theme") == theme
    seen = routes(p)
    assert len(seen) >= 36, seen  # 33 before R4; + Bản đồ tài chính (client, RM) and the CIO run graph
    bad = {}
    for r in seen:
        p.errors.clear()
        p.go(r)
        if not (p.page.is_visible("#cp-q") or p.page.is_visible("#ws-fab")):  # docked, or its button (the client, B3.2)
            p.errors.append("no assistant")
        if p.problems():
            bad[r] = p.problems()
    assert not bad, bad
