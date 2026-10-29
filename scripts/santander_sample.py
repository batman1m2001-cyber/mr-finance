"""D1 of CLIENT_DATASET_PLAN: draw the sample of Santander clients that becomes the santander_vn book.

Reads Kaggle's `train_ver2.csv` (or the `.zip` as downloaded; ~13.6M rows, 17 monthly snapshots) in two passes,
only the needed columns:

1. the last snapshot (2016-05-28): who is eligible — active, aged 25–80, income known; then a stratified, seeded
   draw of `--n` clients. The book is Private only (the submission: ~6,500 Private clients; Priority is a later
   phase), so every client is drawn from segment TOP, except `--priority-upgrade`, a share drawn from the top
   income decile of PARTICULARES (Priority clients already over the Private line; `book` = "priority_upgrade").
   If TOP runs short, the rest comes from that decile too, marked `book` = "private_from_particulares".
   `--foreign` is the share of foreign or non-resident clients in each group;
2. the 12 last snapshots (2015-06…2016-05) of the drawn clients.

Nested: every eligible client gets one seeded random key and each cell takes its clients in key order, so the
1,000 are the first 1,000 of the 6,500 (same seed, same file). Writes `out/santander/sample_<n>.csv.gz` (row-level Santander data: under out/, never committed — D0) and
prints the mix it reached. Same file, same arguments → the same sample.

    .venv/bin/python scripts/santander_sample.py ~/Downloads/train_ver2.csv.zip [--n 1000] [--n 6500]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "santander"
LAST = "2016-05-28"
FIRST_KEPT = "2015-06-28"  # the 12 last snapshots
CHUNK = 1_000_000

PRODUCTS = [
    "ind_ahor_fin_ult1", "ind_aval_fin_ult1", "ind_cco_fin_ult1", "ind_cder_fin_ult1", "ind_cno_fin_ult1",
    "ind_ctju_fin_ult1", "ind_ctma_fin_ult1", "ind_ctop_fin_ult1", "ind_ctpp_fin_ult1", "ind_deco_fin_ult1",
    "ind_deme_fin_ult1", "ind_dela_fin_ult1", "ind_ecue_fin_ult1", "ind_fond_fin_ult1", "ind_hip_fin_ult1",
    "ind_plan_fin_ult1", "ind_pres_fin_ult1", "ind_reca_fin_ult1", "ind_tjcr_fin_ult1", "ind_valo_fin_ult1",
    "ind_viv_fin_ult1", "ind_nomina_ult1", "ind_nom_pens_ult1", "ind_recibo_ult1",
]  # fmt: skip
PROFILE = [
    "fecha_dato", "ncodpers", "sexo", "age", "fecha_alta", "antiguedad", "pais_residencia", "indresi", "indext",
    "nomprov", "ind_actividad_cliente", "renta", "segmento",
]  # fmt: skip
TOP, PART = "01 - TOP", "02 - PARTICULARES"
UPGRADE_PCT = 0.9  # PARTICULARES at or over this income percentile may stand in for Private


def _chunks(path: Path):
    return pd.read_csv(path, usecols=PROFILE + PRODUCTS, dtype=str, chunksize=CHUNK, low_memory=False)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ncodpers"] = pd.to_numeric(df["ncodpers"], errors="coerce").astype("Int64")
    df["age"] = pd.to_numeric(df["age"].str.strip(), errors="coerce")
    df["antiguedad"] = pd.to_numeric(df["antiguedad"].str.strip(), errors="coerce")
    df["renta"] = pd.to_numeric(df["renta"].str.strip(), errors="coerce")
    df["ind_actividad_cliente"] = pd.to_numeric(df["ind_actividad_cliente"], errors="coerce")
    for c in ("segmento", "indresi", "indext", "pais_residencia", "sexo", "nomprov"):
        df[c] = df[c].str.strip()
    for c in PRODUCTS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int8")
    return df


def eligible(path: Path, min_income_pct: float) -> pd.DataFrame:
    """Pass 1: the clients of the last snapshot the book may draw from: TOP, and the top income decile of
    PARTICULARES."""
    last = pd.concat(_clean(c[c["fecha_dato"] == LAST]) for c in _chunks(path))
    ok = last[(last["ind_actividad_cliente"] == 1) & last["age"].between(25, 80) & last["renta"].notna()]
    top = ok[ok["segmento"] == TOP]
    top = top[top["renta"] >= top["renta"].quantile(min_income_pct)]
    part = ok[ok["segmento"] == PART]
    part = part[part["renta"] >= part["renta"].quantile(UPGRADE_PCT)]
    pool = pd.concat([top, part]).drop_duplicates("ncodpers").copy()
    pool["foreign"] = (pool["indext"] == "S") | (pool["indresi"] == "N") | (pool["pais_residencia"] != "ES")
    return pool.sort_values("ncodpers").reset_index(drop=True)


def _pick(cell: pd.DataFrame, want: int) -> pd.DataFrame:
    """The first `want` clients of the cell in key order: a smaller draw is a prefix of a larger one."""
    return cell.sort_values("key").head(max(want, 0))


def draw(pool: pd.DataFrame, n: int, upgrade: float, foreign: float, seed: int) -> pd.DataFrame:
    """A stratified draw: book group × foreign cells sized to the target mix, each a seeded random pick."""
    pool = pool.assign(key=np.random.default_rng(seed).random(len(pool)))
    top, part = pool[pool["segmento"] == TOP], pool[pool["segmento"] == PART]
    n_up = round(n * upgrade)
    picked = []
    for is_f in (True, False):
        share = foreign if is_f else 1 - foreign
        want_priv, want_up = round((n - n_up) * share), round(n_up * share)
        if not is_f:  # the rounding remainder goes to the larger cells
            want_priv = (n - n_up) - round((n - n_up) * foreign)
            want_up = n_up - round(n_up * foreign)
        priv = _pick(top[top["foreign"] == is_f], want_priv).assign(book="private")
        part_f = part[part["foreign"] == is_f]
        short = want_priv - len(priv)
        if short:
            print(f"  TOP foreign={is_f}: {len(priv)} of {want_priv}; {short} from PARTICULARES", file=sys.stderr)
        fill = _pick(part_f, short).assign(book="private_from_particulares")
        up = _pick(part_f.drop(fill.index), want_up).assign(book="priority_upgrade")
        picked += [priv, fill, up]
    sample = pd.concat(picked).drop(columns="key").sort_values("ncodpers")
    if len(sample) < n:
        print(f"  only {len(sample)} clients drawn, wanted {n}", file=sys.stderr)
    return sample


def history(path: Path, ids: set[int]) -> pd.DataFrame:
    """Pass 2: the 12 last snapshots of the drawn clients."""
    parts = []
    for c in _chunks(path):
        c = c[c["fecha_dato"] >= FIRST_KEPT]
        if len(c):
            c = _clean(c)
            parts.append(c[c["ncodpers"].isin(ids)])
    return pd.concat(parts).sort_values(["ncodpers", "fecha_dato"])


def mix(sample: pd.DataFrame) -> dict:
    return {
        "clients": len(sample),
        "book": {k: int(v) for k, v in sample["book"].value_counts().sort_index().items()},
        "foreign_share": round(float(sample["foreign"].mean()), 3),
        "age_median": float(sample["age"].median()),
        "renta_median_eur": round(float(sample["renta"].median())),
        "provinces": int(sample["nomprov"].nunique()),
        "products_held_mean": round(float(sample[PRODUCTS].sum(axis=1).mean()), 2),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("raw", type=Path, help="train_ver2.csv or train_ver2.csv.zip from Kaggle")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--priority-upgrade", type=float, default=0.0, help="share of Priority clients over the line")
    ap.add_argument("--foreign", type=float, default=0.07, help="share of foreign / non-resident (→ Việt kiều)")
    ap.add_argument("--min-income-pct", type=float, default=0.0, help="income floor within TOP, a percentile")
    ap.add_argument("--seed", type=int, default=20261023)
    a = ap.parse_args(argv)

    print(f"pass 1: eligible clients in {LAST} …")
    pool = eligible(a.raw, a.min_income_pct)
    print(f"  {len(pool)} eligible")
    sample = draw(pool, a.n, a.priority_upgrade, a.foreign, a.seed)
    print(f"pass 2: 12 snapshots of {len(sample)} clients …")
    rows = history(a.raw, set(sample["ncodpers"].astype(int)))
    rows = rows.merge(sample[["ncodpers", "foreign", "book"]], on="ncodpers")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"sample_{a.n}.csv.gz"
    rows.to_csv(out, index=False, compression={"method": "gzip", "mtime": 0})
    summary = {"file": str(out.relative_to(ROOT)), "rows": len(rows), **mix(sample), **vars(a) | {"raw": a.raw.name}}
    (OUT / f"sample_{a.n}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
