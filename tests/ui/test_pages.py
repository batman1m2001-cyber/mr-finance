"""The pages rebuilt in UI redesign R3, driven through their actions: a statement and a declaration change the book,
the risk test goes back and forth and sets the drawdown limit the dashboard uses, a goal's action sent from Kế
hoạch is approved by the RM and the client sees the note, the policy filter keeps one side, and a row of the
all-clients performance opens that client."""

import json
import urllib.request

from conftest import in_thread
from test_apply import MARKET, approved


def api(base, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(req))


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
    p.page.wait_for_selector("#panel .pill.ai")  # “Chờ chuyên gia duyệt” where the button was
    p.go("#/client/chuyen-gia")
    assert p.page.locator(".qitem").count() == 1 and "Chờ chuyên gia duyệt" in p.page.inner_text(".qitem")
    assert p.page.locator("[data-ok]").count() == 0  # the client only reads the queue
    p.go("#/rm/khach-hang/duyet")
    p.page.locator(".qitem input").fill("Đồng ý, gọi khách tuần sau")
    p.page.click("[data-ok]")
    p.page.wait_for_function("/Đã xử lý/.test(document.querySelector('#page').textContent)")
    p.go("#/client/chuyen-gia")
    item = p.page.inner_text(".qitem")
    assert "Đã duyệt" in item and "Đồng ý, gọi khách tuần sau" in item
    p.go("#/client/muc-tieu/ke-hoach")
    p.page.wait_for_selector("#panel .pill.good")  # and Kế hoạch says so beside the action
    assert not p.problems()


def test_the_policy_filter_keeps_one_side(open_page, base_url):
    p = open_page()
    p.go("#/client/tin/chinh-sach")
    rep = api(base_url, "/api/alerts", {"client_id": "C01", "scope": "personal"})["report"]
    assert p.page.locator("#sections .acard").count() == len(rep["alerts"])
    p.page.click("[data-af=opp]")
    opp = [a for a in rep["alerts"] if a["opportunity"]]
    assert p.page.locator("#sections .acard").count() == len(opp)
    assert p.page.locator("#impact .dbar").count() == min(10, len(opp))
    assert all(v.startswith("+") for v in p.page.locator("#impact .dv").all_inner_texts())
    p.page.click("[data-af=risk]")
    assert all(not v.startswith("+") for v in p.page.locator("#impact .dv").all_inner_texts())
    assert not p.problems()


def test_a_row_of_all_clients_opens_that_client(open_page):
    p = open_page()
    p.go("#/rm/hieu-qua")
    row = p.page.locator("tr.rowlink").nth(2)
    cid, name = row.get_attribute("data-client"), row.locator("b").inner_text()
    row.click()
    p.page.wait_for_function("location.hash === '#/rm/khach-hang/hieu-qua'")
    p.page.wait_for_function("(c) => document.querySelector('#client').value === c", arg=cid)
    p.page.wait_for_function("(n) => document.querySelector('.lede')?.textContent.includes(n)", arg=name)
    assert not p.problems()


def test_the_overview_graph_selects_expands_and_opens_pages(open_page, base_url):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/client/tong-quan/ban-do")
    o = api(base_url, "/api/overview", {"client_id": "C01", "role": "client"})["overview"]
    shown = [n for n in o["nodes"] if n["kind"] in ("family", "class", "goal", "risk", "event")]
    assert p.page.locator(".mnode").count() == len(shown)  # sources and policy items start hidden
    p.page.click("[data-k=alert]")
    assert p.page.locator(".mnode").count() == len(shown) + len([n for n in o["nodes"] if n["kind"] == "alert"])
    stock = next(n for n in o["nodes"] if n["id"] == "CL:stock")
    node = p.page.locator('.mnode[data-n="CL:stock"]')
    node.focus()
    p.page.keyboard.press("Enter")  # the keyboard selects as a click does
    assert node.get_attribute("aria-pressed") == "true"
    p.page.click("#m-open")
    assert p.page.locator('.mnode[data-n^="HD:"]').count() == stock["count"]
    p.page.click("#m-open")
    assert p.page.locator('.mnode[data-n^="HD:"]').count() == 0
    ev = next(n for n in o["nodes"] if n["kind"] == "event")
    p.page.locator(f'.mnode[data-n="{ev["id"]}"]').click()
    p.page.click("[data-go]")  # an event opens its path on Đồ thị tác động, selected
    p.page.wait_for_function("location.hash === '#/client/tin/do-thi'")
    p.page.wait_for_selector(f'[data-focus="event:{ev["ref"]}"][aria-pressed="true"]')
    assert not p.problems()


def test_the_overview_graph_is_a_list_on_a_phone(open_page):
    in_thread(approved, *MARKET)
    p = open_page("phone")
    p.go("#/client/tong-quan/ban-do")
    assert p.page.locator(".mapsvg").count() == 0 and p.page.locator(".mgroup .mrow").count() > 0
    p.page.locator(".mgroup .mrow").first.click()
    p.page.wait_for_selector("#m-side #m-clear")
    assert not p.problems()


def test_the_timeline_the_news_impact_card_and_the_cio_run_graph(open_page, base_url):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/client/tin/thi-truong")
    items = json.load(urllib.request.urlopen(base_url + "/api/families/C01/impact?role=client"))["items"]
    assert p.page.locator("#timeline .trow").count() == len(items)
    assert p.page.locator("#timeline .tstep").count() == sum(len(i["timeline"]) for i in items)
    p.go("#/client/tin/do-thi")
    p.page.locator('.gnode[data-focus^="event:"]').first.click()
    card = p.page.locator(".impactcard")
    assert "Chuỗi tác động" in card.inner_text() and card.locator(".mrow").count() > 0
    p.go("#/cio/do-thi")
    assert p.page.locator(".gnode").count() > 0 and "gia đình" in p.page.inner_text("#page h3")
    assert not p.problems()
