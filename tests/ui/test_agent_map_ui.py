"""The Agent Ecosystem Map (A7, ADR-0033; OWN-AS-20…22) on the Agent page: every part and every line the endpoint
names is drawn, a part lights its lines, opens on what it does and its runs, a run on its steps; on a phone it is a
list per group with no sideways scroll; the panel links to it."""


def ask(p, message="tổng quan tài sản"):  # one assistant turn as the CIO, through the server (no model: keywords)
    r = p.ctx.request.post(f"{p.base}/api/assistant", data={"message": message, "role": "cio", "route": "#/cio/agent"})
    assert r.ok, r.text()
    return r.json()["assistant"]


def test_the_map_draws_what_the_endpoint_says_and_opens_a_run(open_page):
    p = open_page()
    p.go("#/cio/agent")
    a = ask(p)
    p.go("#/cio/agent")
    p.page.wait_for_selector(".eco-wire", state="attached")
    m = p.ctx.request.get(f"{p.base}/api/agents/map").json()
    assert p.page.locator(".eco-node").count() == len(m["nodes"])
    assert p.page.locator(".eco-wire").count() == len(m["edges"])
    assert "Danh mục agent" in p.page.inner_text("#page")  # the catalogue stays, below

    p.page.hover("[data-node='assistant']")
    lit = p.page.locator(".eco-wire.on").count()
    assert lit == sum(1 for e in m["edges"] if "assistant" in (e["from"], e["to"]))
    assert p.page.locator(".eco-node.dim").count() > 0

    p.page.click("[data-node='assistant']")
    p.page.wait_for_selector(".drawer [data-run]")
    text = p.page.inner_text(".drawer")
    assert "Nối với" in text and "src/assistant/registry.py::agent_tools" in text and "Hoàn tất" in text
    p.page.click(".drawer [data-run]")
    p.page.wait_for_selector(".drawer [data-back]")
    steps = p.page.inner_text(".drawer")
    assert all(s["tool"] in steps for s in a["steps"]) and "tổng quan tài sản" not in steps  # tools, not the question
    p.page.click(".drawer [data-back]")
    p.page.wait_for_selector(".drawer [data-run]")
    assert not p.problems()


def test_on_a_phone_the_map_is_a_list_per_group(open_page):
    p = open_page("phone")
    p.go("#/compliance/agent")
    p.page.wait_for_selector(".eco-list .eco-node")
    assert p.page.locator(".eco-wire").count() == 0 and p.page.locator(".eco-list .mgroup").count() == 6
    p.page.click("[data-node='policy_sweep']")
    p.page.wait_for_selector(".drawer .eco-links")
    assert "src/impact/graph.py::alerts_flow" in p.page.inner_text(".drawer")
    assert not p.problems()


def test_the_panel_links_the_desk_to_the_map(open_page):
    p = open_page()
    p.go("#/admin/he-thong")
    p.panel()
    p.page.click("#cp-hist")
    p.page.click("text=Bản đồ agent →")
    p.page.wait_for_selector(".eco-node")
    assert p.page.evaluate("location.hash").startswith("#/admin/agent")
    p.go("#/client/tong-quan/toan-canh")
    p.panel()
    p.page.click("#cp-hist")
    p.page.wait_for_selector(".cp-hist")
    assert p.page.locator("text=Bản đồ agent →").count() == 0  # a client has no Agent page
    assert not p.problems()
