"""The pages rebuilt in UI redesign R3, driven through their actions: a statement and a declaration change the book,
the risk test goes back and forth and sets the drawdown limit the dashboard uses, a goal's action sent from Kế
hoạch is approved by the RM and the client sees the note, the policy filter keeps one side, and a row of the
all-clients performance opens that client."""

from conftest import api, in_thread
from test_apply import MARKET, approved


def test_a_statement_and_a_declaration_reach_the_book(open_page):
    p = open_page()
    p.go("#/client/tai-san")
    rows = p.page.locator("#book tbody tr").count()
    p.page.click("[data-sample]")
    p.page.wait_for_function("/Đã đọc \\d+ khoản/.test(document.querySelector('#stmt-out')?.textContent)")
    assert p.page.locator("#book tbody tr").count() > rows  # the page drew again with the statement's holdings
    p.page.fill("#chat-in", "Nhà tôi có 10 lượng vàng")
    p.page.press("#chat-in", "Enter")
    p.page.wait_for_function("/ghi \\d+ mục/.test(document.querySelector('#chat-log')?.textContent)")
    p.page.wait_for_function("/lượng/.test(document.querySelector('#book')?.textContent)")
    p.go("#/client/tong-quan/chi-tiet")
    p.go("#/client/tai-san")  # kept for the tab: the last read and the chat are still there
    assert "Đã đọc" in p.page.inner_text("#stmt-out") and "10 lượng vàng" in p.page.inner_text("#chat-log")
    assert not p.problems()


def test_the_risk_test_goes_back_and_sets_the_limit(open_page, base_url):
    p = open_page()
    p.go("#/client/muc-tieu/khau-vi")
    p.page.click("#risk-start")
    p.page.wait_for_selector(".opt")
    first = p.page.inner_text(".qtext")
    p.page.locator(".opt").first.click()
    p.page.wait_for_function("/Câu 2/.test(document.querySelector('.qtop').textContent)")
    p.page.click("#risk-back")
    p.page.wait_for_function("/Câu 1/.test(document.querySelector('.qtop').textContent)")
    assert p.page.inner_text(".qtext") == first
    for _ in range(15):  # always the boldest answer
        if not p.page.locator(".opt").count():
            break
        n = p.page.text_content(".qtop")
        p.page.locator(".opt").last.click()
        moved = "(n) => !document.querySelector('.qtop') || document.querySelector('.qtop').textContent !== n"
        p.page.wait_for_function(moved, arg=n)
    p.page.wait_for_selector(".rhero")
    limit = api(base_url, "/api/dashboard", {"client_id": "C01", "scope": "personal"})["dashboard"]["risk"]["limit"]
    assert f"{round(limit * 100)}%" in p.page.inner_text(".rhero")  # the overview now measures against this limit
    assert p.page.locator(".rbands[role=meter]").count() == 2
    assert not p.problems()


def test_a_proposal_is_approved_by_the_rm_and_the_client_sees_it(open_page):
    p = open_page()
    p.go("#/client/muc-tieu/ke-hoach")
    p.page.locator("[data-act]").first.click()
    p.page.wait_for_selector("#panel .pill.ai")  # “Chờ RM duyệt” where the button was
    p.go("#/client/chuyen-gia")
    assert p.page.locator(".qitem").count() == 1 and "Chờ RM duyệt" in p.page.inner_text(".qitem")
    assert p.page.locator("[data-ok]").count() == 0  # the client only reads the queue
    p.go("#/rm/khach-hang/duyet")
    p.page.locator(".qitem input").fill("Đồng ý, gọi khách tuần sau")
    p.page.click("[data-ok]")
    # the RM's approval is the last (OWN-FB-18)
    p.page.wait_for_function("/Đã xử lý/.test(document.querySelector('#page').textContent)")
    p.go("#/client/chuyen-gia")
    item = p.page.inner_text(".qitem")
    assert "Đã duyệt" in item and "Đồng ý, gọi khách tuần sau" in item
    p.go("#/client/muc-tieu/ke-hoach")
    p.page.wait_for_selector("#panel .pill.good")  # and Kế hoạch says so beside the action
    assert not p.problems()


def _direction(a):
    """An item's direction as News and Prediction shows it: its evidence's, else its impact's sign."""
    e = (a.get("evidence") or {}).get("direction")
    if e == "unclear" or (not e and not a["impact"]):
        return "neutral"
    return ("positive" if e == "positive" else "negative") if e else ("positive" if a["opportunity"] else "negative")


def test_the_policy_filter_keeps_one_side(open_page, base_url):
    p = open_page()
    p.go("#/client/tin/chinh-sach")
    rep = api(base_url, "/api/alerts", {"client_id": "C01", "scope": "personal"})["report"]
    items = list({a["factor"]: a for a in reversed(rep["alerts"])}.values())  # one per news, its largest hit
    assert p.page.locator("#sections .acard").count() == len(items)
    assert p.page.locator("#impact .nrow").count() == len(items)
    p.page.click("[data-af=positive]")
    pos = [a for a in items if _direction(a) == "positive"]
    assert p.page.locator("#sections .acard").count() == len(pos)
    # each row ends in its direction only (business feedback 2026-10-29): no amount, no horizon, a positive one green
    assert p.page.locator("#impact .nrow .pill").count() == p.page.locator("#impact .nrow .pill.good").count() == len(pos) > 0
    assert all(" · " not in v for v in p.page.locator("#impact .nrow .pill").all_inner_texts())
    p.page.click("[data-af=negative]")
    assert p.page.locator("#impact .nrow .pill.good").count() == 0
    p.page.click("[data-hz='1w']")  # the horizon filter: only what lands within a week
    week = [a["id"] for a in items if _direction(a) == "negative" and a["horizon"] == "1w"]
    # by id: the titles show in the page's language
    shown = [r.get_attribute("data-a") for r in p.page.locator("#impact .nrow").all()]
    assert set(shown) == set(week)
    assert not p.problems()


def test_a_row_of_all_clients_opens_that_client(open_page):
    p = open_page()
    p.go("#/rm/hieu-qua/tat-ca")
    row = p.page.locator("tr.rowlink").nth(2)
    cid, name = row.get_attribute("data-client"), row.locator("b").inner_text()
    row.locator("b").click()  # the name: a figure in the row is its own “Cách tính” button, which does not navigate
    p.page.wait_for_function("location.hash === '#/rm/khach-hang/hieu-qua'")
    p.page.wait_for_function("(c) => document.querySelector('#client').value === c", arg=cid)
    p.page.wait_for_function("(n) => document.querySelector('.lede')?.textContent.includes(n)", arg=name)
    assert not p.problems()


def test_the_timeline_the_news_impact_card_and_the_cio_run_graph(open_page, base_url):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/client/tin/thi-truong")
    items = api(base_url, "/api/families/C01/impact?role=client")["items"]
    assert p.page.locator("#timeline .trow").count() == len(items)
    assert p.page.locator("#timeline .tstep").count() == sum(len(i["timeline"]) for i in items)
    p.go("#/client/tin/do-thi")
    p.page.locator('.gnode[data-focus^="event:"]').first.click()
    card = p.page.locator(".impactcard")
    assert "Chuỗi tác động" in card.inner_text() and card.locator(".mrow").count() > 0
    p.go("#/cio/do-thi")
    assert p.page.locator(".gnode").count() > 0 and "gia đình" in p.page.inner_text("#page h3")
    assert not p.problems()
