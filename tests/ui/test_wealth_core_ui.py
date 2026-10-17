"""The central wealth core (OWN-GW-20…25, GRAPH_CORE_LAYOUT_PLAN.md §3): its ports light when a spark reaches the rim
(income) or leaves it (spending, repayments), read off the animations' own clocks; the out-flows leave on the income's
beat; its states follow the real events (selected, a tool running, the answer streaming, a flow picked); nothing of it
moves under reduced motion; the net worth keeps ≥ 7:1 contrast against the core behind it, whatever the light does."""

import io

import pytest

# the next arrival (spark head at the path's end) and departure (head at its start) of each money edge's sparks, the
# next peak of each port, and each edge's period — from the running animations (seconds)
CLOCKS = r"""() => {
  const ws = (el, name) => el.getAnimations().find(a => a.animationName === name);
  const out = {};
  for (const q of document.querySelectorAll('.ws-sparks .wspark')) {
    const a = ws(q, 'ws-money'); if (!a) continue;
    const t = a.effect.getComputedTiming(), dur = t.duration / 1000, loc = t.progress * dur, len = q.getTotalLength();
      // progress counts the delay
    const SL = +q.style.getPropertyValue('--a');  // its dash pattern, end to end: it scales with the amount (F7)
    const v = (len + SL) / dur, f = v * loc;
    const arr = f <= len ? (len - f) / v : dur - (f - len) / v, dep = dur - loc;
    const k = q.dataset.e, e = out[k] ||= {arr: [], dep: [], dur};
    e.arr.push(arr); e.dep.push(dep);
  }
  for (const p of document.querySelectorAll('.wport')) {
    const a = ws(p, 'ws-port'); if (!a) continue;
    const t = a.effect.getComputedTiming(), per = t.duration / 1000, loc = t.progress * per;
    const e = out[p.dataset.e] ||= {};
    e.port = per - loc; e.per = per;
  }
  const b = document.querySelector('.wme-band');
  const ba = b && ws(b, 'ws-band');
  if (ba) { const t = ba.effect.getComputedTiming(), per = t.duration / 1000; out.band = {next: per - t.progress * per,
    per}; }
  return out;
}"""


def near(x, y, period, tol=0.02):
    d = (x - y) % period
    return min(d, period - d) <= tol


def test_the_ports_and_the_band_keep_the_sparks_beat(open_page):
    p = open_page(theme="dark")
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wport")
    p.page.wait_for_timeout(400)
    c = p.page.evaluate(CLOCKS)
    income, spending = c["FL:in>ME"], c["ME>FL:out"]
    # each port lights on its own sparks: income as one arrives, spending as one leaves
    assert near(income["port"], min(income["arr"]), income["per"]), income
    assert near(spending["port"], min(spending["dep"]), spending["per"]), spending
    # the band crosses the core on an income arrival, and the spending leaves .36 s later (one clock)
    assert near(c["band"]["next"], min(income["arr"]), income["per"]), (c["band"], income)
    step = min(income["per"], spending["per"])
    assert near(min(spending["dep"]) - min(income["arr"]), 0.36, step, 0.03), (income, spending)
    for k, e in c.items():  # a repayment runs on the beat too, and its port with it
        if k.startswith(("CL:", "GR:")) and "port" in e:
            assert near(e["port"], min(e["dep"]), e["per"]), (k, e)
    assert not p.problems()


STREAM = """(() => { const real = window.fetch;
  window.fetch = (url, opts) => {
    if (!String(url).includes('/api/assistant/stream')) return real(url, opts);
    const enc = new TextEncoder(), ev = [{type: 'start'},
      {type: 'step', phase: 'start', call_id: 'c1', tool: 'tong_quan', label: 'Tổng quan', nodes: ['ME', 'class']}];
    const later = [[900, {type: 'step', phase: 'end', call_id: 'c1', tool: 'tong_quan', ok: true, ms: 900, focus:
      ['kpi:net_worth']}],
      [1000, {type: 'text', text: 'Tài sản '}], [1500, {type: 'text', text: 'ròng tăng.'}],
      [2600, {type: 'answer', assistant: {status: 'ok', mode: 'model', text: 'Tài sản ròng tăng.', focus:
        ['kpi:net_worth'], steps: []}}]];
    const body = new ReadableStream({start(c) { let n = 0;
      ev.forEach(e => c.enqueue(enc.encode(`id: ${++n}\\ndata: ${JSON.stringify(e)}\\n\\n`)));
      for (const [t, e] of later) setTimeout(() => {
        c.enqueue(enc.encode(`id: ${++n}\\ndata: ${JSON.stringify(e)}\\n\\n`)); if (e.type === 'answer') c.close(); },
          t); }});
    return Promise.resolve(new Response(body, {status: 200, headers: {'content-type': 'text/event-stream'}}));
  }; })();"""
OPACITY = "(s) => +getComputedStyle(document.querySelector(s)).opacity"


def test_the_core_answers_selection_the_assistant_and_a_flow(open_page):
    p = open_page(theme="dark")
    p.ctx.add_init_script(STREAM)
    p.page.reload()  # the stub is installed on a new document only
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wnode.k-family .wme-aura")
    aura = """document.querySelector('.wme-aura').getAnimations()
      .map(a => a.animationName + ' ' + a.effect.getTiming().duration)"""
    assert p.page.evaluate(aura) == ["ws-breathe 7000"]  # idle: the slow breath
    assert p.page.evaluate(OPACITY, ".wme-sel") == 0
    p.page.click(".wnode.k-family .wme-l")  # selected: the accent ring, the aura still
    p.page.wait_for_function("+getComputedStyle(document.querySelector('.wme-sel')).opacity > .9")
    assert p.page.evaluate(aura) == []
    p.page.click(".wnode.k-family .wme-l")
    p.page.click("#ws-tab-a")
    p.page.fill("#cp-q", "Tài sản ròng của tôi?")
    p.page.press("#cp-q", "Enter")  # a tool running: the rim takes the data colour and breathes faster
    p.page.wait_for_function("document.querySelector('.ws-svg').classList.contains('busy')")
    p.page.wait_for_function("+getComputedStyle(document.querySelector('.wme-act')).opacity > .3")
    assert p.page.evaluate("getComputedStyle(document.querySelector('.wme-act')).stroke") == p.page.evaluate(
        "getComputedStyle(document.querySelector('.wburst')).stroke"
    )  # --pulse, the data colour
    p.page.wait_for_selector(".wme-ripple", state="attached", timeout=4000)  # streaming: a ripple per text event
    p.page.wait_for_selector(".wnode.k-family.kept")
    p.page.wait_for_function("!document.querySelector('.wme-ripple')", timeout=4000)  # ripples leave, none stays
    p.page.evaluate("""document.querySelector('.wnode[data-n="FL:in"]')
      .dispatchEvent(new MouseEvent('click', {bubbles: true}))""")
    p.page.wait_for_selector(".wnode.k-family.flow")  # a flow picked: the core leans toward it
    band, flow_in = p.page.evaluate("""() => [getComputedStyle(document.querySelector('.wme-band')).fill,
      getComputedStyle(document.querySelector('.wglow[data-e="FL:in>ME"]')).stroke]""")  # the flow's own tone
    assert band == flow_in
    assert p.page.locator(".wport.faint").count() >= 1  # the other flows' ports step back
    assert not p.problems()


def test_nothing_of_the_core_moves_under_reduced_motion(open_page):
    p = open_page(reduced=True, theme="dark")
    p.ctx.add_init_script(STREAM)
    p.page.reload()  # the stub is installed on a new document only
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wnode.k-family .wme-aura")
    p.page.wait_for_timeout(300)
    moving = """() => document.getAnimations().filter(a => a.playState === 'running' && a.effect && a.effect.target
      && a.effect.target.closest && a.effect.target.closest('.wnode.k-family, .ws-edges'))
      .map(a => a.animationName || 'web')"""
    assert p.page.evaluate(moving) == []
    p.page.click("#ws-tab-a")
    p.page.fill("#cp-q", "Tài sản ròng của tôi?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_function("document.querySelector('.ws-svg').classList.contains('busy')")
    assert p.page.evaluate(OPACITY, ".wme-act") > 0.5  # thinking: a still rim in the data colour
    p.page.wait_for_selector(".wnode.k-family.kept")
    assert p.page.evaluate(moving) == [] and p.page.locator(".wme-ripple").count() == 0
    assert not p.problems()


def luminance(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (ch(x) for x in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_the_net_worth_stays_readable_whatever_the_light(open_page, theme):
    Image = pytest.importorskip("PIL.Image")
    p = open_page(theme=theme)
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wnode.k-family .wme-v")
    box = p.page.locator(".wme-v").bounding_box()
    p.page.add_style_tag(content=".ws-svg .wme-v { opacity: 0 !important; }")  # the background behind the figure
    worst = 0
    for _ in range(8):  # through a beat and the breath: the brightest the core gets behind the figure
        shot = Image.open(io.BytesIO(p.page.screenshot(clip=box))).convert("RGB")
        raw = shot.tobytes()
        worst = max(worst, max(luminance(raw[i : i + 3]) for i in range(0, len(raw), 3)))
        p.page.wait_for_timeout(140)
    contrast = (1.0 + 0.05) / (worst + 0.05)
    assert contrast >= 7, f"{theme}: {contrast:.1f}:1"
