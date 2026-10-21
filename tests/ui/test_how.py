"""BRD-NFR-11 in the browser (BRD_REMAINING_PLAN G1): every money or percent figure on every route of every role
opens its “cách tính”. A figure outside a ``data-metric`` fails, except a client's own quoted words or a headline
(``data-quote``), a chart axis tick (``data-axis``) and the text of an explanation itself (``data-explains``).
The client's Bảng số liệu (the workspace's dashboard, outside #page) is scanned as well whenever it is shown.
Besides each route as it opens, the states a click reveals: a group of Toàn cảnh, a flow band and a month, the map
as a list and with a node picked, a source tier, decisions and stress tests on Kế hoạch, the opportunities filter.
Every metric a page names is in the catalogue, and opening one shows its formula."""

from conftest import api, in_thread
from test_apply import MARKET, approved
from test_routes import routes

SCAN = r"""() => {
  const SKIP = '[data-metric],[data-axis],[data-explains],[data-quote],' +
    'input,textarea,select,option,script,style,[hidden]';
  const re = /[+−-]?\d[\d.,]*\s?(?:đ(?!\p{L})|triệu|tỷ|%|tr(?!\p{L}))/gu;
  const out = [];
  for (const root of document.querySelectorAll('#page, #ws-cashview')) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      const el = n.parentElement;
      if (!el || el.closest(SKIP)) continue;
      if (!el.offsetParent && el.tagName !== 'text' && el.tagName !== 'tspan') continue;
      const m = n.textContent.match(re);
      if (m) out.push(m.join(' | ') + '  ⟵  ' + n.textContent.trim().slice(0, 70));
    }
  }
  return out;
}"""
METRICS = "() => [...new Set([...document.querySelectorAll('#page [data-metric], #ws-cashview:not([hidden]) [data-metric]')].map(e => e.dataset.metric))]"
CLICK = (
    "(el) => el.dispatchEvent(new MouseEvent('click', {bubbles: true}))"  # on the element itself, not a figure in it
)

# route → the clicks (selector, how many of its matches) whose results are scanned too
STATES = {
    # the client's Toàn cảnh and Chi tiết addresses open the Bảng số liệu (UX_TOOLBAR_PLAN T3+T4)
    "/tong-quan/toan-canh": [("#d-month .sankey .band", 1), ("#d-month [data-cat]", 1)],
    "/tong-quan/ban-do": [('[data-v="list"]', 1), ("[data-n]", 2), ('[data-v="graph"]', 1), ("[data-n]", 1)],
    "/tong-quan/chi-tiet": [("#ws-cashview [data-tier]", 1)],
    "/khach-hang/toan-canh": [(".crow[data-g]", 1)],
    "/khach-hang/ban-do": [('[data-v="list"]', 1), ("[data-n]", 1)],
    "/muc-tieu/ke-hoach": [("[data-sim]", 99)],
    "/tin/chinh-sach": [('[data-af="opp"]', 1), ("#views-more", 1)],
}
# route → a link to a detail page, opened and scanned (an event's view, a run, a newsletter, a policy document)
DETAILS = {
    "/cio/nhan-dinh": "a.item",
    "/cio/ban-tin": "a.item",
    "/cio/chinh-sach": "a.item",
    "/compliance/chinh-sach": "a.item",
}


def scan(p, where, bad, seen):
    p.page.wait_for_function("!document.querySelector('#page:not([hidden]) .skeleton, #panel.loading')")
    p.page.wait_for_timeout(250)
    found = p.page.evaluate(SCAN)
    if found:
        bad[where] = found[:12]
    seen.update(p.page.evaluate(METRICS))


def states(p, route, bad, seen):
    for suffix, clicks in STATES.items():
        if not route.endswith(suffix):
            continue
        for sel, count in clicks:
            for i in range(min(count, p.page.locator(sel).count())):
                p.page.locator(sel).nth(i).evaluate(CLICK)
                scan(p, f"{route} · {sel}[{i}]", bad, seen)


def test_every_figure_on_every_route_has_its_formula(open_page, base_url):
    in_thread(approved, *MARKET)
    p = open_page()
    bad, seen = {}, set()
    for r in routes(p):
        p.go(r)
        scan(p, r, bad, seen)
        states(p, r, bad, seen)
        link = next((sel for suffix, sel in DETAILS.items() if r.endswith(suffix)), None)
        if link and p.page.locator(f"#page {link}").count():
            p.go(p.page.locator(f"#page {link}").first.get_attribute("href"))
            scan(p, p.page.evaluate("location.hash"), bad, seen)
    assert not bad, "\n" + "\n".join(f"{k}\n    " + "\n    ".join(v) for k, v in bad.items())
    known = api(base_url, "/api/how")
    assert len(seen) > 50, sorted(seen)
    assert not seen - set(known), seen - set(known)
    assert not p.problems(), p.problems()


def test_a_figure_opens_its_formula_by_click_and_by_keyboard(open_page):
    p = open_page("phone")
    p.go("#/client/tong-quan/toan-canh")  # the Bảng số liệu
    p.page.locator("#ws-cashview [data-metric]").first.click()
    drawer = p.page.locator(".drawer")
    drawer.locator("h4", has_text="Công thức").wait_for()
    assert "chưa có cách tính" not in drawer.inner_text()
    assert "Tính tại" not in drawer.inner_text()  # the code path is for staff
    drawer.locator("button[aria-label='Đóng']").click()
    p.go("#/rm/khach-hang/toan-canh")
    p.page.locator("#page [data-metric]").first.focus()
    p.page.keyboard.press("Enter")
    p.page.locator(".drawer h4", has_text="Công thức").wait_for()
    assert "Tính tại" in p.page.locator(".drawer").inner_text()
    assert not p.problems(), p.problems()
