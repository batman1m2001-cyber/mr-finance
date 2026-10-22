"""The client's classic app in the browser (BUSINESS_FEEDBACK_1021_PLAN B3, WEALTH_NAMES_PLAN): Wealth view is the
home page, the bar's four sections lead to each section's page with its tabs, a page has no way "back to the graph"
(the graph is hidden from the client, ADR-0037), every old address still opens its page; the assistant is closed
until its button opens it, kept per person, over the page on a phone; the client's look is light by default and
larger. The staff's desks are untouched (test_role_desks_ui)."""

HOMES = {  # the bank's four sections (business feedback 2, ADR-0037)
    "tong-quan": "#/client/tong-quan",
    "muc-tieu": "#/client/muc-tieu/ke-hoach",
    "tin": "#/client/tin/thi-truong",
    "chuyen-gia": "#/client/chuyen-gia",
}
SHEET_TABS = {
    "muc-tieu": [["Wealth planning advisor", True], ["Risk profile test", False]],
    "tin": [["Tác động tin", True], ["Đồ thị tác động", False], ["Chi phí chính sách", False]],
    "chuyen-gia": [],
}
TABS = "(sel) => [...document.querySelectorAll(sel + ' a')].map(a => [a.textContent, a.hasAttribute('aria-current')])"


def test_the_home_the_bar_and_the_tabs(open_page):
    p = open_page()
    p.go("#/client")
    # the home: Wealth view, the Bảng số liệu as a page (the overview first, then cash flow), not the graph
    p.page.wait_for_selector("#ws-cashview #d-cash")
    assert p.page.eval_on_selector("#ws-cashview .cols > .panel", "p => p.id") == "d-nw"  # business feedback 2026-10-22
    assert p.page.is_hidden("#ws-canvas") and p.page.is_hidden("#ws-sheet") and p.page.is_hidden(".ws-ctl")
    assert p.page.is_hidden(".ws-strip")  # its cards are in the dashboard
    assert p.page.evaluate(TABS, "#ws-pages") == [["Wealth view", True], ["Dữ liệu chi tiết tài sản", False]]
    assert p.page.eval_on_selector_all(".ws-tool", "ts => ts.map(t => [t.dataset.tool, t.getAttribute('href')])") == [list(x) for x in HOMES.items()]
    # Wealth View's second tab: Tài sản's page, Wealth View still lit; back by its first tab
    p.page.click("#ws-pages a:has-text('Dữ liệu chi tiết tài sản')")
    p.page.wait_for_function("location.hash === '#/client/tai-san' && !document.querySelector('#page .skeleton')")
    assert p.page.is_visible("#ws-sheet") and p.page.is_visible('[data-tool="tong-quan"][aria-current]')
    assert p.page.evaluate(TABS, "#ws-sheet-tabs") == [["Wealth view", False], ["Dữ liệu chi tiết tài sản", True]]
    p.page.click("#ws-sheet-tabs a:has-text('Wealth view')")
    p.page.wait_for_function("!document.querySelector('#ws-cashview').hidden")
    assert p.page.is_hidden("#ws-canvas") and p.page.is_hidden("#ws-sheet")
    # each section from the bar: its page, the bar's place lit, its tabs when it has more than one page
    for tool, home in HOMES.items():
        if tool == "tong-quan":
            continue
        p.page.click(f'.ws-tool[data-tool="{tool}"]')
        p.page.wait_for_function("(h) => location.hash === h", arg=home)
        p.page.wait_for_function("!document.querySelector('#page .skeleton')")
        assert p.page.is_visible("#ws-sheet") and p.page.get_attribute(f'[data-tool="{tool}"]', "aria-current") is not None, tool
        assert p.page.locator("#ws-sheet-back, #ws-sheet-x").count() == 0, tool  # a page, not a sheet over the graph
        tabs = p.page.evaluate(TABS, "#ws-sheet-tabs")
        assert tabs == SHEET_TABS[tool], (tool, tabs)
        if not tabs:
            assert p.page.is_hidden(".ws-sheet-h"), tool
    p.go("#/client/tin/thi-truong")
    p.page.click("#ws-sheet-tabs a:has-text('Chi phí chính sách')")
    p.page.wait_for_function("location.hash === '#/client/tin/chinh-sach'")
    assert p.page.evaluate(TABS, "#ws-sheet-tabs")[2] == ["Chi phí chính sách", True]
    p.page.keyboard.press("Escape")  # a page stays
    p.page.wait_for_timeout(200)
    assert p.page.is_visible("#ws-sheet") and p.page.evaluate("location.hash") == "#/client/tin/chinh-sach"
    assert not p.problems()


def test_old_addresses_open_what_they_did(open_page):
    p = open_page()
    p.go("#/client/tong-quan/ban-do")  # the former Đồ thị tài chính tab: Wealth view, not the graph (ADR-0037)
    p.page.wait_for_selector("#ws-cashview #d-nw")
    assert p.page.is_hidden("#ws-canvas")
    p.go("#/client/tong-quan/chi-tiet")  # Chi tiết: the Bảng số liệu, at net worth
    assert p.page.is_visible("#ws-cashview #d-nw") and p.page.is_hidden("#ws-sheet")
    p.go("#/client/xem/tong-quan")  # the graph's own address, linked from nowhere, still opens it
    p.page.wait_for_selector(".wnode.k-family")
    p.go("#/client/muc-tieu/khau-vi")  # Khẩu vị rủi ro: Risk profile test, under Wealth Planning Advisor
    p.page.wait_for_function("!document.querySelector('#page .skeleton')")
    assert p.page.get_attribute('[data-tool="muc-tieu"]', "aria-current") is not None
    assert p.page.evaluate(TABS, "#ws-sheet-tabs") == [["Wealth planning advisor", False], ["Risk profile test", True]]
    assert not p.problems()


def test_dong_tien_is_the_cash_flow_part_of_the_dashboard(open_page):
    p = open_page()
    p.go("#/client/dong-tien")  # its menu item is gone: Wealth view, at its cash flow
    p.page.wait_for_selector("#ws-cashview #d-month .sankey")
    assert p.page.is_hidden("#ws-sheet") and p.page.get_attribute('[data-tool="tong-quan"]', "aria-current") is not None
    at = "() => { const t = document.querySelector('#d-cash').getBoundingClientRect().top - document.querySelector('#ws-cashview').getBoundingClientRect().top; return t > -2 && t < 120; }"  # noqa: E501
    p.page.wait_for_function(at)  # scrolled to it
    assert not p.problems()


def test_the_assistant_is_closed_until_asked_and_kept(open_page):
    p = open_page(dock=False)
    p.go("#/client/tai-san")
    assert p.page.is_hidden("#ws-dock") and p.page.is_visible("#ws-fab")
    width = p.page.evaluate("document.querySelector('#ws-sheet').getBoundingClientRect().width")
    p.page.click("#ws-fab")
    p.page.wait_for_function("document.activeElement && document.activeElement.id === 'cp-q'")
    assert p.page.is_visible("#ws-dock") and p.page.is_hidden("#ws-fab")
    assert p.page.evaluate("document.querySelector('#ws-sheet').getBoundingClientRect().width") < width - 300  # beside the page
    p.page.reload()
    p.page.wait_for_selector("#cp-q")
    assert p.page.is_visible("#ws-dock")  # kept
    p.page.click("#ws-close")
    assert p.page.is_hidden("#ws-dock") and p.page.is_visible("#ws-fab")
    p.go("#/client/xem/tai-san")  # a node picked opens it at Thông tin
    p.page.click('.wnode[data-n="CL:stock"] .wcore')
    p.page.wait_for_selector("#ws-pane-i:not([hidden])")
    assert p.page.is_visible("#ws-dock")
    phone = open_page("phone", dock=False)
    phone.go("#/client/tai-san")
    assert phone.page.is_hidden("#ws-dock")
    phone.page.click("#ws-fab")
    box = phone.page.evaluate("(() => { const r = document.querySelector('#ws-dock').getBoundingClientRect(); return [r.top, r.height, innerHeight]; })()")
    assert box[0] == 0 and box[1] == box[2], box  # over the page, the whole screen
    phone.page.keyboard.press("Escape")
    assert phone.page.is_hidden("#ws-dock")
    assert not p.problems() and not phone.problems()


def test_the_client_looks_calmer_everyone_opens_light(open_page):
    p = open_page(theme=None)
    p.go("#/client/tai-san")
    look = p.page.evaluate("""() => ({theme: document.documentElement.dataset.theme,
      body: getComputedStyle(document.body).fontSize, table: getComputedStyle(document.querySelector('#page .table')).fontSize,
      glow: getComputedStyle(document.body).backgroundImage})""")
    assert look == {"theme": "light", "body": "16px", "table": "15px", "glow": "none"}, look
    p.go("#/cio")
    look = p.page.evaluate("[document.documentElement.dataset.theme, getComputedStyle(document.body).fontSize]")
    assert look == ["light", "14px"], look  # light for the staff too (2026-10-21); their type as it was
    assert not p.problems()
