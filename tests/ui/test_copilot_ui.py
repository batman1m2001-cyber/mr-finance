"""The Copilot in the browser (FEAT-32, FEAT-33): an answer marks the page elements it read; states follow the
request; a refusal is shown as one; reduced motion runs no animation; answers carry their card, time and sources."""

from conftest import in_thread
from test_apply import MARKET, approved


def ask(p, q):
    if p.page.is_hidden(".cp-panel"):
        p.page.click(".cp-fab")
    n = p.page.locator("#cp-msgs .cp-bot:not([data-busy])").count()
    p.page.fill("#cp-q", q)
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function(f"document.querySelectorAll('#cp-msgs .cp-bot:not([data-busy])').length > {n}")
    return p.page.locator("#cp-msgs .cp-bot:not([data-busy])").last


def test_an_answer_marks_what_it_read_and_the_states_follow(open_page):
    p = open_page()
    p.go("#/client/tong-quan/toan-canh")
    ask(p, "Tài sản của tôi thế nào?")
    assert p.page.inner_text("#cp-ctx").startswith("Đang xem: Toàn cảnh · Khách hàng")  # the page's context
    marked = p.page.eval_on_selector_all(".mf-focus", "es => es.map(e => e.dataset.focus)")
    assert sorted(marked) == ["kpi:liquidity", "kpi:net_worth", "kpi:risk"]
    assert p.page.get_attribute(".cp-fab", "data-state") == "ok"
    p.page.wait_for_function("document.querySelector('.cp-fab').dataset.state === 'idle'")  # after 1.6 s
    p.page.wait_for_function("!document.querySelector('.mf-focus')")  # marks clear themselves
    refused = ask(p, "Duyệt đề xuất đang chờ")
    assert "Không có quyền" in refused.inner_text() and p.page.get_attribute(".cp-panel", "data-state") == "error"
    assert not p.problems()


def test_the_phone_waits_for_the_panel_to_close(open_page):
    p = open_page("phone")
    p.go("#/client/tong-quan/toan-canh")
    ask(p, "Tài sản của tôi thế nào?")
    assert p.page.locator(".mf-focus").count() == 0
    p.page.click("#cp-close")
    assert p.page.locator(".mf-focus").count() == 3


def test_reduced_motion_runs_no_animation(open_page):
    p = open_page(reduced=True)
    p.go("#/client/tong-quan/toan-canh")
    ask(p, "Tài sản của tôi thế nào?")
    assert p.page.locator(".mf-focus").count() == 3
    assert p.page.evaluate("document.getAnimations().length") == 0


def test_busy_lasts_exactly_as_long_as_the_request(open_page):
    p = open_page()
    p.go("#/client/tong-quan/toan-canh")
    p.page.evaluate(
        """() => { const f0 = window.fetch; window.__hold = null;
             window.fetch = (u, o) => String(u).endsWith('/api/assistant')
               ? new Promise(r => { window.__hold = () => r(f0(u, o)); }) : f0(u, o); }"""
    )
    p.page.click(".cp-fab")
    p.page.fill("#cp-q", "Tài sản của tôi thế nào?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function("!!window.__hold")
    assert p.page.get_attribute(".cp-fab", "data-state") == "busy"
    assert p.page.get_attribute("#cp-msgs", "aria-busy") == "true" and p.page.locator(".cp-dots").count() == 1
    p.page.wait_for_timeout(1000)
    assert p.page.get_attribute(".cp-fab", "data-state") == "busy"  # nothing finishes until the answer does
    p.page.evaluate("window.__hold()")
    p.page.wait_for_function("document.querySelector('.cp-fab').dataset.state === 'ok'")
    assert p.page.locator(".cp-dots").count() == 0 and p.page.get_attribute("#cp-msgs", "aria-busy") == "false"


def test_answers_show_their_card_their_time_and_sources_and_offer_next_steps(open_page):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/client/tong-quan/toan-canh")
    a = ask(p, "Vì sao tin này ảnh hưởng tới tôi?")
    assert a.locator(".cp-chain li").count() >= 4  # tin, sự kiện, kịch bản, yếu tố, tài sản
    assert "trả lời lúc" in a.locator(".cp-meta").inner_text() and "Lần áp dụng" in a.locator(".cp-meta").inner_text()
    assert p.page.inner_text("#cp-sugg").startswith("Bạn có thể muốn:")
    p.page.locator("#cp-sugg [data-s]").first.click()  # a suggestion is a question
    p.page.wait_for_function("document.querySelectorAll('#cp-msgs .cp-card .cp-figs').length > 0")
    b = ask(p, "Mục tiêu của tôi thế nào?")
    assert b.locator(".cp-li").count() > 0 and b.locator(".bar-track").count() == b.locator(".cp-li").count()
    assert not p.problems()


def test_the_assistant_asks_before_a_write_and_shows_its_steps(open_page, monkeypatch):
    """A2: a model (scripted) plans a write; the panel shows what will be written and writes it only on Xác nhận."""
    from operonx_agents.testing import ScriptedLLM, asks, says, scripted

    from contacts import store as contacts

    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    llm = ScriptedLLM(asks(("hom_nay", {})), asks(("ghi_lien_he", {"channel": "call"})), says("Đã ghi cuộc gọi."))
    with scripted(copilot=llm):
        p = open_page()
        p.go("#/rm/khach-hang/toan-canh")
        a = ask(p, "Hôm nay gọi ai, rồi ghi lại cuộc gọi với khách này")
        assert "Ghi một cuộc gọi với gia đình" in a.inner_text() and contacts.recent() == []
        assert p.page.get_attribute(".cp-fab", "data-state") == "pending"
        assert p.page.inner_text("#cp-router") == "mô hình scripted-model"
        n = p.page.locator("#cp-msgs .cp-bot").count()
        a.locator("[data-ok]").click()
        p.page.wait_for_function(f"document.querySelectorAll('#cp-msgs .cp-bot:not([data-busy])').length > {n}")
        done = p.page.locator("#cp-msgs .cp-bot").last
        assert "Đã ghi cuộc gọi." in done.inner_text() and len(contacts.recent()) == 1
    assert not p.problems()


def test_a_conversation_is_picked_up_on_another_device_listed_and_deleted(open_page):
    """A3: the conversation lives on the server — a second browser (another device) opens the panel on it; the list
    opens and deletes it; “Mới” starts another. Nothing is left in the browser's storage."""
    p = open_page()
    p.go("#/client/tong-quan/toan-canh")
    ask(p, "Tài sản của tôi thế nào?")
    cid = p.page.get_attribute("#cp-msgs", "data-conversation")
    assert cid and p.page.evaluate("Object.keys(sessionStorage).filter(k => k.startsWith('mf.copilot')).length") == 0
    q = open_page("phone")  # another device, the same person
    q.go("#/client/tong-quan/toan-canh")
    q.page.click(".cp-fab")
    q.page.wait_for_function(f"document.querySelector('#cp-msgs').dataset.conversation === '{cid}'")
    assert q.page.inner_text("#cp-msgs .cp-me") == "Tài sản của tôi thế nào?"
    assert q.page.locator("#cp-msgs .cp-bot .cp-figs").count() == 1  # the answer's card, as first shown
    q.page.click("#cp-new")
    assert q.page.locator("#cp-msgs .cp-me").count() == 0
    q.page.click("#cp-hist")
    q.page.wait_for_selector(".cp-convs li")
    assert "Tài sản của tôi thế nào?" in q.page.inner_text(".cp-convs") and "1 lượt" in q.page.inner_text(".cp-convs")
    q.page.click(f"[data-open='{cid}']")
    q.page.wait_for_function("document.querySelectorAll('#cp-msgs .cp-me').length === 1")
    q.page.click("#cp-hist")
    q.page.wait_for_selector(".cp-convs li")
    q.page.once("dialog", lambda d: d.accept())
    q.page.click(f"[data-del='{cid}']")
    q.page.wait_for_selector("text=Chưa có cuộc trò chuyện nào.")
    assert not p.problems() and not q.problems()
