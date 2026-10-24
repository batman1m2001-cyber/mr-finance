"""Newsletters, kept (``NL-0001``): DRAFT → PENDING_COMPLIANCE → APPROVED (a preview, never sent) or RETURNED (back
to the CIO) → … ; WITHDRAWN by the CIO. The author is a CIO; Compliance approves and the approver is never the author
(BRD-RULE-SEC-04). Distribution: Private and retail clients at the same time by default; Private earlier only with a
written reason Compliance reads (FR-801). Every step is audited."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from control import audit, db, roles
from control.errors import BadRequest, Conflict
from newsletter import compose
from research import conflict

EDITABLE = ("DRAFT", "RETURNED")
NEEDS = {"edit": "cio", "submit": "cio", "withdraw": "cio", "approve": "compliance", "return": "compliance"}


def _ts(text: Any) -> float:
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        raise BadRequest("send_at: thời điểm ISO có múi giờ, ví dụ 2026-10-20T08:00:00+07:00") from None
    if dt.tzinfo is None:
        raise BadRequest("send_at cần múi giờ (ví dụ +07:00)")
    return dt.astimezone(timezone.utc).timestamp()


def _distribution(given: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    g = dict(given or {})
    at = _ts(g["send_at"]) if g.get("send_at") else _next_morning()
    early = float(g.get("private_early_hours") or 0)
    if not 0 <= early <= 72:
        raise BadRequest("private_early_hours: 0–72 giờ")
    reason = str(g.get("early_reason") or "").strip()
    if early and len(reason) < 20:
        raise BadRequest("Cho khách Private nhận sớm hơn cần ghi căn cứ từ 20 ký tự để Tuân thủ xem (FR-801)")
    return {
        "retail_at": at,
        "private_at": at - early * 3600,
        "private_early_hours": early,
        "early_reason": reason if early else "",
    }


def _next_morning() -> float:
    lt = time.localtime(time.time() + 86400)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 8, 0, 0, 0, 0, -1))


def _body(text: Any) -> str:
    """The CIO's own words: paragraphs kept (blank lines between), spaces inside each folded."""
    paras = [" ".join(p.split()) for p in str(text or "").replace("\r", "").split("\n\n")]
    return "\n\n".join(p for p in paras if p)


def _labels(sections: List[Dict[str, Any]], author: str, letter_conflict: Dict[str, Any]) -> Dict[str, Any]:
    who = roles.users()[author]
    coi = sorted(
        {c for s in sections for c in s["conflicts"]}
        | ({conflict.disclosure(letter_conflict)} if letter_conflict.get("related") else set())
    )
    return {
        "ai": "Có AI hỗ trợ soạn (CIO duyệt)"
        if any(s["ai"] for s in sections)
        else "Soạn theo mẫu từ nhận định CIO duyệt"
        if sections
        else "Bài viết của CIO, không dùng AI",
        "responsible": f"{who['name']} — {who['title']}",
        "time": time.strftime("%H:%M %d/%m/%Y", time.localtime()),
        "not_advice": compose.NOT_ADVICE,
        "contact": compose.CONTACT,
        "conflicts": coi or [conflict.NONE],
    }


def _section_text(sections: List[Dict[str, Any]]) -> List[str]:
    return [t for s in sections for t in (s.get("heading", s["event"]), *s["impacts"])]


def _covered(sections: List[Dict[str, Any]]) -> List[str]:
    """Parties the quoted research already discloses: the letter carries that disclosure, no second declaration."""
    return [p for s in sections for p in s.get("parties", [])]


def get(nid: str) -> Dict[str, Any]:
    with db.tx() as con:
        n = db.load(con.execute("select * from newsletters where id = ?", (str(nid),)).fetchone())
    if n is None:
        raise BadRequest(f"không có bản tin {nid}")
    return n


def listing() -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from newsletters order by created desc").fetchall()
    return [{k: v for k, v in db.load(r).items() if k not in ("sections",)} for r in rows]


def _save(n: Dict[str, Any], status: str, by: str, action: str, note: str = "", **audit_data: Any) -> Dict[str, Any]:
    now = time.time()
    n["history"].append({"at": now, "by": by, "status": status, "note": note})
    data = {k: v for k, v in n.items() if k not in ("id", "status", "created")}
    with db.tx() as con:
        con.execute("update newsletters set status = ?, data = ? where id = ?", (status, db.dumps(data), n["id"]))
        audit.append(con, by, f"newsletter.{action}", n["id"], {"status": status, "note": note, **audit_data})
    return get(n["id"])


def _check(n: Dict[str, Any]) -> Dict[str, Any]:
    n["labels"] = _labels(n["sections"], n["author"], n["conflict"])
    found = compose.guard(n)
    n["guard"] = {"ok": not found, "findings": found}
    return n


async def draft(
    view_ids: List[str],
    by: str,
    title: str = "",
    mode: str = "template",
    distribution: Optional[Dict[str, Any]] = None,
    conflict_: Any = None,
    body: str = "",
) -> Dict[str, Any]:
    """A CIO drafts from 1–6 approved views, or writes an article of their own (a body, no views: their news or a
    policy note), which goes to Private clients only (OWN-FB-15)."""
    roles.require(by, "cio")
    ids = list(dict.fromkeys(str(v) for v in (view_ids or [])))
    text = _body(body)
    if len(ids) > 6 or not (ids or text):
        raise BadRequest("Chọn 1–6 nhận định đã duyệt hoặc viết nội dung bài")
    if text and not 40 <= len(text) <= 6000:
        raise BadRequest("Nội dung bài từ 40 đến 6000 ký tự")
    if not ids:
        mode = "article"
    elif mode not in ("template", "agent"):
        raise BadRequest("mode là template hoặc agent")
    try:
        sections = [compose.section(v) for v in ids]
    except (ValueError, KeyError) as exc:
        raise Conflict(str(exc)) from None
    title = str(title or "").strip() or f"{'Bản tin thị trường' if ids else 'Bài viết'} {time.strftime('%d/%m/%Y')}"
    findings: List[str] = []
    if mode == "article":
        intro, written_by = "", by
    elif mode == "agent":
        intro, written_by, findings = await compose.agent_intro(sections)
    else:
        intro, written_by = compose.template_intro(sections), "template"
    try:
        coi = conflict.declare(conflict_, title, intro, text, *_section_text(sections), covered=_covered(sections))
    except conflict.ConflictError as exc:
        raise BadRequest(str(exc)) from None
    n = {
        "title": title[:200],
        "intro": intro,
        "body": text,
        "audience": "all" if ids else "private",
        "sections": sections,
        "view_ids": ids,
        "author": by,
        "mode": mode,
        "intro_by": written_by,
        "distribution": _distribution(distribution),
        "conflict": coi,
        "agent_findings": findings,
        "history": [],
        "sent": False,
    }
    n = _check(n)
    if mode == "agent" and written_by == "live" and not n["guard"]["ok"]:  # the agent's words fail: the template's
        n["agent_findings"] = [
            f"Phần mở đầu do AI viết không qua kiểm tra nội dung ({'; '.join(n['guard']['findings'])}): dùng mẫu"
        ]
        n["intro"], n["intro_by"] = compose.template_intro(sections), "template"
        n = _check(n)
    now = time.time()
    n["history"] = [{"at": now, "by": by, "status": "DRAFT", "note": ""}]
    with db.tx() as con:
        nid = f"NL-{db.next_seq(con, 'newsletter'):04d}"
        con.execute("insert into newsletters values (?, ?, ?, ?)", (nid, "DRAFT", now, db.dumps(n)))
        audit.append(con, by, "newsletter.draft", nid, {"views": ids, "mode": mode, "intro_by": n["intro_by"]})
    return get(nid)


def act(nid: str, action: str, by: str, note: str = "", changes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """edit / submit / withdraw (the CIO), approve / return (Compliance, never the author)."""
    if action not in NEEDS:
        raise BadRequest("action là edit, submit, approve, return hoặc withdraw")
    roles.require(by, NEEDS[action])  # who may, before whether the letter exists
    n = get(nid)
    note = str(note or "").strip()
    if action == "edit":
        if n["status"] not in EDITABLE:
            raise Conflict(f"Chỉ sửa được bản nháp hoặc bản bị trả lại (đang {n['status']})")
        ch = dict(changes or {})
        if "title" in ch:
            n["title"] = str(ch["title"]).strip()[:200] or n["title"]
        if "intro" in ch:
            n["intro"], n["intro_by"] = " ".join(str(ch["intro"]).split())[:1500], by
        if "body" in ch:
            text = _body(ch["body"])
            if not (text or n["sections"]):
                raise BadRequest("Bài viết không có nhận định nào cần nội dung")
            if text and not 40 <= len(text) <= 6000:
                raise BadRequest("Nội dung bài từ 40 đến 6000 ký tự")
            n["body"] = text
        if "headings" in ch:  # {view_id: text}: a section's heading, reworded by the CIO
            given = dict(ch["headings"] or {})
            for sec in n["sections"]:
                text = " ".join(str(given.get(sec["view_id"]) or "").split())[:200]
                if text:
                    sec["heading"] = text
        if "distribution" in ch:
            n["distribution"] = _distribution(ch["distribution"])
        if {"conflict", "title", "intro", "body", "headings"} & set(ch):
            try:
                n["conflict"] = conflict.declare(
                    ch.get("conflict", n["conflict"]),
                    n["title"],
                    n["intro"],
                    n.get("body", ""),
                    *_section_text(n["sections"]),
                    covered=_covered(n["sections"]),
                )
            except conflict.ConflictError as exc:
                raise BadRequest(str(exc)) from None
        n = _check(n)
        return _save(n, n["status"], by, "edit", note or "Sửa", fields=sorted(ch))
    if action == "submit":
        if n["status"] not in EDITABLE:
            raise Conflict(f"Không gửi duyệt được khi đang {n['status']}")
        n = _check(n)
        if not n["guard"]["ok"]:
            raise Conflict("Chưa gửi được: " + "; ".join(n["guard"]["findings"]))
        return _save(n, "PENDING_COMPLIANCE", by, "submit", note)
    if action in ("approve", "return"):
        if by == n["author"]:
            raise roles.Forbidden("Người duyệt bản tin phải khác người soạn (SEC-04)")
        if n["status"] != "PENDING_COMPLIANCE":
            raise Conflict(f"Bản tin không chờ duyệt (đang {n['status']})")
        if action == "return" and len(note) < 10:
            raise BadRequest("Trả lại cần ghi lý do từ 10 ký tự")
        if action == "approve":
            n = _check(n)
            if not n["guard"]["ok"]:
                raise Conflict("Không duyệt được: " + "; ".join(n["guard"]["findings"]))
            n["approved_by"] = by
            return _save(n, "APPROVED", by, "approve", note or "Duyệt", preview_only=True)
        return _save(n, "RETURNED", by, "return", note)
    if n["status"] == "WITHDRAWN":  # withdraw
        raise Conflict("Đã rút")
    return _save(n, "WITHDRAWN", by, "withdraw", note)
