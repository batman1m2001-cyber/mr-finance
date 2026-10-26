"""Pages switch at once: a page seen before is drawn from what it read, before the server answers again, and once
more when the answer changed; a change made in the tab forgets what was kept. The Cá nhân / Gia đình switch shows
only where the family has someone else, and says whose assets each view counts. The app opens dark."""

from conftest import api

CONTROL = {"share": 0.2, "seed": "speed", "strata": ["segment"]}


def held(page, pattern):
    """Requests to ``pattern`` kept waiting until the test lets them go."""
    out = []
    page.route(pattern, lambda route: out.append(route))
    return out


def test_a_page_seen_before_draws_at_once_and_then_shows_the_new_answer(open_page, base_url):
    p = open_page()
    p.go("#/cio/cau-hinh")
    rows = p.page.locator("#page tr").count()
    p.go("#/cio/nhan-dinh")
    proposal = {"kind": "control_group", "data": CONTROL, "by": "cio"}
    api(base_url, "/api/config/propose", proposal, who="cio")
    waiting = held(p.page, "**/api/config")
    p.page.evaluate("location.hash = '#/cio/cau-hinh'")
    p.page.wait_for_function("(n) => document.querySelectorAll('#page tr').length === n", arg=rows)
    assert waiting and p.page.locator("#page .skeleton").count() == 0  # drawn while the server has not answered
    for route in waiting:
        route.continue_()
    p.page.unroute("**/api/config")
    p.page.wait_for_function("(n) => document.querySelectorAll('#page tr').length === n + 1", arg=rows)
    assert not p.problems()


def test_a_change_made_in_the_tab_forgets_what_was_kept(open_page):
    p = open_page()
    p.go("#/cio/cau-hinh")
    p.go("#/cio/nhan-dinh")
    # any write, even a refused one: what was kept is no longer sure
    write = "m => m.post('/api/news/dismiss', {news_ids: [], by: 'cio'})"
    p.page.evaluate(f"() => import('/core/core.js').then({write}).catch(() => {{}})")
    waiting = held(p.page, "**/api/config")
    p.page.evaluate("location.hash = '#/cio/cau-hinh'")
    p.page.wait_for_timeout(300)
    assert waiting and p.page.locator("#page .skeleton").count() > 0  # waits for the server, draws nothing old
    for route in waiting:
        route.continue_()
    p.page.unroute("**/api/config")
    p.page.wait_for_function("!document.querySelector('#page .skeleton') && document.querySelector('#page tr')")


def test_the_scope_switch_says_whose_assets_and_hides_for_one_person(open_page):
    p = open_page()
    p.go("#/client/tong-quan")
    assert p.page.is_visible("#scope-wrap")  # C01: his wife consented
    p.page.click("#scope-help")
    tip = p.page.inner_text("#scope-tip")
    assert "Nguyễn Minh Khoa" in tip and "Trần Thu Hà" in tip and "đã đồng ý" in tip
    p.page.keyboard.press("Escape")
    assert p.page.is_hidden("#scope-tip")
    p.go("#/rm/khach-hang")
    p.page.select_option("#client", "C05")  # one person: nothing to add
    p.page.wait_for_function("document.querySelector('#scope-wrap').hidden")
    assert not p.problems()


def test_the_app_opens_light_unless_dark_was_chosen(browser, base_url):
    ctx = browser.new_context(color_scheme="dark")  # whatever the system's scheme (2026-10-21: light for everyone)
    page = ctx.new_page()
    page.goto(base_url + "/")
    assert page.evaluate("document.documentElement.dataset.theme") == "light"
    page.evaluate("localStorage.setItem('mf.theme', 'dark')")
    page.reload()
    assert page.evaluate("document.documentElement.dataset.theme") == "dark"
    ctx.close()
