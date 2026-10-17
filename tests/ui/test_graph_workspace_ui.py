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
    assert same(p) and shown["tai-san"] > shown["tong-quan"] > shown["muc-tieu"]
    assert (
        p.page.locator(".wnode.k-flow:not(.off)").count() == 2
        and p.page.locator(".wnode.k-liquidity:not(.off)").count() == 1
    )
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
    assert p.page.locator(".wspark").count() == 0  # reduced motion: no particles


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
    for lens in ("tai-san", "muc-tieu", "tong-quan"):
        phone.go(f"#/client/xem/{lens}")
    phone.page.click(".ws-ask")
    phone.page.wait_for_function("document.activeElement && document.activeElement.id === 'cp-q'")
    phone.go("#/client/tai-san")  # a sheet on a phone takes the graph's place; the dock below stays reachable
    phone.page.locator("#cp-q").scroll_into_view_if_needed()
    on_top = """() => { const r = document.querySelector('#cp-q').getBoundingClientRect();
                         return document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)?.id; }"""
    assert phone.page.evaluate(on_top) == "cp-q"
    assert not phone.problems()  # no sideways scroll, no error
