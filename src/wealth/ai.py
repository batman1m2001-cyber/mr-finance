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
