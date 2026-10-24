"""Policy documents (``PD-0001``; the BRD's ``policy_documents``) and the radar (BRD-FR-306; F-D8).

A document is added by a CIO — fetched from the Official Gazette, or pasted with an official address — and
**verified** by a second CIO (never the one who added it, with a note of at least 20 characters): the
policy agent reads only verified documents, and the text's hash at verification is what its quotes are checked
against. Each document also carries where it stands — dự thảo → lấy ý kiến → đã ban hành → có hiệu lực, or dừng —
with a dated history; the radar lists them by their last change and marks what changed since the reader last
looked. Every step is audited.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from control import audit, db, roles
from control.errors import BadRequest, Conflict
from policy import source, text

STATUS = {
    "draft": "Dự thảo",
    "consultation": "Lấy ý kiến",
    "issued": "Đã ban hành",
    "effective": "Có hiệu lực",
    "dropped": "Dừng / bãi bỏ",
}
MAX_TEXT = 200_000


def get(doc_id: str, with_text: bool = True) -> Dict[str, Any]:
    with db.tx() as con:
        d = db.load(con.execute("select * from policy_documents where id = ?", (str(doc_id),)).fetchone())
    if d is None:
        raise BadRequest(f"không có văn bản {doc_id}")
    d["status_label"] = STATUS[d["status"]]
    d["articles"] = [{"label": a["label"], "title": a["title"]} for a in text.articles(d.get("text") or "")]
    if not with_text:
        d.pop("text", None)
    return d


def listing() -> List[Dict[str, Any]]:
    with db.tx() as con:
        ids = [r[0] for r in con.execute("select id from policy_documents order by created desc")]
    return [get(i, with_text=False) for i in ids]


def _save(d: Dict[str, Any], by: str, action: str, **audit_data: Any) -> Dict[str, Any]:
    data = {k: v for k, v in d.items() if k not in ("id", "status", "created", "status_label", "articles")}
    with db.tx() as con:
        con.execute(
            "update policy_documents set status = ?, data = ? where id = ?", (d["status"], db.dumps(data), d["id"])
        )
        audit.append(con, by, f"policy.{action}", d["id"], audit_data)
    return get(d["id"])


def add(item: Dict[str, Any], by: str, get_url: Optional[Callable[[str], bytes]] = None) -> Dict[str, Any]:
    """A CIO adds a document (Compliance's register before OWN-FB-18): ``{gazette_url}`` (fetched) or ``{source_url
    (official), title, number?, issuer?, issued?, text?, status}``. A document under discussion may have no text yet;
    the agent waits for it."""
    roles.require(by, "cio")
    item = dict(item or {})
    status = item.get("status") or ("issued" if item.get("gazette_url") else "draft")
    if status not in STATUS:
        raise BadRequest(f"status là một trong {', '.join(STATUS)}")
    if item.get("gazette_url"):
        try:
            doc = source.gazette(str(item["gazette_url"]).strip(), get=get_url)
        except source.SourceError as exc:
            raise BadRequest(f"Công báo: {exc}") from None
    else:
        url = str(item.get("source_url") or "").strip()
        if not source.official(url):
            raise BadRequest(f"source_url: https trên tên miền chính thức ({', '.join(source.OFFICIAL)})")
        title = " ".join(str(item.get("title") or "").split())
        if len(title) < 10:
            raise BadRequest("title: tên văn bản từ 10 ký tự")
        doc = {
            "title": title[:300],
            "number": str(item.get("number") or "").strip()[:80],
            "issuer": str(item.get("issuer") or "").strip()[:120] or source.issuer_of(item.get("number")),
            "issued": str(item.get("issued") or "").strip()[:20],
            "source_url": url,
            "file_url": "",
            "file_sha256": "",
            "text": str(item.get("text") or "")[:MAX_TEXT],
            "fetched": False,
        }
    if doc["text"] and len(text.norm(doc["text"])) < 200:
        raise BadRequest("text: văn bản từ 200 ký tự (hoặc để trống khi chưa có)")
    note = " ".join(str(item.get("note") or "").split())[:500]
    now = time.time()
    doc.update(
        added_by=by,
        verified=None,
        summary=None,
        history=[{"at": now, "by": by, "status": status, "note": note or "Thêm vào radar", "date": doc["issued"]}],
    )
    with db.tx() as con:
        dup = con.execute(
            "select id from policy_documents where json_extract(data, '$.source_url') = ?", (doc["source_url"],)
        ).fetchone()
        if dup:
            raise Conflict(f"Văn bản này đã có ({dup[0]})")
        did = f"PD-{db.next_seq(con, 'policy'):04d}"
        con.execute("insert into policy_documents values (?, ?, ?, ?)", (did, status, now, db.dumps(doc)))
        audit.append(
            con,
            by,
            "policy.add",
            did,
            {"source": doc["source_url"], "fetched": doc["fetched"], "file_sha256": doc["file_sha256"]},
        )
    return get(did)


def verify(doc_id: str, by: str, note: str) -> Dict[str, Any]:
    """A second CIO, not the one who added it, confirms the text is the source's (SEC-04): the agent may read it from
    now on."""
    roles.require(by, "cio")
    d = get(doc_id)
    note = " ".join(str(note or "").split())
    if by == d["added_by"]:
        raise roles.Forbidden("Người xác nhận nguồn phải khác người thêm văn bản (SEC-04)")
    if d["verified"]:
        raise Conflict(f"Đã xác nhận bởi {d['verified']['by']}")
    if not d.get("text"):
        raise Conflict("Chưa có văn bản để xác nhận")
    if len(note) < 20:
        raise BadRequest("Ghi chú xác nhận nguồn từ 20 ký tự")
    d["verified"] = {"by": by, "at": time.time(), "note": note[:500], "text_sha256": text.sha(d["text"])}
    return _save(d, by, "verify", note=note, text_sha256=d["verified"]["text_sha256"])


def set_status(doc_id: str, status: str, by: str, note: str, date: str = "") -> Dict[str, Any]:
    """Where the document stands now, with the date it happened and why it is known."""
    roles.require(by, "cio")
    d = get(doc_id)
    note = " ".join(str(note or "").split())
    if status not in STATUS:
        raise BadRequest(f"status là một trong {', '.join(STATUS)}")
    if status == d["status"]:
        raise Conflict(f"Văn bản đang {STATUS[status]}")
    if len(note) < 10:
        raise BadRequest("Ghi chú thay đổi từ 10 ký tự (nguồn của thông tin)")
    d["history"].append({"at": time.time(), "by": by, "status": status, "note": note[:500], "date": str(date)[:20]})
    old, d["status"] = d["status"], status
    return _save(d, by, "status", old=old, new=status, note=note)


def keep_summary(doc_id: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    d = get(doc_id)
    d["summary"] = summary
    return _save(d, "agent:policy", "summary", run=summary.get("run_id"), mode=summary.get("mode"))


def radar(since: float = 0.0) -> Dict[str, Any]:
    """F-D8 (our reading of “radar chính sách”, labelled đề xuất): every tracked document by its last change, what
    changed since ``since`` (the reader's last look), counts by status."""
    docs = listing()
    for d in docs:
        d["changed_at"] = d["history"][-1]["at"]
        d["new"] = since > 0 and d["created"] > since
        d["changed"] = since > 0 and not d["new"] and d["changed_at"] > since
    docs.sort(key=lambda d: d["changed_at"], reverse=True)
    return {
        "documents": docs,
        "counts": {k: sum(d["status"] == k for d in docs) for k in STATUS},
        "statuses": STATUS,
        "since": since,
        "changed": sum(d["new"] or d["changed"] for d in docs),
    }
