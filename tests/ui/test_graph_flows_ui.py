"""Data-driven flow animation (UNIFIED_FLOWS_PLAN F7/F8, OWN-GW-41…45): each money edge's sparks run the way the
money goes, more of them, faster, longer and brighter as the monthly amount grows; a relation never moves; an
estimate looks unlike a real transfer; off-screen or under a sheet everything pauses; under reduced motion nothing
moves. The amounts are read back from the overview the page drew, so the motion is checked against the data."""

import pytest

# per moving edge: its certainty, amount carried, sparks a beat (from the period), trail, opacity, the direction its
# sparks run (start and end of their path against the wire's) — and every wire that has no amount
SPARKS = r"""() => {
  const wire = (k) => document.querySelector(`.wedge[data-e="${k}"]`);
  const ends = (d) => [d.match(/^M(\S+)/)[1], d.match(/(\S+)$/)[1]];
  const out = {};
  for (const q of document.querySelectorAll('.ws-sparks .wspark')) {
    const k = q.dataset.e, w = wire(k), [ws, we] = ends(w.getAttribute('d')), [s, e] = ends(q.getAttribute('d'));
    const dur = parseFloat(q.style.animationDuration), cs = getComputedStyle(q);
    const o = out[k] ||= {cert: [...q.classList].find(c => c.startsWith('c-')), m: +q.dataset.m, n: 0, dur,
      trail: +q.style.getPropertyValue('--a'), so: +q.style.getPropertyValue('--so'),
      way: s === ws && e === we ? 'fwd' : s === we && e === ws ? 'back' : '?',
      dash: q.style.strokeDasharray.split(' ').slice(0, 5).join(' '), width: parseFloat(cs.strokeWidth),
      filter: cs.filter, glow: !!document.querySelector(`.ws-sparks .wglow[data-e="${k}"]`), stroke: cs.stroke,
      wire: getComputedStyle(w).stroke};
    o.n++;
  }
  return out;
}"""


def drawn(p):
    """Keep the overview the page draws from (POST /api/overview), as the server sent it."""
    seen = []
    p.page.on("response", lambda r: r.url.endswith("/api/overview") and r.ok and seen.append(r))
    return seen


def edges_of(seen):
    o = seen[-1].json()["overview"]
    return {f"{e['from']}>{e['to']}": e for e in o["edges"]}, {n["id"]: n for n in o["nodes"]}


@pytest.mark.parametrize("lens", ["tong-quan", "tin", "muc-tieu", "dong-tien"])
def test_sparks_run_the_way_the_money_goes_and_only_on_amounts(open_page, lens):
    p = open_page(theme="dark")
    seen = drawn(p)
    p.as_role("client", f"#/client/xem/{lens}")  # a new document, its overview kept
    p.page.wait_for_selector(".wnode.k-family")
    p.page.wait_for_timeout(300)
    got = p.page.evaluate(SPARKS)
    assert got, "money moves on every lens"
    edges, _ = edges_of(seen)
    for k, s in got.items():
        e = edges.get(k)
        if e is None:  # a derived spoke (a news or policy item's total) or a folded group: its wire says the amount
            assert s["m"] > 0 and s["way"] in ("fwd", "back"), (k, s)
            continue
        assert e["value"] is not None, (k, "a relation moved")
        if e.get("repaid") and s["cert"] == "c-actual" and s["way"] == "back":
            assert s["m"] == round(abs(e["repaid"])), (k, s)
            continue
        assert s["way"] == e["dir"], (k, s, e.get("dir"))  # the money's way, not the wire's
        assert s["m"] == round(abs(e.get("monthly") if e.get("monthly") is not None else e["value"])), (k, s, e)
    for k, e in edges.items():
        if e["value"] is None:
            assert k not in got, (k, "a relation implies no transfer")
    assert not p.problems()


def test_a_bigger_monthly_amount_moves_more_faster_longer_brighter(open_page):
    p = open_page(theme="dark")
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wspark")
    got = p.page.evaluate(SPARKS)
    for cert in ("c-actual", "c-estimate"):
        rows = sorted((s for s in got.values() if s["cert"] == cert), key=lambda s: s["m"])
        for a, b in zip(rows, rows[1:]):
            if b["m"] > a["m"]:
                assert b["trail"] >= a["trail"] and b["so"] >= a["so"], (a, b)
    income, spending = got["FL:in>ME"], got["ME>FL:out"]
    assert income["m"] > spending["m"] > 0
    assert income["trail"] > spending["trail"] and income["so"] > spending["so"]
    p.go("#/client/xem/tin")
    p.page.wait_for_selector(".wspark.c-estimate")
    news = sorted((s for s in p.page.evaluate(SPARKS).values() if s["cert"] == "c-estimate"), key=lambda s: s["m"])
    assert news[-1]["m"] > news[0]["m"] and news[-1]["trail"] > news[0]["trail"]
    assert not p.problems()


def test_an_estimate_does_not_look_like_a_real_transfer(open_page):
    p = open_page(theme="dark")
    p.go("#/client/xem/tin")
    p.page.wait_for_selector(".wspark.c-estimate")
    got = p.page.evaluate(SPARKS)
    actual = [s for s in got.values() if s["cert"] == "c-actual"]
    estimate = [s for s in got.values() if s["cert"] == "c-estimate"]
    assert actual and estimate
    assert all(s["glow"] for s in actual)  # a real transfer glows (a faint wider stroke under its core)
    assert not any(s["glow"] for s in estimate)  # an estimate does not: even dashes, dimmer
    assert {len(set(s["dash"].split())) for s in estimate} == {3}  # dash, gap, the last gap: no bright head
    assert max(s["so"] for s in estimate) <= 0.72 < max(s["so"] for s in actual)  # at most ¾ of a transfer's light
    assert not p.problems()


# the graph's looping animations still running (a transition finishing is not activity: it ends by itself)
PLAYING = """() => document.getAnimations().filter(a => a instanceof CSSAnimation && a.playState === 'running'
  && a.effect.target.closest && a.effect.target.closest('.ws-canvas')).length"""


def test_everything_pauses_off_screen_and_under_a_sheet(open_page):
    p = open_page(theme="dark")
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_selector(".wspark")
    p.page.wait_for_timeout(200)
    assert p.page.evaluate(PLAYING) > 0
    p.go("#/client/tong-quan/toan-canh")  # a sheet over the graph
    p.page.wait_for_function("document.querySelector('.ws-svg').classList.contains('asleep')")
    assert p.page.evaluate(PLAYING) == 0
    p.go("#/client/xem/tong-quan")
    p.page.wait_for_function("!document.querySelector('.ws-svg').classList.contains('asleep')")
    assert p.page.evaluate(PLAYING) > 0
    p.page.set_viewport_size({"width": 390, "height": 844})  # the phone's graph scrolled away
    p.page.evaluate("document.querySelector('.ws-canvas').style.marginTop = '3000px'")
    p.page.wait_for_function("document.querySelector('.ws-svg').classList.contains('asleep')")
    assert p.page.evaluate(PLAYING) == 0
    assert not [e for e in p.problems() if "horizontal" not in e]


def test_nothing_moves_under_reduced_motion(open_page):
    p = open_page(reduced=True, theme="dark")
    for lens in ("tong-quan", "tin"):
        p.go(f"#/client/xem/{lens}")
        p.page.wait_for_selector(".wedge")
        shown = "[...document.querySelectorAll('.wspark')].filter(s => getComputedStyle(s).display !== 'none').length"
        assert p.page.evaluate(shown) == 0
    assert not p.problems()


LAYER = """() => { const s = document.querySelector('.ws-svg'), f = document.querySelector('.ws-fxsvg');
  const moving = [...f.querySelectorAll('.wspark, .wglow')];
  const quiet = [...document.querySelectorAll('.wedge.money:not(.on):not(.hot)')];
  return {same_box: s.getAttribute('viewBox') === f.getAttribute('viewBox'),
          same_view: s.querySelector('.ws-world').getAttribute('transform')
            === f.firstElementChild.getAttribute('transform'),
          events: getComputedStyle(f).pointerEvents, inside: f.parentElement === s.parentElement,
          stray: s.querySelectorAll('.wspark, .wglow').length,
          filters: moving.filter(q => getComputedStyle(q).filter !== 'none').length,
          edge: Math.max(...quiet.map(q => +getComputedStyle(q).strokeOpacity))}; }"""


def test_a_spark_stands_off_its_edge_on_its_own_layer_without_filters(open_page):
    """The energy flow, tuned against measurement (docs/brd/testing/ui/flows_perf.md): the sparks sit on their own layer
    (same viewBox and pan/zoom as the graph, no pointer events) so a moving dash repaints only that layer; no spark or
    glow carries a CSS filter (two drop-shadows per spark were 61% of the graph's CPU); a spark's core is not its
    edge's colour (it stands off the line), but keeps its hue; static edges stay quieter than what moves on them; a
    bigger monthly flow draws a wider core, and the smallest still shows."""
    for theme in ("dark", "light"):
        p = open_page(theme=theme)
        p.go("#/client/xem/tong-quan")
        p.page.wait_for_selector(".wspark")
        p.page.click("[data-z='in']")  # zoomed: the spark layer follows the graph's pan and zoom
        p.page.wait_for_timeout(300)
        layer = p.page.evaluate(LAYER)
        assert layer["same_box"] and layer["same_view"] and layer["inside"], layer
        assert layer["events"] == "none" and layer["stray"] == 0 and layer["filters"] == 0, layer
        got = p.page.evaluate(SPARKS)
        for k, s in got.items():
            assert s["stroke"] != s["wire"], (theme, k, s)  # the core stands off its line
            assert s["cert"] == "c-hypothetical" or s["so"] >= 0.42, (theme, k, s)  # the smallest flow still shows
        assert layer["edge"] < min(s["so"] for s in got.values()), (
            theme,
            layer,
            got,
        )  # the line quieter than its spark
        income, spending = got["FL:in>ME"], got["ME>FL:out"]
        assert income["m"] > spending["m"] and income["width"] > spending["width"]
        assert not p.problems()
