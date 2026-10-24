"""Each staff role's own assistant reads its desk (FEAT-41, OWN-MR-10): read tools over the composition the desk
draws (src/desk/reads.py), so the assistant says the numbers the screen shows. Read-only; a tool is offered only to
its role, and the read under it is that role's alone. Their steps light the desk (assistant/stream.py ``NODES``)."""

from __future__ import annotations

import time
from typing import Any, Dict

from assistant.base import Ctx, Param, Tool, ToolFailed
from assistant.tools import _pct, _vnd


def _desk(ctx: Ctx, role: str) -> Dict[str, Any]:
    from desk import reads

    return reads.desk(role, {"id": ctx.user, "role": ctx.role})


RUN_STATES = (("NEEDS_CIO_REVIEW", "chờ CIO xem lại"), ("COMPUTING", "đang tính"), ("POST_CHECKING", "đang hậu kiểm"),
              ("FAILED", "lỗi tính"), ("SUPERSEDED", "đã thay thế"), ("WITHDRAWN", "đã thu hồi"))  # fmt: skip


def _spct(x: float, digits: int = 1) -> str:
    return ("+" if x > 0 else "−" if x < 0 else "") + _pct(abs(x), digits)


# -- CIO ---------------------------------------------------------------------------------------------------------


async def cio_desk(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Decision board: what waits for the CIO, then where each stage of the pipeline stands."""
    d = _desk(ctx, "cio")
    waits = d["decide"]
    listed = "; ".join(f"{x['title']} ({x['id']}, {x['status']})" for x in waits[:6])
    head = f"{len(waits)} việc chờ CIO quyết định: {listed}." if waits else "Không có việc nào chờ CIO quyết định."
    stages = " ".join(
        f"{s['label']}: {s['count']} {s['unit']}" + (f" ({s['note']})." if s["note"] else ".") for s in d["pipeline"]
    )
    return {
        "text": f"{head} Dòng chảy: {stages}",
        "data": {"waiting": len(waits), "stages": {s["id"]: s["count"] for s in d["pipeline"]}},
        "focus": ["decide"] + [f"stage:{s['id']}" for s in d["pipeline"] if s["waits"]],
        "sources": ["Decision board"],
    }


async def exposure(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Phơi nhiễm: the newest effective run's expected 3-month change, by factor, and the worst families."""
    e = _desk(ctx, "cio")["exposure"]
    if not e:
        raise ToolFailed("Chưa có lần áp dụng nào đang hiệu lực")
    factors = "; ".join(f"{f['name']} {_vnd(f['value'], True)}" for f in e["factors"])
    flag = lambda w: " (RM xem trước)" if w["pre_review"] else ""  # noqa: E731
    worst = "; ".join(f"{w['name']} {_spct(w['expected_3m_pct'], 2)}{flag(w)}" for w in e["worst"])
    return {
        "text": (
            f"Lần áp dụng {e['run_id']} ({e['event']}): kỳ vọng 3 tháng {_vnd(e['expected_3m'], True)} trên "
            f"{e['families']} gia đình, {e['pre_review']} gia đình chạm ngưỡng RM xem trước. Theo yếu tố, tổng mọi gia "
            f"đình: {factors}. Gia đình ảnh hưởng nhiều nhất: {worst}. Tham số mô hình là giả định; đây là ước tính, "
            "không phải dự báo."
        ),
        "data": {"run_id": e["run_id"], "expected_3m": e["expected_3m"], "families": e["families"]},
        "focus": ["exposure", "stage:families"],
        "as_of": e["run_id"],
        "sources": [f"lần áp dụng {e['run_id']}"],
    }


def _when(v: Any) -> str:
    """A record's time as the person reads it (dd/mm hh:mm): a desk item's age, so “the oldest” can be said (D08)."""
    from datetime import datetime

    try:
        t = datetime.fromtimestamp(float(v)) if isinstance(v, (int, float)) else datetime.fromisoformat(str(v))
    except (TypeError, ValueError):
        return "—"
    return t.strftime("%d/%m %H:%M")


STATE_SAY = {"done": "chạy xong", "active": "đang chạy", "waiting": "đang chờ", "failed": "lỗi", "idle": "chưa chạy"}


def _can_run(ctx: Ctx) -> str:
    """What this role may start (owner 2026-10-18): the CIO, Agent CIO on an event with no view and the challenger
    where it failed; Admin, the jobs on the list; Compliance, nothing. Each runs on the person's Xác nhận, or from the
    Việc nền page."""
    if ctx.role == "cio":
        from app.web import agents_read

        a = agents_read()
        evs = (
            "; ".join(f"{e['id']} “{e['title']}”" for e in a["can_run"][:6])
            or "không sự kiện nào (đều đã có nhận định)"
        )
        ch = "; ".join(f"{v['id']} (sự kiện “{v['title']}”)" for v in a["can_challenge"]) or "không"
        return (
            f"Bạn chạy được Agent CIO cho sự kiện chưa có nhận định: {evs}. Phản biện lỗi chờ chạy lại: {ch}. Trợ lý "
            "chạy được khi bạn bấm Xác nhận, hoặc làm ở trang Việc nền; nhận định ra vẫn chờ bạn duyệt ở trang Sự "
            "kiện & nhận định."
        )
    if ctx.role == "admin":
        from control import jobs

        busy = [r["label"] for r in jobs.recent(50) if r["status"] == "running"]
        return (
            "Việc chạy tay được: "
            + ", ".join(jobs.RUNNABLE.values())
            + ". "
            + (f"Đang chạy: {', '.join(busy)}. " if busy else "")
            + "Trợ lý chạy được khi bạn bấm Xác nhận, hoặc làm ở trang Việc nền. Các agent do CIO chạy."
        )
    return "CIO chạy các agent, Quản trị chạy các việc nền (trang Việc nền); Tuân thủ xem."


async def background(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The agents and the background jobs, as the Agent page's map reads them from their records: each one's state,
    its last run and today's runs and failures (staff stress test D07: the CIO asked, and nothing could say)."""
    from views import ecosystem

    e = ecosystem.ecosystem()
    nodes = [n for n in e["nodes"] if n.get("group") in ("cio", "rules", "background") or n["id"] == "news"
             or n["id"] == "market"]  # fmt: skip

    def line(n: Dict[str, Any]) -> str:
        day = n.get("day") or {}
        last = f", lần gần nhất {time.strftime('%d/%m %H:%M', time.localtime(n['at']))}" if n.get("at") else ""
        waits = f", {n['waiting']} việc chờ" if n.get("waiting") else ""
        return (f"{n['label']}: {STATE_SAY.get(n.get('state') or 'idle', n.get('state'))}{last}, hôm nay "
                f"{day.get('runs', 0)} lần, {day.get('failed', 0)} lỗi{waits}")  # fmt: skip

    failing = [n for n in nodes if n.get("state") == "failed" or (n.get("day") or {}).get("failed")]
    text = (
        (
            "Có việc lỗi: " + ", ".join(n["label"] for n in failing) + ". "
            if failing
            else "Không agent hay việc nền nào lỗi. "
        )
        + "; ".join(line(n) for n in nodes)
        + ". "
        + _can_run(ctx)
    )
    return {
        "text": text,
        "data": {
            "nodes": [
                {"id": n["id"], "state": n.get("state"), "at": n.get("at"), **(n.get("day") or {})} for n in nodes
            ]
        },  # fmt: skip
        "focus": ["agents"],
        "as_of": _when(e.get("as_of")),  # a string: the model's result type refused the ecosystem's epoch
        "sources": ["Bản đồ agent (trang Agent)"],
    }


async def runs(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Lần áp dụng: the runs in force, and any held for the CIO's review or still computing."""
    from apply import run as apply_run

    rows = apply_run.runs()
    if not rows:
        raise ToolFailed("Chưa có lần áp dụng nào")
    by: Dict[str, list] = {}
    for r in rows:
        by.setdefault(r["status"], []).append(r)
    eff = by.get("EFFECTIVE", [])
    each = "; ".join(
        f"{r['id']} kỳ vọng 3 tháng {_vnd(r['totals']['expected_3m'], True)}, {r['families']} gia đình, "
        f"{r['totals']['pre_review']} chạm ngưỡng"
        for r in eff[:5]
    )
    parts = [f"{len(eff)} lần áp dụng đang hiệu lực" + (f": {each}" if eff else "")]
    for status, label in RUN_STATES:
        if by.get(status):
            parts.append(f"{len(by[status])} {label} ({', '.join(r['id'] for r in by[status][:4])})")
    return {
        "text": ". ".join(parts) + ".",
        "data": {s: len(v) for s, v in by.items()},
        "focus": ["stage:runs"],
        "sources": [f"{len(rows)} lần áp dụng"],
    }


async def accuracy(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Độ chính xác: the model walked over history (share inside P10–P90, VN-Index direction) and the approved views'
    forecasts waiting to be scored."""
    from measure import backtest, forecasts

    h = backtest.cached()
    names = {"1w": "1 tuần", "3m": "3 tháng", "12m": "12 tháng"}
    cover = "; ".join(
        f"{names[k]}: {_pct(v['pooled_coverage'], 0)} trong dải P10–P90 ({v['pooled_verdict']})"
        for k, v in (h.get("horizons") or {}).items()
        if (v or {}).get("pooled_coverage") is not None
    )
    kpi = "; ".join(
        f"{names[k]}: đúng hướng {_pct(v['hit'], 0)} trên {v['n']} lần ({'đạt' if v['met'] else 'chưa đạt'})"
        for k, v in (h.get("kpi03") or {}).items()
        if (v or {}).get("hit") is not None
    )
    rows = forecasts.all_rows()
    waiting = [r for r in rows if r.get("scored") is None]
    due = min((r["due"] for r in waiting), default=None)
    history = (
        f"Mô hình chạy lại trên lịch sử {h['from']} đến {h['to']}: {cover}. "
        f"Hướng VN-Index so với mục tiêu {_pct(h['target'], 0)}: {kpi or 'chưa đủ lần để chấm'}."
        if cover
        else "Chưa có lịch sử thị trường để chạy lại mô hình."
    )
    return {
        "text": (
            f"{history} Dự báo của các nhận định đã duyệt: {len(rows)} dự báo, {len(waiting)} chờ đến hạn chấm"
            + (f", hạn gần nhất {due}." if due else ".")
        ),
        "data": {"forecasts": len(rows), "waiting": len(waiting), "next_due": due},
        "focus": ["model"],
        "as_of": h.get("to"),
        "sources": ["lịch sử thị trường", f"{len(rows)} dự báo"],
    }


# -- RM ----------------------------------------------------------------------------------------------------------


async def book(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Sổ khách hàng: the RM's families by how soon they need the RM, with why; proposals, goal tasks, contacts."""
    d = _desk(ctx, "rm")
    fams = d["families"]
    if not fams:
        raise ToolFailed("Bạn chưa được giao gia đình nào")
    soon = [f for f in fams if f["level"] >= 2]
    why = lambda f: ", ".join(w["text"] for w in f["why"])  # noqa: E731
    each = "; ".join(f"{f['name']} — {f['level_label'].lower()}: {why(f)}" for f in soon[:6])
    last = d["contacts"][0] if d["contacts"] else None
    name = {f["id"]: f["name"] for f in fams}
    # every family named with its code: a family outside this list is another RM's (staff stress test D04)
    listed = ", ".join(f"{f['name']} ({f['id']})" for f in fams)
    waiting = "; ".join(f"{p['title']} ({name.get(p['family_id'], p['family_id'])})" for p in d["proposals"][:4])
    text = (
        f"Sổ của bạn có {len(fams)} gia đình: {listed}; gia đình khác không thuộc sổ của bạn. "
        + (f"{len(soon)} cần bạn sớm: {each}. " if soon else "Không gia đình nào cần gọi ngay hay chờ bạn duyệt. ")
        + f"{len(d['proposals'])} đề xuất chờ duyệt{': ' + waiting if waiting else ''}, "
        + f"{len(d['tasks'])} việc theo mục tiêu. "
        + (
            f"Liên hệ gần nhất: {name.get(last['family_id'], last['family_id'])} qua {last['channel_label'].lower()}."
            if last
            else "Chưa ghi liên hệ nào."
        )
        + (f" {len(d['control'])} gia đình trong nhóm đối chứng: không có tín hiệu cho họ." if d["control"] else "")
    )
    return {
        "text": text,
        "data": {"families": len(fams), "soon": len(soon), "proposals": len(d["proposals"]), "tasks": len(d["tasks"])},
        "focus": ["book"] + [f"family:{f['id']}" for f in soon],
        "sources": ["Sổ khách hàng", "Hôm nay", "Duyệt đề xuất"],
    }


# -- Admin (and Compliance: the chain and configuration) ---------------------------------------------------------


async def operations(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Vận hành: what on the operations map is not green, the alerts open, the jobs failing, configuration waiting."""
    d = _desk(ctx, "admin")
    off = [n for n in d["nodes"] if n["state"] in ("bad", "warn")]
    opened = [a for a in d["alerts"] if a["status"] == "open"]
    parts = [
        "Mọi phần của hệ thống đều ổn ở lần chạy gần nhất."
        if not off
        else f"{len(off)} phần cần xem: "
        + "; ".join(
            f"{n['label']} ({'lỗi' if n['state'] == 'bad' else 'cần xem'}: {n['error'] or n['value']})" for n in off
        )
        + "."
    ]
    if opened:
        parts.append(f"{len(opened)} cảnh báo đang mở: " + "; ".join(a["title"] for a in opened[:4]) + ".")
    if d["failing"]:
        parts.append(f"{len(d['failing'])} việc lỗi: " + ", ".join(j["id"] for j in d["failing"][:5]) + ".")
    if d["config"]:
        parts.append(f"{len(d['config'])} cấu hình chờ duyệt.")
    idle = [n["label"] for n in d["nodes"] if n["state"] == "idle"]
    if idle:
        parts.append("Chưa có lần chạy nào để đánh giá: " + ", ".join(idle) + ".")
    return {
        "text": " ".join(parts),
        "data": {"off": len(off), "alerts": len(opened), "failing": len(d["failing"]), "config": len(d["config"])},
        "focus": ["ops"] + [f"node:{n['id']}" for n in off] + (["alerts"] if opened else []),
        "sources": ["Hệ thống"],
    }


async def chain(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Chuỗi nhật ký: the audit chain checked now (BRD-BR-12, FR-702) and its write-once copy."""
    from control import audit, db, worm

    with db.tx() as con:
        c, w = audit.verify(con), worm.verify(con)
    head = (
        f"Chuỗi nhật ký nguyên vẹn: {c['count']} dòng, đầu chuỗi {str(c['head'])[:12]}…"
        if c["ok"]
        else f"Chuỗi nhật ký GÃY ở dòng {c['broken_at']}: {c.get('reason') or 'băm không khớp'}"
    )
    copy = (
        f"Bản chỉ-ghi-một-lần: {w['segments']} đoạn, {'khớp' if w['ok'] else 'lệch: ' + str(w.get('reason') or '')}."
        if w.get("on")
        else "Bản chỉ-ghi-một-lần đang tắt."
    )
    return {
        "text": f"{head}. {copy}",
        "data": {"ok": c["ok"], "count": c["count"], "worm_ok": w["ok"]},
        "focus": ["chain", "node:chain"],
        "sources": ["chuỗi nhật ký kiểm toán"],
    }


async def config_waiting(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Cấu hình chờ duyệt: each kind with a version proposed, who proposed it, whether a second person must approve."""
    from control import config

    waiting = [k for k in config.overview() if k.get("pending")]
    if not waiting:
        return {"text": "Không cấu hình nào chờ duyệt.", "data": {"waiting": 0}, "focus": ["config", "node:config"]}
    each = "; ".join(
        f"{k['label']} ({k['pending']['id']}, đề xuất bởi {k['pending'].get('proposed_by') or '—'}, "
        f"{k['owner_label']} duyệt{', cần người thứ hai' if k['two_person'] else ''})"
        for k in waiting
    )
    return {
        "text": f"{len(waiting)} cấu hình chờ duyệt: {each}. Duyệt ở trang Cấu hình.",
        "data": {"waiting": len(waiting)},
        "focus": ["config", "node:config"],
        "sources": ["Cấu hình"],
    }


# -- Expert (specialist) -------------------------------------------------------------------------------------------


async def expert_desk(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Bàn chuyên gia: the recommendations waiting for this specialist, oldest first, and the certificate."""
    d = _desk(ctx, "specialist")
    cert = d["certificate"]
    head = (
        f"Chứng chỉ {cert['certificate']} ({cert['issuer']}) hiệu lực đến {cert['valid_until']}."
        if cert
        else "Bạn chưa có chứng chỉ còn hiệu lực nên chưa duyệt được khuyến nghị; Tuân thủ cập nhật trong Cấu hình."
    )
    w = d["waiting"]
    each = "; ".join(
        f"{x['title']} cho {x['name']} ({x['id']}, gia đình {x['family_id']}, RM {x['rm'] or '—'}, gửi "
        f"{_when(x['created'])})"
        for x in w[:6]
    )
    mine = ", ".join(f["id"] for f in d["families"])
    return {
        "text": f"{head} "
        + (f"{len(w)} khuyến nghị chờ bạn duyệt, cũ nhất trước: {each}." if w else "Không khuyến nghị nào chờ bạn.")
        + (f" Gia đình được giao cho bạn: {mine}." if mine else ""),
        "data": {"waiting": len(w), "certified": bool(cert), "families": [f["id"] for f in d["families"]]},
        "focus": ["queue"],
        "sources": ["Duyệt khuyến nghị"],
    }


async def family_profile(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Hồ sơ khách: an assigned family's picture — net worth, allocation, risk against its limit, liquidity, goals —
    through the reads the dashboard and the plan use; refused for a family not assigned to this specialist (Q-26)."""
    from dataclasses import replace

    from assistant.tools import goals, overview
    from people import store as people

    d = _desk(ctx, "specialist")
    fid = str(args.get("gia_dinh") or "").strip().upper()
    if not fid:
        waiting = sorted({x["family_id"] for x in d["waiting"]})
        if len(waiting) != 1:
            raise ToolFailed("Cần biết gia đình nào: hãy nói mã gia đình (lấy từ bàn chuyên gia)")
        fid = waiting[0]
    if fid not in {f["id"] for f in d["families"]} or ctx.user not in people.specialists_of(fid):
        raise ToolFailed(f"Gia đình {fid} không được giao cho bạn")
    one = replace(ctx, client_id=fid, scope="family", followed=None)
    a = await overview(one, {})
    try:
        g = (await goals(one, {}))["text"]
    except ToolFailed:
        g = ""
    day = f" Số liệu ngày {a['as_of']}." if a.get("as_of") else ""  # the data's own date (D10)
    return {
        "text": f"Gia đình {fid}: {a['text']} {g}".strip() + day,
        "data": {"family": fid},
        "as_of": a.get("as_of"),
        "focus": ["evidence"],
        "sources": ["Bảng tổng quan", "Kế hoạch mục tiêu"],
    }


# -- Compliance ----------------------------------------------------------------------------------------------------


async def controls(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Bàn kiểm soát: what waits for Compliance, oldest first, then each control's steps and the chain."""
    d = _desk(ctx, "compliance")
    label = {c["id"]: c["label"] for c in d["controls"]}
    q = d["queue"]
    # the item's own line too (a report's number, who uploaded it): “HV-2026-10” was “not in the system” (cmp-lim-02)
    oldest = "; ".join(
        f"{x['title']} ({label[x['control']]}, {x['id']}{', ' + x['sub'] if x.get('sub') else ''}, từ {_when(x['at'])})"
        for x in q[:5]
    )
    head = f"{len(q)} việc chờ Tuân thủ, cũ nhất trước: {oldest}." if q else "Không việc nào chờ Tuân thủ."
    each = "; ".join(
        f"{c['label']}: " + ", ".join(f"{s['count']} {s['label'].lower()}" for s in c["steps"]) for c in d["controls"]
    )
    ch = d["chain"]
    chain = "Chuỗi nhật ký nguyên vẹn" if ch["ok"] else f"Chuỗi nhật ký gãy ở dòng {ch['broken_at']}"
    return {
        "text": f"{head} Từng chốt: {each}. {chain} ({ch['count']} dòng). Quyết định ở trang của từng chốt.",
        "data": {
            "waiting": len(q),
            "controls": {c["id"]: c["steps"][0]["count"] for c in d["controls"]},
            "chain_ok": ch["ok"],
        },  # fmt: skip
        "focus": ["controls", "queue"] + [c["id"] for c in d["controls"] if c["steps"][0]["count"]],
        "sources": ["Bàn kiểm soát"],
    }


CATALOGUE: Dict[str, Tool] = {
    t.name: t
    for t in (
        Tool(
            "ban_quyet_dinh",
            "bàn quyết định của CIO: việc chờ CIO quyết định (nhận định chờ duyệt, lần áp dụng chờ xem lại, cấu hình, "
            "bản tin bị trả lại, sự kiện chưa có nhận định) và dòng chảy từ tin đến gia đình",
            ("cio",),
            cio_desk,
            page="ban-lam-viec",
            follow=["Tác động lớn nhất tới tài sản ở đâu?", "Lần áp dụng nào đang hiệu lực?"],
        ),
        Tool(
            "phoi_nhiem",
            "phơi nhiễm của mọi gia đình trong lần áp dụng mới nhất đang hiệu lực: tổng kỳ vọng ba tháng, theo yếu tố, "
            "gia đình ảnh hưởng nhiều nhất",
            ("cio",),
            exposure,
            page="phoi-nhiem",
            follow=["Có gì chờ tôi duyệt?", "Độ chính xác của mô hình?"],
        ),
        Tool(
            "lan_ap_dung",
            "các lần áp dụng: đang hiệu lực, chờ CIO xem lại, đang tính, đã thay thế hay thu hồi",
            ("cio",),
            runs,
            page="ap-dung",
            follow=["Tác động lớn nhất tới tài sản ở đâu?"],
        ),
        Tool(
            "do_chinh_xac",
            "độ chính xác của mô hình: tỉ lệ biến động thực nằm trong dải trên lịch sử, hướng VN-Index so với mục "
            "tiêu, dự báo của nhận định đã duyệt chờ chấm",
            ("cio",),
            accuracy,
            page="do-chinh-xac",
            timeout=60.0,
        ),
        Tool(
            "so_khach_hang",
            "sổ khách hàng của RM: các gia đình được giao, ai cần gọi ngay và vì sao (ngưỡng xem trước, việc theo mục "
            "tiêu), đề xuất chờ duyệt, liên hệ gần đây",
            ("rm",),
            book,
            page="ban-lam-viec",
            follow=["Hôm nay cần gọi ai?", "Có gì cần chú ý với khách này?"],
        ),
        Tool(
            "agent_nen",
            "các agent và việc chạy nền (Agent CIO, Phản biện, Chính sách, hàng đợi, lấy tin, dữ liệu thị trường, quét "
            "chính sách, tổng hợp trí nhớ, lưu giữ): trạng thái, lần chạy gần nhất, số lần chạy và lỗi hôm nay; với "
            "CIO các sự kiện chạy được Agent CIO và phản biện lỗi, với Quản trị các việc chạy tay được",
            ("cio", "compliance", "admin"),
            background,
            page="viec-nen",
            follow=["Có việc nền nào lỗi không?", "Có gì chờ tôi duyệt?"],
        ),
        Tool(
            "van_hanh",
            "tình trạng vận hành: phần nào của hệ thống không ổn (nguồn tin, dữ liệu thị trường, lịch chạy, chuỗi nhật "
            "ký, sẵn sàng, agent), cảnh báo đang mở, việc lỗi, cấu hình chờ duyệt",
            ("admin",),
            operations,
            page="ban-lam-viec",
            follow=["Chuỗi nhật ký còn nguyên không?", "Cấu hình nào chờ duyệt?"],
        ),
        Tool(
            "ban_chuyen_gia",
            "bàn chuyên gia: các khuyến nghị RM đã duyệt đang chờ bạn duyệt, cũ nhất trước, và chứng chỉ của bạn",
            ("specialist",),
            expert_desk,
            page="ban-lam-viec",
            follow=["Hồ sơ của gia đình này thế nào?"],
        ),
        Tool(
            "ho_so_khach",
            "hồ sơ một gia đình được giao cho bạn: tài sản ròng, phân bổ, rủi ro so với ngưỡng, thanh khoản, mục tiêu",
            ("specialist",),
            family_profile,
            params={
                "gia_dinh": Param(
                    str, "mã gia đình, lấy từ công cụ ban_chuyen_gia; bỏ trống khi chỉ một gia đình chờ", ""
                )
            },
            page="ban-lam-viec",
            timeout=60.0,
        ),
        Tool(
            "ban_kiem_soat",
            "bàn kiểm soát của Tuân thủ: việc đang chờ Tuân thủ, cũ nhất trước (tin bị giữ, nghiên cứu chờ phát hành, "
            "bản tin chờ duyệt, văn bản chính sách chờ xác nhận, cấu hình chờ duyệt), từng chốt và chuỗi nhật ký",
            ("compliance",),
            controls,
            page="ban-lam-viec",
            follow=["Chuỗi nhật ký còn nguyên không?", "Cấu hình nào chờ duyệt?"],
        ),
        Tool(
            "chuoi_nhat_ky",
            "đọc tình trạng chuỗi nhật ký kiểm toán ngay bây giờ: nguyên vẹn hay gãy ở đâu, số dòng, bản chỉ ghi một "
            "lần (chỉ đọc; Quản trị bảo “chạy ngay việc” kiểm tra chuỗi thì là chay_viec_nen)",
            ("admin", "compliance"),
            chain,
            page="nhat-ky",
        ),
        Tool(
            "cau_hinh_cho_duyet",
            "các cấu hình đang chờ duyệt: loại, ai đề xuất, vai trò nào duyệt, có cần người thứ hai không",
            ("admin", "compliance"),
            config_waiting,
            page="cau-hinh",
        ),
    )
}
