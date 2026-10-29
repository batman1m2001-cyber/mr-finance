"""Follow-ups (A6, FEAT-39, ADR-0031): a condition the person asked to be told about, checked by rules, never a model.

- **Kinds**: ``market`` — a market series (``data/market_sources.json``) above or below a level, read from the
  stored closes; ``topic`` — an event whose application run became effective (the CIO approved its view, the
  post-checks passed) with every word of the topic in its title, accents folded.
- **Created** by the assistant's ``theo_doi`` tool (a write: the person confirms the line), at most 20 open per
  person, for 30 days unless they say otherwise (at most 180).
- **Checked** at the end of each market job (the series it loaded) and of the news job (the runs made effective
  since), with no model call. A hit **fires once**: the follow-up closes as ``fired`` with the value or the event,
  and shows in the person's bell (and a client's feed) until they open it.
- States: ``open`` → ``fired`` | ``expired`` | ``cancelled``. A topic's words are the person's: sealed like the rest
  of ``assistant.db``.
"""

from __future__ import annotations

import json
import time
import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional

from assistant import conversations as conv
from assistant.base import Ctx, Param, Tool, ToolFailed
from control import crypto
from control.roles import ROLES
from wealth.paths import ROOT

OPEN_MAX = 20
DAYS, DAYS_MAX = 30, 180
SEEN_FOR = 7 * 86400.0  # a fired follow-up stays in the bell this long, or until opened
SCHEMA = """
create table if not exists follow_ups (id text primary key, owner text not null, role text not null, client_id text,
    kind text not null, series text, op text, level real, topic text, created real not null, expires real not null,
    status text not null, fired_at real, fired text, seen real, conversation_id text);
create index if not exists follow_ups_open on follow_ups (status, kind);
create index if not exists follow_ups_owner on follow_ups (owner, status);
"""
OPS = {"above": "trên", "below": "dưới"}
EVERYONE = ROLES


@lru_cache(maxsize=1)
def series() -> Dict[str, Dict[str, Any]]:
    """The market series a follow-up may watch: id → name, unit, the job that loads it."""
    d = json.loads((ROOT / "data" / "market_sources.json").read_text(encoding="utf-8"))
    return {s["id"]: {"name": s["name"], "unit": s.get("unit") or "", "job": s.get("job")} for s in d["series"]}


def job_series(job: str) -> List[str]:
    """The series a market job loads: the ones its follow-ups are checked on."""
    return [k for k, s in series().items() if s["job"] == job]


def _ensure(con) -> None:
    con.executescript(SCHEMA)


def _place(fid: str) -> bytes:
    return f"follow_ups:{fid}:topic".encode()


def _fold(text: str) -> str:
    from assistant.memory import fast_fold

    return fast_fold(text)


def _num(x: float) -> str:
    return f"{x:,.2f}".rstrip("0").rstrip(".").replace(",", "\0").replace(".", ",").replace("\0", ".")


def describe(f: Dict[str, Any]) -> str:
    """The follow-up in one line, as the person confirms it and the bell shows it."""
    if f["kind"] == "market":
        s = series().get(f["series"], {"name": f["series"], "unit": ""})
        return f"{s['name']} {OPS[f['op']]} {_num(f['level'])} {s['unit']}".strip()
    return f"có sự kiện được duyệt về “{f['topic']}”"


def _row(r) -> Dict[str, Any]:
    d = dict(r)
    if d.get("topic"):
        d["topic"] = crypto.open_(d["topic"], _place(d["id"]))
    d["fired"] = json.loads(d["fired"]) if d.get("fired") else None
    d["text"] = describe(d)
    d["fired_text"] = _fired_text(d)
    return d


def _fired_text(f: Dict[str, Any]) -> str:
    """What fired, as the bell and the page say it: the close and its day, or the approved event's title."""
    x = f.get("fired")
    if not x:
        return ""
    if f["kind"] == "topic":
        return x.get("title") or ""
    y, m, d = (x.get("date") or "--").split("-")[:3]
    unit = series().get(f["series"], {}).get("unit", "")
    return f"{d}/{m}/{y}: {_num(x['value'])} {unit}".strip()


def listing(ctx: Ctx, statuses=("open", "fired")) -> List[Dict[str, Any]]:
    """The person's follow-ups, newest first (open ones and those that fired)."""
    with conv.db() as con:
        _ensure(con)
        q = ",".join("?" * len(statuses))
        rows = con.execute(f"select * from follow_ups where owner = ? and status in ({q}) order by created desc",
                           (conv.owner(ctx), *statuses)).fetchall()  # fmt: skip
    return [_row(r) for r in rows]


def unseen(ctx: Ctx) -> List[Dict[str, Any]]:
    """What the bell shows: fired, not opened, within a week."""
    now = time.time()
    return [f for f in listing(ctx, ("fired",)) if not f["seen"] and now - (f["fired_at"] or 0) < SEEN_FOR]


def create(ctx: Ctx, kind: str, *, series_id: str = "", op: str = "", level: Optional[float] = None,
           topic: str = "", days: int = DAYS) -> Dict[str, Any]:  # fmt: skip
    if kind == "market":
        if series_id not in series():
            raise ValueError("Không theo dõi được chuỗi này (xem danh sách chuỗi thị trường)")
        if op not in OPS:
            raise ValueError("so sánh là above (trên) hoặc below (dưới)")
        if level is None or not float(level) > 0:
            raise ValueError("cần một mức lớn hơn 0")
    elif kind == "topic":
        topic = " ".join(str(topic or "").split())
        if not 2 <= len(topic) <= 80:
            raise ValueError("chủ đề từ 2 đến 80 ký tự")
    else:
        raise ValueError("loại là market hoặc topic")
    days = max(1, min(int(days or DAYS), DAYS_MAX))
    fid, now, owner = uuid.uuid4().hex[:12], time.time(), conv.owner(ctx)
    with conv.db() as con:
        _ensure(con)
        n = con.execute("select count(*) from follow_ups where owner = ? and status = 'open'", (owner,)).fetchone()[0]
        if n >= OPEN_MAX:
            raise ValueError(f"Bạn đã có {OPEN_MAX} việc theo dõi đang mở: huỷ bớt ở trang Bộ nhớ")
        con.execute(
            "insert into follow_ups (id, owner, role, client_id, kind, series, op, level, topic, created, expires,"
            " status, conversation_id) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)",
            (fid, owner, ctx.role, ctx.client_id, kind, series_id or None, op or None,
             float(level) if level is not None else None, crypto.seal(topic, _place(fid)) if topic else None,
             now, now + days * 86400, ctx.conversation or None),
        )  # fmt: skip
    return get(ctx, fid)


def get(ctx: Ctx, fid: str) -> Optional[Dict[str, Any]]:
    with conv.db() as con:
        _ensure(con)
        r = con.execute("select * from follow_ups where id = ? and owner = ?", (fid, conv.owner(ctx))).fetchone()
    return _row(r) if r else None


def cancel(ctx: Ctx, fid: str) -> bool:
    with conv.db() as con:
        _ensure(con)
        cur = con.execute("update follow_ups set status = 'cancelled' where id = ? and owner = ? and status = 'open'",
                          (fid, conv.owner(ctx)))  # fmt: skip
    return cur.rowcount == 1


def seen(ctx: Ctx, fid: str) -> bool:
    with conv.db() as con:
        _ensure(con)
        cur = con.execute("update follow_ups set seen = ? where id = ? and owner = ? and status = 'fired'",
                          (time.time(), fid, conv.owner(ctx)))  # fmt: skip
    return cur.rowcount == 1


def forget_owner(con, owner: str) -> int:
    _ensure(con)
    return con.execute("delete from follow_ups where owner = ?", (owner,)).rowcount


# -- the checks (the market and news jobs; no model) -------------------------------------------------------------


def _fire(con, fid: str, fired: Dict[str, Any], now: float) -> None:
    con.execute("update follow_ups set status = 'fired', fired_at = ?, fired = ? where id = ? and status = 'open'",
                (now, json.dumps(fired, ensure_ascii=False), fid))  # fmt: skip


def _expire(con, now: float) -> int:
    return con.execute("update follow_ups set status = 'expired' where status = 'open' and expires <= ?",
                       (now,)).rowcount  # fmt: skip


def check_market(series_ids: Optional[List[str]] = None, now: Optional[float] = None) -> Dict[str, int]:
    """Open market follow-ups on ``series_ids`` (all when None) against each series' latest stored close."""
    from market import store as market

    now = time.time() if now is None else now
    out = {"checked": 0, "fired": 0, "expired": 0}
    with conv.db() as con:
        _ensure(con)
        out["expired"] = _expire(con, now)
        rows = con.execute("select id, series, op, level from follow_ups where status = 'open' and kind = 'market'"
                           ).fetchall()  # fmt: skip
        latest: Dict[str, Any] = {}
        for r in rows:
            if series_ids is not None and r["series"] not in series_ids:
                continue
            out["checked"] += 1
            if r["series"] not in latest:
                pts = market.points(r["series"])
                latest[r["series"]] = pts[-1] if pts else None
            p = latest[r["series"]]
            if p is None:
                continue
            day, value = p
            if (value < r["level"]) if r["op"] == "below" else (value > r["level"]):
                _fire(con, r["id"], {"value": value, "date": day, "series": r["series"]}, now)
                out["fired"] += 1
    return out


def check_topics(now: Optional[float] = None) -> Dict[str, int]:
    """Open topic follow-ups against the events whose run became effective after the follow-up was made."""
    from apply import run as runs
    from events import store as events

    now = time.time() if now is None else now
    out = {"checked": 0, "fired": 0, "expired": 0}
    with conv.db() as con:
        _ensure(con)
        out["expired"] = _expire(con, now)
        rows = con.execute("select id, topic, created from follow_ups where status = 'open' and kind = 'topic'"
                           ).fetchall()  # fmt: skip
        if not rows:
            return out
        effective = []
        for r in runs.runs(statuses=("EFFECTIVE", "SUPERSEDED")):
            when = max((h["at"] for h in r.get("history") or [] if h.get("status") == "EFFECTIVE"), default=None)
            if when is None:
                continue
            try:
                title = events.get(r["event_id"]).get("title") or ""
            except Exception:  # an event no longer there: nothing to match
                continue
            effective.append({"at": when, "event_id": r["event_id"], "run_id": r["id"], "title": title,
                              "folded": _fold(title)})  # fmt: skip
        effective.sort(key=lambda e: e["at"])
        for r in rows:
            out["checked"] += 1
            words = _fold(crypto.open_(r["topic"], _place(r["id"]))).split()
            hit = next((e for e in effective if e["at"] >= r["created"] and all(w in e["folded"] for w in words)),
                       None)  # fmt: skip
            if hit:
                _fire(con, r["id"], {"event_id": hit["event_id"], "run_id": hit["run_id"], "title": hit["title"]}, now)
                out["fired"] += 1
    return out


# -- the tools ----------------------------------------------------------------------------------------------------


def _args(args: Dict[str, Any]) -> Dict[str, Any]:
    kind = "market" if args.get("series") else "topic" if args.get("topic") else ""
    if not kind:
        raise ToolFailed("Cần một chuỗi thị trường (series, so sánh, mức) hoặc một chủ đề tin")
    level = args.get("level")
    try:
        level = float(level) if level not in (None, "") else None
    except (TypeError, ValueError):
        raise ToolFailed("mức phải là một số") from None
    return {"kind": kind, "series_id": str(args.get("series") or ""), "op": str(args.get("op") or ""),
            "level": level, "topic": str(args.get("topic") or ""), "days": int(args.get("days") or DAYS)}  # fmt: skip


def _plan_follow(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    a = _args(args)
    probe = {"kind": a["kind"], "series": a["series_id"], "op": a["op"] or "below", "level": a["level"] or 0,
             "topic": a["topic"]}  # fmt: skip
    if a["kind"] == "market":
        if a["series_id"] not in series():
            raise ToolFailed("Không theo dõi được chuỗi này")
        if a["op"] not in OPS or not a["level"]:
            raise ToolFailed("Cần so sánh (above/below) và một mức lớn hơn 0")
    days = max(1, min(a["days"], DAYS_MAX))
    return {"summary": f"Báo cho bạn một lần khi {describe(probe)} (theo dõi {days} ngày)?", "args": a}


async def _follow(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        f = create(ctx, args["kind"], series_id=args["series_id"], op=args["op"], level=args["level"],
                   topic=args["topic"], days=args["days"])  # fmt: skip
    except ValueError as exc:
        raise ToolFailed(str(exc)) from None
    return {"text": f"Đã đặt theo dõi: {f['text']}. Khi điều kiện xảy ra, chuông thông báo sẽ báo một lần; bạn xem "
            "hoặc huỷ ở trang Bộ nhớ.", "data": {"id": f["id"]}}  # fmt: skip


async def _verify_follow(ctx: Ctx, out: Dict[str, Any]):
    f = get(ctx, out["data"]["id"])
    return True if f and f["status"] == "open" else "việc theo dõi chưa được lưu"


def _plan_cancel(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    f = get(ctx, str(args.get("follow_up_id") or ""))
    if f is None or f["status"] != "open":
        raise ToolFailed("Không có việc theo dõi đang mở với mã này (xem danh sách bằng công cụ theo_doi_cua_toi)")
    return {"summary": f"Huỷ theo dõi “{f['text']}”?", "args": {"follow_up_id": f["id"]}}


async def _cancel(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    if not cancel(ctx, args["follow_up_id"]):
        raise ToolFailed("Không có việc theo dõi đang mở với mã này")
    return {"text": "Đã huỷ việc theo dõi.", "data": {"id": args["follow_up_id"]}}


async def _verify_cancel(ctx: Ctx, out: Dict[str, Any]):
    f = get(ctx, out["data"]["id"])
    return True if f and f["status"] == "cancelled" else "việc theo dõi vẫn mở"


async def _mine(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    fs = listing(ctx)
    if not fs:
        return {"text": "Bạn chưa đặt việc theo dõi nào.", "data": {"follow_ups": []}}
    text = "Việc theo dõi của bạn: " + " ".join(
        f"({'đang theo dõi' if f['status'] == 'open' else 'đã báo'}) {f['text']}." for f in fs[:10]
    )
    return {"text": text, "data": {"follow_ups": [{"id": f["id"], "status": f["status"], "text": f["text"]}
                                                  for f in fs]}}  # fmt: skip


CATALOGUE = {
    t.name: t
    for t in [
        Tool(
            "theo_doi",
            "đặt một việc theo dõi người dùng nhờ: báo một lần khi một chuỗi thị trường vượt lên trên hoặc xuống dưới "
            "một mức, hoặc khi có sự kiện được duyệt về một chủ đề; chỉ hai loại này, không theo dõi điều kiện khác. "
            "Mã chuỗi: VNINDEX là VN-Index, SJC vàng miếng, XAUUSD vàng thế giới, USDVND tỷ giá, BTCUSD Bitcoin, "
            "BRENT dầu, SPX S&P, mã cổ phiếu là chính nó",
            EVERYONE,
            _follow,
            write=True,
            args={"series": sorted(series()), "op": ["above", "below"]},
            params={
                "level": Param(float, "mức của chuỗi, theo đơn vị của chuỗi (vd 1200 điểm)", 0.0),
                "topic": Param(str, "chủ đề tin, vài từ (vd “lãi suất”), để trống khi theo dõi chuỗi", ""),
                "days": Param(int, "theo dõi bao nhiêu ngày, mặc định 30, tối đa 180", DAYS),
            },
            page="bo-nho",
            plan=_plan_follow,
            verify=_verify_follow,
        ),
        Tool(
            "theo_doi_cua_toi",
            "các việc theo dõi người dùng đã đặt (đang theo dõi, đã báo) kèm mã từng việc",
            EVERYONE,
            _mine,
            page="bo-nho",
        ),
        Tool(
            "huy_theo_doi",
            "huỷ một việc theo dõi đang mở, khi người dùng yêu cầu",
            EVERYONE,
            _cancel,
            write=True,
            params={"follow_up_id": Param(str, "mã việc theo dõi, lấy từ công cụ theo_doi_cua_toi")},
            page="bo-nho",
            plan=_plan_cancel,
            verify=_verify_cancel,
        ),
    ]
}
