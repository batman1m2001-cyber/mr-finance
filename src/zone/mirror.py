"""The AI zone's side of the sync (ZONE-06): TCB's bundle, checked (signature with ``MF_ZONE_KEY``, form, each
catalogue by its kind's own check) before anything is kept; then each catalogue in force here as TCB approved it
(``config.mirror``) and the released research as news items."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from control import config
from inbox import sign
from news import store as news_store
from zone import sync


def receive(body: bytes, signature: Optional[str]) -> Tuple[int, Dict[str, Any]]:
    key = sync.zone_key()
    if key and not sign.valid(body, signature, key):
        return 401, {"error": "Chưa ký hoặc chữ ký sai (MF_ZONE_KEY)"}
    try:
        got = json.loads(body)
    except ValueError:
        return 400, {"error": "Không đọc được JSON"}
    if not isinstance(got, dict) or got.get("version") != sync.VERSION:
        return 400, {"error": f"Gói phải là đối tượng JSON, version {sync.VERSION}"}
    cats, research = got.get("catalogues"), got.get("research", [])
    if not isinstance(cats, dict) or not isinstance(research, list):
        return 400, {"error": "catalogues: đối tượng; research: danh sách"}
    for kind, c in cats.items():
        if kind not in sync.KINDS or not isinstance(c, dict) or not str(c.get("id") or ""):
            return 400, {"error": f"Danh mục {kind!r} không được gửi vào vùng AI"}
        try:
            config.KINDS[kind]["check"](c.get("data"))
        except ValueError as exc:
            return 400, {"error": f"{kind}: {exc}"}
    for it in research:
        if (
            not isinstance(it, dict)
            or it.get("source") != "research"
            or not all(it.get(k) for k in ("url_key", "title_key", "title", "ingested"))
        ):
            return 400, {"error": "research[]: mỗi mục là tin nghiên cứu đã phát hành, đủ url_key, title_key, title"}
    applied = [v["id"] for k, c in cats.items() if (v := config.mirror(k, c["data"], str(c["id"])))]
    added, _ = news_store.add([{**{k: it.get(k) for k in sync.NEWS_FIELDS}, "status": "new"} for it in research])
    return 200, {"applied": applied, "research_added": len(added)}
