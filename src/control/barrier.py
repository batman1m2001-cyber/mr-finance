"""The client-data barrier (BRD-NFR-08, BRD_REMAINING_PLAN G-D2): no client's name, id or account number leaves for
a model outside the bank unless the ``client_ai`` configuration says it may.

``client_ai`` (Admin, two people):

- ``demo`` — today's behaviour (ADR-0018): the two client steps (reading a statement, the declaring chat) call
  ``llm:assistant`` and nothing is refused. The public demo runs this way.
- ``onprem`` — the two client steps call ``llm:onprem``; a model counts as inside only when its address's host is
  on ``onprem_hosts``, and ``llm:onprem`` off the list is refused every call (the steps then take their rules).
- ``off`` — the two client steps take their rule path; no model hears from a client.

In ``onprem`` and ``off`` every model call passes one check before it is sent (:func:`check`, an operonx resource
guard on every ``llm:`` resource, whichever op or agent makes the call): bound for a host not on the list and
carrying any client's identifier, it is refused with :class:`ClientDataRefused` (403), logged and audited, and
nothing is sent. The identifiers are every client's and household member's id and full name, their dependents'
names (seeded or declared) and every account, card, loan and property number in their source systems; a name
matches with or without its accents.
"""

from __future__ import annotations

import json
import re
import threading
import time
import unicodedata
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from operonx.core.loggings import LOGGER

MODES = ("demo", "onprem", "off")
ONPREM = "llm:onprem"
BASE = {"mode": "demo", "onprem_hosts": ["localhost", "127.0.0.1"]}

_INSTALLED: Dict[str, Any] = {}
_LOCK = threading.Lock()


class ClientDataRefused(PermissionError):
    """A prompt with client data was bound for a model outside the bank (BRD-NFR-08): 403, nothing sent."""

    http_status = 403


def setting() -> Dict[str, Any]:
    """The ``client_ai`` configuration in force."""
    from control import config

    return config.data("client_ai")


def mode() -> str:
    return setting()["mode"]


def host(key: str) -> str:
    """The host a resource's calls go to; empty when its config names none (counted as outside)."""
    from operonx.providers.ops._utils import resolve_hub

    try:
        url = getattr(resolve_hub().get_config(key), "base_url", None) or ""
    except Exception:  # noqa: BLE001 — a resource we cannot read is not one we can call inside
        return ""
    return (urlparse(url).hostname or "").lower()


def inside(key: str, hosts: Optional[Iterable[str]] = None) -> bool:
    """Whether ``key``'s model runs inside the bank: its host is on ``onprem_hosts``."""
    h = host(key)
    allowed = {str(x).strip().lower() for x in (setting()["onprem_hosts"] if hosts is None else hosts)}
    return bool(h) and h in allowed


def plain(text: str) -> str:
    """Case and accents folded, whitespace collapsed: “Nguyễn  Minh\\nKhoa” and “nguyen minh khoa” read the same."""
    t = unicodedata.normalize("NFD", str(text).replace("đ", "d").replace("Đ", "D"))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t).casefold()


def identifiers() -> List[str]:
    """Every client identifier the store holds (see the module docstring), folded with :func:`plain`. None in the
    AI zone, which holds no client (ZONE-01)."""
    from people import store as people
    from wealth import store
    from wealth.paths import in_zone

    if in_zone():
        return []
    out = set()
    with people._db() as con:
        for r in con.execute("select id, name, kind from people where kind in ('client', 'dependent')"):
            if r["kind"] == "client":
                out.add(r["id"])
            out.add(people._open(r["name"], r["id"], "name"))
        for r in con.execute("select client_id, source, data from client_sources"):
            _numbers(json.loads(people._open_source(r["data"], r["client_id"], r["source"])), out)
    for cid in people.client_ids(members=True):
        for d in store.profile(cid, "dependent"):
            if d.get("name"):
                out.add(d["name"])
    names = {plain(x).strip() for x in out if isinstance(x, str)}
    # a name is a full name (two words or more); an id or number is at least three characters
    return sorted(x for x in names if (" " in x if not re.search(r"\d", x) else len(x) >= 3))


def _numbers(x: Any, out: set) -> None:
    """The ids in a source system's record: accounts, cards, loans, properties, margin accounts."""
    if isinstance(x, dict):
        for k, v in x.items():
            if isinstance(v, str) and (k == "id" or k.endswith(("_id", "_no", "number")) or k in ("account", "cif")):
                out.add(v)
            else:
                _numbers(v, out)
    elif isinstance(x, list):
        for v in x:
            _numbers(v, out)


def _strings(x: Any, out: List[str], depth: int = 0) -> None:
    """Every piece of text in a call's arguments: messages, tool results, pydantic objects."""
    if depth > 12:
        return
    if isinstance(x, str):
        out.append(x)
    elif isinstance(x, (bytes, bytearray)):
        out.append(x.decode("utf-8", "ignore"))
    elif isinstance(x, dict):
        for v in x.values():
            _strings(v, out, depth + 1)
    elif isinstance(x, (list, tuple, set)):
        for v in x:
            _strings(v, out, depth + 1)
    elif hasattr(x, "model_dump"):
        _strings(x.model_dump(), out, depth + 1)
    elif x is not None and not isinstance(x, (int, float, bool)):
        out.append(str(x))


def found(text: str, ids: Optional[List[str]] = None) -> List[str]:
    """The client identifiers in ``text`` (folded), each a whole word."""
    ids = identifiers() if ids is None else ids
    if not ids:
        return []
    hay = plain(text)
    pattern = re.compile(r"(?<![\w-])(?:" + "|".join(re.escape(i) for i in ids) + r")(?![\w-])")
    return sorted(set(pattern.findall(hay)))


def check(key: str, method: str, args: tuple, kwargs: dict) -> None:
    """The guard on every ``llm:`` call (operonx ``ResourceHub.guard``): raise :class:`ClientDataRefused` when the
    mode is not ``demo``, the model is outside and the call carries a client identifier."""
    cfg = setting()
    if cfg["mode"] == "demo" or inside(key, cfg["onprem_hosts"]):
        return
    if key == ONPREM:  # the client steps' model, its host not on the list: none of its calls go out
        _refused(key, method, cfg["mode"], 0)
        where = host(key) or "(không rõ)"
        raise ClientDataRefused(f"{ONPREM}: máy chủ {where} không có trong onprem_hosts (BRD-NFR-08)")
    texts: List[str] = []
    _strings((args, kwargs), texts)
    hits = found("\n".join(texts))
    if not hits:
        return
    _refused(key, method, cfg["mode"], len(hits))
    raise ClientDataRefused(
        f"Dữ liệu khách hàng không được gửi tới mô hình ngoài ngân hàng ({key}, chế độ {cfg['mode']}; BRD-NFR-08)"
    )


def _refused(key: str, method: str, mode_: str, hits: int) -> None:
    """Logged and audited — what was refused, never the identifiers themselves."""
    from control import audit, db

    LOGGER.warning("client-data barrier: %s.%s refused (%s, %d identifiers)", key, method, mode_, hits)
    try:
        with db.tx() as con:
            audit.append(con, "system", "ai.refused", key, {"method": method, "mode": mode_, "identifiers": hits})
    except Exception as e:  # noqa: BLE001 — the refusal stands even when the audit write fails
        LOGGER.warning("client-data barrier: audit write failed: %s", e)
    _COUNTS["refused"] += 1
    _COUNTS["last"] = time.time()


_COUNTS: Dict[str, Any] = {"refused": 0, "last": None}


def counts() -> Dict[str, Any]:
    """Refusals since the process started."""
    return dict(_COUNTS)


def install() -> None:
    """Guard every ``llm:`` resource of this process (idempotent); app/main.py calls it at import."""
    from operonx.core.registry import ResourceHub

    with _LOCK:
        if "remove" not in _INSTALLED:
            _INSTALLED["remove"] = ResourceHub.guard("llm:", check)


def uninstall() -> None:
    with _LOCK:
        remove = _INSTALLED.pop("remove", None)
    if remove:
        remove()


def guard(client: Any, key: str) -> Any:
    """A model client built outside the hub (views/agents._llm: another model name on the same resource), guarded
    as the hub's own are."""
    from operonx.core.registry.guards import guard_instance

    return guard_instance(client, key=key)
