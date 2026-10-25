"""The desk's sources (FORECAST_DESK_PLAN steps 3–5): the market snapshot and the knowledge base read nothing after
the origin's close, the odds learn what the data holds, and the desk's answer becomes a track as any draft would."""

from datetime import date, timedelta

import numpy as np

from measure.realised import Series
from trial import desk, kb, odds, shadow


def days(first: str, n: int):
    d = date.fromisoformat(first)
    return [(d + timedelta(days=i)).isoformat() for i in range(n)]


class Guard:
    """A series that fails the test when asked for anything after the origin."""

    def __init__(self, s, origin):
        self.s, self.origin, self.unit = s, origin, s.unit

    def move(self, d0, d1):
        assert d1 <= self.origin, f"move to {d1}, after the origin {self.origin}"
        return self.s.move(d0, d1)

    def level(self, d):
        assert d <= self.origin, f"level on {d}, after the origin {self.origin}"
        return self.s.level(d)


def market(n=500):
    rng = np.random.default_rng(1)
    out = {}
    for fid, unit in (("VNINDEX", "pct"), ("GLOBAL_EQ", "pct"), ("BTC", "pct"), ("DXY", "pct")):
        levels = 1000 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
        out[fid] = Series(fid, unit, list(zip(days("2025-01-01", n), levels.tolist())))
    return out


def test_the_snapshot_reads_nothing_after_the_origin():
    s, origin = market(), "2026-02-10"
    guarded = {k: Guard(v, origin) for k, v in s.items()}
    feats = odds.snapshot("VNINDEX", origin, "1w", guarded, shadow.model())
    assert set(odds.FEATURES) <= set(feats)


def test_the_logistic_fit_finds_the_sign_the_data_holds():
    rng = np.random.default_rng(2)
    x = rng.normal(size=(2000, 1))
    y = (x[:, 0] + rng.normal(0, 0.5, 2000) > 0).astype(float)
    w = odds.fit(np.hstack([x, np.ones((2000, 1))]), y, l2=1.0)
    assert w[0] > 1 and abs(w[1]) < 0.3


def test_the_knowledge_base_finds_like_headlines_only_before_and_moves_only_over():
    base = kb.Base([("2026-05-04", "Giá vàng SJC tăng mạnh"), ("2026-06-20", "Giá vàng SJC lập đỉnh mới"),
                    ("2026-05-05", "Khối ngoại bán ròng")])
    hits = base.search("giá vàng SJC hôm nay", before="2026-06-01")
    assert [d for _, d, _ in hits] == ["2026-05-04"]
    s = {"VNINDEX": Series("VNINDEX", "pct", list(zip(days("2026-04-01", 120), [1000 + i for i in range(120)])))}
    m = shadow.model()
    assert kb.after("2026-05-04", "1w", "2026-05-09", s, m) == {}  # due 10/05: not over by the origin
    assert kb.after("2026-05-04", "1w", "2026-05-10", s, m)["VNINDEX"] > 0
    got = kb.analogs(base, ["giá vàng SJC"], "2026-05-20", "1w", s, m)
    assert got["VNINDEX"]["days"] == 1 and got["VNINDEX"]["up"] == 1.0


def test_the_desks_answer_is_a_track_of_one_draft_a_factor():
    m = shadow.model()
    s = {"VNINDEX": object(), "GOLD": object()}
    got = desk.parse({"calls": [
        {"factor": "VNINDEX", "horizon": "1w", "direction": "down", "size": 1.2},
        {"factor": "GOLD", "horizon": "3d", "direction": "flat", "size": 0.8},
        {"factor": "NOPE", "horizon": "1w", "direction": "up", "size": 1},
        {"factor": "GOLD", "horizon": "3m", "direction": "up", "size": 1},
    ]}, "2026-07-09", "2026-07-10", s, m)
    assert got == {("2026-07-10", "1w", "VNINDEX"): -1.2 * desk.sigma("VNINDEX", "1w", m),
                   ("2026-07-10", "3d", "GOLD"): 0.0}


def test_the_record_holds_only_moves_over_by_the_origin():
    rows = [
        {"horizon": "1w", "due": "2026-07-09", "verdict": "correct", "claim": "up", "realised": 3.0, "material": True,
         "expected": 1.0},
        {"horizon": "1w", "due": "2026-07-12", "verdict": "missed", "claim": None, "realised": -3.0, "material": True,
         "expected": 0.1},
    ]
    got = desk.record("2026-07-10", rows)
    assert got["1w"]["calls"] == 1 and got["1w"]["big_moves"] == 1 and got["1w"]["big_missed"] == 0
