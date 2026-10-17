"""The Customer's workspace in the browser (FEAT-40, ADR-0035, OWN-GW-01…14): one page whose graph survives lenses,
sheets and answers; old addresses open their page as a sheet; the strip and the dock; the assistant's real stream
drives the graph (here the keyword path, no model: its one tool, said as it runs); a stream that breaks is said and
marked failed; keyboard and phone."""

STUB_BREAK = """(() => { const real = window.fetch;
  window.fetch = (url, opts) => {
    if (!String(url).includes('/api/assistant/stream')) return real(url, opts);
    const enc = new TextEncoder();
    const ev = [{type: 'start'},
      {type: 'step', phase: 'start', call_id: 'c1', tool: 'dong_tien', label: 'Dòng tiền', nodes: ['FL:in', 'FL:out']}];
    const body = new ReadableStream({async start(c) {
      ev.forEach((e, i) => c.enqueue(enc.encode(`id: ${i + 1}\\ndata: ${JSON.stringify(e)}\\n\\n`)));
      await new Promise(r => setTimeout(r, 300)); c.error(new TypeError('network error')); }});
    return Promise.resolve(new Response(body, {status: 200, headers: {'content-type': 'text/event-stream'}}));
  }; })();"""


# overlapping node discs, and overlapping labels of two different nodes (shown ones only)
CLEAR = """() => {
  const discs = [...document.querySelectorAll('.wnode:not(.off):not(.gone) .wcore')]
    .map(c => c.getBoundingClientRect());
  let d = 0;
  for (let i = 0; i < discs.length; i++) for (let j = i + 1; j < discs.length; j++) {
    const a = discs[i], b = discs[j], ra = a.width / 2, rb = b.width / 2;
    if (Math.hypot(a.left + ra - b.left - rb, a.top + ra - b.top - rb) < ra + rb - 1) d++; }
  const t = [...document.querySelectorAll('.wnode:not(.off):not(.gone) :is(.wlbl, .wfig)')]
    .filter(x => x.textContent && getComputedStyle(x).opacity > 0.5)
    .map(x => [x.closest('.wnode').dataset.n, x.getBoundingClientRect()]);
  let o = 0;
  for (let i = 0; i < t.length; i++) for (let j = i + 1; j < t.length; j++) {
    const [na, a] = t[i], [nb, b] = t[j];
    const x = a.left < b.right - 1 && b.left < a.right - 1, y = a.top < b.bottom - 1 && b.top < a.bottom - 1;
    if (na !== nb && x && y) o++; }
  return [d, o];
}"""


def mark(p):
    p.page.evaluate("document.querySelector('.ws-svg').dataset.kept = 'same'")


def same(p):
    return p.page.evaluate("document.querySelector('.ws-svg').dataset.kept") == "same"


def test_one_page_the_graph_survives_lenses_and_sheets(open_page):
    p = open_page()
    p.go("#/client")
    p.page.wait_for_selector(".wnode.k-family")
    assert p.page.is_hidden("#nav") and p.page.is_hidden(".cp-fab")  # the toolbar and the dock instead
    mark(p)
    shown = {}
    for lens in ("tai-san", "dong-tien", "muc-tieu", "tin", "rui-ro", "tong-quan"):
        p.go(f"#/client/xem/{lens}")
        shown[lens] = p.page.locator(".wnode:not(.off)").count()
        assert p.page.get_attribute(f'[data-tool="{lens}"]', "aria-current") is not None
    assert same(p) and shown["tong-quan"] > shown["muc-tieu"]
    # OWN-GW-15: by default only the spokes of “My Wealth”; no node on another, no label on another
    ends = p.page.eval_on_selector_all(".ws-edges .wedge", "es => es.map(e => e.dataset.e.split('>'))")
    assert ends and all("ME" in e for e in ends)
    assert p.page.evaluate(CLEAR) == [0, 0]
    assert (
        p.page.locator(".wnode.k-flow:not(.off)").count() == 2
        and p.page.locator(".wnode.k-liquidity:not(.off)").count() == 1
    )
    p.go("#/client/xem/tai-san")  # holdings on demand: a class picked opens to them, the rest steps back
    assert p.page.locator(".wnode.k-holding:not(.off)").count() == 0
    p.page.click('.wnode[data-n="CL:stock"] .wcore')
    p.page.wait_for_function("document.querySelectorAll('.wnode.k-holding:not(.off)').length > 0")
    p.page.wait_for_timeout(600)  # the nodes' move (transform transition) has ended
    assert p.page.locator(".wnode.dim").count() > 0 and p.page.evaluate(CLEAR) == [0, 0]
    p.page.click('.wnode[data-n="CL:stock"] .wcore')
    p.go("#/client/tai-san")  # an old address: its page as a sheet over the Tài sản lens
    assert p.page.is_visible("#ws-sheet") and p.page.inner_text("#ws-sheet-t") == "Tài sản"
    assert p.page.locator("#ws-sheet #page .holdings, #ws-sheet #page table, #ws-sheet #page .card").count() > 0
    p.page.keyboard.press("Escape")
    p.page.wait_for_function("location.hash === '#/client/xem/tai-san'")
    assert p.page.is_hidden("#ws-sheet") and same(p)
    assert not p.problems()


def test_the_inspector_the_strip_and_a_hypothetical_scenario(open_page):
    p = open_page()
    p.go("#/client/xem/muc-tieu")
    me = p.page.text_content(".wme-v")
    p.page.click('.wnode[data-n="SC:vni_30"]')
    assert p.page.get_attribute("#ws-tab-i", "aria-selected") == "true"
    assert "giả định" in p.page.inner_text("#ws-pane-i") and "Chưa chạy" in p.page.inner_text("#ws-pane-i")
    p.page.click("#ws-run")
    p.page.wait_for_selector("#ws-pane-i .ws-sum")
    assert "không cộng vào tài sản ròng" in p.page.inner_text("#ws-pane-i")
    assert p.page.text_content('.wnode[data-n="SC:vni_30"] .wfig').startswith("nếu xảy ra −")
    assert p.page.text_content(".wme-v") == me  # a scenario never changes the actual net worth
    # the strip: the Toàn cảnh cards; a card focuses its lens; folding is remembered
    assert p.page.locator(".scard").count() == 5
    p.page.click('.scard[data-lens="dong-tien"] .pc-head')
    p.page.wait_for_function("location.hash === '#/client/xem/dong-tien'")
    p.page.click("#ws-strip-fold")
    assert p.page.is_hidden("#ws-strip-b")
    p.go("#/client/xem/tong-quan")
    assert p.page.is_hidden("#ws-strip-b")
    assert not p.problems()


def test_the_assistant_stream_drives_the_graph(open_page):
    p = open_page()
    p.go("#/client")
    p.page.wait_for_selector(".wnode.k-family")
    p.page.evaluate(
        """() => { window.__ev = []; const f0 = window.fetch;
             window.fetch = async (u, o) => { const r = await f0(u, o);
               if (!String(u).includes('/api/assistant/stream')) return r;
               const [a, b] = r.body.tee();
               (async () => { const rd = b.pipeThrough(new TextDecoderStream()).getReader();
                 for (;;) { const {value, done} = await rd.read(); if (done) break; window.__ev.push(value); } })();
               return new Response(a, {status: r.status, headers: r.headers}); }; }"""
    )
    p.page.fill("#cp-q", "Tháng này tôi chi bao nhiêu?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_selector("#cp-msgs .cp-bot:not([data-busy])")
    raw = "".join(p.page.evaluate("window.__ev"))
    assert '"phase": "start"' in raw and '"phase": "end"' in raw and '"type": "answer"' in raw  # the real stream
    p.page.wait_for_function("document.querySelectorAll('.wnode.kept').length > 0")
    assert p.page.locator(".wnode.act").count() == 0 and p.page.locator(".wnode.k-flow.ok").count() == 2
    assert not p.page.evaluate("document.querySelector('.ws-svg').classList.contains('busy')")
    assert not p.problems()


def test_a_broken_stream_is_said_and_marked_failed(open_page):
    p = open_page(reduced=True)
    p.ctx.add_init_script(STUB_BREAK)
    p.page.reload()  # the same address: a reload, so the stub is in before the app
    p.page.wait_for_selector(".wnode.k-family")
    p.page.fill("#cp-q", "Tháng này tôi chi bao nhiêu?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_selector(".cp-err")
    assert "Mất kết nối" in p.page.locator(".cp-err").last.inner_text()
    assert p.page.locator(".wnode.bad").count() == 2 and p.page.locator(".wnode.act").count() == 0
    assert p.page.locator(".wcomet").count() == 0  # reduced motion: no pulses


def test_keyboard_and_phone(open_page):
    p = open_page()
    p.go("#/client")
    p.page.focus('[data-tool="tong-quan"]')
    p.page.keyboard.press("ArrowDown")
    p.page.keyboard.press("Enter")
    p.page.wait_for_function("location.hash === '#/client/xem/tai-san'")
    p.page.locator(".wnode.k-class").first.focus()
    p.page.keyboard.press("Enter")
    assert p.page.get_attribute("#ws-tab-i", "aria-selected") == "true"
    phone = open_page("phone")
    phone.go("#/client")
    phone.page.wait_for_selector(".wnode.k-family")
    for lens in ("tai-san", "muc-tieu", "tin", "tong-quan"):
        phone.go(f"#/client/xem/{lens}")
        assert phone.page.evaluate(CLEAR) == [0, 0], lens
    phone.page.click(".ws-ask")
    phone.page.wait_for_function("document.activeElement && document.activeElement.id === 'cp-q'")
    phone.go("#/client/tai-san")  # a sheet on a phone takes the graph's place; the dock below stays reachable
    phone.page.locator("#cp-q").scroll_into_view_if_needed()
    on_top = """() => { const r = document.querySelector('#cp-q').getBoundingClientRect();
                         return document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)?.id; }"""
    assert phone.page.evaluate(on_top) == "cp-q"
    assert not phone.problems()  # no sideways scroll, no error


TIMED = """(() => { const real = window.fetch;
  window.fetch = (url, opts) => {
    if (!String(url).includes('/api/assistant/stream')) return real(url, opts);
    const enc = new TextEncoder(), ev = window.__script || [];
    const body = new ReadableStream({start(c) { let n = 0;
      for (const [t, e] of ev) setTimeout(() => {
        c.enqueue(enc.encode(`id: ${++n}\\ndata: ${JSON.stringify(e)}\\n\\n`));
        if (e.type === 'answer') c.close(); }, t); }});
    return Promise.resolve(new Response(body, {status: 200, headers: {'content-type': 'text/event-stream'}}));
  }; })();"""
SCRIPT = [
    [0, {"type": "start"}],
    [
        50,
        {
            "type": "step",
            "phase": "start",
            "call_id": "c1",
            "tool": "kich_ban",
            "label": "Kịch bản",
            "nodes": ["SC:vni_30"],
        },
    ],
    [
        50,
        {"type": "step", "phase": "start", "call_id": "c2", "tool": "muc_tieu", "label": "Mục tiêu", "nodes": ["goal"]},
    ],
    [1200, {"type": "step", "phase": "end", "call_id": "c2", "tool": "muc_tieu", "ok": False, "ms": 1100, "focus": []}],
    [
        2400,
        {
            "type": "step",
            "phase": "end",
            "call_id": "c1",
            "tool": "kich_ban",
            "ok": True,
            "ms": 2300,
            "focus": ["scenario:vni_30"],
            "scenario": {"id": "vni_30", "effect": -1820000000},
        },
    ],
    [2500, {"type": "text", "text": "Nếu VN-Index giảm 30%… "}],
    [
        4200,
        {
            "type": "answer",
            "assistant": {
                "status": "ok",
                "mode": "model",
                "text": "Mô phỏng xong.",
                "focus": ["scenario:vni_30"],
                "steps": [],
            },
        },
    ],
]
STATE = """() => ({hot: document.querySelectorAll('.wedge.hot').length,
  bad: document.querySelectorAll('.wedge.bad').length,
  comets: document.querySelectorAll('.wcomet').length, hollow: document.querySelectorAll('.wcomet.hollow').length,
  focusing: document.querySelector('.ws-svg').classList.contains('focusing'),
  writing: !!document.querySelector('.wnode.writing'), kept: document.querySelectorAll('.wnode.kept').length})"""


def test_the_dataflow_follows_the_stream_and_only_the_stream(open_page):
    """OWN-GW-16…18: nothing glows or runs before an event; a running tool's paths glow and the rest steps back; a
    failed read turns red and sends nothing; a scenario's read runs home hollow; the answer's paths stay until a
    background click (a scripted stream through the real panel)."""
    import json

    p = open_page()
    p.ctx.add_init_script(TIMED)
    p.ctx.add_init_script(f"window.__script = {json.dumps(SCRIPT)};")
    p.page.reload()
    p.go("#/client/xem/muc-tieu")
    p.page.wait_for_selector('.wnode[data-n="SC:vni_30"]')
    assert p.page.evaluate(STATE)["hot"] == 0 and p.page.evaluate(STATE)["comets"] == 0  # at rest: nothing moves
    p.page.fill("#cp-q", "Nếu VN-Index giảm mạnh thì sao?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function(
        "document.querySelectorAll('.wedge.hot').length >= 5"
    )  # the scenario's and the goals' spokes
    assert p.page.evaluate(STATE)["focusing"] and p.page.evaluate(STATE)["comets"] == 0  # running: no pulse yet
    p.page.wait_for_function("document.querySelectorAll('.wedge.bad').length === 4")  # the goals' read failed
    assert p.page.evaluate(STATE)["comets"] == 0  # a failure sends nothing home
    p.page.wait_for_function(
        "document.querySelectorAll('.wcomet.hollow').length > 0", timeout=4000
    )  # a hypothesis, hollow
    p.page.wait_for_function("!!document.querySelector('.wnode.k-family.writing')")
    p.page.wait_for_function("document.querySelectorAll('.wnode.kept').length > 0", timeout=6000)
    st = p.page.evaluate(STATE)
    assert st["hot"] >= 1 and st["bad"] == 4 and st["focusing"] and not st["writing"]
    p.page.mouse.click(
        *p.page.evaluate(
            "(() => { const r = document.querySelector('.ws-svg').getBoundingClientRect();"
            " return [r.left + 12, r.bottom - 12]; })()"
        )
    )
    p.page.wait_for_function("!document.querySelector('.ws-svg').classList.contains('focusing')")
    assert p.page.evaluate(STATE)["hot"] == 0 and not p.problems()
