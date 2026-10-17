"""What a session is about (SESSIONS_PLAN.md S2, OWN-SS-02/06): a short title and a one-line goal, written by the
copilot model after the answer — the first turn, the fourth, and every turn that compacted — never in the reply's
time. A title the person set is kept (``conversations.describe`` replaces only a generated one).

Only a model allowed to read the conversation is asked (``ctx.reads``): in template mode the title stays the
question's first clause (``conversations.local_title``) and no goal is written. A failed or malformed answer changes
nothing; the request's cost is returned so it is counted (A8)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from operonx.core.loggings import LOGGER

from assistant import conversations as conv
from assistant.base import Ctx

WHEN = (1, 4)  # turns after which the title and goal are written again; and after every compaction
ANSWER_TOKENS = 400  # the model thinks first; at 120 it wrote nothing
ROOM = 2500  # tokens of the conversation it reads (the newest turns)
WORDS = 8
SYSTEM = (
    "Bạn đặt tên cho một cuộc trò chuyện giữa người dùng và trợ lý tài chính OneWealth. Trả về đúng một JSON: "
    '{"title": "...", "goal": "..."}. title: tiếng Việt, 2–7 từ, nói chủ đề (vd “Dòng tiền tháng 9”, “Kịch bản '
    "VN-Index giảm”), không dấu chấm, không số tiền. goal: một câu ngắn, điều người dùng muốn đạt được trong cuộc "
    "trò chuyện này. Không thêm gì ngoài JSON."
)


def due(turns: int, compacted: bool) -> bool:
    return compacted or turns in WHEN


def parse(text: str) -> Dict[str, str]:
    """The model's title and goal, cleaned; ValueError when there is no usable title."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("không có JSON")
    got = json.loads(m.group())
    title = " ".join(str(got.get("title") or "").split()).strip(" .\"'“”")
    goal = " ".join(str(got.get("goal") or "").split())
    if not title:
        raise ValueError("thiếu title")
    words = title.split()
    if len(words) > WORDS:
        title = " ".join(words[:WORDS]) + "…"
    return {"title": title[: conv.TITLE], "goal": goal[:200]}


async def _ask(messages):
    from operonx.providers.ops._utils import resolve_hub

    return (
        await resolve_hub()
        .get("llm:copilot")
        .generate(messages=messages, temperature=0, max_tokens=ANSWER_TOKENS, reasoning={"effort": "low"})
    )


def last_compacted(cid: str) -> bool:
    turns = conv.turns_of(cid)
    return bool(turns and (turns[-1].get("answer") or {}).get("compacted"))


async def after_turn(ctx: Ctx, cid: Optional[str], compacted: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """Write the session's title and goal when due (the panel asks once the answer is drawn: ``describe``); the
    session as listed (with ``cost_usd`` when a model was asked), or None when nothing was due."""
    from assistant import consolidate, turn

    if not cid:
        return None
    try:
        c = conv.own(ctx, cid)
    except ValueError:
        return None
    if not due(c["turns"], last_compacted(cid) if compacted is None else compacted) or c.get("described") == c["turns"]:
        return None
    if not (ctx.reads and turn.live()):  # template mode, or no model: the local title stays
        return {**c, "cost_usd": None}
    cost = None
    try:
        text, _ = consolidate.transcript(cid, ROOM)
        if c.get("summary"):
            text = f"Tóm tắt phần trước:\n{c['summary']}\n\n{text}"
        resp = await _ask([{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}])
        cost = float(getattr(getattr(resp, "usage", None), "cost", 0) or 0)
        got = parse(resp.choices[0].message.content or "")
        conv.describe(cid, title=got["title"], goal=got["goal"], at=c["turns"])
    except Exception as exc:  # noqa: BLE001 - a title is a nicety: the session keeps the one it has
        LOGGER.warning("session title: %s: %s", type(exc).__name__, exc)
    return {**conv.own(ctx, cid), "cost_usd": cost}
