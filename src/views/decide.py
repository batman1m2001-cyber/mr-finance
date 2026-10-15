"""What the CIO may do with a view, and when (BRD FR-304, BR-06, BR-07, BR-14, F04, F11, F12).

- ``edit`` the summary, impact rows or scenarios: checked against the schema, kept with the reason,
  and the view goes back to the challenger on the new content (F12).
- ``respond`` to findings: accept or reject each, with a reason.
- ``approve``, ``return`` (rework: the agent runs again as a new version), ``reject``, ``withdraw``
  (an approved view): each with a reason, each once per ``idem_key``.

Approval needs every check in ``checks()``; the UI shows the same list.
"""

from __future__ import annotations

import copy
import time
from typing import Any, Dict, List, Optional

from engine import ScenarioError, default_model
from engine.scenario import Branch, validate
from events import store as events
from views import schema
from views import store as vstore

ACTIONS = ("edit", "respond", "challenge", "approve", "return", "reject", "withdraw")
FROM = {
    "edit": ("PENDING_CHALLENGE", "PENDING_APPROVAL"),
    "respond": ("PENDING_APPROVAL",),
    "challenge": ("PENDING_CHALLENGE",),  # the challenger failed: run it again
    "approve": ("PENDING_APPROVAL",),
    "return": ("PENDING_CHALLENGE", "PENDING_APPROVAL"),
    "reject": ("PENDING_CHALLENGE", "PENDING_APPROVAL"),
    "withdraw": ("APPROVED",),
}
TO = {"approve": "APPROVED", "return": "REWORK_REQUESTED", "reject": "REJECTED", "withdraw": "WITHDRAWN"}
MIN_REASON = 5


class DecisionError(ValueError):
    pass


def checks(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The approval conditions, each with whether it holds now and why not."""
    cur = view.get("current") or {}
    out: List[Dict[str, Any]] = []

    def add(code: str, label: str, ok: bool, detail: str = "") -> None:
        out.append({"code": code, "label": label, "ok": bool(ok), "detail": "" if ok else detail})

    add("a", "Đang chờ duyệt", view["status"] == "PENDING_APPROVAL", f"Trạng thái hiện tại: {view['status']}")
    ch = vstore.latest_challenge(view["id"])
    fresh = bool(ch) and ch.get("content_hash") == view.get("content_hash")
    add("b", "Đã phản biện trên nội dung hiện hành", fresh, "Nội dung đã sửa sau lần phản biện cuối")
    open_critical = []
    if ch:
        answered = (view.get("responses") or {}).get(ch["id"], {})
        open_critical = [f["title"] for f in ch["findings"] if f["severity"] == "critical" and f["id"] not in answered]
    add(
        "c",
        "Mọi phát hiện Nghiêm trọng đã được trả lời",
        fresh and not open_critical,
        "Chưa trả lời: " + "; ".join(open_critical) if open_critical else "Chưa có phản biện",
    )
    branches = (cur.get("scenarios") or {}).get("branches") or []
    add("d", "Có ít nhất 2 nhánh kịch bản", len(branches) >= 2, f"Có {len(branches)} nhánh")
    engine_ok, engine_err = True, ""
    try:
        validate(
            [Branch.from_dict(b) for b in schema.to_engine(branches, cur["scenarios"]["priced_in"])], default_model()
        )
    except (ScenarioError, KeyError, TypeError, ZeroDivisionError) as exc:
        engine_ok, engine_err = False, str(exc)
    add("e", "Kịch bản hợp lệ với động cơ", engine_ok and bool(branches), engine_err or "Thiếu kịch bản")
    independent = bool(ch) and ch.get("independent", False)
    add("f", "Phản biện độc lập (mô hình khác Agent CIO)", independent, "Phản biện chưa độc lập")
    try:
        ev = events.get(view["event_id"])
        held = ev["held"]
    except events.EventError:
        held = ["?"]
    add("g", "Không còn tin bị giữ vì danh sách hạn chế", not held, "Đang giữ: " + ", ".join(held))
    return out


def _require_reason(reason: Optional[str], action: str) -> str:
    r = str(reason or "").strip()
    if len(r) < MIN_REASON:
        raise DecisionError(f"“{action}” cần lý do (từ {MIN_REASON} ký tự)")
    return r


def apply_edit(view: Dict[str, Any], edits: Dict[str, Any], by: str, reason: str) -> Dict[str, Any]:
    if not isinstance(edits, dict) or not edits or set(edits) - {"summary", "impacts", "scenarios"}:
        raise DecisionError("edits chỉ gồm summary, impacts, scenarios")
    before = view["current"]
    after = {**copy.deepcopy(before), **copy.deepcopy(edits)}
    ev = events.get(view["event_id"])
    errs = schema.check(after, ev["news_ids"])
    if errs:
        raise DecisionError("Bản sửa không hợp lệ: " + "; ".join(errs[:5]))
    view = dict(view)
    view["current"] = after
    view["content_hash"] = vstore.content_hash(after)
    view["edits"] = view.get("edits", []) + [
        {
            "at": time.time(),
            "by": by,
            "reason": reason,
            "changed": sorted(edits),
            "before_hash": vstore.content_hash(before),
            "after_hash": view["content_hash"],
        }
    ]
    return vstore.save(view, "PENDING_CHALLENGE", by, f"CIO sửa {', '.join(sorted(edits))}: {reason}")


def apply_responses(view: Dict[str, Any], responses: Dict[str, Any], by: str) -> Dict[str, Any]:
    ch = vstore.latest_challenge(view["id"])
    if ch is None:
        raise DecisionError("Chưa có phản biện để trả lời")
    ids = {f["id"] for f in ch["findings"]}
    if not isinstance(responses, dict) or not responses:
        raise DecisionError("responses: {mã phát hiện: {decision: accept|reject, reason}}")
    got = dict((view.get("responses") or {}).get(ch["id"], {}))
    for fid, r in responses.items():
        if fid not in ids:
            raise DecisionError(f"Không có phát hiện {fid} trong lần phản biện {ch['id']}")
        if not isinstance(r, dict) or r.get("decision") not in ("accept", "reject"):
            raise DecisionError(f"{fid}: decision là accept hoặc reject")
        text = str(r.get("reason") or "").strip()
        if len(text) < 10:
            raise DecisionError(f"{fid}: cần lý do từ 10 ký tự")
        got[fid] = {"decision": r["decision"], "reason": text, "by": by, "at": time.time()}
    view = dict(view)
    view["responses"] = {**(view.get("responses") or {}), ch["id"]: got}
    return vstore.save(view, view["status"], by)


def supersede_older(view: Dict[str, Any], by: str) -> List[str]:
    """A newly approved version replaces the event's previous approved one."""
    out = []
    for v in vstore.for_event(view["event_id"]):
        if v["id"] != view["id"] and v["status"] == "APPROVED":
            vstore.save(v, "SUPERSEDED", by, f"Thay bởi {view['id']}")
            out.append(v["id"])
    return out
