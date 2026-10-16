"""The Financial Intelligence Graph (redesign kit K3, decision D5): a view over stored records, no graph store.

Columns: news → event → scenario branch → factor → asset (holding for staff, asset class for the client) →
family → goal. Every edge names the stored records it was read from (``sources``: event, view, run), so it can
be checked. Edges say “có thể ảnh hưởng” (a potential impact under the CIO's scenarios), never a cause.

Only EFFECTIVE runs are drawn (the current picture). The client sees no headline and no holding: news by outlet
and time, events by type, assets by class (BRD flow 2).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from apply import reads
from apply import run as runs
from control import roles
from engine import FactorModel
from events import store as events
from views import schema
from views import store as vstore

COLUMNS = [
    ("news", "Tin"),
    ("event", "Sự kiện"),
    ("branch", "Kịch bản"),
    ("factor", "Yếu tố"),
    ("asset", "Tài sản"),
    ("family", "Gia đình"),
    ("goal", "Mục tiêu"),
]
TOP_FACTORS = 5  # beside the core shocks, the factors that move the family most
TOP_HOLDINGS = 8
WORDING = "có thể ảnh hưởng"
SIZE = {"S": "nhỏ", "M": "vừa", "L": "lớn"}
CLASSES = {**schema.ASSET_CLASSES, "loan": "Khoản vay", "card": "Dư nợ thẻ"}
VN = timezone(timedelta(hours=7))


def _when(ts: Any) -> str:
    try:
        return datetime.fromtimestamp(float(ts), VN).strftime("%d/%m %H:%M")
    except (TypeError, ValueError):
        return ""


def family_graph(family_id: str, role: str = "client", run_id: Optional[str] = None) -> Dict[str, Any]:
    if role not in reads.VISIBLE:
        raise roles.Forbidden(f"vai trò {role!r} không có")
    client = role == "client"
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: Dict[tuple, Dict[str, Any]] = {}

    def node(nid: str, kind: str, label: str, **extra: Any) -> str:
        nodes.setdefault(nid, {"id": nid, "kind": kind, "label": label, **extra})
        return nid

    def edge(a: str, b: str, source: tuple, label: str = WORDING, value: Optional[float] = None) -> None:
        e = edges.setdefault((a, b), {"from": a, "to": b, "label": label, "value": None, "sources": []})
        if value is not None:
            e["value"] = (e["value"] or 0.0) + value
            if source[0] == "run":  # one event's share of an edge several runs add to (the News Impact panel)
                e.setdefault("by_run", {})[source[1]] = e.get("by_run", {}).get(source[1], 0.0) + value
        src = {"type": source[0], "id": source[1]}
        if src not in e["sources"]:
            e["sources"].append(src)

    fam_name = None
    selected = [r for r in runs.runs(statuses=("EFFECTIVE",)) if not run_id or r["id"] == run_id]
    for run in selected:
        try:
            fam = runs.family_result(run["id"], family_id)
        except KeyError:
            continue
        fam_name = fam["name"]
        fid = node(f"FAM:{family_id}", "family", fam["name"], net_worth=fam["net_worth"])
        h3 = fam["horizons"]["3m"]
        view = vstore.get(run["view_id"])
        ev = events.get(run["event_id"])
        model = FactorModel.from_dict(runs.snapshot_head(run["snapshot_id"])["factor_model"])
        rsrc = ("run", run["id"])

        eid = node(
            f"EV:{ev['id']}",
            "event",
            reads._type_label(ev.get("type")) if client else ev["title"],
            ref=ev["id"],
            run=run["id"],
            expected_3m=h3["expected"],
        )
        for n in ev["news"]:
            label = f"{n.get('outlet') or 'Nguồn công khai'} · {_when(n.get('published'))}"
            nid = node(
                f"NW:{n['id']}",
                "news",
                label if client else n["title"],
                ref=n["id"],
                **({} if client else {"url": n.get("url"), "outlet": n.get("outlet")}),
            )
            edge(nid, eid, ("event", ev["id"]), label="thuộc sự kiện")

        core: set = set()
        fam_branch = {b["id"]: b for b in h3["branches"]}
        for b in view["current"]["scenarios"]["branches"]:
            bid = node(
                f"BR:{view['id']}:{b['id']}",
                "branch",
                f"{b['name']} · {round(b['probability'] * 100)}%",
                ref=view["id"],
                probability=b["probability"],
                family_expected=fam_branch.get(b["id"], {}).get("expected"),
            )
            edge(eid, bid, ("view", view["id"]), label="kịch bản CIO duyệt")
            for s in b["core_shocks"]:
                core.add(s["factor"])
                fnode = node(f"FA:{s['factor']}", "factor", model.factor(s["factor"]).name, ref=s["factor"])
                arrow = "▲" if s["direction"] == "up" else "▼"
                edge(bid, fnode, ("view", view["id"]), label=f"cú sốc {arrow} {SIZE.get(s['size'], s['size'])}")

        top = sorted(h3["by_factor"], key=lambda k: -abs(h3["by_factor"][k]))[:TOP_FACTORS]
        shown = core | set(top)
        for f in shown:
            node(f"FA:{f}", "factor", model.factor(f).name, ref=f)
            nodes[f"FA:{f}"]["contribution"] = nodes[f"FA:{f}"].get("contribution", 0.0) + h3["by_factor"].get(f, 0.0)

        if client:
            for cls, v in h3["by_class"].items():
                if not v:
                    continue
                aid = node(f"AC:{cls}", "asset", CLASSES.get(cls, cls), ref=cls)
                edge(aid, fid, rsrc, value=v)
                for x in fam["holdings"]:
                    if x["class"] == cls:
                        for f in x["loads"]:
                            if f in shown:
                                edge(f"FA:{f}", aid, rsrc, label="độ nhạy")
        else:
            held = sorted(
                (x for x in fam["holdings"] if h3["by_holding"].get(x["key"])),
                key=lambda x: -abs(h3["by_holding"][x["key"]]),
            )[:TOP_HOLDINGS]
            for x in held:
                aid = node(f"HD:{x['key']}", "asset", x["name"], ref=x["key"], asset_class=x["class"])
                edge(aid, fid, rsrc, value=h3["by_holding"][x["key"]])
                for f in x["loads"]:
                    if f in shown:
                        edge(f"FA:{f}", aid, rsrc, label="độ nhạy")

        for g in (fam.get("goal_impact") or {}).get("goals", []):
            gid = node(f"GL:{g['goal_id']}", "goal", g["label"], ref=g["goal_id"], date=g["date"])
            nodes[gid].update(before=g["before"]["level"], after=g["after"]["level"])
            edge(fid, gid, rsrc, label=f"{g['before']['level']} → {g['after']['level']}")

    # drop factor nodes that reach no asset: a core shock this family does not hold
    reach = {e["from"] for e in edges.values() if e["to"].startswith(("HD:", "AC:"))}
    for nid in [n for n in nodes if n.startswith("FA:") and n not in reach]:
        if not any(e["to"] == nid for e in edges.values()):
            del nodes[nid]
    return {
        "family_id": family_id,
        "family": fam_name,
        "role": role,
        "columns": [{"kind": k, "label": label} for k, label in COLUMNS],
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "runs": [r["id"] for r in selected],
        "wording": WORDING,
        "note": "Mỗi cạnh ghi nguồn đã lưu (sự kiện, nhận định, lần áp dụng). “Có thể ảnh hưởng” theo kịch bản "
        "CIO duyệt; không phải quan hệ nhân quả.",
    }


RUN_COLUMNS = [
    ("news", "Tin"),
    ("event", "Sự kiện"),
    ("branch", "Kịch bản"),
    ("factor", "Yếu tố"),
    ("asset", "Nhóm tài sản"),
    ("family", "Gia đình"),
]


def run_graph(run_id: str) -> Dict[str, Any]:
    """The CIO's whole run (UI redesign R4): news → event → scenario → factor → asset class → every family the run
    computed, from the run's stored results. Asset class → family edges carry that family's 3-month expected change
    by class; a factor reaches a class when a holding of that class loads on it."""
    run = runs.get(run_id)
    view = vstore.get(run["view_id"])
    ev = events.get(run["event_id"])
    model = FactorModel.from_dict(runs.snapshot_head(run["snapshot_id"])["factor_model"])
    results = runs.family_results(run_id)
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: Dict[tuple, Dict[str, Any]] = {}
    src = ("run", run_id)

    def node(nid: str, kind: str, label: str, **extra: Any) -> str:
        nodes.setdefault(nid, {"id": nid, "kind": kind, "label": label, **extra})
        return nid

    def edge(a: str, b: str, source: tuple, label: str = WORDING, value: Optional[float] = None) -> None:
        e = edges.setdefault((a, b), {"from": a, "to": b, "label": label, "value": None, "sources": []})
        if value is not None:
            e["value"] = (e["value"] or 0.0) + value
        s = {"type": source[0], "id": source[1]}
        if s not in e["sources"]:
            e["sources"].append(s)

    eid = node(
        f"EV:{ev['id']}",
        "event",
        ev["title"],
        ref=ev["id"],
        run=run_id,
        expected_3m=(run.get("totals") or {}).get("expected_3m"),
    )
    for n in ev["news"]:
        nid = node(f"NW:{n['id']}", "news", n["title"], ref=n["id"], url=n.get("url"), outlet=n.get("outlet"))
        edge(nid, eid, ("event", ev["id"]), label="thuộc sự kiện")
    core: set = set()
    for b in view["current"]["scenarios"]["branches"]:
        bid = node(
            f"BR:{view['id']}:{b['id']}",
            "branch",
            f"{b['name']} · {round(b['probability'] * 100)}%",
            ref=view["id"],
            probability=b["probability"],
        )
        edge(eid, bid, ("view", view["id"]), label="kịch bản CIO duyệt")
        for s in b["core_shocks"]:
            core.add(s["factor"])
            fid = node(f"FA:{s['factor']}", "factor", model.factor(s["factor"]).name, ref=s["factor"])
            arrow = "▲" if s["direction"] == "up" else "▼"
            edge(bid, fid, ("view", view["id"]), label=f"cú sốc {arrow} {SIZE.get(s['size'], s['size'])}")
    total: Dict[str, float] = {}
    for fam in results.values():
        for f, v in fam["horizons"]["3m"]["by_factor"].items():
            total[f] = total.get(f, 0.0) + v
    shown = core | set(sorted(total, key=lambda k: -abs(total[k]))[:TOP_FACTORS])
    for f in shown:
        node(f"FA:{f}", "factor", model.factor(f).name, ref=f, contribution=total.get(f, 0.0))
    for fam_id, fam in sorted(results.items()):
        h3 = fam["horizons"]["3m"]
        famn = node(
            f"FAM:{fam_id}",
            "family",
            fam["name"],
            ref=fam_id,
            net_worth=fam["net_worth"],
            expected_3m=h3["expected"],
            pre_review=fam["pre_review"],
        )
        for cls, v in h3["by_class"].items():
            if not v:
                continue
            aid = node(f"AC:{cls}", "asset", CLASSES.get(cls, cls), ref=cls)
            edge(aid, famn, src, value=v)
            for x in fam["holdings"]:
                if x["class"] == cls:
                    for f in x["loads"]:
                        if f in shown:
                            edge(f"FA:{f}", aid, src, label="độ nhạy")
    reach = {e["from"] for e in edges.values() if e["to"].startswith("AC:")}
    for nid in [n for n in nodes if n.startswith("FA:") and n not in reach]:
        if not any(e["to"] == nid for e in edges.values()):
            del nodes[nid]
    return {
        "run_id": run_id,
        "status": run["status"],
        "family": None,
        "role": "cio",
        "columns": [{"kind": k, "label": label} for k, label in RUN_COLUMNS],
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "runs": [run_id],
        "families": len(results),
        "wording": WORDING,
        "note": "Toàn bộ lần áp dụng: mỗi cạnh ghi nguồn đã lưu (sự kiện, nhận định, lần áp dụng). “Có thể ảnh hưởng” "
        "theo kịch bản CIO duyệt; không phải quan hệ nhân quả.",
    }
