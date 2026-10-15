"""Estimate the factor model from the stored history, and validate it out of sample (BRD_COMPLETION_PLAN F2,
F-D4, F-D5; BRD §9.2, BRD-RULE-ENG-11, BRD-RULE-MEAS-08).

- **Estimate.** For every factor backed by data with at least ``MIN_MONTHS`` monthly moves in the window (the last
  ``WINDOW`` = 55 months to ``end``): the monthly volatility is the sample standard deviation of its moves, and
  each correlation between two such factors is the sample correlation over their common months shrunk 20 %
  toward zero. Factors without data keep their assumed volatility and correlations, labelled “Giả định”. The
  BRD's sizes, realisation shares, the stressed regime and the loadings are not estimated and stay as they are.
  If the mix of estimated and assumed correlations is not positive definite it is nudged back (the engine's
  ``clip_to_correlation``) and the change is reported.
- **Propose.** The result is a new ``factor_model`` version: proposed by a CIO, approved by a second CIO (ADR-0016).
- **Validate.** Estimate with the months up to ``split`` only, then count, month by month after it, how often each
  factor's move fell inside its P10–P90 band (±1.2816 σ; 3 months: ±1.2816 σ √3 over non-overlapping quarters).
  80 % is expected; the BRD accepts 70–90 % (KPI-04). Correlations in and out of sample are compared.
"""

from __future__ import annotations

import copy
import math
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from engine import linalg
from market import factors as mf

WINDOW = 55
SHRINK = 0.2
MIN_MONTHS = 24
Z80 = 1.2815515655446004  # P90 of the standard normal
ACCEPT = (0.70, 0.90)


def _last_complete_month(today: Optional[date] = None) -> str:
    t = today or date.today()
    y, m = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
    return f"{y:04d}-{m:02d}"


def _month_back(month: str, n: int) -> str:
    y, m = map(int, month.split("-"))
    k = y * 12 + (m - 1) - n
    return f"{k // 12:04d}-{k % 12 + 1:02d}"


def _sd(xs: List[float]) -> float:
    mu = sum(xs) / len(xs)
    return math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def _corr(a: Dict[str, float], b: Dict[str, float]) -> Tuple[Optional[float], int]:
    common = sorted(set(a) & set(b))
    if len(common) < MIN_MONTHS:
        return None, len(common)
    xs, ys = [a[m] for m in common], [b[m] for m in common]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if not sx or not sy:
        return None, len(common)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy), len(common)


def history(months: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Dict[str, Any]]:
    """Each data-backed factor's monthly moves {month: move} and its provenance (from SQLite)."""
    out = {}
    for f in mf.factor_series(with_moves=True):
        if f.get("moves"):
            out[f["id"]] = {"moves": {m["month"]: m["move"] for m in f["moves"]}, "provenance": f["provenance"]}
    return out


def estimate(
    base: Dict[str, Any],
    end: Optional[str] = None,
    hist: Optional[Dict[str, Dict[str, Any]]] = None,
    window: int = WINDOW,
    shrink: float = SHRINK,
) -> Dict[str, Any]:
    """``base`` (a factor model as data) with what the history supports estimated; and the report of what changed."""
    end = end or _last_complete_month()
    start = _month_back(end, window - 1)
    hist = history() if hist is None else hist
    model = copy.deepcopy(base)
    ids = [f["id"] for f in model["factors"]]
    inside = {fid: {m: v for m, v in h["moves"].items() if start <= m <= end} for fid, h in hist.items()}
    rows, used = [], {}
    for f in model["factors"]:
        mv = inside.get(f["id"]) or {}
        row = {"id": f["id"], "name": f["name"], "unit": f["unit"], "assumed_vol": f["vol_month"], "months": len(mv)}
        if len(mv) >= MIN_MONTHS:
            vol = _sd(list(mv.values()))
            if vol > 0:
                used[f["id"]] = mv
                f["vol_month"] = float(f"{vol:.4g}")
                f["assumed"] = False
                f["brd_parameter"] = "Ước lượng"
                f["estimated"] = {
                    "months": len(mv),
                    "from": min(mv),
                    "to": max(mv),
                    "source": hist[f["id"]]["provenance"],
                    "shrinkage": shrink,
                }
                row.update(estimated_vol=f["vol_month"], source=hist[f["id"]]["provenance"])
        else:
            f["assumed"] = True
            f.pop("estimated", None)
            f["brd_parameter"] = "Giả định"
        rows.append(row)

    n = len(ids)
    corr = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for a, b, rho in base["correlations"]:
        i, j = ids.index(a), ids.index(b)
        corr[i][j] = corr[j][i] = float(rho)
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = ids[i], ids[j]
            if a in used and b in used:
                rho, _ = _corr(used[a], used[b])
                if rho is not None:
                    corr[i][j] = corr[j][i] = (1 - shrink) * rho
                    pairs += 1
    before = min(linalg.eigh(corr)[0])
    repaired = linalg.clip_to_correlation(corr) if before < 1e-6 else corr
    change = max(abs(x - y) for ra, rb in zip(repaired, corr) for x, y in zip(ra, rb))
    model["correlations"] = [
        [ids[i], ids[j], round(repaired[i][j], 3)]
        for i in range(n)
        for j in range(i + 1, n)
        if abs(round(repaired[i][j], 3)) >= 0.001
    ]
    done = [r for r in rows if "estimated_vol" in r]
    model["version"] = f"FM-EST-{end}"
    model["status"] = "estimated"
    model["note"] = (
        f"Biến động và tương quan của {len(done)}/{n} yếu tố ước lượng từ {window} tháng dữ liệu thị trường đến {end} "
        f"(cần tối thiểu {MIN_MONTHS} tháng), tương quan co về 0 thêm {round(shrink * 100)} % (BRD mục 9.2). "
        "Yếu tố không có dữ liệu giữ tham số giả định. Cỡ cú sốc, tỷ lệ thể hiện, chế độ căng thẳng và hệ số tải "
        "giữ theo BRD và giả định."
    )
    report = {
        "end": end,
        "start": start,
        "window": window,
        "shrinkage": shrink,
        "factors": rows,
        "estimated": len(done),
        "correlation_pairs": pairs,
        "repair": {"min_eigenvalue_before": round(before, 6), "max_change": round(change, 6)},
    }
    return {"model": model, "report": report}


def validate(
    base: Dict[str, Any],
    split: str = "2024-01",
    test_to: Optional[str] = None,
    hist: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Out-of-sample check (MEAS-08): estimated up to ``split``, scored on the months after it up to ``test_to``."""
    hist = history() if hist is None else hist
    test_to = test_to or _last_complete_month()
    est = estimate(base, end=split, hist=hist)
    vols = {f["id"]: f["vol_month"] for f in est["model"]["factors"] if not f.get("assumed")}
    rows = []
    for fid, vol in vols.items():
        moves = sorted((m, v) for m, v in hist[fid]["moves"].items() if split < m <= test_to)
        if not moves:
            continue
        inside = sum(abs(v) <= Z80 * vol for _, v in moves)
        quarters = [moves[k : k + 3] for k in range(0, len(moves) - 2, 3)]
        q_in = sum(abs(sum(v for _, v in q)) <= Z80 * vol * math.sqrt(3) for q in quarters)
        cov = inside / len(moves)
        out_vol = _sd([v for _, v in moves]) if len(moves) > 2 else None
        rows.append(
            {
                "id": fid,
                "months": len(moves),
                "vol_in": vol,
                "vol_out": round(out_vol, 4) if out_vol else None,
                "coverage_1m": round(cov, 3),
                "quarters": len(quarters),
                "coverage_3m": round(q_in / len(quarters), 3) if quarters else None,
                "verdict": "đạt" if ACCEPT[0] <= cov <= ACCEPT[1] else ("dải hẹp" if cov < ACCEPT[0] else "dải rộng"),
            }
        )
    total = sum(r["months"] for r in rows)
    pooled = sum(r["coverage_1m"] * r["months"] for r in rows) / total if total else None
    ids = sorted(vols)
    diffs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            ins = {m: v for m, v in hist[a]["moves"].items() if m <= split}
            inb = {m: v for m, v in hist[b]["moves"].items() if m <= split}
            outa = {m: v for m, v in hist[a]["moves"].items() if split < m <= test_to}
            outb = {m: v for m, v in hist[b]["moves"].items() if split < m <= test_to}
            r_in, _ = _corr(ins, inb)
            r_out, n_out = _corr(outa, outb)
            if r_in is not None and r_out is not None:
                diffs.append(abs(r_in - r_out))
    return {
        "split": split,
        "test_to": test_to,
        "estimated_from": est["report"]["start"],
        "factors": rows,
        "pooled_coverage_1m": round(pooled, 3) if pooled is not None else None,
        "accept": list(ACCEPT),
        "pass": pooled is not None and ACCEPT[0] <= pooled <= ACCEPT[1],
        "correlation_drift": round(sum(diffs) / len(diffs), 3) if diffs else None,
        "correlation_pairs": len(diffs),
    }
