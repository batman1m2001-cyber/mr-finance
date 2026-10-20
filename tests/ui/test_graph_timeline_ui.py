"""Money on the edges and a node's timeline (docs/NODE_TIMELINE_PLAN.md): every spoke that holds or moves money shows
its signed change over the period picked (Ngày · Tháng · Năm, Tháng first, kept for the tab), an estimate's spoke its
own figure in grey; a money node picked shows Diễn biến — the chart and its table — by the same period."""

import pytest
from test_graph_edges_ui import open_lens

PILLS = "() => Object.fromEntries([...document.querySelectorAll('.wmoney')].map(g => [g.dataset.e, [g.textContent, g.getAttribute('class')]]))"  # noqa: E501


def pills(p):
    return p.page.evaluate(PILLS)


def wait_pills(p, before):
    for _ in range(40):
        now = pills(p)
        if now and now != before:
            return now
        p.page.wait_for_timeout(100)
    return pills(p)


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_spokes_say_their_change_and_a_node_its_timeline(open_page, size):
    p = open_lens(open_page, "tong-quan", size=size)
    month = pills(p)
    money = {k: v for k, v in month.items() if "m-est" not in v[1]}
    assert len(money) >= 6, month
    assert all(t[0] in "+−±" for t, _ in money.values()), money
    assert month["FL:in>ME"][0].startswith("+") and month["ME>FL:out"][0].startswith("−")
    assert "m-out" in month["ME>FL:out"][1]
    assert p.page.get_attribute("[data-u=month]", "aria-pressed") == "true"
    if size == "desktop":
        assert "m-est" in month["RK:drawdown>ME"][1] and month["RK:drawdown>ME"][0].startswith("−")  # an estimate, grey

    p.page.click("[data-u=year]")
    year = wait_pills(p, month)
    assert [k for k in money if k in year and year[k][0] != money[k][0]], (money, year)  # a year moves, not a month
    assert p.page.evaluate("sessionStorage.getItem('mf.ws.unit')") == "year"
    assert p.page.get_attribute("[data-u=year]", "aria-pressed") == "true"

    p.page.click(".wnode[data-n='CL:stock']")
    p.page.wait_for_selector("#ws-tl-chart svg.tl")
    assert p.page.get_attribute("[data-tl=year]", "aria-pressed") == "true"  # the inspector follows the switch
    assert p.page.locator("#ws-tl-table tbody tr").count() == 6  # 2021 … 2026
    assert "mô phỏng" in p.page.inner_text(".ws-tl")
    p.page.click("[data-tl=month]")
    p.page.wait_for_function("document.querySelectorAll('#ws-tl-table tbody tr').length === 70")  # T1/21 … T10/26
    assert p.page.get_attribute("[data-u=month]", "aria-pressed") == "true"  # and the graph's switch follows it
    assert not p.problems()
