"""The assistant knows the graph (UNIFIED_FLOWS_PLAN F10, OWN-GW-47/48): a question asked on the workspace carries
the lens, what is picked and the active scenarios; a comparison read lights those scenarios and runs home along
their hypothetical edges, hollow (a scripted stream through the real panel; the server side is
tests/test_assistant_graph.py)."""

import json

KEY = "mf.ws.scn.C01"
# the panel's stream, played from window.__script; the request body it was sent kept in window.__body
TIMED = """(() => { const real = window.fetch;
  window.fetch = (url, opts) => {
    if (!String(url).includes('/api/assistant/stream')) return real(url, opts);
    window.__body = JSON.parse(opts.body);
    const enc = new TextEncoder(), ev = window.__script || [];
    const body = new ReadableStream({start(c) { let n = 0;
      for (const [t, e] of ev) setTimeout(() => {
        c.enqueue(enc.encode(`id: ${++n}\\ndata: ${JSON.stringify(e)}\\n\\n`));
        if (e.type === 'answer') c.close(); }, t); }});
    return Promise.resolve(new Response(body, {status: 200, headers: {'content-type': 'text/event-stream'}}));
  }; })();"""
STEP = {"type": "step", "call_id": "c1", "tool": "so_sanh_kich_ban", "label": "So sánh kịch bản"}
SCRIPT = [
    [0, {"type": "start"}],
    [50, {**STEP, "phase": "start", "nodes": ["SC:vni_30", "SC:rates_up"]}],
    [900, {**STEP, "phase": "end", "ok": True, "ms": 850, "focus": ["scenario:vni_30", "scenario:rates_up"]}],
    [3000, {"type": "answer", "assistant": {"status": "ok", "mode": "model", "text": "Cùng lúc: −3,87 tỷ.",
                                            "focus": ["scenario:vni_30", "scenario:rates_up"], "steps": []}}],
]  # fmt: skip
HOT = """() => [...document.querySelectorAll('.wedge.hot')].map(w => w.dataset.e)"""


def test_a_question_carries_the_workspace_and_a_comparison_lights_its_scenarios(open_page):
    p = open_page(theme="dark")
    p.ctx.add_init_script(TIMED)
    p.ctx.add_init_script(f"window.__script = {json.dumps(SCRIPT)};")
    p.go("#/client/xem/muc-tieu")
    p.page.evaluate(f"localStorage.setItem('{KEY}', JSON.stringify({{ids: ['vni_30', 'rates_up'], params: {{}}}}))")
    p.page.reload()
    p.page.wait_for_selector('.wnode.live[data-n="SC:rates_up"]', state="attached")
    p.page.wait_for_function("!document.querySelector('#ws-scn').classList.contains('busy')")
    p.page.click('.wnode[data-n="GL:tuition"] .wcore')
    assert p.page.evaluate(HOT) == []  # at rest: nothing glows
    p.page.click("#ws-tab-a")  # back to the assistant, the pick kept
    p.page.fill("#cp-q", "Các kịch bản đang bật cùng lúc thì mục tiêu này sao?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function("!!window.__body")
    graph = p.page.evaluate("window.__body.graph")
    assert graph["lens"] == "muc-tieu" and graph["active"] == ["vni_30", "rates_up"] and graph["params"] == {}
    assert graph["selected"]["id"] == "GL:tuition" and graph["selected"]["kind"] == "goal"
    assert graph["selected"]["label"]  # the name: the server lets a model see it, never the keyword path
    p.page.wait_for_function("document.querySelectorAll('.wcomet.hollow').length > 0", timeout=4000)
    hot = p.page.evaluate(HOT)
    for sid in ("SC:vni_30", "SC:rates_up"):  # each scenario's own hypothetical edges, not only its spoke home
        assert any(k.startswith(f"{sid}>") for k in hot), (sid, hot)
    assert p.page.locator(".wnode.ok[data-n='SC:vni_30']").count() == 1
    p.page.wait_for_selector("#cp-msgs .cp-bot:not([data-busy])")
    assert not p.problems()


def test_the_panel_names_the_lens_on_screen_after_a_reload_and_a_lens_change(open_page):
    """Stress test D30: on Mục tiêu & kịch bản the docked panel said “Đang xem: Tổng quan tài chính” — it was drawn
    before the workspace named its lens, and never again."""
    p = open_page(theme="dark")
    p.go("#/client/xem/muc-tieu")
    name = "Wealth Planning"  # the lens's section (ADR-0037)
    p.page.wait_for_function("(n) => document.querySelector('#ws-title').textContent === n", arg=name)
    ctx = "(n) => document.querySelector('#cp-ctx').textContent.startsWith(`Đang xem: ${n}`)"
    p.page.wait_for_function(ctx, arg=name)
    p.go("#/client/xem/rui-ro")  # the bar opens Rủi ro's page now (B3.1); the lens is its address
    p.page.wait_for_function("document.querySelector('#cp-ctx').textContent.startsWith('Đang xem: Rủi ro')")
