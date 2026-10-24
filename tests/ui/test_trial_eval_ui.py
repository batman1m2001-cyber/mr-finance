"""The trial page's two views (AGENT_EVALUATION_PLAN E5): A · Thu thập tin and B · Hiệu quả agent. Every rate
shows k/n beside it; nothing scored reads “—”, never 0 %; the simulated VND says it is simulated; a move opens from
the news to its verdict and VND by family. Desktop and phone, no error and no sideways scroll."""

import time

import pytest

from control import db

DAY = "2026-10-20"


def _seed():
    rows = [
        (
            f"{DAY}:1w:VNINDEX",
            "correct",
            {
                "claim": "up",
                "move": "up",
                "realised": 0.05,
                "expected": 0.04,
                "material": True,
                "reason": None,
                "family": "stocks",
            },
        ),
        (f"{DAY}:1w:GOLD", "pending", {"claim": None, "reason": "not_due", "family": "other"}),
    ]
    with db.tx() as con:
        for sid, verdict, extra in rows:
            data = {
                "id": sid,
                "day": DAY,
                "horizon": "1w",
                "factor": sid.split(":")[-1],
                "verdict": verdict,
                "origin": "2026-10-19",
                "due": "2026-10-26",
                "unit": "pct",
                "scale": 0.05,
                "material_sigma": 1.0,
                "claim_share": 0.25,
                "drafts": [],
                **extra,
            }
            con.execute(
                "insert into eval_scores values (?, ?, ?, ?, ?, ?, ?)",
                (sid, DAY, "1w", data["factor"], verdict, time.time(), db.dumps(data)),
            )
        snap = {
            "exposure": {"1w": {"C01": {"VNINDEX": 100_000_000}}},
            "families": {"C01": "Gia đình thử"},
            "late": False,
        }
        con.execute("insert into eval_snapshots values (?, ?, ?)", (DAY, time.time(), db.dumps(snap)))


@pytest.mark.parametrize("size", ["desktop", "phone"])
def test_view_b_shows_every_rate_with_its_count_and_a_move_opens_to_its_vnd(open_page, size):
    _seed()
    p = open_page(size)
    p.go("#/cio/mo-hinh/thu-nghiem")
    page = p.page
    page.locator("text=Theo ngày").wait_for()  # View A first
    page.click('[data-view="b"]')
    kpis = page.locator("#page .kpis").first.inner_text()
    assert "100%" in kpis and "(1/1)" in kpis  # precision 1 of 1 called
    for t in page.locator("#page .how-n").all_inner_texts():  # no bare 0 % where nothing was counted
        assert t.strip() != "0%"
    text = page.locator("#page").inner_text()
    assert "mô phỏng" in text and "+5 triệu" in text  # |E x| = 100 m × 5 %
    page.click(f'[data-move="{DAY}:1w:VNINDEX"]')
    drawer = page.locator(".drawer")
    drawer.locator("text=Gia đình thử").wait_for()
    assert "đúng" in drawer.inner_text()
    assert page.evaluate("document.documentElement.scrollWidth") <= page.viewport_size["width"]
    assert not p.problems()
