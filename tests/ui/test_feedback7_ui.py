"""Business feedback 7 in the browser (OWN-FB-19…25): the RM's desk is Tổng quan, its list "Khách hàng đang quản lý"
with the net worth in colour; no Hôm nay (its address opens the desk, its contact log is in Thông tin); the client
picker in the Khách hàng and Advisory performance sheets, none on "Tất cả khách hàng"; a phone keeps it on screen."""

from conftest import api


def rail(p):
    return p.page.eval_on_selector_all("[data-tool]", "as => as.map(a => a.getAttribute('aria-label'))")


def test_the_rms_desk_is_tong_quan_and_hom_nay_is_gone(open_page):
    p = open_page()
    p.go("#/rm")
    p.page.wait_for_selector(".desk-rm [data-fam]")
    assert rail(p)[0] == "Tổng quan" and "Hôm nay" not in rail(p) and "Sổ khách hàng" not in rail(p)  # OWN-FB-25, -21
    assert p.page.inner_text("#dk-title") == "Tổng quan"
    assert p.page.inner_text("#rk-t") == "Khách hàng đang quản lý"  # OWN-FB-19
    assert "3 khách hàng" in p.page.inner_text(".desk-rm .ws-sub")
    worth = p.page.eval_on_selector_all(".desk-rm [data-fam] .rk-nw", "ns => ns.map(n => n.textContent.trim())")
    assert len(worth) == 3 and not any(w.startswith("+") for w in worth)  # OWN-FB-20: a net worth, not a change
    assert p.page.eval_on_selector(".rk-nw", "n => getComputedStyle(n).backgroundColor") != "rgba(0, 0, 0, 0)"
    assert p.page.locator('.desk-rm a[href="#/rm/hom-nay"]').count() == 0
    p.page.evaluate("location.hash = '#/rm/hom-nay'")  # an old link: the desk
    p.page.wait_for_function("location.hash === '#/rm'")
    assert p.page.is_hidden("#ws-sheet") and not p.problems()


def test_a_contact_is_logged_from_the_desk(open_page, base_url):
    p = open_page()
    p.go("#/rm")
    p.page.wait_for_selector(".desk-rm [data-fam]")
    p.page.click('.desk-rm [data-fam="C04"]')
    p.page.click("#ws-pane-i [data-log]")
    p.page.wait_for_selector("#ws-pane-i #contact-form")
    assert p.page.eval_on_selector("#contact-form [name=family]", "s => s.value") == "C04"
    p.page.select_option("#contact-form [name=channel]", "call")
    p.page.fill("#contact-form [name=note]", "Hẹn gặp tuần sau về học phí")
    p.page.click("#contact-form button[type=submit]")
    p.page.wait_for_selector("#ws-pane-i .dk-row:has-text('Hẹn gặp tuần sau về học phí')")
    got = api(base_url, "/api/rm/today", who="rm01")["contacts"]
    assert got[0]["family_id"] == "C04" and got[0]["note"] == "Hẹn gặp tuần sau về học phí"
    p.page.wait_for_selector('.desk-rm [data-node="contacts"] [data-pick="C04"]')  # the desk read again
    p.page.click('.desk-rm [data-node="contacts"] [data-log]')  # Liên hệ gần đây's own way in
    p.page.wait_for_selector("#ws-pane-i #contact-form")
    assert not p.problems()


def test_the_client_picker_is_in_the_sheet(open_page):
    p = open_page()
    p.go("#/rm/khach-hang/tong-quan")
    assert p.page.is_visible("#dk-who #client-pick") and p.page.locator(".shell-bar #client-pick").count() == 0  # OWN-FB-22
    assert "Khách hàng" in p.page.inner_text("#dk-who")
    sheet, picker = (p.page.locator(s).bounding_box() for s in ("#ws-sheet", "#client-pick"))
    assert sheet["y"] <= picker["y"] <= sheet["y"] + 120  # at the top of the sheet, by its tabs
    p.page.select_option("#client", "C04")
    p.page.wait_for_function("document.querySelector('#page').innerText.includes('Đỗ Thị Hạnh')")
    p.go("#/rm/hieu-qua/khach-hang")  # OWN-FB-24: "Khách hàng này" says which
    assert p.page.is_visible("#dk-who #client-pick")  # its two pages are the sheet's top tabs here
    p.go("#/rm/hieu-qua/tat-ca")  # every client: no picker, and no empty line for it
    assert p.page.is_hidden("#client-pick") and p.page.is_hidden("#dk-line")
    p.go("#/rm/khach-hang/tat-ca")
    assert p.page.is_hidden("#client-pick") and p.page.is_visible("#dk-tabs2")
    p.go("#/rm/khach-hang/ke-hoach")  # one page, no inner tabs: the line holds the picker alone
    assert p.page.is_hidden("#dk-tabs2") and p.page.is_visible("#dk-who #client-pick")
    p.go("#/rm")
    assert p.page.is_hidden("#ws-sheet") and not p.problems()


def test_the_picker_on_a_phone(open_page):
    for theme in ("light", "dark"):
        p = open_page(size="phone", theme=theme)
        p.go("#/rm/khach-hang/tong-quan")
        box = p.page.locator("#client").bounding_box()
        width = p.page.evaluate("innerWidth")
        assert box["x"] >= 0 and box["x"] + box["width"] <= width and box["width"] > width / 2
        assert p.page.evaluate("document.documentElement.scrollWidth") <= width
        assert not p.problems()
