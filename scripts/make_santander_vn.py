"""D3 of CLIENT_DATASET_PLAN: the santander_vn book — Santander's clients, matched SCF households, Techcombank's totals.

Reads the D1 sample (`out/santander/sample_6500.csv.gz`), the SCF 2022 summary extract (`SCFP2022.csv`) and the two
calibration tables (`data/calibration/tcb.json`, `vn.json`), and writes one client file per client in the
fixtures' schema (scripts/make_fixtures.py) under `data/datasets/santander_vn/clients/`, plus `book.json` (what the
book came out as) and `subset_1000.json` (the ids of the first 1,000 of the draw).

1. AUM at TCB: Santander's income rank (with noise) on a Pareto curve with floor 25 tỷ, scaled to sum to 428,000 tỷ;
2. total wealth = AUM ÷ the share held at TCB, a curve falling with wealth whose book aggregate is 35 %;
3. each client matched to the nearest SCF household ≥ US$1M on wealth rank, age and four yes/no products;
4. the household's shares, made Vietnamese (no retirement accounts, more property, gold);
5. the AUM spread over the TCB products the client holds; the rest of the wealth held elsewhere;
6. quantised into shares, bonds, fund units, m², lượng.

Deterministic: same inputs, same files.

    .venv/bin/python scripts/make_santander_vn.py out/santander/sample_6500.csv.gz ~/Downloads/scf2022/SCFP2022.csv
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import sys
from datetime import date
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from make_fixtures import AS_OF, MARKET, MONTHS, TR, TY, monthly_out, noise, salary_rows  # noqa: E402

CAL = ROOT / "data" / "calibration"
OUT = ROOT / "data" / "datasets" / "santander_vn"
NOTE = (
    "Dữ liệu mô phỏng: hành vi từ dữ liệu ẩn danh Santander (Kaggle 2016); cơ cấu tài sản từ hộ thật trong SCF 2022 "
    "(Fed); quy mô theo AUM Private 428.000 tỷ / 6.500 khách; hiệu chỉnh Việt Nam là giả định."
)
# Santander's products, by what they become in the app. The interest-paying accounts (savings, particular, más
# particular, e-account) are read as term deposits: only the plain current account is CASA
PRODUCT = {
    "ind_ahor_fin_ult1": "savings", "ind_cco_fin_ult1": "casa", "ind_ctma_fin_ult1": "savings",
    "ind_ctop_fin_ult1": "savings", "ind_ctpp_fin_ult1": "savings", "ind_ecue_fin_ult1": "savings",
    "ind_viv_fin_ult1": "casa", "ind_cno_fin_ult1": "payroll",
    "ind_nomina_ult1": "payroll", "ind_nom_pens_ult1": "pension", "ind_deco_fin_ult1": "td", "ind_deme_fin_ult1": "td",
    "ind_dela_fin_ult1": "td", "ind_fond_fin_ult1": "funds", "ind_valo_fin_ult1": "securities",
    "ind_cder_fin_ult1": "margin", "ind_plan_fin_ult1": "insurance", "ind_hip_fin_ult1": "mortgage",
    "ind_pres_fin_ult1": "loan", "ind_tjcr_fin_ult1": "card", "ind_reca_fin_ult1": "tax",
    "ind_recibo_ult1": "direct_debit", "ind_ctju_fin_ult1": "junior", "ind_aval_fin_ult1": "guarantee",
}  # fmt: skip
CLASSES = ["deposits", "bonds", "funds", "stocks", "insurance", "home", "other_re", "business", "gold"]
AS_OF_D = date.fromisoformat(AS_OF)


def _val(table: dict, key: str):
    return table[key]["value"]


def _add_months(d: date, k: int) -> date:
    m = d.month - 1 + k
    return date(d.year + m // 12, m % 12 + 1, min(d.day, 28))


# ---- 1–2. AUM, share at TCB, total wealth -------------------------------------------------------------------------


def aum(renta: np.ndarray, tcb: dict, rng: np.random.Generator) -> np.ndarray:
    """AUM at TCB in tỷ: the income rank, with noise, on a Pareto curve; the part above the floor scaled to the total."""
    n, floor, total = len(renta), _val(tcb, "aum_floor_ty"), _val(tcb, "aum_total_ty")
    rho = _val(tcb, "aum_rank_correlation")
    nd = NormalDist()
    z_income = np.array([nd.inv_cdf((r - 0.5) / n) for r in pd.Series(renta).rank(method="first")])
    z = rho * z_income + math.sqrt(1 - rho * rho) * rng.standard_normal(n)
    u = (pd.Series(z).rank(method="first").to_numpy() - 0.5) / n
    mean = total / n
    alpha = mean / (mean - floor)
    a = floor * (1 - u) ** (-1 / alpha)
    return floor + (a - floor) * (total - floor * n) / (a - floor).sum()


def share_curve(a: np.ndarray, s0: float, s750: float, floor: float) -> np.ndarray:
    t = np.clip(1 - np.log(a / floor) / math.log(750 / floor), 0, 1)
    return s750 + (s0 - s750) * t


def share_at_tcb(a: np.ndarray, tcb: dict) -> tuple[np.ndarray, float]:
    """The share held at TCB per client, its floor value solved so the book's aggregate is the target."""
    target, s750, floor = _val(tcb, "share_at_tcb")["mean"], _val(tcb, "share_at_tcb")["at_750"], _val(tcb, "aum_floor_ty")
    lo, hi = s750, 0.99
    for _ in range(60):
        s0 = (lo + hi) / 2
        agg = a.sum() / (a / share_curve(a, s0, s750, floor)).sum()
        lo, hi = (s0, hi) if agg < target else (lo, s0)
    return share_curve(a, s0, s750, floor), s0


# ---- 3. the SCF match ---------------------------------------------------------------------------------------------


def scf_rich(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The SCF households with net worth ≥ US$1M: one row each (implicate means), and their implicate rows."""
    d = pd.read_csv(path)
    d.columns = d.columns.str.upper()
    hh = d.groupby("YY1").agg(NETWORTH=("NETWORTH", "mean"), AGE=("AGE", "mean"), WGT=("WGT", "mean"),
                              STOCKS=("STOCKS", "mean"), NMMF=("NMMF", "mean"), MRTHEL=("MRTHEL", "mean"),
                              RETQLIQ=("RETQLIQ", "mean"))  # fmt: skip
    hh = hh[hh["NETWORTH"] >= 1e6].sort_values("NETWORTH")
    hh["pct"] = (hh["WGT"].cumsum() - hh["WGT"] / 2) / hh["WGT"].sum()
    return hh.reset_index(), d[d["YY1"].isin(hh.index)]


def match(clients: pd.DataFrame, wealth: np.ndarray, hh: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """For each client, the index (in hh) of the nearest household: wealth rank, age, four yes/no products."""
    pc = (pd.Series(wealth).rank(method="first").to_numpy() - 0.5) / len(wealth)
    cf = np.stack([clients[c].to_numpy() > 0 for c in
                   ("ind_valo_fin_ult1", "ind_fond_fin_ult1", "ind_hip_fin_ult1", "ind_plan_fin_ult1")], axis=1)  # fmt: skip
    hf = np.stack([hh[c].to_numpy() > 0 for c in ("STOCKS", "NMMF", "MRTHEL", "RETQLIQ")], axis=1)
    out = np.empty(len(clients), dtype=int)
    for s in range(0, len(clients), 500):
        e = slice(s, s + 500)
        dist = (np.abs(pc[e, None] - hh["pct"].to_numpy()[None, :]) / 0.05
                + np.abs(clients["age"].to_numpy()[e, None] - hh["AGE"].to_numpy()[None, :]) / 7
                + (cf[e, None, :] != hf[None, :, :]).sum(axis=2)
                + rng.uniform(0, 0.3, size=(len(pc[e]), len(hh))))  # fmt: skip
        out[e] = dist.argmin(axis=1)
    return out


# ---- 4. a household's shares, made Vietnamese ---------------------------------------------------------------------


def shares(row: pd.Series, vn: dict, r: random.Random) -> tuple[dict, float]:
    """The class shares of total wealth, and the property-debt ratio."""
    groups = _val(vn, "scf_classes")
    amt = {k: float(sum(max(row[v], 0) for v in cols)) for k, cols in groups.items() if k != "dropped"}
    for k, w in _val(vn, "retirement_to").items():
        amt[k] += amt["retirement"] * w
    amt.pop("retirement")
    j = _val(vn, "jitter")
    mult = _val(vn, "multipliers")
    amt = {k: v * r.uniform(1 - j, 1 + j) * mult.get(k, 1.0) for k, v in amt.items()}
    tot = sum(amt.values()) or 1.0
    sh = {k: v / tot for k, v in amt.items()} if sum(amt.values()) else {"deposits": 1.0}
    g = r.uniform(*_val(vn, "gold_share"))
    sh = {k: sh.get(k, 0.0) * (1 - g) for k in CLASSES if k != "gold"} | {"gold": g}
    debt = (max(row["MRTHEL"], 0) + max(row["RESDBT"], 0)) / max(row["ASSET"], 1.0)
    return sh, min(debt, 0.5)


# ---- 5–6. one client file -----------------------------------------------------------------------------------------


def _weighted(r: random.Random, pairs):
    names, weights = zip(*pairs)
    return r.choices(names, weights=weights)[0]


def _name(r: random.Random, male: bool, vn: dict) -> str:
    n = _val(vn, "names")
    middle, given = (n["middle_male"], n["given_male"]) if male else (n["middle_female"], n["given_female"])
    return f"{_weighted(r, n['surnames'])} {r.choice(middle)} {r.choice(given)}"


def _tier(a_ty: float, tcb: dict) -> str:
    return next(t["label"] for t in _val(tcb, "tiers") if t["to"] is None or a_ty < t["to"])


def _date_between(r: random.Random, start: str, end: str) -> str:
    a, b = date.fromisoformat(start).toordinal(), date.fromisoformat(end).toordinal()
    return date.fromordinal(r.randint(a, b)).isoformat()


def _stocks(r: random.Random, value: float, k: int) -> list:
    tickers = r.sample(sorted(MARKET["stocks"]), k=min(k, len(MARKET["stocks"])))
    weights = [r.random() + 0.2 for _ in tickers]
    out = []
    for t, w in zip(tickers, weights):
        price = MARKET["stocks"][t]["price"]
        qty = int(value * w / sum(weights) / price // 100 * 100)
        if qty:
            out.append({"ticker": t, "qty": qty, "avg_price": int(round(price * r.uniform(0.7, 1.15), -2)),
                        "bought": _date_between(r, "2019-01-02", "2026-09-30")})  # fmt: skip
    return out


def _stocks_value(rows: list) -> float:
    return sum(s["qty"] * MARKET["stocks"][s["ticker"]]["price"] for s in rows)


def build(i: int, c: pd.Series, a: float, w: float, sh: dict, debt: float, ctx: dict, r: random.Random) -> dict:
    """One client in the fixtures' schema. a, w: AUM at TCB and total wealth, in đồng."""
    vn, tcb = ctx["vn"], ctx["tcb"]
    cid = f"S{i + 1:04d}"
    held = {PRODUCT[p] for p in PRODUCT if c[p] > 0}
    age, male = int(c["age"]), c["sexo"] == "V"
    city = ctx["city"][i]

    # 5. the AUM over the TCB products the client holds (deposits always: every client has a CASA)
    tcb_classes = ["deposits"] + (["stocks"] if "securities" in held else []) + (["funds"] if "funds" in held else [])
    if "securities" in held and (sh["bonds"] > 0 or age >= 55):
        tcb_classes.append("bonds")
    wts = {k: max(sh[k], 0.03) for k in tcb_classes}
    tcb_amt = {k: a * v / sum(wts.values()) for k, v in wts.items()}
    need = {k: max(0.0, w * sh[k] - tcb_amt.get(k, 0.0)) for k in CLASSES}
    ext = {k: (w - a) * v / (sum(need.values()) or 1.0) for k, v in need.items()}

    # TCBS, Techcom Capital
    stocks = _stocks(r, tcb_amt.get("stocks", 0), r.randint(2, 6))
    bonds = []
    if tcb_amt.get("bonds"):
        codes = ["TD2535", "TCB12401"] if age >= 55 else ["TCB12401", "HBE12403", "SMR12501", "TD2535"]
        for code in r.sample(codes, k=min(2, len(codes))):
            m = MARKET["bonds"][code]
            qty = int(tcb_amt["bonds"] / 2 / m["price"] // 10 * 10)
            if qty:
                bonds.append({"code": code, "qty": qty, "avg_price": m["par"], "bought": _date_between(r, "2024-01-02", "2026-09-30")})
    funds = []
    if tcb_amt.get("funds"):
        equity_tilt = sh["stocks"] / max(sh["stocks"] + sh["bonds"] + sh["deposits"], 1e-9)
        picks = (["TCEF", "TCBF"] if equity_tilt > 0.3 else ["TCBF", "TCMF"])[: r.randint(1, 2)]
        for code in picks:
            nav = MARKET["funds"][code]["nav"]
            units = int(tcb_amt["funds"] / len(picks) / nav)
            funds.append({"code": code, "units": units, "avg_nav": int(round(nav * r.uniform(0.85, 1.05), -1)),
                          "bought": _date_between(r, "2021-01-04", "2026-09-30")})  # fmt: skip
    securities = (_stocks_value(stocks) + sum(b["qty"] * MARKET["bonds"][b["code"]]["price"] for b in bonds)
                  + sum(f["units"] * MARKET["funds"][f["code"]]["nav"] for f in funds))  # fmt: skip

    # Techcombank: term deposits, then CASA takes the rest so the AUM is exact
    deposits = a - securities
    accounts, n_acc = [], 1
    if held & {"td", "savings"}:
        td_total = deposits * (1 - r.uniform(*_val(vn, "casa_in_deposits_with_td")))
        k = r.randint(1, 3)
        for j in range(k):
            tenor, _, rate = _weighted(r, [((t, wt, rt), wt) for t, wt, rt in _val(vn, "td_tenors")])
            opened = _add_months(AS_OF_D, -r.randint(0, tenor - 1)).replace(day=r.randint(1, 28))
            bal = round(td_total / k, -6)
            accounts.append({"id": f"{cid}-TD-{j + 1:02d}", "type": "TD", "name": f"Tiền gửi {tenor} tháng", "balance": int(bal),
                             "rate": rate, "opened": opened.isoformat(), "maturity": _add_months(opened, tenor).isoformat()})  # fmt: skip
            n_acc += 1
    casa = a - securities - sum(x["balance"] for x in accounts)
    accounts.insert(0, {"id": f"{cid}-CASA-01", "type": "CASA", "name": "Tài khoản thanh toán", "balance": int(round(casa))})

    tier = _tier(a / TY, tcb)
    cards = []
    if "card" in held:
        limit = {"Mới lên Private": 500, "HNW": 1_000, "HNW cao": 2_000}.get(tier, 5_000) * TR
        cards.append({"id": f"{cid}-CARD-01", "name": "Visa Infinite", "limit": limit, "outstanding": int(round(limit * r.uniform(0.03, 0.2), -5))})

    # property: a home, then investment properties; in TP.HCM / Đồng Nai valued by an area, elsewhere at the client's word
    props, declared, loans = [], [], []
    home_v = min(ext["home"], 150 * TY)
    other_v = ext["other_re"] + ext["home"] - home_v
    plan = [("home", home_v)] if home_v >= 1 * TY else []
    n_inv = 0 if other_v < 2 * TY else min(5, max(1, int(other_v // (60 * TY)) + 1))
    plan += [("invest", other_v / n_inv)] * n_inv if n_inv else []
    mortgage_tcb = "mortgage" in held
    for j, (use, v) in enumerate(plan):
        pid = f"{cid}-RE-{j + 1:02d}"
        area = None
        if city == "TP.HCM":
            area = (r.choice(["quan_3", "thao_dien", "phu_my_hung"]) if use == "home"
                    else r.choice(["vinhomes_grand_park", "phu_my_hung", "long_thanh"]))  # fmt: skip
        elif city == "Đồng Nai":
            area = "long_thanh"
        rental = int(round(v * 0.04 / 12, -6)) if use == "invest" and area != "long_thanh" and r.random() < 0.6 else 0
        kind = "Đất nền" if area == "long_thanh" else ("Biệt thự" if v > 40 * TY else "Căn hộ")
        name = f"{kind} {'đang ở' if use == 'home' else ('cho thuê' if rental else 'đầu tư')}"
        row = {"id": pid, "name": name, "purchase_year": r.randint(2008, 2024), "purchase_price": int(round(v * r.uniform(0.4, 0.85), -8)),
               "rental_monthly": rental}  # fmt: skip
        if area:
            row |= {"area": area, "sqm": max(30, int(v / MARKET["areas"][area]["price_sqm"]))}
        if use == "home" and mortgage_tcb and area:
            props.append(row | {"type": kind, "use": "Ở"})
        else:
            declared.append({"class": "real_estate", "location": city} | row | ({} if area else {"value": int(round(v, -8))}))
    debt_v = debt * w
    if debt_v >= 500 * TR or mortgage_tcb:
        principal = int(round(max(debt_v, 0.2 * home_v, 1 * TY), -8))
        n, rate = r.randint(60, 240), 0.092
        pay = int(round(principal * rate / 12 / (1 - (1 + rate / 12) ** -n), -5))
        if mortgage_tcb:
            coll = (props or declared or [{}])[0].get("id")
            loans.append({"id": f"{cid}-LN-HOME", "name": "Vay mua nhà", "outstanding": principal, "rate": rate, "rate_type": "floating",
                          "monthly_payment": pay, "end": _add_months(AS_OF_D, n).isoformat(), "collateral": coll})  # fmt: skip
        else:
            declared.append({"id": f"{cid}-D-LOAN", "class": "loan", "name": f"Vay mua nhà tại {r.choice(_val(vn, 'other_banks')['banks'])}",
                             "value": principal, "rate": rate, "rate_type": "floating", "monthly_payment": pay})  # fmt: skip
    if "loan" in held:
        p = int(round(a * r.uniform(0.01, 0.05), -8))
        loans.append({"id": f"{cid}-LN-PER", "name": "Vay tiêu dùng", "outstanding": p, "rate": 0.11, "rate_type": "fixed",
                      "monthly_payment": int(round(p / 36, -5)), "end": _add_months(AS_OF_D, 36).isoformat()})  # fmt: skip

    # elsewhere: other banks, other brokers, gold, business, insurance, bonds and funds
    names = _val(vn, "other_banks")
    open_api = []
    if ext["deposits"] >= 100 * TR:
        bank = r.choice(names["banks"])
        open_api.append({"institution": bank, "consent": True, "accounts": [
            {"id": f"{cid}-{bank[:3].upper()}-01", "type": r.choice(["CASA", "TD"]), "name": f"Tiền gửi {bank}", "balance": int(round(ext["deposits"], -6))}]})
    if ext["stocks"] >= 100 * TR:
        broker = r.choice(names["brokers"])
        rows = _stocks(r, ext["stocks"] * 0.95, r.randint(2, 5))
        open_api.append({"institution": broker, "consent": True, "stocks": rows, "accounts": [
            {"id": f"{cid}-{broker[:3].upper()}-CASH", "type": "SECURITIES_CASH", "name": f"Tiền tại {broker}",
             "balance": int(round(ext["stocks"] - _stocks_value(rows), -6))}]})  # fmt: skip
    if ext["gold"] >= 50 * TR:
        declared.append({"id": f"{cid}-D-GOLD", "class": "gold", "name": "Vàng miếng SJC", "qty": round(ext["gold"] / MARKET["gold"]["price_per_luong"])})
    if ext["business"] >= 500 * TR:
        sector = r.choice(_val(vn, "business_sectors"))
        declared.append({"id": f"{cid}-D-BIZ", "class": "business", "name": f"{r.choice([10, 20, 30, 51, 70, 100])}% cổ phần công ty {sector.lower()}",
                         "value": int(round(ext["business"], -8)), "sector": sector})  # fmt: skip
    if ext["insurance"] >= 100 * TR or "insurance" in held:
        v = max(ext["insurance"], 300 * TR)
        declared.append({"id": f"{cid}-D-INS", "class": "insurance", "name": "Bảo hiểm nhân thọ", "value": int(round(v, -6)),
                         "premium_annual": int(round(v * r.uniform(0.03, 0.08), -6)), "premium_month": r.randint(1, 12)})  # fmt: skip
    for k, label in (("bonds", "Trái phiếu"), ("funds", "Chứng chỉ quỹ")):
        if ext[k] >= 100 * TR:
            declared.append({"id": f"{cid}-D-{k.upper()}", "class": k[:-1], "name": f"{label} tại {r.choice(names['brokers'])}", "value": int(round(ext[k], -6))})
    for j, d in enumerate(declared):
        d.setdefault("id", f"{cid}-D-{j + 1:02d}")

    # who the client is
    occ = _val(vn, "occupations")
    kind = ("retired" if age >= 65 or ("pension" in held and age >= 60) else
            "owner" if sh["business"] > 0.2 else "investor" if sh["stocks"] + sh["funds"] > 0.4 else r.choice(["executive", "professional"]))  # fmt: skip
    income = max(100 * TR, w * _val(vn, "income_yield") * math.sqrt(c["renta"] / ctx["renta_median"]) / 12)
    income = int(round(income, -6))
    spending = int(round(income * r.uniform(*_val(vn, "spending_of_income")), -6))
    equity = sh["stocks"] + 0.5 * sh["funds"]
    financial = sh["deposits"] + sh["bonds"] + sh["funds"] + sh["stocks"]
    dependents = []
    if "junior" in held or (35 <= age <= 62 and r.random() < 0.7):
        for k in range(r.randint(1, 3)):
            dependents.append({"name": f"{_name(r, r.random() < 0.5, vn).split()[0]} {r.choice(['Minh', 'Gia', 'Bảo', 'Ngọc'])} {r.choice(['An', 'Khôi', 'Linh', 'Vy', 'Nam', 'Châu'])}",
                               "relation": "Con", "birth_year": 2026 - r.randint(max(1, age - 45), max(2, age - 25))})  # fmt: skip

    # cash flows: income, card, loans, rent, living
    label = {"retired": "LUONG HUU", "owner": "CHIA LOI NHUAN CONG TY"}.get(kind, "LUONG")
    tx = (salary_rows(r, MONTHS, label, income * 0.8, day=r.randint(1, 10))
          + noise(r, MONTHS, 2, 2 * TR, 30 * TR))  # fmt: skip
    if cards:
        tx += monthly_out(r, MONTHS, "THANH TOAN DU NO THE TIN DUNG", spending * 0.3, "card", day=25, jitter=0.2)
    for ln in loans:
        tx += monthly_out(r, MONTHS, f"TRA NO {ln['name'].upper()}", ln["monthly_payment"], "loan", day=20)
    for d in declared + props:
        if d.get("rental_monthly"):
            tx += [{"date": f"{m}-05", "amount": d["rental_monthly"], "direction": "in", "desc": f"TIEN THUE {d['id']}", "category": "rent"} for m in MONTHS]
    tx.sort(key=lambda x: x["date"])

    events = [{"date": "2027-03-31", "direction": "out", "amount": int(round(income * 12 * 0.05, -6)), "label": "Quyết toán thuế TNCN 2026", "category": "tax"}]
    ev = _val(vn, "events")
    for key, label_, cat, ok in (("school_abroad", "Học phí du học của con", "school", bool(dependents)),
                                 ("business_capital", "Góp vốn bổ sung cho doanh nghiệp", "business", sh["business"] > 0.05),
                                 ("property_deposit", "Đặt cọc mua bất động sản", "property", True),
                                 ("health", "Chi phí phẫu thuật (dự kiến)", "health", age >= 60)):  # fmt: skip
        p, (lo, hi) = ev[key]
        if ok and r.random() < p:
            events.append({"date": _date_between(r, "2026-11-01", "2028-03-31"), "direction": "out",
                           "amount": int(round(w * r.uniform(lo, hi), -7)), "label": label_, "category": cat})  # fmt: skip

    # the April 2026 dip: what Santander shows the client did between the months shifted to March and May 2026
    tl = ctx["timeline"].get(c["ncodpers"], [])
    moved = [e for e in tl if e["month"] in ("2026-04", "2026-05") and ({"securities", "funds"} & set(e["opened"] + e["closed"]))]
    action = ("sell" if any(set(e["closed"]) & {"securities", "funds"} for e in moved) else
              "buy" if any(set(e["opened"]) & {"securities", "funds"} for e in moved) else "hold")  # fmt: skip
    note = {"sell": "Đóng một phần chứng khoán/quỹ khi VN-Index giảm 6%", "buy": "Mở thêm chứng khoán/quỹ khi VN-Index giảm 6%",
            "hold": "Giữ nguyên danh mục khi VN-Index giảm 6%"}[action]  # fmt: skip

    return {
        "id": cid, "name": _name(r, male, vn), "age": age, "occupation": r.choice(occ[kind]), "segment": "Private",
        "tier": tier, "persona_hint": tier, "city": city,
        "nationality": ("Việt kiều" if r.random() < 0.6 else "Nước ngoài") if c["foreign"] else "Việt Nam",
        "client_since": f"{int(str(c['fecha_alta'])[:4]) + 10}{str(c['fecha_alta'])[4:10]}" if isinstance(c["fecha_alta"], str) else None,
        "income_monthly": income, "spending_monthly": spending,
        "benchmark": "VNINDEX" if financial and equity / financial >= 0.2 else "TD12M",
        "drawdown_limit": round(min(0.30, max(0.08, (0.25 if age < 45 else 0.18 if age <= 60 else 0.10) + equity * 0.2)), 2),
        "household": [], "dependents": dependents,
        "sources": {
            "techcombank": {"accounts": accounts, "cards": cards, "loans": loans, "transactions": tx},
            "tcbs": {"stocks": stocks, "bonds": bonds, "realized_ytd": int(round(_stocks_value(stocks) * r.uniform(-0.05, 0.1), -6))}
            | ({"margin": {"id": f"{cid}-MRG", "name": "Vay ký quỹ TCBS", "outstanding": int(round(_stocks_value(stocks) * r.uniform(0.1, 0.3), -6)), "rate": 0.12}}
               if "margin" in held and stocks else {}),
            "techcom_capital": {"funds": funds},
            "onehousing": {"properties": props},
            "open_api": open_api,
        },
        "declared": declared,
        "events": events,
        "behaviour": [{"date": "2026-04-15", "market_move": -0.06, "action": action, "note": note}],
        "samples": [],
        "timeline": tl,
        "provenance": {"scf_household": int(ctx["scf_id"][i]), "aum_tcb": int(round(a)), "wealth_total": int(round(w)), "share_at_tcb": round(a / w, 3)},
        "note": NOTE,
    }  # fmt: skip


# ---- the book -----------------------------------------------------------------------------------------------------


def timeline(rows: pd.DataFrame) -> dict:
    """Per client: the months (shifted +10 years 4 months) where an app product appears or disappears."""
    months = sorted(rows["fecha_dato"].unique())
    shift = dict(zip(months, MONTHS[-len(months):]))
    out = {}
    for cid, g in rows.sort_values("fecha_dato").groupby("ncodpers"):
        prev, events = None, []
        for _, row in g.iterrows():
            now = {PRODUCT[p] for p in PRODUCT if row[p] > 0}
            if prev is not None and now != prev:
                events.append({"month": shift[row["fecha_dato"]], "opened": sorted(now - prev), "closed": sorted(prev - now)})
            prev = now
        out[cid] = events
    return out


def cities(clients: pd.DataFrame, vn: dict, rng: np.random.Generator) -> list:
    """Provinces keep their rank (most frequent first) and are cut to the Vietnamese city shares."""
    freq = clients["nomprov"].fillna("?").value_counts()
    order = clients.assign(r=clients["nomprov"].fillna("?").map({p: k for k, p in enumerate(freq.index)}),
                           k=rng.random(len(clients))).sort_values(["r", "k"]).index  # fmt: skip
    cuts, out, start = _val(vn, "cities"), {}, 0
    for k, (city, share) in enumerate(cuts):
        end = len(order) if k == len(cuts) - 1 else start + round(share * len(order))
        out |= {i: city for i in order[start:end]}
        start = end
    return [out[i] for i in clients.index]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sample", type=Path, help="out/santander/sample_6500.csv.gz (D1)")
    ap.add_argument("scf", type=Path, help="SCFP2022.csv (the SCF 2022 summary extract)")
    ap.add_argument("--subset", type=Path, default=ROOT / "out" / "santander" / "sample_1000.csv.gz")
    ap.add_argument("--seed", type=int, default=20261023)
    a = ap.parse_args(argv)

    tcb, vn = (json.loads((CAL / f).read_text()) for f in ("tcb.json", "vn.json"))
    rows = pd.read_csv(a.sample, dtype={"fecha_alta": str})
    last = rows.sort_values("fecha_dato").groupby("ncodpers").tail(1).sort_values("ncodpers").reset_index(drop=True)
    rng = np.random.default_rng(a.seed)

    a_ty = aum(last["renta"].to_numpy(), tcb, rng)
    s, s0 = share_at_tcb(a_ty, tcb)
    w_ty = a_ty / s
    hh, imp = scf_rich(a.scf)
    m = match(last, w_ty, hh, rng)
    imp_by = {k: g.reset_index(drop=True) for k, g in imp.groupby("YY1")}
    ctx = {"tcb": tcb, "vn": vn, "city": cities(last, vn, rng), "timeline": timeline(rows),
           "renta_median": float(last["renta"].median()), "scf_id": hh["YY1"].to_numpy()[m]}  # fmt: skip

    out = OUT / "clients"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    book = []
    for i, c in last.iterrows():
        r = random.Random(a.seed * 100_003 + i)
        imps = imp_by[ctx["scf_id"][i]]
        sh, debt = shares(imps.iloc[r.randrange(len(imps))], vn, r)
        client = build(i, c, a_ty[i] * TY, w_ty[i] * TY, sh, debt, ctx, r)
        (out / f"{client['id']}.json").write_text(json.dumps(client, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        book.append({"id": client["id"], "ncodpers": int(c["ncodpers"]), "tier": client["tier"], "city": client["city"],
                     "aum": a_ty[i], "wealth": w_ty[i], "foreign": bool(c["foreign"]), "max_share": max(sh.values()),
                     "top_class": max(sh, key=sh.get), "casa": client["sources"]["techcombank"]["accounts"][0]["balance"] / TY})  # fmt: skip

    b = pd.DataFrame(book)
    sub = set(pd.read_csv(a.subset, usecols=["ncodpers"])["ncodpers"]) if a.subset.exists() else set()
    (OUT / "subset_1000.json").write_text(json.dumps(sorted(b[b["ncodpers"].isin(sub)]["id"])) + "\n")
    summary = {
        "note": NOTE,
        "clients": len(b), "aum_total_ty": round(b["aum"].sum()), "aum_min_ty": round(b["aum"].min(), 1),
        "aum_median_ty": round(b["aum"].median(), 1), "aum_max_ty": round(b["aum"].max()),
        "wealth_total_ty": round(b["wealth"].sum()), "share_at_tcb_book": round(b["aum"].sum() / b["wealth"].sum(), 3),
        "share_at_tcb_at_floor": round(s0, 3),
        "tiers": b["tier"].value_counts().to_dict(), "cities": b["city"].value_counts().to_dict(),
        "foreign_share": round(b["foreign"].mean(), 3),
        "scf_households_used": int(pd.Series(ctx["scf_id"]).nunique()),
        "more_than_half_in_one_class": round((b["max_share"] > 0.5).mean(), 3),
        "top_class": b["top_class"].value_counts().to_dict(),
        "casa_over_half_of_aum": int((b["casa"] > b["aum"] / 2).sum()),
        "subset_1000": len(sub & set(b["ncodpers"])),
        "inputs": {"sample": a.sample.name, "scf": a.scf.name, "seed": a.seed},
    }  # fmt: skip
    (OUT / "book.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
