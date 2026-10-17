"""The workspace graph's two read tools (UNIFIED_FLOWS_PLAN F10, OWN-GW-47/48). ``lien_ket``: a node's (or an edge's)
links, read from the overview the graph is drawn from — what each joins, its amount and monthly rate, its certainty
and how many records it was read from. ``so_sanh_kich_ban``: stress tests side by side, each alone and all together,
through the one engine that never counts twice (``scenarios.combine``). Both answer from the server's numbers by
template; neither writes anything, and no scenario is ever added to net worth."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from assistant.base import Ctx, Param, Tool, ToolFailed, run_graph
from assistant.tools import STRESS, _need_client, _vnd
from scenarios import _sim

CERT = {"actual": "thực tế", "estimate": "ước tính", "hypothetical": "giả định"}
# the scenarios the model may name: the stress tests' words, and the person's own what-if (only with its inputs)
COMPARE = {**STRESS, "cua_ban": "custom"}
LINKS = 12  # at most, the largest first
GOAL_WORD = {"on_track": "đúng tiến độ", "at_risk": "cần chú ý", "off_track": "chậm tiến độ"}


def keys_of(n: Dict[str, Any]) -> List[str]:
    """The focus keys a node answers to on the graph (web/workspace/graph.js keysOf)."""
    ref = n.get("ref")
    k = {
        "family": ["kpi:net_worth"],
        "goal": [f"goal:{ref}"],
        "event": [f"event:{ref}"],
        "alert": [f"policy:{ref}"],
        "class": [f"class:{ref}"],
        "liquidity": ["kpi:liquidity"],
        "flow": list(n.get("keys") or []),
        "category": list(n.get("keys") or []),
        "scenario": [f"scenario:{ref}"],
    }.get(n["kind"], [])
    if n["id"] == "RK:drawdown":
        k.append("kpi:risk")
    if n["id"] == "RK:liquidity":
        k.append("kpi:liquidity")
    return k


def _amount(e: Dict[str, Any]) -> str:
    if e.get("value") is None:
        return ""
    v = e["value"]
    s = _vnd(v, e.get("certainty") != "actual") if e.get("certainty") != "actual" else _vnd(abs(v))
    if e.get("monthly") is not None and abs(e["monthly"] - abs(v)) > 0.5:
        s += f" (~{_vnd(e['monthly'])}/tháng)"
    return s


async def links(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The links of the node (or edge ``A>B``) named, else of what is picked on the graph."""
    from overview.graph import overview_flow

    target = str(args.get("node") or (ctx.graph.get("selected") or {}).get("id") or "").strip()
    if not target:
        raise ToolFailed("Chưa chọn mục nào: bấm một nút hoặc một liên kết trên đồ thị rồi hỏi lại")
    o = (
        await run_graph(
            overview_flow,
            client_id=_need_client(ctx),
            scope=ctx.scope,
            role="client" if ctx.role == "client" else "rm",
            goals=ctx.followed,
        )
    )["overview"]
    by = {n["id"]: n for n in o["nodes"]}
    picked = None
    if ">" in target:  # an edge: its own line first, then the links of its end that is not “My Wealth”
        a, b = target.split(">", 1)
        picked = next((e for e in o["edges"] if e["from"] == a and e["to"] == b), None)
        target = b if a == "ME" else a
    node = by.get(target)
    if node is None:
        raise ToolFailed("Mục này không có trên đồ thị của khách hàng đang chọn")
    mine = [e for e in o["edges"] if node["id"] in (e["from"], e["to"])]
    mine.sort(key=lambda e: (e.get("value") is None, -abs(e.get("value") or 0)))
    rows = []
    for e in mine[:LINKS]:
        other = by[e["to"] if e["from"] == node["id"] else e["from"]]
        rows.append(
            {
                "with": other["label"],
                "id": other["id"],
                "says": e["label"],
                "value": e.get("value"),
                "monthly": e.get("monthly"),
                "dir": e.get("dir"),
                "certainty": e.get("certainty", "actual"),
                "records": len(e.get("sources") or []),
            }
        )
    said = [
        f"{r['with']} — {r['says']}{(' ' + _amount(e)) if _amount(e) else ''} ({CERT[r['certainty']]})"
        for r, e in zip(rows[:5], mine[:5])
    ]
    head = ""
    if picked is not None:
        head = f"Liên kết {by[picked['from']]['label']} → {by[picked['to']]['label']}: {picked['label']}"
        head += f" {_amount(picked)} ({CERT[picked.get('certainty', 'actual')]}). "
    text = (
        head
        + f"{node['label']} có {len(mine)} liên kết"
        + (": " + "; ".join(said) if said else "")
        + ". Thực tế là số đã ghi nhận; ước tính và giả định không cộng vào tài sản ròng."
    )
    near = [by[r["id"]] for r in rows]
    return {
        "text": text,
        "data": {"node": node["id"], "kind": node["kind"], "links": rows, "edge": picked and target},
        "focus": [k for n in [node, *near] for k in keys_of(n)],
        "as_of": o.get("as_of"),
        "sources": ["Đồ thị tài chính: các liên kết và bản ghi của chúng"],
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": r["with"],
                    "sub": f"{r['says']} · {CERT[r['certainty']]} · {r['records']} bản ghi",
                    "chip": _amount(e) or "quan hệ",
                }
                for r, e in zip(rows, mine)
            ],
        },
    }


def _ids(ctx: Ctx, args: Dict[str, Any]) -> List[str]:
    named = [COMPARE[w] for w in (args.get("scenarios") or []) if w in COMPARE]
    ids = list(dict.fromkeys(named or (ctx.graph.get("active") or [])))
    if "custom" in ids and "custom" not in (ctx.graph.get("params") or {}):
        ids.remove("custom")  # the person's what-if has no inputs here: it is theirs to set on the graph
    return ids


async def compare(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Each scenario alone, then all together: the difference is the compounding and the costs counted once."""
    from scenarios.graph import combine_flow

    ids = _ids(ctx, args)
    if not ids:
        raise ToolFailed("Chưa có kịch bản nào: bật kịch bản trên đồ thị, hoặc nêu tên kịch bản cần so sánh")
    params = ctx.graph.get("params") or {}

    async def run(which: List[str]) -> Dict[str, Any]:
        return (
            await run_graph(
                combine_flow,
                client_id=_need_client(ctx),
                scenarios=which,
                params=params,
                scope=ctx.scope,
                goals=ctx.followed,
            )
        )["result"]

    together = await run(ids)
    alone = {sid: (await run([sid]))["change"] for sid in ids} if len(ids) > 1 else {ids[0]: together["change"]}
    title = {s["id"]: s["title"] for s in together["scenarios"]}
    b, a = together["before"]["net_worth"], together["after"]["net_worth"]
    text = (
        ("Riêng từng kịch bản: " + "; ".join(f"{title[s]} {_vnd(c, True)}" for s, c in alone.items()) + ". ")
        if len(ids) > 1
        else ""
    )
    text += f"{'Cùng lúc' if len(ids) > 1 else title[ids[0]]}: tài sản ròng {_vnd(b)} → {_vnd(a)} "
    text += f"({_vnd(together['change'], True)})."
    gap = together["change"] - sum(alone.values())
    if len(ids) > 1 and abs(gap) >= 1e6:
        text += (
            f" Cộng riêng lẻ ra {_vnd(sum(alone.values()), True)}, khác {_vnd(gap, True)}: các cú sốc nhân nhau trên "
            "cùng một khoản và chi phí trùng chỉ tính một lần."
        )
    for w in together["warnings"]:
        text += f" {w}."
    picked = str((ctx.graph.get("selected") or {}).get("id") or "")
    goals = sorted(together["goals"], key=lambda g: f"GL:{g['id']}" != picked)  # the picked goal first
    if goals:
        word = lambda s: GOAL_WORD.get(s, s)  # noqa: E731
        said = [
            f"{g['title']} {word(g['before']['status'])}"
            + (f" → {word(g['after']['status'])}" if g["before"]["status"] != g["after"]["status"] else " (giữ nguyên)")
            for g in goals
        ]
        text += " Mục tiêu: " + "; ".join(said) + "."
    text += " Đây là giả định trên tài sản hiện có, không phải dự báo, không cộng vào tài sản ròng."
    return {
        "text": text,
        "data": {
            "scenarios": ids,
            "alone": alone,
            "together": together["change"],
            "before": b,
            "after": a,
            "by_class": together["by_class"],
            "goals": {g["id"]: [g["before"]["status"], g["after"]["status"]] for g in goals},
        },
        "focus": [f"scenario:{s}" for s in ids]
        + [f"class:{c}" for c, v in together["by_class"].items() if v]
        + [f"goal:{g['id']}" for g in goals if g["before"]["status"] != g["after"]["status"]],
        "as_of": together.get("as_of"),
        "sources": ["Mô phỏng kịch bản trên các khoản hiện có: một bộ máy cho riêng lẻ và cùng lúc"],
        "card": {
            "kind": "figures",
            "title": "So sánh kịch bản",
            "items": [{"label": title[s], "value": _vnd(c, True)} for s, c in alone.items()]
            + ([{"label": "Cùng lúc", "value": _vnd(together["change"], True)}] if len(ids) > 1 else []),
        },
    }


CATALOGUE: Dict[str, Tool] = {
    t.name: t
    for t in [
        Tool(
            "lien_ket",
            "các liên kết của một mục trên đồ thị tài chính (mục đang chọn nếu không nêu): nối với gì, số tiền, mỗi "
            "tháng, thực tế hay ước tính hay giả định, từ bản ghi nào",
            ("client", "rm"),
            links,
            params={
                "node": Param(str, "mã mục trên đồ thị (vd GL:tuition) hoặc liên kết A>B; để trống: mục đang chọn", "")
            },
            follow=["Vì sao tin này ảnh hưởng tới tôi?", "So sánh các kịch bản đang bật"],
        ),
        Tool(
            "so_sanh_kich_ban",
            "so sánh các kịch bản sốc: từng kịch bản riêng và tất cả cùng lúc, không tính trùng (mặc định: các kịch "
            "bản đang bật trên đồ thị)",
            ("client", "rm"),
            compare,
            params={
                "scenarios": Param(List[Literal[tuple(COMPARE)]], "các kịch bản cần so sánh; để trống: đang bật", [])
            },
            page="ke-hoach",
            follow=["Mục tiêu của tôi thế nào?", "Kịch bản lãi suất tăng"],
        ),
    ]
}
assert set(STRESS.values()) | {"custom"} == {s for s, m in _sim.SCENARIOS.items() if m["kind"] == "stress"}
