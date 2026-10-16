"""The memory consolidator (A6, FEAT-39, ADR-0031): a finished conversation distilled into at most five long-term
items, the way a person would ask the assistant to remember them.

- **When**: the ``assistant_consolidate`` job (every 5 minutes) takes the conversations idle for 15 minutes whose
  turns changed since their last consolidation (a hash of the turns' numbers and times: nothing is opened to tell),
  at most 20 a tick, oldest first. A conversation is never consolidated twice for the same content.
- **Only where the model may read it**: ``client_ai = demo``, or the model inside the bank (the turn's own rule,
  ``turn.model_reads``). Otherwise the run is recorded ``skipped`` and nothing leaves.
- **What is sent**: the person's questions and the assistant's answers (each cut to 600 characters), newest kept
  when the 8,000-token budget is short, and the owner's active items to merge with. Nothing else.
- **What is kept**: every item passes ``memory.refused`` (no amount, account or outsider) like a person's own
  “hãy nhớ…”; an item the model says repeats one already kept, or whose words mostly do (≥ 60 % shared, same kind),
  is merged: a confirmed item (confidence 1) is left as the person wrote it, another one takes the newer wording.
  New items have confidence 0.7 and name the conversation as their source.
- **Runs** (``consolidations`` in ``assistant.db``): status, attempts, tokens, the provider's cost, counts — never the
  text. A failure is retried on the next ticks, twice; then it stays ``failed`` until the conversation changes.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from assistant import conversations as conv
from assistant import memory
from assistant.base import Ctx

IDLE = 15 * 60
PER_TICK = 20
BUDGET = 8000  # tokens a conversation may cost, prompt and answer
ANSWER_TOKENS = 1500  # of the budget, the model's (it thinks first: ADR-0030's notes)
MAX_ITEMS = 5
RETRIES = 2
CONFIDENCE = 0.7
SAME = 0.6  # shared words over the smaller item's: the same thing said again
CUT = 600
SCHEMA = """
create table if not exists consolidations (id text primary key, conversation_id text not null, owner text not null,
    hash text not null, status text not null, attempts integer not null, started real not null, finished real,
    tokens_in integer, tokens_out integer, cost real, added integer, merged integer, refused integer, error text);
create index if not exists consolidations_conv on consolidations (conversation_id, hash);
create index if not exists consolidations_day on consolidations (started);
"""
SYSTEM = (
    "Bạn đọc một cuộc trò chuyện giữa một người và trợ lý tài chính OneWealth, rồi chọn tối đa năm điều đáng nhớ VỀ "
    "NGƯỜI ĐÓ cho các lần sau: sở thích (preference), mục tiêu (goal), thông tin về hoàn cảnh (fact), giới hạn "
    "(constraint). Chỉ điều người đó nói hoặc xác nhận, có ích về lâu dài; không chép chi tiết của một câu hỏi. "
    "Mỗi điều là một câu ngắn (dưới 200 ký tự), viết thẳng nội dung (vd “thích báo cáo ngắn”). TUYỆT ĐỐI không "
    "ghi số tiền, tỷ lệ, số tài khoản, hay tên người ngoài gia đình. Nếu một điều trùng ý với một mục đã có, ghi mã "
    "mục đó vào same_as. Không có gì đáng nhớ thì trả mảng rỗng. Chỉ trả JSON: "
    '{"items": [{"kind": "preference|goal|fact|constraint", "text": "...", "same_as": "m1 hoặc null"}]}'
)


def _ensure(con) -> None:
    con.executescript(SCHEMA)


def tokens(text: str) -> int:
    """A Vietnamese text's tokens, estimated on the safe side: the model counted 1.64–1.70 characters a token on
    five conversations (2026-10-17); 1.6 is used, so the estimate is a little high, never low."""
    return int(len(text) / 1.6) + 1


def content_hash(con, cid: str) -> str:
    rows = con.execute("select seq, at from turns where conversation_id = ? order by seq", (cid,)).fetchall()
    return hashlib.sha256(json.dumps([[r[0], r[1]] for r in rows]).encode()).hexdigest()[:16]


def due(now: Optional[float] = None, limit: int = PER_TICK) -> List[Dict[str, Any]]:
    """The conversations to consolidate now: idle, changed since their last run, not given up on."""
    now = time.time() if now is None else now
    out = []
    with conv.db() as con:
        _ensure(con)
        rows = con.execute(
            "select id, owner, role, client_id from conversations where turns > 0 and updated <= ? order by updated",
            (now - IDLE,),
        ).fetchall()
        for r in rows:
            h = content_hash(con, r["id"])
            runs = con.execute("select status, attempts from consolidations where conversation_id = ? and hash = ?",
                               (r["id"], h)).fetchall()  # fmt: skip
            if any(x["status"] in ("done", "skipped") for x in runs):
                continue
            if sum(x["attempts"] for x in runs if x["status"] == "failed") > RETRIES:
                continue
            out.append({**dict(r), "hash": h, "attempt": 1 + sum(x["attempts"] for x in runs)})
            if len(out) >= limit:
                break
    return out


def _ctx(c: Dict[str, Any]) -> Ctx:
    owner = c["owner"]
    return Ctx(role=c["role"], client_id=c["client_id"], scope="personal", question="",
               user=None if owner.startswith("client:") else owner, conversation=c["id"])  # fmt: skip


def transcript(cid: str, room: int) -> Tuple[str, int]:
    """The conversation as the model reads it, newest turns kept within ``room`` tokens; and the turns left out."""
    lines: List[str] = []
    used, turns = 0, conv.turns_of(cid)
    for t in reversed(turns):
        a = " ".join(str((t.get("answer") or {}).get("text") or "").split())[:CUT]
        block = (f"Người dùng: {t['question']}\n" if t.get("question") else "") + (f"Trợ lý: {a}\n" if a else "")
        if used + tokens(block) > room:
            break
        lines.append(block)
        used += tokens(block)
    return "\n".join(reversed(lines)), len(turns) - len(lines)


def _words(text: str) -> set:
    return set(memory.fast_fold(text).split())


def overlap(a: str, b: str) -> float:
    x, y = _words(a), _words(b)
    return len(x & y) / max(1, min(len(x), len(y)))


def parse(text: str) -> List[Dict[str, Any]]:
    """The model's items: the first JSON object in its answer, at most five well-formed ones."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("không có JSON trong câu trả lời")
    got = json.loads(m.group())
    items = got.get("items") if isinstance(got, dict) else None
    if not isinstance(items, list):
        raise ValueError("thiếu mảng items")
    out = []
    for i in items:
        if isinstance(i, dict) and i.get("kind") in memory.KINDS and str(i.get("text") or "").strip():
            out.append({"kind": i["kind"], "text": " ".join(str(i["text"]).split()), "same_as": i.get("same_as")})
    return out[:MAX_ITEMS]


async def keep(ctx: Ctx, found: List[Dict[str, Any]], existing: List[Dict[str, Any]], cid: str) -> Dict[str, int]:
    """The items into the owner's memory: refused ones dropped, repeats merged, the rest added."""
    counts = {"added": 0, "merged": 0, "refused": 0}
    marks = {f"m{k + 1}": e for k, e in enumerate(existing)}
    for i in found:
        if memory.refused(i["text"], ctx):
            counts["refused"] += 1
            continue
        same = marks.get(str(i.get("same_as") or ""))
        if same is None:
            same = next((e for e in existing if e["kind"] == i["kind"] and overlap(e["text"], i["text"]) >= SAME), None)
        if same is not None:
            if same["confidence"] < 1 and memory.fast_fold(same["text"]) != memory.fast_fold(i["text"]):
                await memory.store().update(conv.owner(ctx), same["id"], text=i["text"])
            counts["merged"] += 1
            continue
        item = await memory.remember(ctx, i["kind"], i["text"], source={"conversation": cid, "by": "consolidator"},
                                     confidence=CONFIDENCE)  # fmt: skip
        existing.append(memory.view(item))
        counts["added"] += 1
    return counts


async def _ask(messages: List[Dict[str, str]]):
    from operonx.providers.ops._utils import resolve_hub

    return (
        await resolve_hub()
        .get("llm:copilot")
        .generate(messages=messages, temperature=0, max_tokens=ANSWER_TOKENS, reasoning={"effort": "low"})
    )


def _record(con, run: Dict[str, Any]) -> None:
    con.execute(
        "insert or replace into consolidations (id, conversation_id, owner, hash, status, attempts, started, finished,"
        " tokens_in, tokens_out, cost, added, merged, refused, error) values (:id, :conversation_id, :owner, :hash,"
        " :status, :attempts, :started, :finished, :tokens_in, :tokens_out, :cost, :added, :merged, :refused, :error)",
        run,
    )


async def consolidate(c: Dict[str, Any], now: Optional[float] = None) -> Dict[str, Any]:
    """One conversation (a row of :func:`due`) → its run, recorded."""
    from assistant import turn

    run = {"id": uuid.uuid4().hex[:12], "conversation_id": c["id"], "owner": c["owner"], "hash": c["hash"],
           "status": "done", "attempts": 1, "started": time.time() if now is None else now, "finished": None,
           "tokens_in": 0, "tokens_out": 0, "cost": 0.0, "added": 0, "merged": 0, "refused": 0,
           "error": None}  # fmt: skip
    try:
        if not (turn.live() and turn.model_reads()):
            run.update(status="skipped", error="Mô hình không được đọc cuộc trò chuyện (client_ai)")
        else:
            ctx = _ctx(c)
            existing = await memory.items(ctx)
            known = "\n".join(f"m{k + 1} ({e['kind']}): {e['text']}" for k, e in enumerate(existing)) or "(chưa có)"
            head = f"Các mục đã có:\n{known}\n\nCuộc trò chuyện:\n"
            room = BUDGET - ANSWER_TOKENS - tokens(SYSTEM) - tokens(head)
            text, left_out = transcript(c["id"], room)
            if not text:
                run.update(status="skipped", error="Cuộc trò chuyện không còn nội dung")
            else:
                resp = await _ask([{"role": "system", "content": SYSTEM}, {"role": "user", "content": head + text}])
                usage = getattr(resp, "usage", None)
                run["tokens_in"] = getattr(usage, "prompt_tokens", 0) or 0
                run["tokens_out"] = getattr(usage, "completion_tokens", 0) or 0
                run["cost"] = float(getattr(usage, "cost", 0) or 0)
                found = parse(resp.choices[0].message.content or "")
                run.update(await keep(ctx, found, existing, c["id"]))
                if left_out:
                    run["error"] = f"{left_out} lượt cũ không đọc (ngân sách {BUDGET} token)"
    except Exception as exc:  # recorded and retried on the next tick: never the conversation's text
        run.update(status="failed", error=f"{type(exc).__name__}: {str(exc)[:200]}")
    run["finished"] = time.time()
    with conv.db() as con:
        _ensure(con)
        if run["status"] == "failed":  # one row per conversation and content: the attempts add up
            prev = con.execute("select id, attempts from consolidations where conversation_id = ? and hash = ? and "
                               "status = 'failed'", (c["id"], c["hash"])).fetchone()  # fmt: skip
            if prev:
                run["id"], run["attempts"] = prev["id"], prev["attempts"] + 1
        _record(con, run)
    return run


async def run_due(now: Optional[float] = None) -> Dict[str, Any]:
    """The job's tick: every conversation due, one after another; the counts and the cost."""
    out = {"conversations": 0, "done": 0, "skipped": 0, "failed": 0, "added": 0, "merged": 0, "refused": 0,
           "tokens": 0, "cost": 0.0}  # fmt: skip
    for c in due(now):
        r = await consolidate(c, now)
        out["conversations"] += 1
        out[r["status"]] += 1
        for k in ("added", "merged", "refused"):
            out[k] += r[k] or 0
        out["tokens"] += (r["tokens_in"] or 0) + (r["tokens_out"] or 0)
        out["cost"] += r["cost"] or 0
    out["cost"] = round(out["cost"], 6)
    return out


def costs(days: int = 14) -> List[Dict[str, Any]]:
    """The consolidator's runs and spend per day (local time), newest first."""
    since = time.time() - days * 86400
    with conv.db() as con:
        _ensure(con)
        rows = con.execute(
            "select date(started, 'unixepoch', 'localtime') day, count(*) runs, sum(status = 'done') done,"
            " sum(status = 'failed') failed, sum(status = 'skipped') skipped, coalesce(sum(tokens_in + tokens_out), 0)"
            " tokens, coalesce(sum(cost), 0) cost, coalesce(sum(added), 0) added from consolidations"
            " where started >= ? group by day order by day desc",
            (since,),
        ).fetchall()
    return [dict(r) for r in rows]


def runs(limit: int = 50) -> List[Dict[str, Any]]:
    """The latest runs (for the ecosystem map): never the text."""
    with conv.db() as con:
        _ensure(con)
        rows = con.execute("select * from consolidations order by started desc limit ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
