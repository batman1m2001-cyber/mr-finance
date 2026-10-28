"""The client's menu by the bank's names in the browser (business feedback 2, WEALTH_NAMES_PLAN, ADR-0037,
OWN-WN-01…08): four sections with the tabs the business asked for, each page's heading its section, the Wealth
Check coloured, every old address on its page — and nothing on screen leading to the graph."""

SECTIONS = [  # rail item, its home, its tabs (label, current at the home)
    ("tong-quan", "Wealth View", "#/client/tong-quan", [["Wealth view", True], ["Dữ liệu chi tiết tài sản", False]]),
    ("muc-tieu", "Wealth Planning Advisor", "#/client/muc-tieu/ke-hoach",
     [["Wealth planning advisor", True], ["Asset allocation", False], ["Risk profile test", False]]),
    ("tin", "Headline News", "#/client/tin/chinh-sach", [["News and Prediction", True], ["Đồ thị tác động", False]]),
    ("chuyen-gia", "Relationship specialist", "#/client/chuyen-gia", []),
]  # fmt: skip
TABS = """(sel) => [...document.querySelectorAll(sel + ' a')].filter(a => a.offsetParent)
  .map(a => [a.textContent, a.getAttribute('aria-current') === 'page'])"""
LIT = "() => [...document.querySelectorAll('.ws-tool[aria-current]')].map(t => t.dataset.tool)"
HEAD = "() => { const h = document.querySelector('#page .pagehead'); return h && [(h.querySelector('.eyebrow') || {}).textContent || '', h.querySelector('.h1').textContent]; }"  # noqa: E501


def test_the_four_sections_their_tabs_and_headings(open_page):
    p = open_page()
    p.go("#/client")
    p.page.wait_for_selector("#ws-cashview #d-nw")
    rail = p.page.eval_on_selector_all(
        ".ws-tool", "ts => ts.map(t => [t.dataset.tool, t.textContent.trim(), t.getAttribute('href')])"
    )
    assert rail == [[t, label, home] for t, label, home, _ in SECTIONS]
    assert p.page.text_content("#ws-title") == "Wealth View" and p.page.evaluate(TABS, "#ws-pages") == SECTIONS[0][3]
    for tool, label, home, tabs in SECTIONS[1:]:
        p.page.click(f'.ws-tool[data-tool="{tool}"]')
        p.page.wait_for_function("(h) => location.hash === h", arg=home)
        p.page.wait_for_function("!document.querySelector('#page .skeleton')")
        assert p.page.evaluate(LIT) == [tool], tool
        assert p.page.evaluate(TABS, "#ws-sheet-tabs") == tabs, tool
    # the second tab of each two-tab section: its own page, the section still lit, the heading its section and name
    for route, tool, head in [
        ("#/client/tai-san", "tong-quan", ["Wealth View", "Dữ liệu chi tiết tài sản"]),
        ("#/client/rui-ro/khau-vi", "muc-tieu", ["Wealth Planning Advisor", "Risk profile test"]),
        ("#/client/muc-tieu/ke-hoach", "muc-tieu", ["Wealth Planning Advisor", "Kế hoạch tài chính"]),
        ("#/client/tin/chinh-sach", "tin", ["Headline News", "News and Prediction"]),
        ("#/client/chuyen-gia", "chuyen-gia", ["", "Relationship specialist"]),
    ]:
        p.go(route)
        p.page.wait_for_function(
            "!document.querySelector('#page .skeleton') && !!document.querySelector('#page .pagehead')"
        )
        assert p.page.evaluate(LIT) == [tool] and p.page.evaluate(HEAD) == head, route
    # the names in the rail break between words, never inside one (a wider rail for the client)
    cut = p.page.eval_on_selector_all(
        ".ws-tool-l", "ls => ls.filter(l => l.scrollHeight > l.clientHeight + 1).map(l => l.textContent)"
    )
    assert cut == []
    assert not p.problems()


def test_every_old_address_opens_its_page_and_none_the_graph(open_page):
    p = open_page()
    for route, tool, at in [
        ("#/client/tong-quan/toan-canh", "tong-quan", "#d-month"),
        ("#/client/tong-quan/chi-tiet", "tong-quan", "#d-nw"),
        ("#/client/tong-quan/ban-do", "tong-quan", "#d-nw"),  # the former Đồ thị tài chính tab
        ("#/client/dong-tien", "tong-quan", "#d-cash"),  # Dòng tiền: on Wealth view
        ("#/client/khong-co-trang-nay", "tong-quan", "#d-nw"),
        ("#/client/rui-ro", "muc-tieu", "#page"),
        ("#/client/muc-tieu/khau-vi", "muc-tieu", "#page"),
        ("#/client/tin", "tin", "#page"),
    ]:
        p.go(route)
        p.page.wait_for_function("(t) => document.querySelector(`.ws-tool[data-tool='${t}'][aria-current]`)", arg=tool)
        p.page.wait_for_selector(f"{at}:visible" if at != "#page" else "#ws-sheet:not([hidden]) #page")
        assert p.page.is_hidden("#ws-canvas"), route
    # nothing on screen names the graph: no tab, no search hit
    p.go("#/client")
    p.page.wait_for_selector("#ws-cashview #d-nw")
    tabs = p.page.eval_on_selector_all("#ws-pages a, #ws-sheet-tabs a", "as => as.map(a => a.getAttribute('href'))")
    assert not [h for h in tabs if "/xem/" in h or h.endswith("/ban-do")]
    links = p.page.eval_on_selector_all("a[href^='#/client/xem/']", "as => as.filter(a => a.offsetParent).length")
    assert links == 0
    assert not p.problems()


def test_the_wealth_check_line_is_coloured(open_page):
    """Business item 6 ("đổ màu như này"): ahead of VN-Index green, behind red — the line had been grey because
    `.kpi .s` outranked `.up` / `.down` (on every page)."""
    p = open_page()
    p.go("#/client/tin/chinh-sach")
    line = p.page.wait_for_selector("[data-focus='policy:check'] .kpi .s.up, [data-focus='policy:check'] .kpi .s.down")
    cls = line.get_attribute("class")
    colour = line.evaluate("el => getComputedStyle(el).color")
    want = p.page.evaluate(
        "(c) => { const s = document.createElement('span'); s.className = c; document.body.append(s);"
        " const v = getComputedStyle(s).color; s.remove(); return v; }",
        "up" if " up" in f" {cls}" else "down",
    )
    grey = p.page.evaluate(
        "() => { const s = document.createElement('span'); s.style.color = 'var(--ink-2)'; document.body.append(s); const v = getComputedStyle(s).color; s.remove(); return v; }"  # noqa: E501
    )
    assert colour == want and colour != grey
    assert not p.problems()


RGB = "(el) => getComputedStyle(el).backgroundColor"
LUM = """([a, b]) => { const l = c => { const v = c.match(/\\d+/g).slice(0, 3).map(x => { x /= 255;
  return x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; });
  return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; };
  const [h, o] = [l(a), l(b)].sort((x, y) => y - x); return (h + .05) / (o + .05); }"""


def test_gold_marks_the_main_action_only(open_page):
    """Business feedback 5 (2026-10-23, the Private palette: gold, champagne, sand, brown). Gold is the main action
    (a primary button, Hỏi trợ lý, the bell's count) with dark words at 4.5:1; tabs and links stay brown or light."""
    gold = "rgb(200, 164, 93)"
    for theme in ("light", "dark"):
        p = open_page(theme=theme, dock=False)
        p.go("#/client/tai-san")
        btn = p.page.wait_for_selector("#page .btn.primary")
        fab = p.page.wait_for_selector("#ws-fab")
        assert btn.evaluate(RGB) == gold and fab.evaluate(RGB) == gold, theme
        words = btn.evaluate("el => getComputedStyle(el).color")
        assert p.page.evaluate(LUM, [words, gold]) >= 4.5, theme
        tab = p.page.wait_for_selector("#ws-sheet-tabs a[aria-current='page']")
        assert gold not in (tab.evaluate(RGB), tab.evaluate("el => getComputedStyle(el).color")), theme
        assert not p.problems()
