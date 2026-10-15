"""Approved scenario branches + holdings → VND impact bands (BRD 9.1, four steps).

1. Each core shock: direction × the factor's S / M / L size × the priced-in multiplier
   (none 1, partial 0.5, full 0).
2. The other factors by conditional expectation on the branch regime's covariance:
   Δn = Σnc Σcc⁻¹ Δc. The band has three parts: the remaining monthly variation of the inferred
   factors (Σn|c = Σnn − Σnc Σcc⁻¹ Σcn) times the horizon in months; the uncertainty of the core
   size itself (sd = 40 % of the shock, spread through the correlations); each directly held
   stock's own risk.
3. Into each holding by its loadings, times each factor's realisation at the horizon.
4. The branches as a normal mixture weighted by probability → expected, P5, P10, P50, P90 for
   1 week, 3 months, 12 months.

Deterministic, no I/O, no AI. Every VND result is rounded to the dong here and only here; the
expected contributions by holding, class and factor are rounded so they add up to the total.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from engine import linalg
from engine.loadings import Exposure, exposures
from engine.model import REGIMES, SIZES, FactorModel, FactorModelError, default_model

PERCENTILES = (("p5", 0.05), ("p10", 0.10), ("p50", 0.50), ("p90", 0.90))
MAX_BRANCHES = 4


class ScenarioError(ValueError):
    """The branches given are not ones the engine may compute."""


@dataclass(frozen=True)
class Shock:
    factor: str
    direction: int  # +1 up, −1 down
    size: str  # S, M, L
    priced_in: str = "none"  # none, partial, full


@dataclass(frozen=True)
class Branch:
    id: str
    name: str
    probability: float
    shocks: Tuple[Shock, ...] = ()
    regime: str = "normal"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Branch":
        return cls(
            id=str(d["id"]),
            name=str(d.get("name") or d["id"]),
            probability=float(d["probability"]),
            shocks=tuple(
                Shock(s["factor"], int(s["direction"]), s["size"], s.get("priced_in", "none"))
                for s in d.get("shocks", [])
            ),
            regime=d.get("regime", "normal"),
        )


@dataclass
class Propagation:
    """One branch's factor moves: the core as given, the rest inferred."""

    branch: Branch
    moves: List[float]  # every factor, in its unit
    core: List[int]  # indexes of the core factors
    lift: linalg.Matrix  # n × c: the full move per unit of each core factor (identity on the core rows)
    residual: linalg.Matrix  # n × n: Σn|c, zero on the core rows and columns (monthly)
    core_cov: linalg.Matrix  # c × c: covariance of the core-size uncertainty


@dataclass
class _Branchwise:
    mean: float
    var: float
    by_holding: List[float]
    by_factor: List[float]
    parts: Dict[str, float] = field(default_factory=dict)


def validate(branches: Sequence[Branch], model: FactorModel) -> None:
    if not 1 <= len(branches) <= MAX_BRANCHES:
        raise ScenarioError(f"cần 1–{MAX_BRANCHES} nhánh, có {len(branches)}")
    if len({b.id for b in branches}) != len(branches):
        raise ScenarioError("mã nhánh bị trùng")
    total = sum(b.probability for b in branches)
    if any(not 0 < b.probability <= 1 for b in branches) or abs(total - 1.0) > 1e-6:
        raise ScenarioError(f"xác suất các nhánh phải dương và cộng bằng 1 (đang là {total:g})")
    for b in branches:
        if b.regime not in REGIMES:
            raise ScenarioError(f"{b.id}: chế độ {b.regime!r} không có")
        seen = set()
        for s in b.shocks:
            try:
                model.index(s.factor)
            except FactorModelError:
                raise ScenarioError(f"{b.id}: yếu tố {s.factor!r} không thuộc danh mục") from None
            if s.factor in seen:
                raise ScenarioError(f"{b.id}: yếu tố {s.factor} có hai cú sốc")
            seen.add(s.factor)
            if s.direction not in (1, -1):
                raise ScenarioError(f"{b.id}: chiều cú sốc {s.factor} phải là +1 hoặc −1")
            if s.size not in SIZES:
                raise ScenarioError(f"{b.id}: cỡ cú sốc {s.factor} phải là S, M hoặc L")
            if s.priced_in not in model.priced_in:
                raise ScenarioError(f"{b.id}: mức đã vào giá {s.priced_in!r} không có")


def core_move(shock: Shock, model: FactorModel) -> float:
    f = model.factor(shock.factor)
    return shock.direction * f.sizes[shock.size] * model.priced_in[shock.priced_in]


def propagate(branch: Branch, model: Optional[FactorModel] = None) -> Propagation:
    model = model or default_model()
    validate([Branch(branch.id, branch.name, 1.0, branch.shocks, branch.regime)], model)
    cov = model.cov[branch.regime]
    n = len(cov)
    core = [model.index(s.factor) for s in branch.shocks]
    dc = [core_move(s, model) for s in branch.shocks]
    rest = [i for i in range(n) if i not in core]
    moves = [0.0] * n
    lift = linalg.zeros(n, len(core))
    residual = [row[:] for row in cov]
    core_cov = linalg.zeros(len(core), len(core))
    if core:
        s_cc = linalg.sub(cov, core, core)
        s_nc = linalg.sub(cov, rest, core)
        beta = linalg.transpose(linalg.solve_spd(s_cc, linalg.transpose(s_nc)))  # (n−c) × c = Σnc Σcc⁻¹
        dn = linalg.matvec(beta, dc)
        for k, i in enumerate(core):
            moves[i] = dc[k]
            lift[i][k] = 1.0
        for r, i in enumerate(rest):
            moves[i] = dn[r]
            lift[i] = beta[r][:]
        cond = linalg.matmul(beta, linalg.sub(cov, core, rest))  # Σnc Σcc⁻¹ Σcn
        residual = linalg.zeros(n, n)
        for a, i in enumerate(rest):
            for b, j in enumerate(rest):
                residual[i][j] = cov[i][j] - cond[a][b]
        corr = model.corr[branch.regime]
        sd = [model.core_uncertainty * abs(x) for x in dc]
        core_cov = [[sd[a] * sd[b] * corr[core[a]][core[b]] for b in range(len(core))] for a in range(len(core))]
    return Propagation(branch, moves, core, lift, residual, core_cov)


def evaluate(
    holdings: List[Dict[str, Any]],
    branches: Iterable[Branch | Dict[str, Any]],
    model: Optional[FactorModel] = None,
) -> Dict[str, Any]:
    """A family's impact: per horizon the expected VND change and P5 / P10 / P50 / P90, the expected
    contributions by holding, asset class and factor, and each branch's own expected change."""
    model = model or default_model()
    branches = [b if isinstance(b, Branch) else Branch.from_dict(b) for b in branches]
    validate(branches, model)
    props = [propagate(b, model) for b in branches]
    ids = model.ids
    out_horizons: Dict[str, Any] = {}
    exp_keys: List[Exposure] = []
    for h, months in model.horizons.items():
        exps = exposures(holdings, model, months)
        exp_keys = exps
        real = [f.realisation[h] for f in model.factors]
        rows = [_branchwise(p, exps, ids, real, months) for p in props]
        probs = [b.probability for b in branches]
        mean = sum(p * r.mean for p, r in zip(probs, rows))
        by_holding = [sum(p * r.by_holding[k] for p, r in zip(probs, rows)) for k in range(len(exps))]
        by_factor = [sum(p * r.by_factor[i] for p, r in zip(probs, rows)) for i in range(len(ids))]
        total = round(mean)
        holding_vnd = _round_to_total(by_holding, total)
        classes: Dict[str, float] = {}
        for e, v in zip(exps, by_holding):
            classes[e.cls] = classes.get(e.cls, 0.0) + v
        class_names = sorted(classes)
        class_vnd = _round_to_total([classes[c] for c in class_names], total)
        factor_vnd = _round_to_total(by_factor, total)
        comps = [(r.mean, r.var) for r in rows]
        out_horizons[h] = {
            "months": months,
            "expected": total,
            **{name: round(_mixture_quantile(probs, comps, q)) for name, q in PERCENTILES},
            "by_holding": {e.key: v for e, v in zip(exps, holding_vnd)},
            "by_class": dict(zip(class_names, class_vnd)),
            "by_factor": {f: v for f, v in zip(ids, factor_vnd) if v},
            "branches": [
                {
                    "id": b.id,
                    "expected": round(r.mean),
                    "sd": round(math.sqrt(r.var)),
                    "sd_parts": {k: round(math.sqrt(v)) for k, v in r.parts.items()},
                }
                for b, r in zip(branches, rows)
            ],
        }
    return {
        "model": {"version": model.version, "hash": model.hash, "assumed": model.status == "assumed"},
        "horizons": out_horizons,
        "branches": [
            {
                "id": p.branch.id,
                "name": p.branch.name,
                "probability": p.branch.probability,
                "regime": p.branch.regime,
                "core": [ids[i] for i in p.core],
                "moves": {f: _r(m) for f, m in zip(ids, p.moves)},
            }
            for p in props
        ],
        "holdings": [
            {
                "key": e.key,
                "owner": e.owner,
                "class": e.cls,
                "name": e.name,
                "value": round(e.value) * e.sign,
                "loads": {f: _r(v) for f, v in e.loads.items()},
                "modelled": e.modelled,
                "method": e.method,
            }
            for e in exp_keys
        ],
    }


def factor_bands(branches: Iterable[Branch | Dict[str, Any]], model: Optional[FactorModel] = None) -> Dict[str, Any]:
    """Each factor's own forecast per horizon, in its unit: the expected move and P10 / P50 / P90 of the branch
    mixture — the same parts as a family's band (residual × months, core-size uncertainty), for one unit of one
    factor. What accuracy tracking (FEAT-18) scores against the realised move."""
    model = model or default_model()
    branches = [b if isinstance(b, Branch) else Branch.from_dict(b) for b in branches]
    validate(branches, model)
    props = [propagate(b, model) for b in branches]
    probs = [b.probability for b in branches]
    out: Dict[str, Any] = {}
    for h, months in model.horizons.items():
        rows = {}
        for i, f in enumerate(model.factors):
            r = f.realisation[h]
            comps = []
            for p in props:
                mean = r * p.moves[i]
                var = p.residual[i][i] * months * r * r
                if p.core:
                    lift = [x * r for x in p.lift[i]]
                    var += linalg.quad(p.core_cov, lift)
                comps.append((mean, max(var, 0.0)))
            rows[f.id] = {
                "expected": _r(sum(pr * c[0] for pr, c in zip(probs, comps))),
                **{name: _r(_mixture_quantile(probs, comps, q)) for name, q in PERCENTILES if name != "p5"},
            }
        out[h] = rows
    return out


def _branchwise(p: Propagation, exps: List[Exposure], ids: List[str], real: List[float], months: float) -> _Branchwise:
    n = len(ids)
    index = {f: i for i, f in enumerate(ids)}
    # VND per unit of each factor's move, summed over the family
    vnd = [0.0] * n
    by_holding = []
    for e in exps:
        signed = e.sign * e.value
        move = 0.0
        for f, per in e.loads.items():
            i = index[f]
            vnd[i] += signed * per
            move += per * real[i] * p.moves[i]
        by_holding.append(signed * move)
    realised = [vnd[i] * real[i] for i in range(n)]
    by_factor = [realised[i] * p.moves[i] for i in range(n)]
    mean = sum(by_factor)
    residual = linalg.quad(p.residual, vnd) * months
    core = 0.0
    if p.core:
        through = linalg.matvec(linalg.transpose(p.lift), realised)  # c: VND per unit of each core shock
        core = linalg.quad(p.core_cov, through)
    idio = sum((e.value * e.idio_var_month) * e.value * months for e in exps)
    parts = {"residual": max(residual, 0.0), "core": max(core, 0.0), "idiosyncratic": idio}
    return _Branchwise(mean, sum(parts.values()), by_holding, by_factor, parts)


def _mixture_cdf(probs: Sequence[float], comps: Sequence[Tuple[float, float]], x: float) -> float:
    out = 0.0
    for p, (mu, var) in zip(probs, comps):
        if var <= 0.0:
            out += p if x >= mu else 0.0
        else:
            out += p * linalg.normal_cdf((x - mu) / math.sqrt(var))
    return out


def _mixture_quantile(probs: Sequence[float], comps: Sequence[Tuple[float, float]], q: float) -> float:
    lo = min(mu - 10.0 * math.sqrt(var) for mu, var in comps) - 1.0
    hi = max(mu + 10.0 * math.sqrt(var) for mu, var in comps) + 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _mixture_cdf(probs, comps, mid) < q:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _round_to_total(values: Sequence[float], total: int) -> List[int]:
    """Round to the dong so the parts add up to ``total`` (largest remainder, ties by position)."""
    floors = [math.floor(v) for v in values]
    short = total - sum(floors)
    order = sorted(range(len(values)), key=lambda i: (-(values[i] - floors[i]), i))
    out = floors[:]
    if short >= 0:
        for i in order[:short]:
            out[i] += 1
    else:
        for i in list(reversed(order))[:-short]:
            out[i] -= 1
    return out


def _r(x: float) -> float:
    return round(x, 10) + 0.0  # + 0.0 turns −0.0 into 0.0
