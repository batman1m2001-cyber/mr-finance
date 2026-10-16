"""The Bộ nhớ page (A4, FEAT-37): the person sees what the assistant remembers, corrects it, forgets one or all;
finds a past conversation and opens it in the panel; the page is reached from the panel and the header."""

import asyncio

from conftest import in_thread

from assistant import memory
from assistant.base import Ctx


def ctx(client_id="C01"):  # the client signed in (the browser's session): their own id is the owner
    return Ctx(role="client", client_id=client_id, scope="personal", question="", user=client_id)


def keep(client_id, kind, text):  # beside Playwright's loop
    return in_thread(lambda: asyncio.run(memory.remember(ctx(client_id), kind, text)))


def test_the_memory_page_shows_corrects_and_forgets(open_page):
    keep("C01", "preference", "Thích báo cáo ngắn")
    keep("C01", "goal", "Mua nhà năm 2028")
    keep("C02", "goal", "Của gia đình khác")
    p = open_page()
    p.go("#/client/bo-nho")
    p.page.wait_for_selector(".mem-item")
    text = p.page.inner_text("#page")
    assert "Thích báo cáo ngắn" in text and "Mua nhà năm 2028" in text and "Của gia đình khác" not in text
    assert "Sở thích" in text and "không hết hạn" in text
    iid = p.page.locator(".mem-item", has_text="Thích báo cáo ngắn").get_attribute("data-item")
    item = p.page.locator(f".mem-item[data-item='{iid}']")
    item.locator("[data-edit]").click()
    p.page.fill(".mem-input", "Thích báo cáo thật ngắn")
    item.locator("[data-edit]").click()
    p.page.wait_for_selector("text=Thích báo cáo thật ngắn")
    p.page.locator(".mem-item", has_text="Mua nhà").locator("[data-forget]").click()
    p.page.wait_for_function("document.querySelectorAll('.mem-item').length === 1")
    p.page.once("dialog", lambda d: d.accept())
    p.page.click("#mem-clear")
    p.page.wait_for_selector("text=Chưa có gì.")
    assert in_thread(lambda: asyncio.run(memory.store().items("C01"))) == []
    assert not p.problems()


def test_a_past_conversation_is_found_and_opened_in_the_panel(open_page):
    p = open_page("phone")
    p.go("#/client/tong-quan/toan-canh")
    p.page.click(".cp-fab")
    p.page.fill("#cp-q", "Tài sản của tôi thế nào?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function("document.querySelectorAll('#cp-msgs .cp-bot:not([data-busy])').length > 0")
    p.page.click("#cp-hist")
    p.page.click("text=Bộ nhớ →")  # the page from the panel
    p.page.wait_for_selector(".mem-conv")
    p.page.fill("#mem-q", "tai san")
    p.page.press("#mem-q", "Enter")
    p.page.wait_for_selector(".mem-hit")
    assert "bạn" in p.page.inner_text(".mem-hit")
    p.page.locator(".mem-hit [data-open]").first.click()
    p.page.wait_for_function("!document.querySelector('.cp-panel').hidden")
    p.page.wait_for_function("document.querySelectorAll('#cp-msgs .cp-me').length === 1")
    assert p.page.evaluate("[document.documentElement.scrollWidth, innerWidth]") == [390, 390]
    assert not p.problems()


def test_a_document_is_added_found_and_deleted(open_page):
    from assistant import knowledge

    p = open_page()
    p.go("#/client/bo-nho")
    p.page.wait_for_selector("#doc-add")
    assert "Chưa có tài liệu nào." in p.page.inner_text("#page")
    note = "# Hợp đồng bảo hiểm\n\nQuyền lợi nằm viện: chi trả tối đa ba mươi ngày mỗi năm.\n".encode()
    p.page.set_input_files("#doc-file", files=[{"name": "bao-hiem.md", "mimeType": "text/markdown", "buffer": note}])
    p.page.click("#doc-add button[type=submit]")
    p.page.wait_for_selector("[data-doc='C01/bao-hiem.md']")
    hits = in_thread(lambda: asyncio.run(knowledge.search_materials(ctx("C01"), "quyền lợi nằm viện")))
    assert hits and "ba mươi ngày" in hits[0]["text"]
    p.page.once("dialog", lambda d: d.accept())
    p.page.click("[data-deldoc='C01/bao-hiem.md']")
    p.page.wait_for_selector("text=Chưa có tài liệu nào.")
    assert in_thread(lambda: asyncio.run(knowledge.search_materials(ctx("C01"), "quyền lợi nằm viện"))) == []
    assert not p.problems()


def test_a_fired_follow_up_rings_once_and_an_open_one_is_cancelled(open_page):
    from assistant import followups
    from market import store as market

    fired = in_thread(lambda: followups.create(ctx("C01"), "market", series_id="VNINDEX", op="below", level=1200))
    in_thread(lambda: followups.create(ctx("C01"), "topic", topic="lãi suất"))
    in_thread(lambda: market.put("VNINDEX", "test", "https://example.test", [("2026-10-16", 1180.0)]))
    in_thread(lambda: followups.check_market(["VNINDEX"]))
    p = open_page()
    p.go("#/client/bo-nho")
    p.page.wait_for_selector("[data-fu]")
    text = p.page.inner_text("#page")
    assert "VN-Index dưới 1.200 điểm" in text and "Đã báo" in text and "Đang theo dõi" in text
    p.page.click("#bell")
    item = p.page.locator(".pop-item", has_text="Theo dõi: VN-Index dưới 1.200 điểm")
    item.wait_for()
    item.click()  # opened: it leaves the bell
    for _ in range(50):
        if in_thread(lambda: followups.get(ctx("C01"), fired["id"]))["seen"]:
            break
        p.page.wait_for_timeout(100)
    assert in_thread(lambda: followups.unseen(ctx("C01"))) == []
    p.go("#/client/bo-nho")
    p.page.wait_for_selector("[data-cancelfu]")
    p.page.click("[data-cancelfu]")
    p.page.wait_for_function("document.querySelectorAll('[data-cancelfu]').length === 0")
    assert [f["status"] for f in in_thread(lambda: followups.listing(ctx("C01")))] == ["fired"]
    assert not p.problems()
