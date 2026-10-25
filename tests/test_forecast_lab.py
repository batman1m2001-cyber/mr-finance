"""The forecast lab (FORECAST_DESK_PLAN step 1): a track judged by the trial's rules, baselines that see nothing after
the origin, the amount measures, and week blocks that keep a week's moves together."""

from datetime import date, timedelta

from measure.realised import Series
from trial import lab, shadow


def days(first: str, n: int):
    d = date.fromisoformat(first)
    return [(d + timedelta(days=i)).isoformat() for i in range(n)]


def vnindex(levels):
    return {"VNINDEX": Series("VNINDEX", "pct", list(zip(days("2026-06-01", len(levels)), levels)))}


def move(day="2026-07-10", horizon="1w", factor="VNINDEX"):
    m = shadow.model()
    return {"day": day, "horizon": horizon, "factor": factor, "origin": shadow.realised.add_days(day, -1),
            "scale": m.factor(factor).vol_month * m.horizons[horizon] ** 0.5}


def test_a_track_is_judged_as_one_draft_made_that_morning():
    series = vnindex([1000 * 1.01 ** i for i in range(60)])  # up 1% a day: a week is a material move up
    up, down, none = move("2026-07-10"), move("2026-07-11"), move("2026-07-12")
    track = {lab.key(up): up["scale"], lab.key(down): -down["scale"]}
    got = {r["day"]: r for r in lab.judge(track, [up, down, none], series, today="2026-10-25")}
    assert got["2026-07-10"]["verdict"] == "correct"
    assert got["2026-07-11"]["verdict"] == "incorrect" and got["2026-07-11"]["reason"] == "wrong_direction"
    assert got["2026-07-12"]["verdict"] == "missed" and got["2026-07-12"]["reason"] == "not_predicted"
    assert got["2026-07-12"]["due"] == "2026-07-18"  # origin 11/07, a week


def test_the_baselines_read_nothing_after_the_origin():
    class Guard:
        def __init__(self, s, origin):
            self.s, self.origin = s, origin

        def move(self, d0, d1):
            assert d1 <= self.origin, f"read {d1} after the origin {self.origin}"
            return self.s.move(d0, d1)

    r = move("2026-07-20")
    s = vnindex([1000 + (i % 3) for i in range(60)])["VNINDEX"]
    guarded = {"VNINDEX": Guard(s, r["origin"])}
    assert lab.momentum(r, guarded) == s.move("2026-07-12", "2026-07-19")
    assert lab.majority(r, guarded) is not None


def test_the_majority_is_a_material_move_when_the_trailing_moves_all_went_one_way():
    r = move("2026-07-20")
    assert lab.majority(r, vnindex([1000 * 1.01 ** i for i in range(60)])) == r["scale"]
    assert lab.majority(r, vnindex([1000 * 0.99 ** i for i in range(60)])) == -r["scale"]


def row(expected, realised, verdict, day="2026-07-10", scale=1.0, claim=None, reason=None):
    return {"day": day, "horizon": "1w", "factor": "VNINDEX", "origin": day, "scale": scale, "material_sigma": 1.0,
            "expected": expected, "realised": realised, "material": abs(realised) >= scale, "verdict": verdict,
            "claim": claim, "reason": reason, "is_due": True}


def test_the_amount_counts_big_forecasts_of_big_moves_the_right_way():
    rows = [
        row(1.5, 2.0, "correct", claim="up"),  # big, said big, right way
        row(-1.2, 1.5, "incorrect", claim="down", reason="wrong_direction"),  # big, said big, wrong way
        row(0.3, -1.1, "correct", claim="down"),  # big, said small
        row(1.1, 0.2, "incorrect", claim="up", reason="not_material"),  # said big, small
        row(0.0, 0.1, "quiet"),
    ]
    got = lab.measures(rows)
    assert got["amount_recall"] == {"value": 0.333, "hits": 1, "n": 3}
    assert got["amount_precision"] == {"value": 0.333, "hits": 1, "n": 3}
    assert got["call_direction"]["n"] == 4 and got["call_direction"]["hits"] == 3


def test_the_baseline_is_measured_on_the_tracks_own_calls():
    rows = [row(1.5, 2.0, "correct", claim="up"), row(0.0, -1.5, "missed", day="2026-07-11")]
    other = {lab.key(rows[0]): -1.0, lab.key(rows[1]): -1.0}  # right on the move the track did not call
    assert lab.same_calls(rows, other) == {"value": 0.0, "hits": 0, "n": 1}


def test_week_blocks_keep_a_weeks_moves_together():
    a = [row(1, 1, "quiet", day=d) for d in ("2026-07-06", "2026-07-07", "2026-07-08")]  # one ISO week
    b = [row(1, 1, "quiet", day=d) for d in ("2026-07-13",)]
    got = lab.bootstrap(a + b, lambda rs: sum(r["day"] < "2026-07-13" for r in rs) / len(rs), n=200)
    assert set(got) <= {0.0, 0.6, 0.75, 1.0}  # whole weeks or nothing: never a single move of week a
    assert lab.interval([0.1 * i for i in range(11)]) == (0.0, 1.0)
