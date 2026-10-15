"""The factor model: the 15 factors, their sizes and realisation, and a covariance per regime.

``FactorModel.load()`` reads data/factor_model.json (scripts/make_factor_model.py) and checks it the
way BRD 9.1 asks before it is used: correlations in [−1, 1], symmetric, positive definite. A model
that fails is refused (``FactorModelError``), never repaired silently. The stressed regime is then
built from the normal one as the BRD describes: correlations × 1.4, clipped to ±0.85, four pairs
overridden, made positive definite by eigenvalue clipping; volatilities × the stress multiplier,
at least 1.2.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from engine import linalg
from engine.linalg import Matrix

REGIMES = ("normal", "stressed")
SIZES = ("S", "M", "L")


class FactorModelError(ValueError):
    """The factor model file is not one the engine may run on."""


@dataclass(frozen=True)
class Factor:
    id: str
    name: str
    group: str
    unit: str  # pct (% change), bp (basis points), pp (percentage points), sd (standard deviations)
    sizes: Dict[str, float]
    realisation: Dict[str, float]
    vol_month: float
    stress_vol_multiplier: float
    brd_parameter: str
    assumed: bool


@dataclass
class FactorModel:
    version: str
    status: str
    note: str
    horizons: Dict[str, float]  # horizon → months
    priced_in: Dict[str, float]
    core_uncertainty: float
    factors: List[Factor]
    loadings: Dict[str, Any]
    hash: str
    corr: Dict[str, Matrix] = field(default_factory=dict)  # regime → correlation
    cov: Dict[str, Matrix] = field(default_factory=dict)  # regime → monthly covariance
    # how far making the stressed matrix positive definite moved it: the smallest eigenvalue
    # before, and the largest change to any correlation (shown with the model, never hidden)
    stressed_repair: Dict[str, float] = field(default_factory=dict)

    @property
    def ids(self) -> List[str]:
        return [f.id for f in self.factors]

    def index(self, factor_id: str) -> int:
        try:
            return self.ids.index(factor_id)
        except ValueError:
            raise FactorModelError(f"unknown factor {factor_id!r}") from None

    def factor(self, factor_id: str) -> Factor:
        return self.factors[self.index(factor_id)]

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "FactorModel":
        factors = [
            Factor(
                id=f["id"],
                name=f["name"],
                group=f["group"],
                unit=f["unit"],
                sizes={k: float(v) for k, v in f["sizes"].items()},
                realisation={k: float(v) for k, v in f["realisation"].items()},
                vol_month=float(f["vol_month"]),
                stress_vol_multiplier=float(f["stress_vol_multiplier"]),
                brd_parameter=f.get("brd_parameter", ""),
                assumed=bool(f.get("assumed", True)),
            )
            for f in raw["factors"]
        ]
        canonical = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        model = cls(
            version=raw["version"],
            status=raw.get("status", "assumed"),
            note=raw.get("note", ""),
            horizons={k: float(v) for k, v in raw["horizons"].items()},
            priced_in={k: float(v) for k, v in raw["priced_in"].items()},
            core_uncertainty=float(raw["core_uncertainty"]),
            factors=factors,
            loadings=raw.get("loadings", {}),
            hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        )
        model._build(raw)
        return model

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "FactorModel":
        if path is None:
            return default_model()
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    # -- checks and regimes ----------------------------------------------------------------

    def _build(self, raw: Dict[str, Any]) -> None:
        ids = self.ids
        n = len(ids)
        if len(set(ids)) != n:
            raise FactorModelError("duplicate factor ids")
        for f in self.factors:
            if set(f.sizes) != set(SIZES) or any(v <= 0 for v in f.sizes.values()):
                raise FactorModelError(f"{f.id}: sizes must be S, M, L and positive")
            if set(f.realisation) != set(self.horizons) or any(not 0 <= v <= 1 for v in f.realisation.values()):
                raise FactorModelError(f"{f.id}: realisation must give each horizon a share in [0, 1]")
            if f.vol_month <= 0:
                raise FactorModelError(f"{f.id}: volatility must be positive")
        corr = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for a, b, rho in raw["correlations"]:
            i, j = self.index(a), self.index(b)
            if i == j:
                raise FactorModelError(f"{a}: a factor's correlation with itself is 1")
            if not -1.0 <= rho <= 1.0:
                raise FactorModelError(f"correlation {a}–{b} = {rho} is outside [−1, 1]")
            if corr[i][j] not in (0.0, rho):
                raise FactorModelError(f"correlation {a}–{b} given twice with different values")
            corr[i][j] = corr[j][i] = float(rho)
        check_correlation(corr)

        st = raw["stressed"]
        stressed = [
            [1.0 if i == j else max(-st["clip"], min(st["clip"], corr[i][j] * st["scale"])) for j in range(n)]
            for i in range(n)
        ]
        for a, b, rho in st.get("overrides", []):
            i, j = self.index(a), self.index(b)
            stressed[i][j] = stressed[j][i] = float(rho)
        before = min(linalg.eigh(stressed)[0])
        repaired = linalg.clip_to_correlation(stressed) if before < 0.01 else stressed
        self.stressed_repair = {
            "min_eigenvalue_before": round(before, 6),
            "max_change": round(max(abs(a - b) for ra, rb in zip(repaired, stressed) for a, b in zip(ra, rb)), 6),
        }
        stressed = repaired
        check_correlation(stressed)

        vols = [f.vol_month for f in self.factors]
        floor = float(st.get("min_vol_multiplier", 1.2))
        svols = [f.vol_month * max(floor, f.stress_vol_multiplier) for f in self.factors]
        self.corr = {"normal": corr, "stressed": stressed}
        self.cov = {"normal": _cov(corr, vols), "stressed": _cov(stressed, svols)}

    def vol(self, regime: str) -> List[float]:
        c = self.cov[regime]
        return [c[i][i] ** 0.5 for i in range(len(c))]


def check_correlation(r: Matrix) -> None:
    n = len(r)
    if any(len(row) != n for row in r):
        raise FactorModelError("correlation matrix is not square")
    if not linalg.is_symmetric(r):
        raise FactorModelError("correlation matrix is not symmetric")
    if any(abs(r[i][i] - 1.0) > 1e-9 for i in range(n)):
        raise FactorModelError("correlation matrix needs a unit diagonal")
    if any(not -1.0 <= r[i][j] <= 1.0 for i in range(n) for j in range(n)):
        raise FactorModelError("a correlation is outside [−1, 1]")
    try:
        linalg.cholesky(r)
    except ValueError:
        raise FactorModelError("correlation matrix is not positive definite") from None


def _cov(corr: Matrix, vols: List[float]) -> Matrix:
    n = len(corr)
    return [[corr[i][j] * vols[i] * vols[j] for j in range(n)] for i in range(n)]


_ACTIVE: Dict[str, FactorModel] = {}


def default_model() -> FactorModel:
    """The factor model in force: the ACTIVE version of the versioned configuration (FR-701), which is the
    shipped data/factor_model.json until a CIO-approved change replaces it. Built once per version."""
    from control import config

    h = config.active_hash("factor_model")
    if h not in _ACTIVE:
        _ACTIVE[h] = FactorModel.from_dict(config.data("factor_model"))
    return _ACTIVE[h]
