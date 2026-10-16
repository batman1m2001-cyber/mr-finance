"""The formula behind every kind of number the pages show (BRD-NFR-11, BRD_REMAINING_PLAN G-D1).

Each metric names what it is (``label``), how it is made in words (``formula``), the inputs a page passes with
it (``inputs``: key → label; the values come from the same server answer as the number), and the function that
computes it (``code``: ``path::name``, checked to exist by ``tests/test_explain.py`` so a formula cannot outlive
its code). A setting or a parameter is an input, not a result: its formula says where it comes from.

A page renders a number with ``n(text, metric, inputs)`` (web/core/core.js); the shared drawer reads this
catalogue from ``GET /api/how``. The browser test ``tests/ui/test_how.py`` fails on any money or percent figure
outside a ``data-metric``, except a client's own quoted words (``data-quote``), chart axis ticks (``data-axis``)
and the text of an explanation itself (``data-explains``).
"""

from __future__ import annotations

from typing import Any, Dict

M: Dict[str, Dict[str, Any]] = {}


def metric(mid: str, label: str, formula: str, code: str, **inputs: str) -> None:
    assert mid not in M, mid
    M[mid] = {"id": mid, "label": label, "formula": formula, "code": code, "inputs": inputs}


def catalogue() -> Dict[str, Dict[str, Any]]:
    return M
