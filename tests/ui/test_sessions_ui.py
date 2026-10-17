"""Sessions in the browser (OWN-SS-01…08, SESSIONS_PLAN.md S4): the bar names the session with the title the model
wrote; a reload keeps the session; it is renamed in place; “Trò chuyện mới” starts an empty one; the history searches,
archives and restores; a turn still answering when the page reloads is followed to its answer, and one the server
never finished says it was cut."""

import json
import time
from types import SimpleNamespace

from conftest import in_thread


def ask(p, q):
    n = p.page.locator("#cp-msgs .cp-bot:not([data-busy])").count()
    p.page.fill("#cp-q", q)
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function(f"document.querySelectorAll('#cp-msgs .cp-bot:not([data-busy])').length > {n}")


def titled(p, title):
    """Wait for the session bar to name the session ``title`` (the pencil's svg adds a space: trimmed)."""
    js = "(t) => ((document.querySelector('#cp-title') || {}).textContent || '').trim() === t"
    p.page.wait_for_function(js, title)


class Hub:
    """The copilot model as the title request reaches it: the next of ``answers`` each call."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def get(self, key):
        return self

    async def generate(self, **kw):
        self.calls.append(kw)
        content = json.dumps(self.answers.pop(0), ensure_ascii=False)
        usage = SimpleNamespace(prompt_tokens=300, completion_tokens=40, cost=0.0002)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=usage)


def test_a_session_is_named_kept_on_reload_renamed_started_anew_archived_and_restored(open_page, monkeypatch):
    from operonx_agents.testing import ScriptedLLM, says, scripted

    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    hub = Hub({"title": "Tài sản tháng này", "goal": "Biết tài sản ròng thay đổi thế nào"},
              {"title": "Học phí cho con", "goal": "Chuẩn bị học phí năm sau"})  # fmt: skip
    monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: hub)
    with scripted(copilot=ScriptedLLM(says("Tài sản ròng tăng nhẹ."), says("Học phí năm sau khoảng 200 triệu."))):
        p = open_page()
        p.go("#/client/tong-quan/toan-canh")
        p.panel()
        assert "Cuộc trò chuyện mới" in p.page.inner_text("#cp-sess")
        ask(p, "Tài sản của tôi tháng này thế nào?")
        titled(p, "Tài sản tháng này")
        assert "Mục tiêu: Biết tài sản ròng thay đổi thế nào" in p.page.inner_text("#cp-sess")
        p.page.reload()  # a refresh: the same session, named, with its turn
        titled(p, "Tài sản tháng này")
        assert p.page.locator("#cp-msgs .cp-me").count() == 1
        p.page.click("#cp-title")
        p.page.fill("#cp-ren-q", "Của tôi")
        p.page.press("#cp-ren-q", "Enter")
        titled(p, "Của tôi")
        p.page.click("#cp-new")  # an empty session; the earlier one stays
        assert p.page.locator("#cp-msgs .cp-me").count() == 0 and "Cuộc trò chuyện mới" in p.page.inner_text("#cp-sess")
        ask(p, "Học phí cho con năm sau cần bao nhiêu?")
        titled(p, "Học phí cho con")
    assert len(hub.calls) == 2
    p.page.click("#cp-hist")
    p.page.wait_for_selector(".cp-convs li")
    assert p.page.locator(".cp-convs li").count() == 2 and "hôm nay" in p.page.inner_text(".cp-hist").lower()
    p.page.fill("#cp-hq", "cua toi")  # accents and case folded
    assert p.page.locator(".cp-convs li").count() == 1 and "Của tôi" in p.page.inner_text(".cp-convs")
    p.page.click(".cp-convs [data-arc]")
    p.page.wait_for_function("document.querySelector('[data-view=archived]').textContent.includes('(1)')")
    p.page.fill("#cp-hq", "")
    p.page.dispatch_event("#cp-hq", "input")
    assert p.page.locator(".cp-convs li").count() == 1 and "Học phí cho con" in p.page.inner_text(".cp-convs")
    p.page.click("[data-view=archived]")
    assert "Của tôi" in p.page.inner_text(".cp-convs")
    p.page.click(".cp-convs [data-res]")
    p.page.wait_for_function("document.querySelector('[data-view=recent]').textContent.includes('(2)')")
    assert not p.problems()


def _seed_running(q, steps, age=0.0):
    from assistant import conversations as conv
    from assistant.base import Ctx

    ctx = Ctx(role="client", client_id="C01", scope="personal", question=q, user="C01")
    cid = conv.start(ctx, q)
    seq = conv.begin(cid, q)
    conv.progress(cid, seq, steps)
    if age:
        with conv.db() as con:
            con.execute("update turns set at = ? where conversation_id = ?", (time.time() - age, cid))
    return cid, seq


def test_a_turn_running_at_reload_is_followed_to_its_answer_and_a_dead_one_says_it_was_cut(open_page):
    from assistant import conversations as conv

    step = [{"tool": "tong_quan", "label": "Tổng quan", "status": "ok"}]
    dead, _ = in_thread(_seed_running, "Câu trước khi máy chủ dừng", step, 600)
    cid, seq = in_thread(_seed_running, "Tài sản của tôi thế nào?", step)
    p = open_page("phone")
    p.go("#/client/tong-quan/toan-canh")
    p.panel()
    p.page.wait_for_selector("#cp-msgs [data-running]")  # the latest session, its turn still answering
    assert "Vẫn đang trả lời" in p.page.inner_text("#cp-msgs") and "Tổng quan" in p.page.inner_text("[data-running]")
    answer = {"status": "ok", "mode": "model", "text": "Tài sản ròng tăng nhẹ.", "steps": step, "conversation_id": cid}
    in_thread(conv.record, cid, "Tài sản của tôi thế nào?", answer, seq)
    p.page.wait_for_selector("text=Tài sản ròng tăng nhẹ.", timeout=8000)  # followed: no reload needed
    assert p.page.locator("#cp-msgs [data-running]").count() == 0
    p.page.click("#cp-hist")
    p.page.click(f"[data-open='{dead}']")
    p.page.wait_for_selector("#cp-msgs .badge.warn")
    assert "Bị ngắt" in p.page.inner_text("#cp-msgs") and "Tổng quan" in p.page.inner_text("#cp-msgs .cp-steps")
    assert not p.problems()
