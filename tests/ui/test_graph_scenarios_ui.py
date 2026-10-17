"""Scenarios on the graph (UNIFIED_FLOWS_PLAN F5/F6, OWN-GW-37…40): turning stress tests on makes them active; the
bar shows the server's combined figure (POST /api/scenario/combine) while the net worth on the core stays the real
one; turning one off recombines the rest; the set survives a reload; only an active scenario's hypothetical edges
move; its trace in Thông tin runs assumptions → classes → debt and spending → liquidity → projected net worth → goals;
the person's own what-if takes their inputs within the server's bounds."""

import pytest

KEY = "mf.ws.scn.C01"
BAR = """() => { const b = document.querySelector('#ws-scn'); if (!b || b.hidden) return null;
  const v = (k) => { const e = b.querySelector(`[data-scn="${k}"]`); return e ? +e.dataset.v : null; };
  const chips = [...b.querySelectorAll('.ws-chip [data-n]')].map(x => x.dataset.n);
  return {after: v('after'), change: v('change'), chips}; }"""
MOVING = """() => [...new Set([...document.querySelectorAll('.wspark.c-hypothetical')].map(q => q.dataset.e))].sort()"""


def fresh(open_page, size="desktop"):
    p = open_page(size=size, theme="dark")
    p.go("#/client/xem/muc-tieu")
    p.page.evaluate(f"localStorage.removeItem('{KEY}')")
    p.page.reload()
    p.page.wait_for_selector(".wnode.k-family")
    return p


def pick(p, node):
    """Select a node through the list view (a folded node is in it too), then go back to the graph."""
    p.page.click('[data-v="list"]')
    p.page.click(f'#ws-list [data-n="{node}"]')
    p.page.click('[data-v="graph"]')


def toggle(p, sid, on=True):
    pick(p, f"SC:{sid}")
    p.page.click("#ws-run")
    p.page.wait_for_selector(f'.wnode[data-n="SC:{sid}"]{".live" if on else ":not(.live)"}', state="attached")
    settle(p)


def settle(p):
    """The server answered and the edges are drawn where the nodes arrived."""
    p.page.wait_for_function("!document.querySelector('#ws-scn').classList.contains('busy')")
    p.page.wait_for_selector(".ws-edges:not(.moving)", state="attached")
    p.page.wait_for_timeout(100)


def server(p, ids, params=None):
    r = p.ctx.request.post(f"{p.base}/api/scenario/combine",
                           data={"client_id": "C01", "scenarios": ids, "params": params or {}})  # fmt: skip
    assert r.ok, r.text()
    return r.json()["result"]


def test_active_scenarios_combine_on_the_server_and_never_touch_net_worth(open_page):
    p = fresh(open_page)
    core = p.page.text_content(".wme-v")
    toggle(p, "vni_30")
    toggle(p, "rates_up")
    bar, want = p.page.evaluate(BAR), server(p, ["vni_30", "rates_up"])
    assert bar["chips"] == ["SC:vni_30", "SC:rates_up"]
    assert bar["after"] == round(want["after"]["net_worth"]) and bar["change"] == round(want["change"])
    assert p.page.text_content(".wme-v") == core  # the real net worth: a what-if is never added to it
    moving = p.page.evaluate(MOVING)
    assert moving and all(k.split(">")[0] in ("SC:vni_30", "SC:rates_up") for k in moving)
    assert any(k.startswith("SC:rates_up>") and k.endswith("FL:out") for k in moving)  # its interest cost: spending
    p.page.reload()  # kept in this browser, recomputed by the server
    p.page.wait_for_selector('.wnode[data-n="SC:rates_up"].live')
    settle(p)
    assert p.page.evaluate(BAR)["after"] == round(want["after"]["net_worth"])
    toggle(p, "vni_30", on=False)  # off: the rest recombined
    one = server(p, ["rates_up"])
    assert p.page.evaluate(BAR)["after"] == round(one["after"]["net_worth"])
    assert all(k.startswith("SC:rates_up>") for k in p.page.evaluate(MOVING))
    p.page.click('#ws-scn [data-off="*"]')
    p.page.wait_for_selector("#ws-scn", state="hidden")
    settle(p)
    assert p.page.evaluate(MOVING) == [] and p.page.locator(".wnode.k-scenario.live").count() == 0
    assert not p.problems()


def test_the_trace_runs_from_the_assumptions_to_the_goals(open_page):
    p = fresh(open_page)
    toggle(p, "rates_up")
    steps = p.page.evaluate("[...document.querySelectorAll('.ws-trace [data-step]')].map(s => s.dataset.step)")
    assert steps == ["assumptions", "classes", "costs", "liquidity", "net_worth", "goals"]
    want = server(p, ["rates_up"])
    text = p.page.inner_text(".ws-trace")
    assert all(a in text for a in want["scenarios"][0]["assumptions"])
    assert "Lãi vay thả nổi" in p.page.inner_text('.ws-trace [data-step="costs"]')
    assert "giả định" in p.page.inner_text("#ws-pane-i").lower()
    assert not p.problems()


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_the_persons_what_if_takes_their_inputs_within_bounds(open_page, size):
    p = fresh(open_page, size)
    pick(p, "SC:custom")
    p.page.fill('#ws-what [name="stock"]', "-90")  # past the bound: held at −50 %
    p.page.fill('#ws-what [name="income"]', "-10")
    p.page.click('#ws-what button[type="submit"]')
    p.page.wait_for_selector('.wnode[data-n="SC:custom"].live', state="attached")
    settle(p)
    params = p.page.evaluate(f"JSON.parse(localStorage.getItem('{KEY}')).params.custom")
    assert params == {"stock": -0.5, "income": -0.1}
    want = server(p, ["custom"], {"custom": params})
    assert p.page.evaluate(BAR)["after"] == round(want["after"]["net_worth"])
    assert "Thu nhập hằng tháng -10%" in p.page.inner_text('.ws-trace [data-step="assumptions"]')
    assert not p.problems()
