"""Living Interface (backlog B-01, FEAT-33): an answer names the page elements it was read from, and the motion
rules hold — only transform and opacity animate, nothing loops in JS, hidden tabs pause, reduced motion stops."""

import re
from pathlib import Path

from test_apply import MARKET, approved
from test_copilot import ask
from test_feed import items

from apply import reads

WEB = Path("web")
CSS = (WEB / "core" / "tokens.css").read_text()
PAGES = "\n".join(p.read_text() for p in [*(WEB / "pages").glob("*.js"), WEB / "charts" / "charts.js"])


def test_an_answer_names_the_elements_it_was_read_from():
    got = ask("Tài sản của tôi thế nào?")
    assert got["status"] == "ok" and got["focus"] == ["kpi:net_worth", "kpi:liquidity", "kpi:risk"]
    flow = ask("Dòng tiền tháng này?")
    month = flow["focus"][0].split(":")[1]
    assert flow["focus"][0] == f"flow:{month}" and f"tháng {month[5:]}/{month[:4]}".lower() in flow["text"].lower()
    assert flow["focus"][1].startswith(f"flow:{month}:out:")


def test_an_impact_answer_points_at_the_largest_event_and_the_feed_at_its_items():
    _, run = approved(*MARKET)
    got = ask("Tin nào ảnh hưởng tới tôi?")
    eff = [i for i in reads.family_impact("C01", "client")["items"] if i["status"] == "EFFECTIVE"]
    big = max(eff, key=lambda i: abs(i["horizons"]["3m"]["expected"]))
    assert got["focus"] == [f"event:{big['event']['id']}"]
    feed = items(role="client")
    keys = [i["key"] for i in feed]
    assert len(set(keys)) == len(keys) and all(k.startswith("feed:") for k in keys)
    watch = ask("Có gì cần chú ý?")
    assert watch["focus"] == keys[:3]


def test_failures_mark_nothing():
    assert "focus" not in ask("Dòng tiền tháng 3/2020?")
    assert not ask("Duyệt đề xuất đang chờ").get("focus")  # forbidden for a client


def test_every_focus_key_has_a_page_that_renders_it():
    for prefix in ("kpi:net_worth", "kpi:liquidity", "kpi:risk", "flow:", "event:", "family:"):
        assert prefix in PAGES, prefix
    assert 'data-focus="${esc(i.key)}"' in PAGES  # the feed's own keys


def test_only_transform_and_opacity_animate():
    frames = re.findall(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", CSS)
    assert {n for n, _ in frames} >= {"mf-rise", "mf-dot", "mf-mark", "mf-lit", "mf-halo"}
    for name, body in frames:
        props = set(re.findall(r"([a-z-]+)\s*:", re.sub(r"[\d.%,\s]+\{", "{", body)))
        # shimmer predates B-01; the graph's money spark slides a dash along its wire, as Studio's data flow does
        # (owner, 2026-10-17: a few thin paths, idle frames measured equal with and without it)
        allowed = {"transform", "opacity", "background-position"}
        if name == "ws-money":
            allowed = allowed | {"stroke-dashoffset"}
        assert props <= allowed, (name, props)
    for decl in re.findall(r"transition:\s*([^;]+);", CSS.split("Living Interface (backlog B-01)")[1]):
        for part in decl.split(","):
            assert part.split()[0] in ("transform", "opacity", "none"), decl


def test_hidden_tabs_pause_reduced_motion_stops_and_no_js_loop():
    assert "html[data-hidden] *, html[data-hidden] *::after { animation-play-state: paused !important; }" in CSS
    reduced = CSS.split("@media (prefers-reduced-motion: reduce) {\n  .cp-panel")[1].split("\n}\n")[0]
    for cls in (".cp-in", ".cp-dots i", ".mf-lit", ".mf-focus::after", ".cp-dot::after"):
        assert cls in reduced
    js = (WEB / "motion.js").read_text() + (WEB / "copilot.js").read_text()
    assert "setInterval" not in js and js.count("requestAnimationFrame") == 1  # one frame after a page renders
