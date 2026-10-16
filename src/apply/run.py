"""An application run: an approved view applied to every family (BRD FR-401…405, FR-501…503, BR-08,
BR-09, BR-13).

1. Snapshot: every family's holdings (the family view: members who consented), the market file's
   date and hash, the whole factor model, the view's branches and its content hash — frozen, and
   identified by the SHA-256 of their canonical JSON. Recomputing from it gives the same numbers to
   the dong (NFR-04); ``verify`` proves it.
2. The engine for every family: bands at three horizons, contributions by holding, class, factor.
3. Post-check (FR-501): concentration, stale prices, share of value from proxies, implausible
   size. A critical finding stops the run at NEEDS_CIO_REVIEW; otherwise it is EFFECTIVE.
4. Ranking (FR-403), the RM pre-review flag — 3-month P10 at or below −5 % of net worth (FR-503,
   decision A9) — and the exposure of all families by factor (BR-13).

Runs: COMPUTING → POST_CHECKING → EFFECTIVE | NEEDS_CIO_REVIEW | FAILED; later SUPERSEDED (a newer
run of the same event) or WITHDRAWN (the view was withdrawn). RMs see EFFECTIVE, SUPERSEDED and
WITHDRAWN only, labelled.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from datetime import date
from typing import Any, Dict, List, Optional

from apply.goals import POOL, goal_impacts
from control import audit, config, crypto, db
from engine import ENGINE_VERSION, FactorModel, evaluate
from people import store as people_store
from procedural import goals as procedural_goals
from views import schema
from wealth import fixtures, profile
from wealth.paths import DATA

# BR-09 default: the 3-month P10 at or below −5 % of net worth; the value in force is versioned (FR-701)
PRE_REVIEW_PCT = config.THRESHOLDS["pre_review_pct"]
RM_VISIBLE = ("EFFECTIVE", "SUPERSEDED", "WITHDRAWN")
STATUS_LABEL = {
    "COMPUTING": "Đang tính",
    "POST_CHECKING": "Đang hậu kiểm",
    "EFFECTIVE": "Hiệu lực",
    "NEEDS_CIO_REVIEW": "Chờ CIO xem lại",
    "FAILED": "Lỗi tính",
    "SUPERSEDED": "Đã thay thế",
    "WITHDRAWN": "Đã thu hồi",
}


class RunError(ValueError):
    pass


def _hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def family_holdings() -> Dict[str, Dict[str, Any]]:
    """Every family's holdings and members, read the way the dashboard reads them."""
    from operonx import Operon

    from consolidate.graph import consolidate_flow

    engine = Operon(consolidate_flow, params={"client_id": None, "scope": None})
    as_of = date.fromisoformat(fixtures.market()["as_of"])
    out = {}
    with people_store.one_read():  # each source op reads the client: once from the database is enough
        for cid in fixtures.client_ids():
            out[cid] = await _family(engine, cid, as_of)
    return out


async def _family(engine, cid: str, as_of: date) -> Dict[str, Any]:
    got = await engine.run(inputs={"client_id": cid, "scope": "family"})
    if "$errors" in got:
        raise RunError(f"không đọc được danh mục {cid}: {got['$errors']}")
    who = profile.build(cid, got["members"])
    rec = fixtures.client(cid)
    return {
        "name": rec["name"],
        "members": got["members"],
        "holdings": [
            {k: h[k] for k in ("key", "owner", "kind", "class", "name", "value", "detail")} for h in got["holdings"]
        ],
        # FR-404: the dated goals and the monthly surplus their level is judged against
        "goals": [
            {k: g[k] for k in ("goal_id", "label", "date", "amount")} for g in procedural_goals.goals_of(rec, as_of)
        ],
        "surplus_monthly": who["income_monthly"] - who["spending_monthly"],
    }


def make_snapshot(view: Dict[str, Any], families: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    market_raw = (DATA / "market.json").read_bytes()
    model_raw = config.data("factor_model")  # FR-701: the approved version in force
    sc = view["current"]["scenarios"]
    body = {
        "view_id": view["id"],
        "view_content_hash": view["content_hash"],
        "branches": schema.to_engine(sc["branches"], sc["priced_in"]),
        "priced_in": sc["priced_in"],
        "families": families,
        "market": {"as_of": fixtures.market()["as_of"], "sha256": hashlib.sha256(market_raw).hexdigest()},
        "factor_model": model_raw,
        "thresholds": config.data("thresholds"),  # frozen with the run, so a recompute uses the same rules
        "engine_version": ENGINE_VERSION,
    }
    return {"id": "SN-" + _hash(body)[:16], "hash": _hash(body), **body}


def compute(snapshot: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """The engine over every family of a snapshot: pure, so the same snapshot gives the same numbers."""
    model = FactorModel.from_dict(snapshot["factor_model"])
    limits = snapshot.get("thresholds") or config.THRESHOLDS
    out = {}
    for fid, fam in sorted(snapshot["families"].items()):
        hs = fam["holdings"]
        assets = sum(h["value"] for h in hs if h["kind"] == "asset")
        debts = sum(h["value"] for h in hs if h["kind"] == "liability")
        nw = assets - debts
        r = evaluate(hs, snapshot["branches"], model)
        h3 = r["horizons"]["3m"]
        modelled = sum(h["value"] for h in r["holdings"] if h["modelled"] and h["value"] > 0)
        loans = {h["key"] for h in hs if h["class"] == "loan"}
        pooled = [h for h in hs if h["kind"] == "asset" and h["class"] in POOL]
        pool_bands = (  # BR-08: the goals' pool through the same engine, for the VND impact by goal
            evaluate(pooled, snapshot["branches"], model)["horizons"] if fam.get("goals") and pooled else None
        )
        out[fid] = {
            "family_id": fid,
            "name": fam["name"],
            "members": [m["name"] for m in fam["members"]],
            "net_worth": nw,
            "assets": assets,
            "horizons": {
                k: {
                    x: v[x]
                    for x in (
                        "months",
                        "expected",
                        "p5",
                        "p10",
                        "p50",
                        "p90",
                        "by_class",
                        "by_factor",
                        "by_holding",
                        "branches",
                    )
                }
                for k, v in r["horizons"].items()
            },
            "pct": {
                k: {x: (v[x] / nw if nw else 0.0) for x in ("expected", "p5", "p10", "p50", "p90")}
                for k, v in r["horizons"].items()
            },
            "holdings": r["holdings"],
            "loan_interest_3m": sum(v for k, v in h3["by_holding"].items() if k in loans),
            "modelled_share": modelled / assets if assets else 0.0,
            "pre_review": bool(nw > 0 and h3["p10"] <= limits["pre_review_pct"] * nw),
            "model": r["model"],
            "goal_impact": goal_impacts(fam, h3["by_holding"], snapshot["market"]["as_of"], pool_bands),
        }
    return out


def postcheck(
    results: Dict[str, Dict[str, Any]], snapshot: Dict[str, Any], today: Optional[str] = None
) -> Dict[str, Any]:
    """FR-501's rules; the summary is a template, not a model (F02: no family data goes to AI)."""
    findings: List[Dict[str, Any]] = []
    limits = snapshot.get("thresholds") or config.THRESHOLDS
    as_of = date.fromisoformat(snapshot["market"]["as_of"])
    age = (date.fromisoformat(today) if today else date.today()) - as_of
    if age.days > 3:
        sev = "critical" if age.days > 45 else "medium" if age.days > 14 else "low"
        findings.append(
            {
                "id": "P2",
                "severity": sev,
                "family_id": None,
                "title": "Giá định giá đã cũ",
                "detail": f"Giá dùng để tính là ngày {as_of.isoformat()} ({age.days} ngày trước).",
            }
        )
    for fid, r in results.items():
        nw = r["net_worth"]
        biggest = max((h for h in r["holdings"] if h["value"] > 0), key=lambda h: h["value"], default=None)
        if biggest and nw > 0 and biggest["value"] / nw > limits["concentration_share"]:
            findings.append(
                {
                    "id": f"P1-{fid}",
                    "severity": "medium",
                    "family_id": fid,
                    "title": "Tài sản tập trung",
                    "detail": f"{biggest['name']} chiếm {biggest['value'] / nw:.0%} tài sản ròng.",
                }
            )
        if r["modelled_share"] > limits["modelled_share"]:
            findings.append(
                {
                    "id": f"P3-{fid}",
                    "severity": "medium",
                    "family_id": fid,
                    "title": "Phần lớn giá trị tính theo mô hình",
                    "detail": f"{r['modelled_share']:.0%} tài sản tính bằng đại diện (BĐS, cổ phần tư nhân).",
                }
            )
        if nw > 0 and abs(r["horizons"]["3m"]["expected"]) > limits["implausible_share"] * nw:
            findings.append(
                {
                    "id": f"P4-{fid}",
                    "severity": "critical",
                    "family_id": fid,
                    "title": "Tác động lớn bất thường",
                    "detail": f"Kỳ vọng 3 tháng {r['pct']['3m']['expected']:.1%} tài sản ròng: cần CIO xem lại.",
                }
            )
    if results and all(r["horizons"]["3m"]["expected"] == 0 for r in results.values()):
        findings.append(
            {
                "id": "P5",
                "severity": "low",
                "family_id": None,
                "title": "Không gia đình nào bị tác động",
                "detail": "Mọi kỳ vọng 3 tháng bằng 0 (ví dụ tin đã vào giá hết).",
            }
        )
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("critical", "medium", "low")}
    flagged = sum(1 for r in results.values() if r["pre_review"])
    summary = (
        f"Hậu kiểm {len(results)} gia đình: {counts['critical']} phát hiện nghiêm trọng, "
        f"{counts['medium']} trung bình, {counts['low']} thấp. "
        f"{flagged} gia đình cần RM xem trước (P10 3 tháng ≤ −5% tài sản ròng)."
    )
    return {"findings": findings, "counts": counts, "summary": summary, "by": "rules"}


def ranking(results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = [
        {
            "family_id": fid,
            "name": r["name"],
            "net_worth": r["net_worth"],
            "expected_3m": r["horizons"]["3m"]["expected"],
            "expected_3m_pct": r["pct"]["3m"]["expected"],
            "p10_3m": r["horizons"]["3m"]["p10"],
            "p10_3m_pct": r["pct"]["3m"]["p10"],
            "pre_review": r["pre_review"],
        }
        for fid, r in results.items()
    ]
    return sorted(rows, key=lambda x: (x["expected_3m"], x["family_id"]))


def exposure(results: Dict[str, Dict[str, Any]], factor_ids: List[str]) -> Dict[str, Any]:
    """BR-13: every family's expected 3-month change by factor, and the total."""
    rows = []
    total = {f: 0 for f in factor_ids}
    for fid, r in sorted(results.items()):
        bf = r["horizons"]["3m"]["by_factor"]
        nw = r["net_worth"]
        rows.append(
            {
                "family_id": fid,
                "name": r["name"],
                "net_worth": nw,
                "vnd": {f: bf.get(f, 0) for f in factor_ids},
                "pct": {f: (bf.get(f, 0) / nw if nw else 0.0) for f in factor_ids},
            }
        )
        for f in factor_ids:
            total[f] += bf.get(f, 0)
    return {"factors": factor_ids, "rows": rows, "total": total}


# -- keeping runs ------------------------------------------------------------------------------


def _set_status(con, run_id: str, status: str, by: str, note: str = "") -> None:
    row = con.execute("select status, data from application_runs where id = ?", (run_id,)).fetchone()
    data = json.loads(row["data"])
    data.setdefault("history", []).append({"at": time.time(), "by": by, "status": status, "note": note})
    con.execute("update application_runs set status = ?, data = ? where id = ?", (status, db.dumps(data), run_id))
    audit.append(con, by, "run.status", run_id, {"from": row["status"], "to": status, "note": note})


async def apply_view(
    view: Dict[str, Any], by: str, decision_id: str, idem_key: str, today: Optional[str] = None
) -> Dict[str, Any]:
    """An approved view → a run kept with its snapshot and every family's result. Idempotent by
    ``idem_key``: the same approval applied twice is one run."""
    if view["status"] != "APPROVED":
        raise RunError(f"Chỉ áp dụng nhận định đã duyệt ({view['id']} đang {view['status']})")
    existing = None
    with db.tx() as con:
        old = con.execute("select id from application_runs where idem_key = ?", (idem_key,)).fetchone()
        if old is not None:
            existing = old["id"]
        else:
            run_id = _insert_run(con, view, by, decision_id, idem_key)
    if existing:  # read it after the write lock is released
        return get(existing)
    return await _compute_run(run_id, view, by, today)


def _insert_run(con, view: Dict[str, Any], by: str, decision_id: str, idem_key: str) -> str:
    n = con.execute("select count(*) from application_runs where view_id = ?", (view["id"],)).fetchone()[0] + 1
    run_id = f"AR-{view['id'][3:]}-{n}"
    data = {
        "view_id": view["id"],
        "event_id": view["event_id"],
        "decision_id": decision_id,
        "by": by,
        "history": [{"at": time.time(), "by": by, "status": "COMPUTING", "note": ""}],
    }
    con.execute(
        "insert into application_runs values (?, ?, ?, ?, ?, ?, ?)",
        (run_id, view["id"], view["event_id"], "COMPUTING", idem_key, time.time(), db.dumps(data)),
    )
    audit.append(con, by, "run.create", run_id, {"view_id": view["id"], "decision_id": decision_id})
    return run_id


async def _compute_run(run_id: str, view: Dict[str, Any], by: str, today: Optional[str]) -> Dict[str, Any]:
    try:
        families = await family_holdings()
        snap = make_snapshot(view, families)
        results = await asyncio.to_thread(compute, snap)
    except Exception as exc:  # noqa: BLE001 — a failed computation is a FAILED run the CIO sees
        with db.tx() as con:
            _set_status(con, run_id, "FAILED", "system", f"{type(exc).__name__}: {exc}")
        return get(run_id)
    pc = postcheck(results, snap, today)
    model = FactorModel.from_dict(snap["factor_model"])
    with db.tx() as con:
        kept = {
            **snap,
            "families": crypto.seal_json(snap["families"], crypto.where("run_snapshots", snap["id"], "families")),
        }
        con.execute("insert or ignore into run_snapshots values (?, ?, ?)", (snap["id"], time.time(), db.dumps(kept)))
        for fid, r in results.items():
            fi = f"FI-{run_id[3:]}-{fid}"
            sealed = crypto.seal(db.dumps(r), crypto.where("family_impacts", fi, "data"))
            con.execute("insert into family_impacts values (?, ?, ?, ?)", (fi, run_id, fid, sealed))
        row = con.execute("select data from application_runs where id = ?", (run_id,)).fetchone()
        data = json.loads(row["data"])
        data.update(
            snapshot_id=snap["id"],
            snapshot_hash=snap["hash"],
            price_date=snap["market"]["as_of"],
            model={"version": model.version, "hash": model.hash, "assumed": model.status == "assumed"},
            engine_version=ENGINE_VERSION,
            view_content_hash=snap["view_content_hash"],
            families=len(results),
            ranking=crypto.seal_json(ranking(results), crypto.where("application_runs", run_id, "ranking")),
            exposure=crypto.seal_json(
                exposure(results, model.ids), crypto.where("application_runs", run_id, "exposure")
            ),
            postcheck=pc,
            totals={
                "expected_3m": sum(r["horizons"]["3m"]["expected"] for r in results.values()),
                "pre_review": sum(1 for r in results.values() if r["pre_review"]),
                "goals_changed": sum(1 for r in results.values() for g in r["goal_impact"]["goals"] if g["changed"]),
            },
        )
        con.execute("update application_runs set data = ? where id = ?", (db.dumps(data), run_id))
        audit.append(con, "system", "run.computed", run_id, {"snapshot": snap["hash"], "families": len(results)})
        _set_status(con, run_id, "POST_CHECKING", "system", pc["summary"])
        final = "NEEDS_CIO_REVIEW" if pc["counts"]["critical"] else "EFFECTIVE"
        _set_status(con, run_id, final, "system", pc["summary"])
        if final == "EFFECTIVE":
            _supersede(con, view["event_id"], run_id, by)
    return get(run_id)


def _supersede(con, event_id: str, new_run: str, by: str) -> None:
    for r in con.execute(
        "select id from application_runs where event_id = ? and status = 'EFFECTIVE' and id != ?", (event_id, new_run)
    ).fetchall():
        _set_status(con, r["id"], "SUPERSEDED", by, f"Thay bởi {new_run}")


def decide_run(run_id: str, action: str, by: str, reason: str) -> Dict[str, Any]:
    """The CIO on a run held by post-check: make it effective (with why) or withdraw it."""
    run = get(run_id)
    if action == "make_effective":
        if run["status"] != "NEEDS_CIO_REVIEW":
            raise RunError(f"{run_id} đang {run['status']}, không chờ CIO xem lại")
        with db.tx() as con:
            _set_status(con, run_id, "EFFECTIVE", by, reason)
            _supersede(con, run["event_id"], run_id, by)
    elif action == "withdraw":
        if run["status"] not in ("EFFECTIVE", "NEEDS_CIO_REVIEW"):
            raise RunError(f"{run_id} đang {run['status']}, không thu hồi được")
        with db.tx() as con:
            _set_status(con, run_id, "WITHDRAWN", by, reason)
    else:
        raise RunError("action là make_effective hoặc withdraw")
    return get(run_id)


def withdraw_view(view_id: str, by: str, reason: str) -> List[str]:
    """BR-14: the view withdrawn → its runs withdrawn; RMs see “Đã thu hồi”."""
    out = []
    with db.tx() as con:
        for r in con.execute(
            "select id from application_runs where view_id = ? and status in "
            "('EFFECTIVE', 'NEEDS_CIO_REVIEW', 'SUPERSEDED')",
            (view_id,),
        ).fetchall():
            _set_status(con, r["id"], "WITHDRAWN", by, reason)
            out.append(r["id"])
    return out


def _same(kept: Any, again: Any) -> bool:
    """Equal on everything ``kept`` holds: a run stored before a field was added (BR-08's goal impact, F10)
    verifies on what it has; a field it has that differs, or is gone, is a difference."""
    if isinstance(kept, dict):
        return isinstance(again, dict) and all(k in again and _same(v, again[k]) for k, v in kept.items())
    if isinstance(kept, list):
        return isinstance(again, list) and len(kept) == len(again) and all(_same(a, b) for a, b in zip(kept, again))
    return kept == again


def verify(run_id: str) -> Dict[str, Any]:
    """FR-405 / NFR-04: recompute every family from the run's snapshot and compare to the dong."""
    run = get(run_id)
    snap = snapshot(run["snapshot_id"])
    if _hash({k: v for k, v in snap.items() if k not in ("id", "hash")}) != snap["hash"]:
        return {"ok": False, "run_id": run_id, "differences": ["snapshot đã bị sửa"]}
    again = compute(snap)
    diffs = []
    for fid, r in family_results(run_id).items():
        new = again.get(fid)
        for h in ("1w", "3m", "12m"):
            for x in ("expected", "p5", "p10", "p50", "p90", "by_class", "by_factor", "by_holding"):
                if new is None or new["horizons"][h][x] != r["horizons"][h][x]:
                    diffs.append(f"{fid} {h} {x}")
        if "goal_impact" in r and (new is None or not _same(r["goal_impact"], new["goal_impact"])):
            diffs.append(f"{fid} goal_impact")
    return {
        "ok": not diffs,
        "run_id": run_id,
        "families": len(again),
        "differences": diffs,
        "snapshot_hash": snap["hash"],
    }


# -- reads -------------------------------------------------------------------------------------


def _opened(r: Dict[str, Any]) -> Dict[str, Any]:
    """A run with its per-family fields opened (control/crypto.py FIELDS)."""
    for f in ("ranking", "exposure"):
        if f in r:
            r[f] = crypto.open_json(r[f], crypto.where("application_runs", r["id"], f))
    return r


def get(run_id: str) -> Dict[str, Any]:
    with db.tx() as con:
        r = db.load(con.execute("select * from application_runs where id = ?", (run_id,)).fetchone())
    if r is None:
        raise KeyError(f"không có lần áp dụng {run_id}")
    r["status_label"] = STATUS_LABEL.get(r["status"], r["status"])
    return _opened(r)


def runs(view_id: Optional[str] = None, statuses: Optional[tuple] = None) -> List[Dict[str, Any]]:
    sql, args = "select * from application_runs", []
    where = []
    if view_id:
        where.append("view_id = ?")
        args.append(view_id)
    if statuses:
        where.append(f"status in ({','.join('?' * len(statuses))})")
        args += list(statuses)
    if where:
        sql += " where " + " and ".join(where)
    with db.tx() as con:
        rows = con.execute(sql + " order by created desc", args).fetchall()
    out = [_opened(db.load(r)) for r in rows]
    for r in out:
        r["status_label"] = STATUS_LABEL.get(r["status"], r["status"])
    return out


def snapshot(snapshot_id: str) -> Dict[str, Any]:
    with db.tx() as con:
        row = con.execute("select data from run_snapshots where id = ?", (snapshot_id,)).fetchone()
    if row is None:
        raise KeyError(f"không có ảnh chụp {snapshot_id}")
    snap = json.loads(row["data"])
    snap["families"] = crypto.open_json(snap["families"], crypto.where("run_snapshots", snapshot_id, "families"))
    return snap


def snapshot_head(snapshot_id: str) -> Dict[str, Any]:
    """A snapshot without its families' holdings: what one family's page needs (model, branches, prices). NFR-01:
    the whole snapshot is 27 MB at 6,500 families, 0.9 s to decode; SQLite drops the families in 0.2 s."""
    with db.tx() as con:
        row = con.execute(
            "select json_remove(data, '$.families') as data from run_snapshots where id = ?", (snapshot_id,)
        ).fetchone()
    if row is None:
        raise KeyError(f"không có ảnh chụp {snapshot_id}")
    return json.loads(row["data"])


def family_results(run_id: str) -> Dict[str, Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select id, family_id, data from family_impacts where run_id = ?", (run_id,)).fetchall()
    return {
        r["family_id"]: json.loads(crypto.open_(r["data"], crypto.where("family_impacts", r["id"], "data")))
        for r in rows
    }


def family_result(run_id: str, family_id: str) -> Dict[str, Any]:
    """One family's result: its row only (NFR-01: decoding every family's to pick one took 2.4 s at 6,500)."""
    with db.tx() as con:
        row = con.execute(
            "select id, data from family_impacts where run_id = ? and family_id = ?", (run_id, family_id)
        ).fetchone()
    if row is None:
        raise KeyError(f"không có kết quả {family_id} trong {run_id}")
    return json.loads(crypto.open_(row["data"], crypto.where("family_impacts", row["id"], "data")))
