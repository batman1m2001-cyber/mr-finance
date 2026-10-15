"""Write the out-of-sample validation of the estimated factor model for Model Risk (BRD-RULE-MEAS-08, F2):
docs/brd/testing/model_validation.md, from the market history in the state file (``MF_STATE``; fill it first with
`operonx run market_backfill`).

    MF_STATE=... uv run python scripts/validate_model.py [--split 2024-01] [--to 2026-08]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from control import config  # noqa: E402
from market import estimate, store  # noqa: E402

OUT = ROOT / "docs" / "brd" / "testing" / "model_validation.md"


def pct(x):
    return "—" if x is None else f"{x * 100:.0f} %"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="2024-01")
    ap.add_argument("--to", default="2026-08")
    args = ap.parse_args()
    base = config.data("factor_model")
    hist = estimate.history()
    full = estimate.estimate(base, hist=hist)
    v = estimate.validate(base, split=args.split, test_to=args.to, hist=hist)
    cov = store.coverage()
    vol_full = {r["id"]: r for r in full["report"]["factors"]}
    lines = [
        "# Model validation, out of sample (BRD-RULE-MEAS-08)",
        "",
        f"Written by `scripts/validate_model.py` on {date.today().isoformat()} from the market history stored by the",
        "market jobs (FEAT-35). Method: [src/market/estimate.py](../../../src/market/estimate.py).",
        "",
        "## Method",
        "",
        f"- Estimated with the months up to **{v['split']}** only (window from {v['estimated_from']}, at most 55 "
        "months, at least 24; correlations shrunk 20 % toward zero, BRD §9.2).",
        f"- Scored on every month **after {v['split']} up to {v['test_to']}**: is the factor's monthly move inside "
        "its P10–P90 band (±1.2816 σ)? 80 % is expected; BRD-RULE-MEAS-01 accepts 70–90 % (below: too narrow, "
        "above: too wide). The same over non-overlapping quarters (±1.2816 σ √3).",
        "- Correlation drift: the mean absolute difference between each pair's correlation in and out of sample.",
        "- The bands here are the model's unconditional ones (no scenario). Scoring each approved view's own bands "
        "as their horizons pass is FEAT-18 (BRD_COMPLETION_PLAN F3).",
        "",
        "## Result",
        "",
        f"- Pooled monthly coverage: **{pct(v['pooled_coverage_1m'])}** over {sum(r['months'] for r in v['factors'])} "
        f"factor-months — {'inside' if v['pass'] else 'outside'} the 70–90 % band.",
        f"- Correlation drift: {v['correlation_drift']} on average over {v['correlation_pairs']} pairs.",
        "",
        "| Factor | Months | σ in sample | σ out of sample | Inside 1 month | Inside 3 months | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in v["factors"]:
        lines.append(
            f"| {r['id']} | {r['months']} | {r['vol_in']:.3g} | {r['vol_out']:.3g} | {pct(r['coverage_1m'])} | "
            f"{pct(r['coverage_3m'])} | {r['verdict']} |"
        )
    lines += [
        "",
        "Not validated (no free series; parameters stay assumed): RE_SPREAD, FIN_SPREAD, VN_HOUSE.",
        "",
        "## Reading it",
        "",
    ]
    for r in v["factors"]:
        if r["verdict"] != "đạt":
            why = "the band was too narrow" if r["verdict"] == "dải hẹp" else "the band was too wide"
            lines.append(
                f"- **{r['id']}**: {why} out of sample (σ {r['vol_in']:.3g} in sample, {r['vol_out']:.3g} after); "
                "the volatility differed between the two windows."
            )
    lines += [
        "",
        "BRD-RULE-MEAS-08's own conclusion — use the model for VN-Index, and make FX and the SJC spread core shocks "
        "rather than inferring them — is a Model Risk decision; the table above is its evidence on this history.",
        "",
        "## Data",
        "",
        "| Series | First | Last | Points | Source |",
        "|---|---|---|---|---|",
    ]
    for sid in sorted(cov):
        c = cov[sid]
        lines.append(f"| {sid} | {c['first']} | {c['last']} | {c['n']} | {c['source']} |")
    lines += [
        "",
        "Limitations: Vietcombank, PNJ and HNX are sampled weekly by the backfill (month-ends are the last sampled "
        "day); FOREIGN_FLOW is standardised over all stored months; cafef's foreign-flow history has gaps before 2022.",
        "",
        "Estimate on all data to "
        + full["report"]["end"]
        + ": "
        + ", ".join(
            f"{k} σ {r['assumed_vol']} → {r['estimated_vol']}" for k, r in vol_full.items() if "estimated_vol" in r
        )
        + ".",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: pooled {pct(v['pooled_coverage_1m'])}, pass={v['pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
