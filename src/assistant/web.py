"""Web search (A5, ADR-0030): questions outside OneWealth answered from the web, with sources and a stated certainty.

- Through the existing OpenRouter key: the copilot model (``llm:copilot``) with OpenRouter's ``web`` plugin (three
  results). Measured in A0: 8 s, US$0.012 a search.
- **What leaves**: the question scrubbed as for the router (``copilot.scrub``: no person's name, no number, no
  code), its placeholders dropped. Never a tool result, a memory item or a document.
- **Caps**: 20 searches per person per day and 500 in total (``web_usage`` in ``assistant.db``); over a cap, or with
  no model configured, the tool says web search is unavailable.
- Nothing found is stored beyond the answer the panel shows.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List

from assistant import conversations as conv
from assistant.base import Ctx, ToolFailed
from copilot import router
from copilot.scrub import scrub

PER_PERSON = 20
IN_TOTAL = 500
RESULTS = 3
SYSTEM = (
    "Bạn trả lời câu hỏi bằng tiếng Việt, ngắn gọn (tối đa 5 câu), chỉ từ kết quả tìm kiếm web. Mở đầu bằng “Theo "
    "các nguồn tìm được,”. Kết thúc bằng một câu “Mức độ chắc chắn: cao / trung bình / thấp” và lý do ngắn (các nguồn "
    "có thống nhất, có mới không). Không đưa khuyến nghị đầu tư. Nếu kết quả không trả lời được, nói thẳng như vậy."
)
PLACEHOLDER = re.compile(r"<(?:người|số|mã)>")


def query_of(question: str) -> str:
    """What is sent out: the scrubbed question without its placeholders."""
    return re.sub(r"\s+", " ", PLACEHOLDER.sub(" ", scrub(question))).strip(" ,.;:")


def _day() -> str:
    return time.strftime("%Y-%m-%d")


def used(owner: str) -> Dict[str, int]:
    with conv.db() as con:
        con.execute("create table if not exists web_usage (day text not null, owner text not null, n integer not null,"
                    " primary key (day, owner))")  # fmt: skip
        mine = con.execute("select n from web_usage where day = ? and owner = ?", (_day(), owner)).fetchone()
        total = con.execute("select coalesce(sum(n), 0) from web_usage where day = ?", (_day(),)).fetchone()
    return {"person": mine[0] if mine else 0, "total": total[0]}


def _count(owner: str) -> None:
    with conv.db() as con:
        con.execute("insert into web_usage (day, owner, n) values (?, ?, 1) on conflict (day, owner) do update "
                    "set n = n + 1", (_day(), owner))  # fmt: skip


async def search(ctx: Ctx, question: str) -> Dict[str, Any]:
    q = query_of(question)
    if len(q) < 3:
        raise ToolFailed("Câu hỏi không còn gì để tìm sau khi bỏ tên, số và mã")
    if not router.live():
        raise ToolFailed("Tìm kiếm web chưa sẵn sàng (chưa cấu hình mô hình)")
    owner = conv.owner(ctx)
    u = used(owner)
    if u["person"] >= PER_PERSON or u["total"] >= IN_TOTAL:
        raise ToolFailed("Tìm kiếm web tạm hết lượt hôm nay")
    from operonx.providers.ops._utils import resolve_hub

    _count(owner)  # counted before the call: a slow or failed search still spends a search
    try:
        resp = (
            await resolve_hub()
            .get("llm:copilot")
            .generate(
                messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}],
                temperature=0,
                max_tokens=1500,  # the model thinks first: at 500 it spent them all and wrote nothing
                plugins=[{"id": "web", "max_results": RESULTS}],  # operonx sends extra keywords as extra_body
                reasoning={"effort": "low"},
            )
        )
    except Exception as exc:  # the provider's failure, said as unavailable
        raise ToolFailed(f"Tìm kiếm web không trả lời được ({type(exc).__name__})") from None
    msg = resp.choices[0].message
    cites: List[Dict[str, str]] = []
    for a in getattr(msg, "annotations", None) or []:
        c = getattr(a, "url_citation", None) or (a.get("url_citation") if isinstance(a, dict) else None)
        url = getattr(c, "url", None) or (c.get("url") if isinstance(c, dict) else None)
        if url and url not in [x["url"] for x in cites]:
            title = getattr(c, "title", None) or (c.get("title") if isinstance(c, dict) else None)
            cites.append({"url": url, "title": title or url})
    text = (msg.content or "").strip()
    if not text:
        raise ToolFailed("Tìm kiếm web không có kết quả")
    from operonx_agents import Usage

    cost = Usage.from_completion(getattr(resp, "usage", None)).cost_usd  # what OpenRouter charged (A8)
    return {"text": text, "query": q, "sources": cites, "cost_usd": cost}
