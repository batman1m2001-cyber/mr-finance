"""Business feedback 6 in the browser (OWN-FB-01…16): the RM's Khách hàng in four tabs, two with inner tabs, and no
title repeated over them; the old addresses that lost their page go to the one that took it; the RM's book without
its drawing; Advisory performance as the owner's mock; the CIO's Decision board (the flow with its client frame, the
decisions' filters, the inbox on the board, the exposure in plain words) and its rail without the model's pages,
which are Admin's now; Tác động danh mục, Bài viết and Hiệu quả."""

from conftest import in_thread
from test_apply import MARKET, approved


def tabs(p, strip="#dk-tabs"):
    return p.page.eval_on_selector_all(f"{strip} a", "as => as.map(a => [a.textContent.trim(), !!a.ariaCurrent])")


def rail(p):
    return p.page.eval_on_selector_all("[data-tool]", "as => as.map(a => a.getAttribute('aria-label'))")


def test_the_rms_client_is_four_tabs_two_with_inner_tabs_and_no_title_over_them(open_page):
    p = open_page()
    p.go("#/rm/khach-hang/tai-san")
    p.page.wait_for_selector("#dk-tabs a")
    four = ["Wealth view", "Wealth planning advisor", "Headline news", "Advisory performance"]
    assert [t for t, _ in tabs(p)] == four
    assert tabs(p)[0][1] and tabs(p, "#dk-tabs2") == [["Tổng quan", False], ["Dữ liệu chi tiết tài sản", True]]
    assert p.page.is_hidden("#ws-sheet-t") and p.page.is_hidden("#ws-sheet-back .dk-back-l")  # OWN-FB-14
    p.go("#/rm/khach-hang/do-thi")
    assert [t for t, cur in tabs(p, "#dk-tabs2") if cur] == ["Đồ thị tác động"]
    p.go("#/rm/khach-hang/ke-hoach")
    assert p.page.is_hidden("#dk-tabs2")  # one page: no inner tabs
    for gone, now in (("toan-canh", "tong-quan"), ("ban-do", "tong-quan")):
        p.go(f"#/rm/khach-hang/{gone}")
        assert p.page.url.endswith(f"#/rm/khach-hang/{now}"), gone
    for kept in ("tac-dong", "duyet"):  # no tab, the address opens
        p.go(f"#/rm/khach-hang/{kept}")
        assert p.page.url.endswith(kept) and kept not in " ".join(t for t, _ in tabs(p)), kept
        assert p.page.is_visible("#ws-sheet-t")  # a page with no tab keeps its title
    assert p.problems() == []


def test_the_rms_book_has_no_drawing_and_advisory_performance_is_the_mock(open_page):
    p = open_page()
    p.go("#/rm")
    p.page.wait_for_selector(".desk-rm [data-fam]")
    assert p.page.locator(".desk-rm svg .rk-me, .desk-rm .rk-ring").count() == 0  # OWN-FB-01
    assert "Advisory performance" in rail(p)
    p.go("#/rm/hieu-qua/khach-hang")
    body = p.page.inner_text("#page")
    assert "Nội bộ" not in body and "Dữ liệu mẫu" in body  # the line went (OWN-FB-23)
    names = p.page.eval_on_selector_all(".pipe .agent", "as => as.map(a => a.title)")
    assert names == ["AI News Reader", "AI Impact Assessor", "AI Planning Advisor", "AI Client Chat"]  # OWN-FB-06
    assert [t for t, _ in tabs(p, "#dk-tabs2") or tabs(p)] == ["Khách hàng này", "Tất cả khách hàng"]
    assert p.problems() == []


def test_the_cio_decision_board_and_its_rail(open_page):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/cio")
    p.page.wait_for_selector(".desk-cio .dk-stage")
    assert p.page.inner_text("#dk-title") == "Decision board"  # OWN-FB-07
    stages = p.page.eval_on_selector_all(".dk-stage", "bs => bs.map(b => b.dataset.stage)")
    assert stages == ["news", "views", "runs", "families", "rm"]  # no Sự kiện (OWN-FB-08)
    assert p.page.eval_on_selector_all(".dk-flow-client .dk-stage", "bs => bs.map(b => b.dataset.stage)") == [
        "families",
        "rm",
    ]
    for f in ("#dk-f-source", "#dk-f-scope", "#dk-f-level", "#dk-f-q"):  # OWN-FB-10
        assert p.page.is_visible(f), f
    assert p.page.inner_text("#dk-exp") == "Tổng quan tác động tới tài sản"  # OWN-FB-12
    plain = p.page.inner_text("#dk-impact")
    assert plain.startswith("Nếu kịch bản") and "AR-" not in plain and "P10: 1 trong 10" in plain
    p.page.wait_for_selector("#dk-inbox-b :is(button, a, table, .panel, p)")
    assert "Đang tải hộp tin" not in p.page.inner_text("#dk-inbox-b")  # the inbox on the board (OWN-FB-11)
    p.go("#/cio/hop-tin")
    assert p.page.url.endswith("#/cio")
    assert rail(p) == ["Decision board", "Tác động", "Nội dung", "Hiệu quả", "Nhật ký", "Bộ nhớ"]  # OWN-FB-13, 16
    p.go("#/cio/phoi-nhiem")
    assert [t for t, _ in tabs(p)] == ["Tác động danh mục", "Đồ thị lần áp dụng"]  # OWN-FB-14
    p.go("#/cio/ban-tin")
    assert "Viết bài mới" in p.page.inner_text("#page") and p.page.locator("textarea[name=body]").count() == 1
    p.go("#/cio/hieu-qua")
    body = p.page.inner_text("#page")
    assert "Hiệu quả" in body and "Dự báo đã duyệt" in body  # OWN-FB-16, nothing technical
    assert not any(w in body for w in ("token", "prompt", "claude", "gpt"))
    p.go("#/cio/cau-hinh")  # an address already sent still opens
    assert p.page.url.endswith("#/cio/cau-hinh")
    p.go("#/cio/mo-hinh/tham-so")
    assert p.page.url.endswith("#/cio/mo-hinh/tham-so") and tabs(p) == []  # its pages are no tab of the board
    p.go("#/cio/giu")
    assert tabs(p) == [] and p.page.is_visible("#ws-sheet-t")
    assert p.problems() == []


def test_admin_has_the_models_pages(open_page):
    p = open_page()
    p.go("#/admin")
    p.page.wait_for_selector("[data-tool]")
    assert "Mô hình" in rail(p)
    p.go("#/admin/mo-hinh/tham-so")
    assert [t for t, _ in tabs(p)] == ["Tham số", "Độ chính xác", "Thử nghiệm hằng ngày", "Đo lường"]
    assert p.problems() == []


def test_the_decisions_say_their_level_and_page_by_twenty_and_filter(open_page):
    p = open_page()

    def many(route):  # the desk's own read, its queue made 25 rows long (OWN-FB-10)
        d = route.fetch().json()
        lv = ["high", "medium", "low", "medium", "high"]
        d["decide"] = [
            {"kind": "event", "id": f"EV-{i}", "title": f"Tin số {i}", "status": "Chưa có nhận định", "at": 1e9 - i,
             "route": "#/cio/nhan-dinh", "level": lv[i % 5], "group": "rates", "outlets": ["VnEconomy"],
             "scope": "domestic"}
            for i in range(25)
        ]  # fmt: skip
        route.fulfill(json=d)

    p.page.route("**/api/desk*", many)
    p.go("#/cio")
    p.page.wait_for_selector("#dk-dec .dk-row")
    assert p.page.locator("#dk-dec .dk-row").count() == 20 and p.page.inner_text("#dk-more") == "Xem thêm (còn 5)"
    first = p.page.inner_text("#dk-dec .dk-row >> nth=0")
    assert "Tác động cao" in first and "Trong nước" in first and "VnEconomy" in first  # OWN-FB-09
    p.page.click("#dk-more")
    assert p.page.locator("#dk-dec .dk-row").count() == 25 and p.page.locator("#dk-more").count() == 0
    p.page.select_option("#dk-f-level", "high")
    assert p.page.locator("#dk-dec .dk-row").count() == 10 and p.page.inner_text("#dk-dec-n") == "10 / 25 việc"
    body = p.page.inner_text(".desk-cio")
    assert not any(c in body for c in ("Mô hình và dữ liệu", "Agent dưới bàn", "Sự kiện gần đây"))  # OWN-FB-13
    p.page.select_option("#dk-f-level", "")  # the module keeps its filters for the next test
    assert p.problems() == []
