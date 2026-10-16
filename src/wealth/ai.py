"""Whether the AI steps run (docs/PLAN.md D2).

``MF_AI``: ``on`` always, ``off`` never, ``auto`` (the default) when ``LLM_API_KEY`` is set. When
they do not run, every feature takes its rule path, so the demo never needs a network.
"""

from __future__ import annotations

import os


def enabled() -> bool:
    mode = (os.environ.get("MF_AI") or "auto").strip().lower()
    if mode in ("on", "1", "true"):
        return True
    if mode in ("off", "0", "false"):
        return False
    return bool((os.environ.get("LLM_API_KEY") or "").strip())


def client_model() -> str | None:
    """The model the two client steps (reading a statement, the declaring chat) use, by the ``client_ai``
    configuration (BRD-NFR-08, control/barrier.py): ``assistant`` in demo when AI is on, ``onprem`` in onprem when
    an on-premises model is set (``LLM_ONPREM_MODEL``), its host is on ``onprem_hosts`` and AI is not switched off,
    None — the rules — otherwise."""
    from control import barrier

    mode = barrier.mode()
    if mode == "demo":
        return "assistant" if enabled() else None
    if mode == "onprem":
        off = (os.environ.get("MF_AI") or "auto").strip().lower() in ("off", "0", "false")
        ready = not off and (os.environ.get("LLM_ONPREM_MODEL") or "").strip() and barrier.inside(barrier.ONPREM)
        return "onprem" if ready else None
    return None
