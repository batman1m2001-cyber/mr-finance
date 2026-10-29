"""Long-term memory and the archive (A4, assistant.md §5, ADR-0028): what OneWealth keeps of a person's
conversations, and the rules on it. The store is operonx-agents' ``SQLiteMemoryStore`` in ``assistant.db``.

- **Items**: ``preference`` (Sở thích), ``goal`` (Mục tiêu), ``fact`` (Thông tin, 180 days), ``constraint``
  (Giới hạn); one sentence of at most 200 characters, with its source (the conversation and the turn) and a
  confidence. Written when the person asks (“hãy nhớ…”, confirmed like every write) or, from A6, by the
  consolidator; corrected or forgotten on the Bộ nhớ page or by asking.
- **What is never kept** (:func:`refused`): an amount, a percentage, an account or card number, or anyone's name
  or identifier outside the person's own family. The rule is checked on every write, whoever writes.
- **The archive** is the conversations themselves (``turns``); :func:`search_history` scans one person's.
- Every call is keyed by the owner the server resolved (``conversations.owner``); no tool takes an owner.
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Dict, List, Optional

from operonx_agents import SQLiteMemoryStore
from operonx_agents.memory import search

from assistant import conversations as conv
from assistant.base import Ctx, Param, Tool, ToolFailed
from control import barrier, crypto
from control.roles import ROLES

KINDS = {"preference": "Sở thích", "goal": "Mục tiêu", "fact": "Thông tin", "constraint": "Giới hạn"}
DAY = 86400.0
EXPIRES = {"fact": 180 * DAY}  # a fact goes stale; preferences, goals and constraints stay until changed
MAX_CHARS = 200
IN_PROMPT = 15  # the active items the assistant's instructions carry

AMOUNT = re.compile(
    r"\d[\d.,]*\s*(?:tỷ|tỉ|triệu|tr\b|nghìn|ngàn|k\b|đồng|đ\b|vnd|vnđ|usd|\$|%|phần trăm)"
    r"|\d{1,3}(?:[.,]\d{3}){2,}",  # 5.000.000
    re.I,
)
ACCOUNT = re.compile(r"\d{6,}|\d{3,}[-‐]\w+")  # 190212345678, 1902-CASA-01


class Codec:
    """The text sealed with the data keys (control/crypto.py), bound to the item's place."""

    def encode(self, text: str, place: str) -> str:
        return crypto.seal(text, place.encode())

    def decode(self, text: str, place: str) -> str:
        return crypto.open_(text, place.encode())


_STORES: Dict[str, SQLiteMemoryStore] = {}


def store() -> SQLiteMemoryStore:
    p = str(conv.db_path())
    if p not in _STORES:
        with conv.db():  # the conversations' tables first: one file
            pass
        _STORES[p] = SQLiteMemoryStore(p, codec=Codec())
    return _STORES[p]


def family_names(ctx: Ctx) -> set:
    """The names a client's own items may hold: their family's (folded). Staff keep no client's name."""
    if ctx.role != "client" or not ctx.client_id:
        return set()
    from people import auth
    from people import store as people
    from wealth import fixtures
    from wealth import store as wealth

    head = fixtures.client(ctx.client_id).get("member_of") or ctx.client_id
    out = set()
    for cid in auth.visible(people.client_ids(members=True)):  # their own family only, under sign-in
        c = fixtures.client(cid)
        if cid == head or c.get("member_of") == head:
            out.add(c.get("name") or "")
            out.update(d.get("name") or "" for d in wealth.profile(cid, "dependent"))
    return {barrier.plain(x).strip() for x in out if x}


def refused(text: str, ctx: Ctx) -> Optional[str]:
    """Why ``text`` may not be kept, or None."""
    t = " ".join(str(text or "").split())
    if not t:
        return "nội dung trống"
    if len(t) > MAX_CHARS:
        return f"dài {len(t)} ký tự, tối đa {MAX_CHARS}"
    if AMOUNT.search(t):
        return "không lưu số tiền hay tỷ lệ"
    if ACCOUNT.search(t):
        return "không lưu số tài khoản, số thẻ hay mã giấy tờ"
    folded, own = barrier.plain(t), family_names(ctx)
    for ident in barrier.identifiers():
        if ident not in own and re.search(rf"(?<!\w){re.escape(ident)}(?!\w)", folded):
            return "không lưu thông tin của người khác"
    return None


def expires(kind: str) -> Optional[float]:
    return time.time() + EXPIRES[kind] if kind in EXPIRES else None


def view(item) -> Dict[str, Any]:
    d = item.to_dict()
    d.pop("owner", None)
    d["kind_label"] = KINDS.get(item.kind, item.kind)
    return d


async def items(ctx: Ctx) -> List[Dict[str, Any]]:
    return [view(i) for i in await store().items(conv.owner(ctx))]


async def remember(ctx: Ctx, kind: str, text: str, source: Optional[Dict[str, Any]] = None, confidence=1.0):
    if kind not in KINDS:
        raise ValueError(f"loại là một trong: {', '.join(KINDS)}")
    why = refused(text, ctx)
    if why:
        raise ValueError(f"Không ghi nhớ được: {why}")
    return await store().add(conv.owner(ctx), kind, " ".join(text.split()), source=source or {},
                             confidence=confidence, expires=expires(kind))  # fmt: skip


async def correct(ctx: Ctx, item_id: str, text: str, kind: Optional[str] = None):
    if kind is not None and kind not in KINDS:
        raise ValueError(f"loại là một trong: {', '.join(KINDS)}")
    why = refused(text, ctx)
    if why:
        raise ValueError(f"Không sửa được: {why}")
    got = await store().update(conv.owner(ctx), item_id, text=" ".join(text.split()), kind=kind,
                               **({"expires": expires(kind)} if kind else {}))  # fmt: skip
    if got is None:
        raise ValueError("Không có mục này")
    return got


async def forget(ctx: Ctx, item_id: str) -> bool:
    return await store().delete(conv.owner(ctx), item_id)


async def forget_all(ctx: Ctx) -> int:
    return await store().clear(conv.owner(ctx))


async def recall(ctx: Ctx, query: str = "", limit: int = IN_PROMPT) -> List[Dict[str, Any]]:
    return [view(i) for i in await search(store(), conv.owner(ctx), query, limit=limit)]


MARKS = re.compile(r"[\u0300-\u036f]")  # the combining marks Vietnamese decomposes to (NFD)
SPACES = re.compile(r"\s+")


def fast_fold(text: str) -> str:
    """``operonx_agents.memory.fold`` for Vietnamese text in one regex pass, not a per-character loop: the archive
    search folds every message (a year's archive: 1.6 M characters)."""
    t = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return SPACES.sub(" ", MARKS.sub("", t)).strip().casefold()


def search_history(ctx: Ctx, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """The person's messages (in this role) holding every word of ``query`` (folded), newest first, each with its
    conversation, time and author: a scan of one person's turns, the text being sealed (ADR-0028)."""
    words = fast_fold(query).split()
    if not words:
        return []
    out = []
    for t in conv.archive(ctx):
        for author, text in [("bạn", t["question"]), ("trợ lý", (t["answer"] or {}).get("text"))]:
            text = " ".join(str(text or "").split())
            hay = fast_fold(text)
            if text and all(w in hay for w in words):
                at = hay.find(words[0])
                out.append({"conversation_id": t["conversation_id"], "title": t["title"], "seq": t["seq"],
                            "at": t["at"], "author": author, "snippet": text[max(0, at - 60) : at + 140]})  # fmt: skip
    out.sort(key=lambda h: (-h["at"], h["author"] != "bạn"))
    return out[:limit]


# -- the assistant's tools (registry) ---------------------------------------------------------------------------

EVERYONE = ROLES


async def _recall(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    got = await recall(ctx, str(args.get("query") or ""))
    if not got:
        return {"text": "Chưa có điều gì được ghi nhớ về bạn.", "data": {"items": []}}
    text = "Điều bạn đã nhờ ghi nhớ: " + " ".join(f"({i['kind_label']}) {i['text']}." for i in got)
    return {"text": text, "data": {"items": [{"id": i["id"], "kind": i["kind"], "text": i["text"]} for i in got]}}


def _plan_remember(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    kind, text = args.get("kind"), " ".join(str(args.get("text") or "").split())
    if kind not in KINDS:
        raise ToolFailed(f"loại là một trong: {', '.join(KINDS)}")
    why = refused(text, ctx)
    if why:
        raise ToolFailed(f"Không ghi nhớ được: {why}")
    return {"summary": f"Ghi nhớ ({KINDS[kind]}): “{text}”?", "args": {"kind": kind, "text": text}}


async def _remember(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        item = await remember(ctx, args["kind"], args["text"], source={"conversation": ctx.conversation or None})
    except ValueError as exc:
        raise ToolFailed(str(exc)) from None
    return {"text": f"Đã ghi nhớ: “{item.text}”. Bạn xem, sửa hoặc xoá ở trang Bộ nhớ.", "data": {"id": item.id}}


async def _verify_remember(ctx: Ctx, out: Dict[str, Any]):
    return True if await store().get(conv.owner(ctx), out["data"]["id"]) is not None else "mục chưa có trong bộ nhớ"


async def _plan_forget(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    item = await store().get(conv.owner(ctx), str(args.get("item_id") or ""))
    if item is None:
        raise ToolFailed("Không có mục này trong bộ nhớ của bạn (lấy mã từ công cụ nho_lai)")
    return {"summary": f"Quên “{item.text}”?", "args": {"item_id": item.id}}


async def _forget(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    if not await forget(ctx, args["item_id"]):
        raise ToolFailed("Không có mục này trong bộ nhớ của bạn")
    conv.scrub()
    return {"text": "Đã quên mục này.", "data": {"id": args["item_id"]}}


async def _verify_forget(ctx: Ctx, out: Dict[str, Any]):
    return True if await store().get(conv.owner(ctx), out["data"]["id"]) is None else "mục vẫn còn"


async def _history(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    hits = search_history(ctx, str(args.get("q") or ""), limit=8)
    if not hits:
        return {"text": "Không thấy trong các cuộc trò chuyện trước của bạn.", "data": {"hits": 0}}
    text = f"{len(hits)} chỗ trong các cuộc trò chuyện trước: " + " ".join(
        f"{k + 1}) “{h['title']}”, {h['author']}: …{h['snippet']}…" for k, h in enumerate(hits[:4])
    )
    return {"text": text, "data": {"hits": len(hits)}}


async def _reread(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The current session's own turns, verbatim (OWN-SS-05): what a compaction summary left out, read back."""
    from assistant import conversations as conv

    turns = conv.turns_of(ctx.conversation) if ctx.conversation else []
    words = fast_fold(str(args.get("q") or "")).split()
    rows = []
    for t in turns:
        said = " ".join(str((t.get("answer") or {}).get("text") or "").split())
        both = f"{t.get('question') or ''} {said}"
        if not words or all(w in fast_fold(both) for w in words):
            rows.append((t["seq"], t.get("question") or "(xác nhận)", said))
    last = max(1, min(int(args.get("n") or 4), 8))
    rows = rows[-last:]
    if not rows:
        return {"text": "Không thấy lượt nào như vậy trong cuộc trò chuyện này.", "data": {"turns": 0}}
    text = " ".join(f"[lượt {seq + 1}] Bạn: {q[:300]} — Trợ lý: {a[:600]}" for seq, q, a in rows)
    return {"text": text, "data": {"turns": len(rows)}}


CATALOGUE = {
    t.name: t
    for t in [
        Tool(
            "nho_lai",
            "những điều người dùng đã nhờ ghi nhớ (sở thích, mục tiêu, thông tin, giới hạn) kèm mã từng mục",
            EVERYONE,
            _recall,
            params={"query": Param(str, "từ khóa để lọc, để trống là tất cả", "")},
            page="bo-nho",
        ),
        Tool(
            "ghi_nho",
            "ghi nhớ một điều ngắn về người dùng cho các cuộc trò chuyện sau, chỉ khi họ nhờ nhớ; không ghi số tiền, "
            "số tài khoản hay thông tin người ngoài gia đình",
            EVERYONE,
            _remember,
            write=True,
            args={"kind": list(KINDS)},
            params={
                "text": Param(
                    str,
                    "một câu ngắn, điều cần nhớ, viết thẳng nội dung (vd “thích báo cáo ngắn”), "
                    "không mở đầu bằng “người dùng” hay tên loại",
                )
            },
            page="bo-nho",
            plan=_plan_remember,
            verify=_verify_remember,
        ),
        Tool(
            "quen",
            "quên một điều đã ghi nhớ, khi người dùng yêu cầu",
            EVERYONE,
            _forget,
            write=True,
            params={"item_id": Param(str, "mã mục, lấy từ công cụ nho_lai")},
            page="bo-nho",
            plan=_plan_forget,
            verify=_verify_forget,
        ),
        Tool(
            "tim_lich_su",
            "tìm trong các cuộc trò chuyện trước của người dùng với trợ lý",
            EVERYONE,
            _history,
            params={"q": Param(str, "từ khóa cần tìm, ngắn")},
            page="bo-nho",
        ),
        Tool(
            "doc_lai_phien",
            "đọc lại nguyên văn các lượt trước của chính cuộc trò chuyện này (khi phần đầu đã được tóm tắt và cần chi "
            "tiết)",
            EVERYONE,
            _reread,
            params={
                "q": Param(str, "từ khóa để lọc, để trống là các lượt gần nhất", ""),
                "n": Param(int, "số lượt, tối đa 8", 4),
            },
            page="bo-nho",
        ),
    ]
}
