"""The overview graph (UI redesign R4, R-D6; kit KIT-UX-04): the client at the centre, the asset classes they hold
(each opening onto its holdings), where the data comes from, the goals they follow, what puts the picture at risk
(stress drawdown, concentration, the liquidity reserve), the policy items that move it and the approved news
events that may affect it. A view over records other pages already show — no graph store, nothing inferred.

Every edge names the record it was read from (``sources``): ``holding`` (a key of the consolidated holdings),
``risk`` (the dashboard's drawdown, concentration or liquidity), ``goal``, ``alert`` (a policy item of FEAT-25) or
``run`` (an EFFECTIVE news-impact run). Holdings are joined to a risk or a policy item by the names those records
list. Edges between a news event and an asset class say “có thể ảnh hưởng”, never a cause. The client reads events
by type, not headline (BRD flow 2), and their impact by asset class only (ADR-0008).

Holding-level edges carry ``parent`` (the class node): the UI shows them when that class is expanded and the
class-level edge (``agg``) otherwise.

The workspace (FEAT-40, OWN-GW-11/12) adds the month's money in and out (``flow``, read from the transactions — the
same month and totals as POST /api/flows), the liquidity reserve (``liquidity``, always, from the dashboard) and the
stress scenarios (``scenario``: hypothetical, with no value until the person runs one — POST /api/scenario — and
never added to net worth). Every edge says how certain it is: ``actual`` (a record), ``estimate`` (a news or policy
impact under the CIO's scenarios) or ``hypothetical`` (a scenario)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from operonx import op

from apply import reads
from control.errors import BadRequest
from people import auth
from scenarios._sim import SCENARIOS
from views import schema
from wealth import fixtures

CLASSES = {
    **schema.ASSET_CLASSES,
    "deposit": "Tiền & tiền gửi",
    "cash": "Tiền & tiền gửi",
    "loan": "Khoản vay",
    "card": "Dư nợ thẻ",
    "insurance": "Bảo hiểm",
    "business": "Cổ phần DN",
}
GROUP = {"cash": "deposit"}  # cash sits with deposits, as on the allocation chart
KINDS = [
    ("family", "Bạn"),
    ("class", "Tài sản"),
    ("holding", "Khoản"),
    ("source", "Nguồn dữ liệu"),
    ("goal", "Mục tiêu"),
    ("risk", "Rủi ro"),
    ("alert", "Chính sách"),
    ("event", "Tin tức"),
    ("flow", "Dòng tiền"),
    ("liquidity", "Thanh khoản"),
    ("scenario", "Kịch bản giả định"),
]
CERTAINTY = {"event": "estimate", "alert": "estimate", "scenario": "hypothetical"}
TOP_ALERTS = 6
WORDING = "có thể ảnh hưởng"
GOAL_STATUS = {"on_track": "Đúng tiến độ", "at_risk": "Cần chú ý", "off_track": "Chậm tiến độ"}


def _pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%".replace(".", ",")


@op
def check_request(client_id: str = None, scope: str = None, role: str = None, goals: list = None) -> dict:
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    scope = scope or "personal"
    if scope not in ("personal", "family"):
        raise ValueError("scope is personal or family")
    role = auth.role_for(role or "client")
    if role not in ("client", "rm"):
        raise ValueError("role is client or rm")
    followed = None if goals is None else [str(g) for g in goals]
    return {"client_id": client_id, "scope": scope, "role": role, "followed": followed}


@op
def build(
    client_id: str,
    scope: str,
    role: str,
    dashboard: dict,
    goals: list,
    alerts: list,
    followed: Optional[list] = None,  # None does not bind across ops: the persona's defaults
    flows: Optional[dict] = None,
) -> dict:
    """Nodes and edges of the overview, each edge with its sources."""
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: Dict[tuple, Dict[str, Any]] = {}

    def node(nid: str, kind: str, label: str, **extra: Any) -> str:
        nodes.setdefault(nid, {"id": nid, "kind": kind, "label": label, **extra})
        return nid

    def edge(a: str, b: str, source: tuple, label: str, value: Optional[float] = None, **extra: Any) -> None:
        e = edges.setdefault((a, b), {"from": a, "to": b, "label": label, "value": None, "sources": [], **extra})
        if value is not None:
            e["value"] = (e["value"] or 0) + value
        src = {"type": source[0], "id": source[1]}
        if src not in e["sources"]:
            e["sources"].append(src)

    d = dashboard
    nw = d["net_worth"]
    me = node(
        "ME",
        "family",
        "Bạn" if role == "client" else fixtures.client(client_id)["name"],
        value=nw["value"],
        assets=nw["assets"],
        liabilities=nw["liabilities"],
        scope=d["scope"],
    )
    held = [h for h in d["holdings"] if h["value"]]
    by_name: Dict[str, List[Dict[str, Any]]] = {}
    for h in held:
        by_name.setdefault(h["name"], []).append(h)
    cls_of = {h["key"]: f"CL:{GROUP.get(h['class'], h['class'])}" for h in held}

    # what is held: classes, each opening onto its holdings
    for h in held:
        c = GROUP.get(h["class"], h["class"])
        cid = node(f"CL:{c}", "class", CLASSES.get(c, c), ref=c, value=0, count=0, liability=h["kind"] == "liability")
        nodes[cid]["value"] += h["value"]
        nodes[cid]["count"] += 1
        hid = node(
            f"HD:{h['key']}",
            "holding",
            h["name"],
            ref=h["key"],
            parent=cid,
            value=h["value"],
            trust=h["trust"],
            source=h["source"],
            owner=h.get("owner_name"),
        )
        if h["kind"] == "liability":
            edge(cid, me, ("holding", h["key"]), "khoản nợ", h["value"])
            edge(hid, cid, ("holding", h["key"]), "thuộc nhóm", h["value"], parent=cid)
        else:
            edge(me, cid, ("holding", h["key"]), "sở hữu", h["value"])
            edge(cid, hid, ("holding", h["key"]), "gồm", h["value"], parent=cid)

    # where the data comes from
    for s in d["sources"]:
        if not s["count"]:
            continue
        sid = node(
            f"SR:{s['source']}",
            "source",
            s["label"],
            ref=s["source"],
            tier=s["tier"],
            what=s["what"],
            status=s["status"],
            trust=s["trust"],
            count=s["count"],
        )
        for h in held:
            if h["source"] == s["source"]:
                edge(sid, cls_of[h["key"]], ("holding", h["key"]), "dữ liệu từ", agg=cls_of[h["key"]])
                edge(sid, f"HD:{h['key']}", ("holding", h["key"]), "dữ liệu từ", parent=cls_of[h["key"]])

    def touch(rid: str, names: List[str], source: tuple, label: str) -> None:
        hit = False
        for name in names:
            for h in by_name.get(name, []):
                hit = True
                edge(cls_of[h["key"]], rid, source, label, agg=cls_of[h["key"]])
                edge(f"HD:{h['key']}", rid, source, label, parent=cls_of[h["key"]])
        if not hit:  # the record names no single holding (a portfolio, an income): it is about the client
            edge(me, rid, source, label)

    # what puts it at risk
    rk = d["risk"]
    if rk["status"] != "ok":
        rid = node(
            "RK:drawdown",
            "risk",
            f"Sụt giảm ước tính {_pct(rk['current'])}",
            status=rk["status"],
            detail=f"ngưỡng {_pct(rk['limit'], 0)} · kịch bản xấu mất {round(rk['stress_loss'] / 1e9, 2)} tỷ".replace(
                ".", ","
            ),
            value=-rk["stress_loss"],
        )
        touch(rid, [t["name"] for t in rk["top"]], ("risk", "drawdown"), "góp vào mức sụt giảm")
    for i, row in enumerate(r for r in d["concentration"]["rows"] if r["flag"]):
        rid = node(
            f"RK:conc{i}",
            "risk",
            f"Tập trung {row['name']}",
            status="over",
            detail=f"{row['kind_label']}: {_pct(row['share'])} tài sản (ngưỡng {_pct(row['limit'], 0)})",
            value=row["value"],
        )
        names = [
            h["name"]
            for h in held
            if h["kind"] == "asset"
            and (
                (
                    row["kind"] == "area"
                    and h["class"] == "real_estate"
                    and (h["detail"].get("area_name") or h["name"]) == row["name"]
                )
                or (
                    row["kind"] == "issuer"
                    and h["class"] in ("stock", "bond")
                    and (h["detail"].get("issuer") or h["name"]) == row["name"]
                )
                or (
                    row["kind"] == "sector"
                    and h["class"] in ("stock", "bond", "business")
                    and h["detail"].get("sector") == row["name"]
                )
            )
        ]
        touch(rid, names, ("risk", "concentration"), "tập trung")
    lq = d["liquidity"]
    if lq["status"] != "ok":
        rid = node(
            "RK:liquidity",
            "risk",
            f"Dự phòng {lq['months']} tháng chi tiêu".replace(".", ","),
            status=lq["status"],
            detail="dưới 6 tháng chi tiêu",
            value=lq["value"],
        )
        edge(me, rid, ("risk", "liquidity"), "thanh khoản")

    # the goals followed
    for g in goals:
        if not (g["id"] in followed if followed is not None else g["followed"]):
            continue
        gl = g["goal"]
        gid = node(
            f"GL:{g['id']}",
            "goal",
            g["title"],
            ref=g["id"],
            status=gl["status"],
            status_label=GOAL_STATUS.get(gl["status"], gl["status"]),
            need=gl["need"],
            have=gl["have"],
            gap=gl["gap"],
            by=gl.get("by"),
            value=gl["need"],
        )
        edge(me, gid, ("goal", g["id"]), GOAL_STATUS.get(gl["status"], "mục tiêu"))

    # the policy items that move it most
    for a in alerts[:TOP_ALERTS]:
        aid = node(
            f"AL:{a['id']}",
            "alert",
            a["title"],
            ref=a["id"],
            opportunity=a["opportunity"],
            severity=a["severity"],
            status_label=a["status_label"],
            value=a["impact"],
            probability=a["probability"],
            source_text=a["source"],
        )
        touch(aid, a["affected"], ("alert", a["id"]), "cơ hội" if a["opportunity"] else "chịu tác động")

    # approved news events that may affect it (EFFECTIVE runs only; by asset class)
    impact = reads.family_impact(client_id, "client" if role == "client" else "rm")
    for it in impact["items"]:
        if it["status"] != "EFFECTIVE":
            continue
        ev = it["event"]
        eid = node(
            f"EV:{ev['id']}",
            "event",
            ev["title"],
            ref=ev["id"],
            run=it["run_id"],
            approved_at=it["approved_at"],
            value=it["horizons"]["3m"]["expected"],
            outlets=it["sources"]["outlets"],
        )
        for c, v in it["by_class"].items():
            if not v:
                continue
            cid = f"CL:{GROUP.get(c, c)}"
            if cid in nodes:
                edge(eid, cid, ("run", it["run_id"]), WORDING, v)

    # the month's money in and out (FEAT-40): the transactions of the latest month with rows, as on Toàn cảnh
    if flows and flows.get("month"):
        m = flows["month"]
        mm = f"T{int(m[5:])}/{m[2:4]}"
        sides = (
            ("in", "inflow", "total_in", f"Thu nhập {mm}", "tiền vào"),
            ("out", "outflow", "total_out", f"Chi tiêu {mm}", "tiền ra"),
        )
        for side, band, total, label, verb in sides:
            if not flows[total]:
                continue
            items = sorted(flows[band], key=lambda b: -b["amount"])
            fid = node(
                f"FL:{side}",
                "flow",
                label,
                side=side,
                month=m,
                value=flows[total],
                items=[{"label": b["label"], "value": b["amount"], "category": b["category"]} for b in items],
                keys=[f"flow:{m}"] + [f"flow:{m}:{side}:{b['category']}" for b in items],
                rows=sum(len(b["rows"]) for b in items),
            )
            a, b = (fid, me) if side == "in" else (me, fid)
            edge(a, b, ("txn", m), verb, flows[total])

    # the liquidity reserve: always shown (a risk node joins it only when the reserve is short)
    lid = node(
        "LQ:reserve",
        "liquidity",
        "Thanh khoản dự phòng",
        value=lq["value"],
        months=round(lq["months"], 1),
        status=lq["status"],
        spending=lq["spending_monthly"],
        items=[{"label": i["name"], "value": i["value"]} for i in lq["items"]],
    )
    edge(me, lid, ("risk", "liquidity"), "dự phòng", lq["value"])

    # the stress scenarios: what if — no figure until one is run, never part of net worth
    for sid, sc in SCENARIOS.items():
        if sc["kind"] != "stress":
            continue
        scn = node(f"SC:{sid}", "scenario", sc["title"], ref=sid, detail=sc["question"], value=None)
        edge(me, scn, ("scenario", sid), "nếu xảy ra")

    for e in edges.values():
        kinds = {nodes[e["from"]]["kind"], nodes[e["to"]]["kind"]}
        e["certainty"] = next((c for k, c in CERTAINTY.items() if k in kinds), "actual")

    return {
        "overview": {
            "client_id": client_id,
            "scope": d["scope"],
            "role": role,
            "as_of": d["as_of"],
            "kinds": [{"kind": k, "label": label} for k, label in KINDS],
            "nodes": list(nodes.values()),
            "edges": list(edges.values()),
            "note": "Mỗi cạnh ghi bản ghi nguồn (khoản tài sản, rủi ro, mục tiêu, chính sách, lần áp dụng tin, "
            "giao dịch). “Có thể ảnh hưởng” theo kịch bản CIO duyệt; không phải quan hệ nhân quả. "
            "Kịch bản là giả định, "
            "không cộng vào tài sản ròng.",
        }
    }
