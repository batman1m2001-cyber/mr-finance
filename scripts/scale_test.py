"""BRD-NFR-01 measured: one approved view applied to N synthetic families (BRD: 6,500 within 5 minutes), then a
family's pages read with all of them in the database (BRD: within 2 seconds).

The families are the demo households cloned with their amounts scaled (×0.5–×2, fixed by the clone's number), each
assigned to one of the RMs, in a fresh state file of their own; the live demo is not touched.

    .venv/bin/python scripts/scale_test.py --families 6500 [--state /tmp/scale.db] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / "tests")]
AMOUNTS = ("balance", "value", "amount", "quantity", "units", "principal", "outstanding", "market_value", "cost")


def _scaled(x, k):
    if isinstance(x, dict):
        return {
            key: (v * k if key in AMOUNTS and isinstance(v, (int, float)) else _scaled(v, k)) for key, v in x.items()
        }
    if isinstance(x, list):
        return [_scaled(v, k) for v in x]
    return x


def clone(n: int) -> int:
    """n synthetic households from the demo ones; returns how many exist after."""
    from people import store

    with store._db(write=True) as con:
        heads = con.execute("select id, data, rm_id from people where kind = 'client' and member_of is null").fetchall()
        srcs = {
            h["id"]: con.execute(
                "select source, pos, data from client_sources where client_id = ?", (h["id"],)
            ).fetchall()
            for h in heads
        }
        seq = con.execute("select max(seq) from people").fetchone()[0]
        rms = [r[0] for r in con.execute("select id from people where role = 'rm' order by id")]
        for i in range(n):
            h = heads[i % len(heads)]
            k = 0.5 + 1.5 * ((i * 7919) % 1000) / 1000  # ×0.5–×2, fixed by the clone's number
            cid = f"S{i + 1:05d}"
            rec = json.loads(h["data"])
            rec.update(id=cid, name=f"Gia đình thử {i + 1}")
            seq += 1
            con.execute(
                "insert into people values (?, ?, 'client', 'client', ?, null, null, ?, ?)",
                (cid, seq, rec["name"], rms[i % len(rms)], json.dumps(_scaled(rec, k), ensure_ascii=False)),
            )
            for s in srcs[h["id"]]:
                con.execute(
                    "insert into client_sources values (?, ?, ?, ?)",
                    (cid, s["source"], s["pos"], json.dumps(_scaled(json.loads(s["data"]), k), ensure_ascii=False)),
                )
            con.execute("insert into teams values (?, ?, 'rm', 0, 0)", (cid, rms[i % len(rms)]))
        return con.execute("select count(*) from people where kind = 'client' and member_of is null").fetchone()[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", type=int, default=6500)
    ap.add_argument("--state", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    os.environ["MF_STATE"] = a.state or tempfile.mktemp(prefix="mf-scale-", suffix=".db")
    os.environ.setdefault("MF_AI", "off")
    os.environ["MF_AUTH"] = "off"  # the reads are timed, not the sign-in

    from operonx.app import Application
    from starlette.testclient import TestClient

    from apply import run as runs
    from people import store
    from wealth import fixtures

    fixtures.client_ids()  # seeds the demo
    have = len(fixtures.client_ids())
    t = time.perf_counter()
    total = clone(max(0, a.families - have))
    print(f"families: {total} ({time.perf_counter() - t:.1f} s to create)", flush=True)

    from test_apply import MARKET
    from test_views import agent, decide, event

    ev = event(*MARKET)  # the news, then the event, as the tests make them
    view = agent(ev["id"])["view"]

    prof = None
    if os.environ.get("MF_PROFILE"):
        import cProfile

        prof = cProfile.Profile()
        prof.enable()
    t = time.perf_counter()
    out = decide(view["id"], "approve", reason="Đo NFR-01")
    apply_s = time.perf_counter() - t
    if prof:
        import pstats

        prof.disable()
        pstats.Stats(prof).sort_stats("cumulative").print_stats(28)
    rid = out["decision"]["run"]["id"]
    rows = len(runs.family_results(rid))
    print(f"approve → run {rid}: {rows} families in {apply_s:.1f} s (BRD ≤ 300 s)", flush=True)

    reads = {}
    with TestClient(Application.find(".").asgi()) as c:
        fam = "S03250" if total >= 3250 else store.client_ids()[-1]
        for name, call in (
            ("impact (client)", lambda: c.get(f"/api/families/{fam}/impact?role=client")),
            ("impact (RM)", lambda: c.get(f"/api/families/{fam}/impact")),
            ("cách tính (client)", lambda: c.get(f"/api/families/{fam}/how?run={rid}")),
            ("trace (RM)", lambda: c.get(f"/api/trace/{rid}/{fam}")),
            ("dashboard", lambda: c.post("/api/dashboard", json={"client_id": fam})),
            ("graph", lambda: c.get(f"/api/families/{fam}/graph")),
        ):
            times = []
            for _ in range(3):
                t = time.perf_counter()
                r = call()
                times.append(time.perf_counter() - t)
                assert r.status_code == 200, (name, r.status_code, r.text[:200])
            reads[name] = round(min(times), 3)
            print(f"  {name}: {min(times):.3f} s (best of 3)", flush=True)
    result = {
        "families": total,
        "run_families": rows,
        "apply_seconds": round(apply_s, 1),
        "reads_seconds": reads,
        "state": os.environ["MF_STATE"],
        "at": time.strftime("%Y-%m-%d %H:%M"),
        "cpu": os.cpu_count(),
    }
    if a.json:
        Path(a.json).write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
