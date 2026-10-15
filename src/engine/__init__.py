"""The scenario engine: approved CIO branches + holdings → VND impact bands. Pure, deterministic,
no I/O beyond reading the factor model file, no AI (BRD §9, docs/NEWS_IMPACT_PLAN.md phase N0)."""

from engine.model import FactorModel, FactorModelError, default_model
from engine.scenario import Branch, ScenarioError, Shock, evaluate, propagate

__all__ = [
    "Branch",
    "FactorModel",
    "FactorModelError",
    "ScenarioError",
    "Shock",
    "default_model",
    "evaluate",
    "propagate",
]
