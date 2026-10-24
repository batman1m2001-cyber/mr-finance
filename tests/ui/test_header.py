"""The header (UI redesign R1): search finds pages and records and opens them; “/” focuses it; the bell counts
the role's items and opens the evidence."""

from conftest import in_thread
from test_apply import MARKET, approved


def test_search_opens_a_holding_a_page_and_a_client(open_page):
    p = open_page()
    p.go("#/client/tong-quan/toan-canh")
    p.page.keyboard.press("/")
    assert p.page.evaluate("document.activeElement.id") == "q"
    p.page.keyboard.type("vàng")
    p.page.wait_for_selector("#q-results .pop-item")
    assert "Vàng miếng SJC" in p.page.inner_text("#q-results")
    p.page.keyboard.press("Enter")  # the first hit
    p.page.wait_for_function("location.hash === '#/client/tai-san'")
    p.page.fill("#q", "kế hoạch")  # its former name finds it under the bank's name (ADR-0037)
    p.page.wait_for_selector("#q-results .pop-head")
    assert p.page.inner_text("#q-results .pop-head") == "Trang"
    assert "Wealth planning advisor" in p.page.inner_text("#q-results .pop-item")
    p.page.click("#q-results .pop-item")
    p.page.wait_for_function("location.hash === '#/client/muc-tieu/ke-hoach'")
    p.go("#/rm/hom-nay")
    p.page.fill("#q", "hanh")  # an RM finds a client by name; the page switches to that client
    p.page.locator("#q-results .pop-item", has_text="Đỗ Thị Hạnh").first.click()
    p.page.wait_for_function("location.hash === '#/rm/khach-hang/tong-quan'")  # Toàn cảnh's place (OWN-FB-02)
    p.page.wait_for_function("document.querySelector('#client').value === 'C04'")
    assert not p.problems()


def test_the_bell_counts_the_feed_and_opens_the_evidence(open_page):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/client/xem/tong-quan")  # the feed: Tổng quan's Thông tin (UX_TOOLBAR_PLAN T4)
    p.page.wait_for_function("document.querySelector('#bell').dataset.count")
    p.page.wait_for_selector("#ws-feed .feed-item", state="attached")
    count = int(p.page.get_attribute("#bell", "data-count"))
    assert count == p.page.locator("#ws-feed .feed-item").count() > 0
    p.page.click("#bell")
    assert p.page.locator("#bell-pop .pop-item").count() == count
    p.page.locator("#bell-pop .pop-item").first.click()
    p.page.wait_for_function("document.querySelector('#bell-pop').hidden")
    assert not p.problems()
