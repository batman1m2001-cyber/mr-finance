"""Each staff role's own assistant reads its desk (FEAT-41, OWN-MR-10): read tools over the composition the desk
draws (src/desk/reads.py), so the assistant says the numbers the screen shows. Read-only; a tool is offered only to
its role, and the read under it is that role's alone. Their steps light the desk (assistant/stream.py ``NODES``)."""

from __future__ import annotations

from typing import Any, Dict

from assistant.base import Ctx, Tool, ToolFailed
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
    """Bàn quyết định: what waits for the CIO, then where each stage of the pipeline stands."""
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
        "sources": ["Bàn quyết định"],
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
    text = (
        f"Sổ của bạn có {len(fams)} gia đình. "
        + (f"{len(soon)} cần bạn sớm: {each}. " if soon else "Không gia đình nào cần gọi ngay hay chờ bạn duyệt. ")
        + f"{len(d['proposals'])} đề xuất chờ duyệt, {len(d['tasks'])} việc theo mục tiêu. "
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
            follow=["Phơi nhiễm lớn nhất ở đâu?", "Lần áp dụng nào đang hiệu lực?"],
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
            follow=["Phơi nhiễm lớn nhất ở đâu?"],
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
    )
}
