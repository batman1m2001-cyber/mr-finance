"""Toàn cảnh in the board's look (UI redesign R2): every figure comes from an API field, the small charts carry the
same numbers, a picked band sends flow dots that respect reduced motion and a hidden tab, and nothing is lost."""

import json
import urllib.request

from conftest import in_thread
from test_apply import MARKET, approved


def api(base, path, body):
    headers = {"content-type": "application/json"}
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(), headers=headers)
    return json.load(urllib.request.urlopen(req))


def test_the_figures_are_the_apis(open_page, base_url):
    in_thread(approved, *MARKET)
    p = open_page()
    p.go("#/client/tong-quan/toan-canh")
    d = api(base_url, "/api/dashboard", {"client_id": "C01", "scope": "personal"})["dashboard"]
    goals = api(base_url, "/api/goals", {"client_id": "C01"})["goals"]
    feed = api(base_url, "/api/feed", {"client_id": "C01", "role": "client"})["feed"]["items"]
    # the month's change by class: Σ (value − value last month), debts against it; the three largest shown
    moved = {}
    for h in d["holdings"]:
        g = "deposit" if h["class"] == "cash" else h["class"]
        delta = (h["value"] - h["prev_value"]) * (-1 if h["kind"] == "liability" else 1)
        if delta:
            moved[g] = moved.get(g, 0) + delta
    top = sorted(moved.items(), key=lambda kv: -abs(kv[1]))[:3]
    shown = p.page.eval_on_selector_all(".crow", "rs => rs.map(r => [r.dataset.g, Number(r.dataset.delta)])")
    assert [(g, round(v)) for g, v in shown] == [(g, round(v)) for g, v in top]
    assert sum(moved.values()) == d["net_worth"]["month_change"]  # the split adds up to the figure it explains
    held = [h for h in d["holdings"] if h["kind"] == "asset" and h["value"] > 0]
    classes = {"deposit" if h["class"] == "cash" else h["class"] for h in held}
    assert p.page.locator("#donut .seg").count() == len(classes)
    assert p.page.locator("#goals .goal").count() == len([g for g in goals if g["followed"]])
    assert p.page.locator("#feed .feed-item").count() == len(feed)
    for key in ("kpi:net_worth", "kpi:liquidity", "kpi:risk"):  # the Copilot's marks still have their targets
        assert p.page.locator(f'[data-focus="{key}"]').count() == 1
    assert not p.problems()


def test_a_picked_band_flows_three_times_and_pauses_with_the_tab(open_page):
    p = open_page()
    p.go("#/client/tong-quan/toan-canh")
    p.page.locator(".sankey .band").first.click()
    assert p.page.locator(".sankey .band.on").count() == 1 and "giao dịch" in p.page.inner_text("#flow-rows")
    dots = "document.getAnimations().filter(a => a.effect.target.closest('.flowdots'))"
    assert p.page.evaluate(f"{dots}.length") == 3
    p.page.evaluate(
        "Object.defineProperty(document, 'hidden', {configurable: true, get: () => true});"
        "document.dispatchEvent(new Event('visibilitychange'))"
    )
    assert p.page.evaluate(f"{dots}.map(a => a.playState)") == ["paused"] * 3
    p.page.evaluate(
        "Object.defineProperty(document, 'hidden', {configurable: true, get: () => false});"
        "document.dispatchEvent(new Event('visibilitychange'))"
    )
    p.page.wait_for_function("!document.querySelector('.flowdots circle')", timeout=12000)  # three passes, then gone


def test_reduced_motion_picks_without_dots(open_page):
    p = open_page(reduced=True)
    p.go("#/client/tong-quan/toan-canh")
    p.page.locator(".sankey .band").first.click()
    assert p.page.locator(".sankey .band.on").count() == 1
    assert p.page.locator(".flowdots circle").count() == 0
