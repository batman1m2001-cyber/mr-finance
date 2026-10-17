"""The graph's layout and routing (OWN-GW-26…32, GRAPH_CORE_LAYOUT_PLAN.md): on every lens, desktop and phone, idle
and with a node of each kind picked, nothing overlaps — discs, labels, a label on a disc — no edge passes through a
node or a label, no two strong edges cross, no label hides for lack of room and nothing leaves the canvas. A graph
three times the demo client's folds its smallest items into group nodes instead of squeezing them. A pick outside
Tài sản, and an answer, move nothing; a lens switch keeps the order around the ring. Measured in screen pixels."""

import json

import pytest

LENSES = ("tong-quan", "tai-san", "dong-tien", "muc-tieu", "tin", "rui-ro")
COUNTS = ("discs", "labels", "labelOnDisc", "edgeThroughNode", "edgeThroughLabel", "cross", "quiet", "outside", "loose")

AUDIT = r"""() => {
  const shown = (el) => { for (let x = el; x && x.tagName !== 'svg'; x = x.parentNode) { const s = getComputedStyle(x);
    if (s.display === 'none' || +s.opacity < 0.05) return false; } return true; };
  const svg = document.querySelector('.ws-svg').getBoundingClientRect();
  const nodes = [...document.querySelectorAll('.wnode:not(.off):not(.gone)')].filter(shown);
  const discs = nodes.map(n => { const r = n.querySelector('.wcore').getBoundingClientRect(); return {id: n.dataset.n,
    x: r.left + r.width / 2, y: r.top + r.height / 2, r: r.width / 2}; });
  const labels = nodes.flatMap(n => [...n.querySelectorAll('.wlbl, .wfig, .wtag, .wme-l, .wme-v, .wme-s')]
    .filter(t => t.textContent.trim() && +getComputedStyle(t).opacity > 0.4 && shown(t))
    .map(t => { const r = t.getBoundingClientRect(); return {id: n.dataset.n, l: r.left, t: r.top, r: r.right, b:
      r.bottom}; })).filter(b => b.r > b.l);
  const edges = [...document.querySelectorAll('.ws-edges .wedge')].filter(shown).map(p => {
    const m = p.getScreenCTM(), L = p.getTotalLength(), n = Math.max(8, Math.round(L / 5)), pts = [];
    for (let i = 0; i <= n; i++) { const q = p.getPointAtLength(L * i / n); pts.push([m.a * q.x + m.c * q.y + m.e, m.b
      * q.x + m.d * q.y + m.f]); }
    return {ends: p.dataset.e.split('>'), pts, faint: p.classList.contains('faint') || +getComputedStyle(p).opacity <
      0.3};
  });
  const out = {nodes: discs.length, edges: edges.length, discs: 0, labels: 0, labelOnDisc: 0, edgeThroughNode: 0,
    edgeThroughLabel: 0, cross: 0, outside: 0, loose: 0, ex: [],
    quiet: nodes.filter(n => n.classList.contains('quiet') && !n.classList.contains('k-holding')).length};
  const note = (s) => { if (out.ex.length < 6) out.ex.push(s); };
  for (let i = 0; i < discs.length; i++) for (let j = i + 1; j < discs.length; j++) {
    const a = discs[i], b = discs[j]; if (Math.hypot(a.x - b.x, a.y - b.y) < a.r + b.r - 1) { out.discs++; note('disc '
      + a.id + ' x ' + b.id); } }
  const ov = (a, b) => a.l < b.r - 1 && b.l < a.r - 1 && a.t < b.b - 1 && b.t < a.b - 1;
  for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++)
    if (labels[i].id !== labels[j].id && ov(labels[i], labels[j])) { out.labels++; note('label ' + labels[i].id + ' x '
      + labels[j].id); }
  for (const lb of labels) {
    if (lb.l < svg.left - 1 || lb.r > svg.right + 1 || lb.t < svg.top - 1 || lb.b > svg.bottom + 1) { out.outside++;
      note('outside ' + lb.id); }
    for (const d of discs) if (d.id !== lb.id) {
      const cx = Math.max(lb.l, Math.min(d.x, lb.r)), cy = Math.max(lb.t, Math.min(d.y, lb.b));
      if (Math.hypot(cx - d.x, cy - d.y) < d.r - 1) { out.labelOnDisc++; note('label ' + lb.id + ' on ' + d.id); } } }
  for (const d of discs) if (d.x - d.r < svg.left - 1 || d.x + d.r > svg.right + 1 || d.y - d.r < svg.top - 1 || d.y +
    d.r > svg.bottom + 1) { out.outside++; note('outside disc ' + d.id); }
  for (const e of edges) {  // each end of an edge meets its node's rim (within 4 px), never short of it
    for (const id of e.ends) { const d = discs.find(x => x.id === id); if (!d) continue;
      const gap = Math.min(...[e.pts[0], e.pts[e.pts.length - 1]].map(([x, y]) => Math.abs(Math.hypot(x - d.x, y - d.y)
        - d.r)));
      if (gap > 4) { out.loose++; note('edge ' + e.ends.join('>') + ' short of ' + id + ' by ' + Math.round(gap)); } }
    for (const d of discs) if (!e.ends.includes(d.id) && e.pts.some(([x, y]) => Math.hypot(x - d.x, y - d.y) < d.r -
      1)) { out.edgeThroughNode++; note('edge ' + e.ends.join('>') + ' through ' + d.id); }
    if (e.faint) continue;
    for (const lb of labels) if (!e.ends.includes(lb.id) && e.pts.some(([x, y]) => x > lb.l + 1 && x < lb.r - 1 && y >
      lb.t + 1 && y < lb.b - 1)) { out.edgeThroughLabel++; note('edge ' + e.ends.join('>') + ' through label ' +
        lb.id); }
  }
  const X = (a, b, c, d) => { const o = (p, q, r) => Math.sign((q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0]));
    return o(a,b,c) * o(a,b,d) < 0 && o(c,d,a) * o(c,d,b) < 0; };
  const strong = edges.filter(e => !e.faint);
  for (let i = 0; i < strong.length; i++) for (let j = i + 1; j < strong.length; j++) {
    const A = strong[i], C = strong[j]; if (A.ends.some(x => C.ends.includes(x))) continue;
    let hit = false;
    for (let s = 0; s < A.pts.length - 1 && !hit; s++) for (let t = 0; t < C.pts.length - 1 && !hit; t++) if
      (X(A.pts[s], A.pts[s+1], C.pts[t], C.pts[t+1])) hit = true;
    if (hit) { out.cross++; note('cross ' + A.ends.join('>') + ' x ' + C.ends.join('>')); }
  }
  return out;
}"""

PLACES = """() => Object.fromEntries([...document.querySelectorAll('.wnode:not(.off):not(.gone)')]
  .map(n => [n.dataset.n, n.style.transform]))"""
PICK = """(i) => document.querySelector(`.wnode[data-n="${CSS.escape(i)}"]`)
  .dispatchEvent(new MouseEvent('click', {bubbles: true}))"""
# one node of each kind on screen (the centre aside): the picks the audit makes
ONE_OF_EACH = """() => { const seen = {}; for (const n of document.querySelectorAll('.wnode:not(.off):not(.gone)')) {
  const k = [...n.classList].find(c => c.startsWith('k-')); if (k !== 'k-family' && !seen[k]) seen[k] = n.dataset.n; }
  return Object.values(seen); }"""

CLASSES = "() => [...document.querySelectorAll('.wnode.k-class:not(.off):not(.gone)')].map(n => n.dataset.n)"


def times(overview, x):
    """``overview`` with every item but the centre, the cash flow, the reserve and the risks copied ``x`` times."""
    nodes, edges = list(overview["nodes"]), list(overview["edges"])
    keep = lambda i: i == "ME" or i.startswith(("FL:", "LQ:", "RK:"))  # noqa: E731
    for k in range(1, x):
        ren = lambda i: i if keep(i) else f"{i}~{k}"  # noqa: E731
        for n in overview["nodes"]:
            if not keep(n["id"]):
                m = {**n, "id": ren(n["id"]), "label": f"{n['label']} {k + 1}"}
                for key in ("parent", "ref"):
                    if m.get(key):
                        m[key] = ren(m[key]) if key == "parent" else f"{m[key]}~{k}"
                nodes.append(m)
        for e in overview["edges"]:
            if not (keep(e["from"]) and keep(e["to"])):
                f = {**e, "from": ren(e["from"]), "to": ren(e["to"])}
                for key in ("agg", "parent"):
                    if f.get(key):
                        f[key] = ren(f[key])
                edges.append(f)
    return {**overview, "nodes": nodes, "edges": edges}


def dense(p, x):
    def fulfil(route):
        r = route.fetch()
        body = r.json()
        body["overview"] = times(body["overview"], x)
        route.fulfill(response=r, json=body)

    p.ctx.route("**/api/overview", fulfil)


def clear(m):
    return {k: m[k] for k in COUNTS if m[k]}


def lens(p, name):
    p.go(f"#/client/xem/{name}")
    p.page.wait_for_timeout(700)  # the nodes' slide and the edges drawn where they arrive


ACTIVE = ["vni_30", "rates_up"]  # two stress tests on (UNIFIED_FLOWS_PLAN F6): they show on Tổng quan and Mục tiêu


@pytest.mark.parametrize("size,active", [("desktop", []), ("phone", []), ("desktop", ACTIVE), ("phone", ACTIVE)],
                         ids=["desktop", "phone", "desktop-scenarios", "phone-scenarios"])  # fmt: skip
def test_every_lens_is_clear_idle_and_with_a_pick(open_page, size, active):
    p = open_page(size)
    if active:
        keep = json.dumps({"ids": active, "params": {}})
        p.ctx.add_init_script(f"try {{ localStorage.setItem('mf.ws.scn.C01', {json.dumps(keep)}); }} catch (_) {{}}")
        p.page.reload()
    p.go("#/client")
    p.page.wait_for_selector(".wnode.k-family")
    if active:
        p.page.wait_for_selector(f'.wnode.live[data-n="SC:{active[-1]}"]', state="attached")
    bad = {}
    for name in LENSES if not active else ("tong-quan", "muc-tieu"):
        lens(p, name)
        m = p.page.evaluate(AUDIT)
        if clear(m):
            bad[f"{name} idle"] = (clear(m), m["ex"])
        picks = p.page.evaluate(ONE_OF_EACH)
        if name == "tai-san":  # every class opens to its holdings here, wherever it sits on the ring (corners differ)
            picks += [i for i in p.page.evaluate(CLASSES) if i not in picks]
        for i in picks:
            p.page.evaluate(PICK, i)
            p.page.wait_for_timeout(560)
            m = p.page.evaluate(AUDIT)
            if clear(m):
                bad[f"{name} {i}"] = (clear(m), m["ex"])
            pressed = "(i) => document.querySelector(`.wnode[data-n=\"${CSS.escape(i)}\"]`)?.ariaPressed"
            if p.page.evaluate(pressed, i) == "true":
                p.page.evaluate(PICK, i)
                p.page.wait_for_timeout(480)
    assert not bad, json.dumps(bad, ensure_ascii=False, indent=1)
    assert not p.problems()


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_a_dense_graph_folds_instead_of_squeezing(open_page, size):
    p = open_page(size)
    dense(p, 3)
    p.go("#/client")
    p.page.wait_for_selector(".wnode.k-family")
    bad, folded = {}, 0
    for name in ("tong-quan", "tai-san", "tin"):
        lens(p, name)
        m = p.page.evaluate(AUDIT)
        folded += p.page.locator(".wnode.k-group:not(.off):not(.gone)").count()
        if clear(m):
            bad[name] = (clear(m), m["ex"])
    assert not bad, json.dumps(bad, ensure_ascii=False, indent=1)
    assert folded, "three times the items, and nothing folded: they were squeezed"
    lens(p, "tong-quan")  # a group opens on a click (another may fold to make room), and the graph stays clear
    gid = p.page.locator(".wnode.k-group:not(.off)").first.get_attribute("data-n")
    p.page.evaluate(PICK, gid)
    p.page.wait_for_timeout(700)
    closer = p.page.locator(f'.wnode[data-n="{gid}:close"]:not(.off)')
    assert closer.count() == 1, "the group opened: its “Thu gọn” shows"
    assert not clear(p.page.evaluate(AUDIT))
    p.page.evaluate(PICK, f"{gid}:close")
    p.page.wait_for_timeout(700)
    assert p.page.locator(f'.wnode[data-n="{gid}"]:not(.off)').count() == 1, "closed again: folded again"
    assert not p.problems()


ANSWER = """(() => { const real = window.fetch;
  window.fetch = (url, opts) => {
    if (!String(url).includes('/api/assistant/stream')) return real(url, opts);
    const enc = new TextEncoder();
    const ev = [{type: 'start'},
      {type: 'step', phase: 'start', call_id: 'c1', tool: 'tong_quan', label: 'Tổng quan', nodes: ['ME', 'class',
        'event']},
      {type: 'step', phase: 'end', call_id: 'c1', tool: 'tong_quan', ok: true, ms: 40, focus: ['kpi:net_worth']},
      {type: 'answer', assistant: {status: 'ok', mode: 'template', text: 'Tài sản ròng.', focus: ['kpi:net_worth'],
        steps: []}}];
    const body = new ReadableStream({start(c) { ev.forEach((e, i) =>
      c.enqueue(enc.encode(`id: ${i + 1}\\ndata: ${JSON.stringify(e)}\\n\\n`))); c.close(); }});
    return Promise.resolve(new Response(body, {status: 200, headers: {'content-type': 'text/event-stream'}}));
  }; })();"""
ORDER = """() => { const c = document.querySelector('.wnode.k-family').getBoundingClientRect();
  const cx = c.left + c.width / 2, cy = c.top + c.height / 2;
  return [...document.querySelectorAll('.wnode:not(.off):not(.gone):not(.k-family):not(.k-holding)')].map(n => {
    const r = n.querySelector('.wcore').getBoundingClientRect(); return [n.dataset.n, Math.atan2(r.top + r.height / 2 -
      cy, r.left + r.width / 2 - cx)]; })
    .sort((a, b) => a[1] - b[1]).map(x => x[0]); }"""


def cyclic(order, ids):
    """``order`` kept to ``ids``, rotated to start at its first: the order around the ring."""
    o = [i for i in order if i in ids]
    k = o.index(min(o)) if o else 0
    return o[k:] + o[:k]


def test_the_layout_holds_still(open_page):
    p = open_page()
    p.ctx.add_init_script(ANSWER)
    p.page.reload()  # the stub is installed on a new document only
    p.go("#/client")
    p.page.wait_for_selector(".wnode.k-family")
    lens(p, "tong-quan")
    at = p.page.evaluate(PLACES)
    # a pick outside Tài sản moves nothing
    for i in [i for i in p.page.evaluate(ONE_OF_EACH) if not i.startswith("GR:")]:
        p.page.evaluate(PICK, i)
        p.page.wait_for_timeout(300)
        assert p.page.evaluate(PLACES) == at, f"picking {i} moved the graph"
        p.page.evaluate(PICK, i)
    p.page.click("#ws-tab-a")  # the dock shows the inspector after a pick: back to the assistant
    p.page.fill("#cp-q", "Tài sản của tôi thế nào?")
    p.page.press("#cp-q", "Enter")
    p.page.wait_for_selector(".wnode.kept")
    assert p.page.evaluate(PLACES) == at, "an answer moved the graph"
    ring = p.page.evaluate(ORDER)
    for name in ("tin", "rui-ro", "dong-tien", "tong-quan"):  # a lens switch keeps the order around the ring
        lens(p, name)
        now = p.page.evaluate(ORDER)
        shared = set(now) & set(ring)
        assert cyclic(now, shared) == cyclic(ring, shared), name
    assert p.page.evaluate(PLACES) == at, "back on Tổng quan, the graph is where it was"
    assert not p.problems()


VIEW = "() => document.querySelector('.ws-world').getAttribute('transform')"
IN_VIEW = """(ids) => { const s = document.querySelector('.ws-svg').getBoundingClientRect();
  return ids.map(i => { const r =
    document.querySelector(`.wnode[data-n="${CSS.escape(i)}"] .wcore`).getBoundingClientRect();
    return r.left >= s.left - 1 && r.right <= s.right + 1 && r.top >= s.top - 1 && r.bottom <= s.bottom + 1; }); }"""


def test_focus_fits_the_selection_and_keeps_the_rest_in_sight(open_page):
    p = open_page()
    p.go("#/client/xem/tin")
    news = ".wnode:is(.k-event, .k-alert):not(.off):not(.gone)"
    p.page.wait_for_selector(news)
    assert p.page.is_disabled("[data-z=focus]")  # nothing picked: nothing to focus on
    ev = p.page.locator(news).first.get_attribute("data-n")
    p.page.evaluate(PICK, ev)
    p.page.wait_for_timeout(500)
    near = p.page.evaluate("""(i) => [...document.querySelectorAll('.ws-edges .wedge:not(.faint)')]
      .map(e => e.dataset.e.split('>')).filter(x => x.includes(i)).flat()""", ev)
    fit = p.page.evaluate(VIEW)
    p.page.click("[data-z=focus]")
    v = p.page.evaluate(VIEW)
    assert v != fit, v  # the view moved to the selection (zoomed in as far as its neighbourhood allows)
    assert all(p.page.evaluate(IN_VIEW, sorted(set(near)))), "the selection and its neighbours fit the view"
    assert p.page.locator(".wnode.dim:not(.off)").count() > 0  # the rest stays drawn, dimmed: context kept
    p.page.focus(".ws-svg")
    p.page.keyboard.press("0")  # Vừa khung, from the keyboard
    assert p.page.evaluate(VIEW) == fit
    p.page.focus(f'.wnode[data-n="{ev}"]')
    p.page.keyboard.press("f")  # and focus again, from the node
    assert p.page.evaluate(VIEW) == v
    assert not p.problems()


EDGES = """() => [...document.querySelectorAll('.ws-edges .wedge')].map(e => ({e: e.dataset.e, cls: [...e.classList],
  shown: +getComputedStyle(e).strokeOpacity * +getComputedStyle(e).opacity,
  dash: getComputedStyle(e).strokeDasharray}))"""


def test_the_edges_say_what_they_are_and_only_the_picked_ones_stand_out(open_page):
    p = open_page(theme="dark")
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".ws-edges .wedge.money")
    p.page.wait_for_timeout(600)
    es = p.page.evaluate(EDGES)
    of = lambda c: [e["shown"] for e in es if c in e["cls"]]  # noqa: E731
    plain = [e["shown"] for e in es if not {"money", "sum", "faint"} & set(e["cls"])]
    assert of("money") and of("sum") and plain, es
    assert min(of("money")) > max(plain) > max(of("sum")), es  # money first, holdings and classes, then summaries
    assert all((e["dash"] == "none") == ("c-actual" in e["cls"]) for e in es), es  # estimates dashed, hypotheses dotted
    p.page.evaluate(PICK, "FL:in")  # a pick: its own edges stand out, the rest drop to a trace
    p.page.wait_for_timeout(500)
    es = p.page.evaluate(EDGES)
    mine = [e for e in es if "FL:in" in e["e"].split(">")]
    rest = [e for e in es if "FL:in" not in e["e"].split(">")]
    assert mine and all(e["shown"] > 0.5 for e in mine), mine
    assert rest and all(e["shown"] < 0.1 for e in rest), [e for e in rest if e["shown"] >= 0.1]
    assert not p.problems()
