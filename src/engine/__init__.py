"""The scenario engine: approved CIO branches + holdings → VND impact bands. Pure, deterministic,
no I/O beyond reading the factor model file, no AI (BRD §9, docs/NEWS_IMPACT_PLAN.md phase N0)."""

from engine.model import FactorModel, FactorModelError, default_model
from engine.scenario import Branch, ScenarioError, Shock, evaluate, factor_bands, propagate

ENGINE_VERSION = "engine-1"  # bump when a formula changes: runs record which one computed them

__all__ = [
    "ENGINE_VERSION",
    "Branch",
    "FactorModel",
    "FactorModelError",
    "ScenarioError",
    "Shock",
    "default_model",
    "evaluate",
    "factor_bands",
    "propagate",
]
