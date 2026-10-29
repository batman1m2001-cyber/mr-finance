"""Nguồn tin in the browser (docs/NEWS_OPS_PLAN.md N1): Admin adds a source, turns one off, deletes one and tests one
(the feed read answered by the page's route, no network), the changes wait on the page until Gửi đề xuất, then the
proposal is approved here and the list in force is the new one. Desktop and phone, no error and no sideways scroll;
the list is put back after."""

import pytest


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_admin_adds_turns_off_deletes_tests_proposes_and_approves(open_page, size):
    p = open_page(size)
    page = p.page
    p.go("#/admin/nguon-tin")
    page.wait_for_selector("#src-list [data-src]")
    before = p.ctx.request.get(f"{p.base}/api/news/sources").json()
    assert page.is_disabled("#src-propose") and page.inner_text("#src-dirty") == "Không có thay đổi"

    page.route(
        "**/api/news/sources/test*",
        lambda r: r.fulfill(json={"ok": True, "items": 42, "ms": 120, "newest": {"title": "Lãi suất giữ nguyên"}}),
    )
    page.click('[data-src="vnexpress_kd"] [data-act=test]')
    page.wait_for_selector('[data-src="vnexpress_kd"] .good-text')
    assert "Đọc được 42 tin" in page.inner_text('[data-src="vnexpress_kd"]')

    page.fill("#src-add-form [name=outlet]", "Tuổi Trẻ")
    page.fill("#src-add-form [name=section]", "Kinh doanh")
    page.fill("#src-add-form [name=url]", "https://tuoitre.vn/rss/kinh-doanh.rss")
    page.click("#src-add-form [type=submit]")
    page.wait_for_selector('[data-src="tuoi_tre_kinh_doanh"]')
    page.click('[data-src="ecb"] [data-act=flip]')
    page.wait_for_selector('[data-src="ecb"] [data-act=flip]:text("Bật")')
    page.click('[data-src="fed"] [data-act=drop]')
    page.wait_for_selector('[data-src="fed"]', state="detached")
    assert page.inner_text("#src-dirty") == "Chưa gửi: 1 thêm, 1 sửa, 1 xoá"
    assert not p.problems()

    page.fill("#src-note", "Thêm Tuổi Trẻ, tạm tắt ECB")
    page.click("#src-propose")
    page.wait_for_selector("#src-pending")
    assert "1 thêm, 1 sửa, 1 xoá" in page.inner_text("#src-pending") and page.is_disabled("#src-propose")
    page.click("#src-pending [data-decide=approve]")
    page.wait_for_selector("#src-pending", state="detached")
    now = p.ctx.request.get(f"{p.base}/api/news/sources").json()
    ids = {s["id"]: s for s in now["sources"]}
    assert "tuoi_tre_kinh_doanh" in ids and "fed" not in ids and ids["ecb"]["approved"] is False
    assert now["active"]["version"] > before["active"]["version"]
    assert page.inner_text("#src-dirty") == "Không có thay đổi" and not p.problems()

    for path, body in (
        ("propose", {"kind": "news_sources", "data": before["sources"], "by": "admin", "note": "trả lại"}),
        ("decide", {"action": "approve", "by": "admin"}),
    ):
        if path == "decide":
            body["version_id"] = p.ctx.request.get(f"{p.base}/api/news/sources").json()["pending"]["id"]
        assert p.ctx.request.post(f"{p.base}/api/config/{path}", data=body).ok
