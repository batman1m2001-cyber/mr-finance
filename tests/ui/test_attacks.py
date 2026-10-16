"""BRD-NFR-07 in the browser (BRD_REMAINING_PLAN G3): text a client typed is shown as text. A declared asset named
with markup and an inline handler appears on Tài sản as the characters typed; the handler never runs, no element is
made from it, and the page's Content-Security-Policy reports no violation (the policy itself: tests/test_security.py).
"""

from wealth import store

EVIL = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>Nhà <b>xấu</b>'


def test_a_stored_script_is_shown_as_text_and_never_runs(open_page):
    store.add_profile("C01", "asset", {"class": "business", "name": EVIL, "value": 1_000_000_000, "via": "chat"})
    p = open_page()
    violations = []
    p.page.on("console", lambda m: "Content Security Policy" in m.text and violations.append(m.text))
    p.go("#/client/tai-san")
    p.page.get_by_text('<img src=x onerror="window.__xss=1">', exact=False).first.wait_for()
    assert p.page.evaluate("window.__xss") is None
    assert p.page.locator("#page img[src='x'], #page b:text('xấu')").count() == 0
    assert not violations, violations
    assert not p.problems(), p.problems()
