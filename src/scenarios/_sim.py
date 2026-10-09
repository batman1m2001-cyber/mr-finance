"""The simulations: life events the client tries, and market stress tests the system runs.

Each takes the client's picture (``Pic``: holdings, profile, market) and its parameters, and
answers with the same shape::

    {"summary": [{"label", "value", "tone"}], "before": {...}, "after": {...},
     "options": [{"id": "light" | "heavy", "title", "actions": [...], "effect": [...]}]}

The arithmetic is deliberately plain (yearly steps, a deposit rate for "safe", no taxes beyond the
ones the scenario is about), so an RM can redo every number by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, List, Optional

from wealth.money import TR, TY, pct, vnd

SAFE = 0.05  # a 12-month deposit
GROWTH = 0.07  # a balanced portfolio, long run
INFLATION = 0.04


@dataclass
class Pic:
    holdings: List[Dict[str, Any]]
    profile: Dict[str, Any]
    market: Dict[str, Any]

    def assets(self, *classes: str) -> List[Dict[str, Any]]:
        return [h for h in self.holdings if h["kind"] == "asset" and (not classes or h["class"] in classes)]

    def value(self, *classes: str) -> float:
        return sum(h["value"] for h in self.assets(*classes))

    @property
    def debt(self) -> float:
        return sum(h["value"] for h in self.holdings if h["kind"] == "liability")

    @property
    def net_worth(self) -> float:
        return self.value() - self.debt

    @property
    def liquid(self) -> float:
        return sum(
            h["value"]
            for h in self.assets()
            if h["class"] in ("cash", "deposit") or (h["class"] == "fund" and h["liquid"])
        )

    @property
    def spending(self) -> float:
        return self.profile.get("spending_monthly") or 1

    @property
    def surplus(self) -> float:
        return (self.profile.get("income_monthly") or 0) - self.spending

    @property
    def payments(self) -> float:
        return sum(h["detail"].get("monthly_payment") or 0 for h in self.holdings if h["kind"] == "liability")

    @property
    def today(self) -> date:
        return date.fromisoformat(self.market["as_of"])

    def months_until(self, year: int, month: int = 1) -> int:
        return max(1, (year - self.today.year) * 12 + month - self.today.month)

    def state(self) -> Dict[str, float]:
        return {"net_worth": self.net_worth, "liquid": self.liquid, "liquid_months": self.liquid / self.spending}


def line(label: str, value: str, tone: str = "neutral") -> Dict[str, str]:
    return {"label": label, "value": value, "tone": tone}


def pmt(principal: float, rate: float, years: int) -> float:
    """A loan's monthly instalment."""
    r, n = rate / 12, years * 12
    return principal * r / (1 - (1 + r) ** -n) if r else principal / n


def saving_for(target: float, months: int, rate: float = SAFE) -> float:
    """What to put aside each month to have ``target`` in ``months`` (a deposit's interest)."""
    r = rate / 12
    return target * r / ((1 + r) ** months - 1) if r else target / months


# ── life events ──────────────────────────────────────────────────────────


def _abroad_event(p: Pic) -> Optional[Dict[str, Any]]:
    return next(
        (e for e in p.profile.get("events", []) if e.get("category") == "school" and e["amount"] >= 500 * TR), None
    )


def tuition(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    ev = _abroad_event(p)
    per_year = float(prm.get("per_year") or (ev["amount"] if ev else 600 * TR))
    years = int(prm.get("years") or 4)
    start = int(prm.get("start_year") or (int(ev["date"][:4]) if ev else p.today.year + 2))
    fx = float(prm.get("fx_rise") if prm.get("fx_rise") is not None else 0.05)
    month = int(ev["date"][5:7]) if ev and not prm.get("start_year") else 9
    total, with_fx = per_year * years, per_year * years * (1 + fx)
    # paid a year at a time: the reserve beyond six months of spending covers what it can, the
    # rest is saved each month until the last year falls due
    reserve = max(0.0, p.liquid - 6 * p.spending)
    gap = max(0.0, with_fx - reserve)
    months = p.months_until(start, month) + (years - 1) * 12
    monthly = saving_for(gap, months) if gap else 0.0
    fits = monthly <= max(0.0, p.surplus)
    return {
        "params": {"per_year": per_year, "years": years, "start_year": start, "fx_rise": fx},
        "summary": [
            line(f"Tổng chi phí ({years} năm)", vnd(total)),
            line(f"Nếu tỷ giá tăng {pct(fx, digits=0)}", vnd(with_fx), "bad"),
            line(
                "Dùng được từ dự phòng (ngoài 6 tháng chi tiêu)",
                vnd(min(reserve, with_fx)),
                "good" if reserve else "neutral",
            ),
            line(
                f"Phần còn lại cần để dành mỗi tháng (đến năm học cuối, {months} tháng)",
                vnd(monthly),
                "neutral" if fits else "bad",
            ),
            line(
                "So với tiền dư mỗi tháng",
                f"{vnd(p.surplus)}" + (" — đủ" if fits else " — chưa đủ"),
                "good" if fits else "bad",
            ),
        ],
        "before": p.state(),
        "after": {**p.state(), "liquid": p.liquid - min(p.liquid, with_fx * 0.25)},
        "options": [
            {
                "id": "light",
                "title": "Tích lũy đều",
                "actions": [
                    f"Giữ riêng {vnd(min(reserve, with_fx))} từ dự phòng cho học phí",
                    f"Gửi tiết kiệm định kỳ {vnd(monthly)}/tháng, kỳ hạn khớp từng năm học",
                    "Mua ngoại tệ dần mỗi quý để trung bình giá",
                ],
                "effect": [f"Đủ {vnd(with_fx)} vào {start}", "Không đụng đến danh mục đầu tư"],
            },
            {
                "id": "heavy",
                "title": "Khóa trước phần lớn",
                "actions": [
                    f"Chuyển ngay {vnd(with_fx * 0.5)} sang ngoại tệ / tiền gửi ngoại tệ",
                    "Phần còn lại: quỹ trái phiếu đến năm nhập học",
                ],
                "effect": ["Hết rủi ro tỷ giá cho một nửa khoản chi", f"Thanh khoản giảm {vnd(with_fx * 0.5)}"],
            },
        ],
    }


def retire_early(p: Pic, prm: Dict[str, Any], withdraw: float = 0.0) -> Dict[str, Any]:
    age = p.profile.get("age") or 45
    at = int(prm.get("retire_age") or 55)
    spend = float(prm.get("spending_after") or p.spending * 0.8) * 12
    investable = p.value("cash", "deposit", "fund", "bond", "stock", "gold", "crypto") - p.debt - withdraw
    rent = sum((h["detail"].get("rental_monthly") or 0) * 12 for h in p.assets("real_estate"))
    years = max(0, at - age)
    pot = investable
    for _ in range(years):
        pot = pot * (1 + GROWTH) + max(0.0, p.surplus) * 12
    passive = pot * 0.04 + rent
    lasts, y, money = at, at, pot
    while y < 100 and money > 0:
        money = money * (1 + GROWTH - INFLATION) + rent - spend
        y += 1
    lasts = y
    ok = passive >= spend
    return {
        "params": {"retire_age": at, "spending_after": spend / 12},
        "summary": [
            line(f"Tài sản đầu tư lúc {at} tuổi", vnd(pot)),
            line("Thu nhập thụ động mỗi năm (rút 4% + tiền thuê)", vnd(passive), "good" if ok else "bad"),
            line("Chi tiêu dự kiến mỗi năm", vnd(spend)),
            line(
                "Tiền đủ dùng tới",
                "trên 100 tuổi" if lasts >= 100 else f"{lasts} tuổi",
                "good" if lasts >= 90 else "bad",
            ),
        ],
        "before": p.state(),
        "after": p.state(),
        "lasts": lasts,
        "options": [
            {
                "id": "light",
                "title": "Giữ mục tiêu, tăng tích lũy",
                "actions": [
                    f"Tăng tiết kiệm thêm {vnd(max(0.0, spend - passive) / 12 / max(1, years))}/tháng",
                    "Làm thêm 2 năm nếu cần",
                ],
                "effect": ["Thu nhập thụ động đủ chi tiêu lúc nghỉ"],
            },
            {
                "id": "heavy",
                "title": "Chuyển sang tài sản tạo dòng tiền",
                "actions": [
                    "Chuyển 30% cổ phiếu sang trái phiếu và quỹ thu nhập",
                    "Cho thuê hoặc bán BĐS không tạo thu nhập",
                ],
                "effect": ["Dòng tiền ổn định hơn, tăng trưởng thấp hơn"],
            },
        ],
    }


def sell_home(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    homes = sorted(p.assets("real_estate"), key=lambda h: -h["value"])
    lived = next((h for h in homes if h["detail"].get("use") == "Ở"), homes[0] if homes else None)
    pick = next((h for h in homes if h is not lived and (not prm.get("key") or h["key"] == prm["key"])), None)
    if not pick:
        return {
            "params": {},
            "summary": [line("Không có BĐS thứ hai để bán", "—")],
            "before": p.state(),
            "after": p.state(),
            "options": [],
        }
    tax, fees = pick["value"] * 0.02, pick["value"] * 0.01
    cash = pick["value"] - tax - fees
    rent = (pick["detail"].get("rental_monthly") or 0) * 12
    area = p.market["areas"].get(pick["detail"].get("area") or "", {})
    keep_yield = rent / pick["value"] + (area.get("yoy") or 0.05)
    loans = [
        h
        for h in p.holdings
        if h["kind"] == "liability" and h["detail"].get("collateral") == pick["key"].split(":")[-1]
    ]
    owed = sum(h["value"] for h in loans)
    after = {**p.state(), "liquid": p.liquid + cash - owed, "net_worth": p.net_worth - tax - fees}
    after["liquid_months"] = after["liquid"] / p.spending
    return {
        "params": {"key": pick["key"], "name": pick["name"]},
        "summary": [
            line("Giá trị hiện tại", vnd(pick["value"])),
            line("Thuế 2% + phí 1%", vnd(tax + fees), "bad"),
            line("Tiền thu về", vnd(cash)),
            line("Giữ lại: lợi suất thuê + tăng giá", pct(keep_yield)),
            line(
                "Bán rồi gửi kỳ hạn / trái phiếu ngân hàng",
                f"{pct(SAFE)} – {pct(0.065)}",
                "good" if keep_yield < 0.065 else "neutral",
            ),
            line("Thời gian bán ước tính", f"{area.get('months_to_sell', 12)} tháng"),
        ],
        "before": p.state(),
        "after": after,
        "options": [
            {
                "id": "light",
                "title": "Bán, giữ an toàn",
                "actions": [f"Gửi {vnd(cash * 0.5)} kỳ hạn 12 tháng", f"{vnd(cash * 0.5)} vào trái phiếu ngân hàng"]
                + ([f"Trả hết khoản vay thế chấp {vnd(owed)}"] if owed else []),
                "effect": [f"Thu nhập cố định khoảng {vnd(cash * 0.057)}/năm", "Giảm tập trung BĐS"],
            },
            {
                "id": "heavy",
                "title": "Bán, tái cân bằng",
                "actions": ["Trả hết các khoản vay lãi thả nổi", "Phần còn lại vào quỹ cân bằng theo hồ sơ rủi ro"],
                "effect": ["Hết áp lực lãi suất", "Danh mục theo đúng hồ sơ rủi ro"],
            },
        ],
    }


def leverage_buy(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    price = float(prm.get("price") or 5 * TY)
    ratio = float(prm.get("loan_ratio") or 0.7)
    years = int(prm.get("years") or 20)
    rate = float(prm.get("rate") or p.market["rates"]["mortgage_floating"])
    rent = float(prm.get("rent_monthly") if prm.get("rent_monthly") is not None else price * 0.035 / 12)
    loan, down = price * ratio, price * (1 - ratio)
    pay, shock = pmt(loan, rate, years), pmt(loan, rate + 0.02, years)
    income = p.profile.get("income_monthly") or 1
    dsr, dsr_shock = (p.payments + pay) / income, (p.payments + shock - rent * 0.7) / income
    after = {**p.state(), "liquid": p.liquid - down}
    after["liquid_months"] = after["liquid"] / p.spending
    return {
        "params": {"price": price, "loan_ratio": ratio, "years": years, "rate": rate, "rent_monthly": rent},
        "summary": [
            line("Vốn tự có cần", vnd(down), "bad" if down > p.liquid else "neutral"),
            line("Trả góp mỗi tháng", vnd(pay)),
            line("Nếu lãi suất +2%", vnd(shock), "bad"),
            line("Tỷ lệ trả nợ / thu nhập", pct(dsr), "bad" if dsr > 0.4 else "neutral"),
            line("Lãi +2% và tiền thuê chỉ đạt 70%", pct(dsr_shock), "bad" if dsr_shock > 0.5 else "neutral"),
        ],
        "before": p.state(),
        "after": after,
        "options": [
            {
                "id": "light",
                "title": "Vay ít, cố định lãi",
                "actions": ["Vay 50% thay vì 70%", "Chọn gói lãi cố định 3 năm đầu"],
                "effect": [f"Trả góp {vnd(pmt(price * 0.5, rate, years))}/tháng"],
            },
            {
                "id": "heavy",
                "title": "Vay 70%, giữ dự phòng",
                "actions": [
                    f"Giữ riêng {vnd(shock * 12)} — 12 tháng trả góp ở kịch bản lãi +2%",
                    "Mua bảo hiểm khoản vay",
                ],
                "effect": ["Chịu được 12 tháng không có tiền thuê"],
            },
        ],
    }


def pass_on(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    share = float(prm.get("share") or 0.5)
    re = p.value("real_estate") * share
    secs = p.value("stock", "fund", "bond") * share
    biz = p.value("business") * share
    tax = (secs + biz) * 0.10  # gifted securities and shares: 10% (real estate between parents and children: exempt)
    notary = (re + secs + biz) * 0.001
    return {
        "params": {"share": share},
        "summary": [
            line("Bất động sản chuyển cho con", vnd(re) + " — miễn thuế TNCN giữa cha mẹ và con", "good"),
            line("Chứng khoán, cổ phần chuyển cho con", vnd(secs + biz)),
            line("Thuế 10% trên chứng khoán, cổ phần", vnd(tax), "bad"),
            line("Công chứng, phí", vnd(notary)),
            line("Lưu ý", "Tham khảo; cần tư vấn pháp lý trước khi thực hiện"),
        ],
        "before": p.state(),
        "after": {**p.state(), "net_worth": p.net_worth - tax - notary},
        "options": [
            {
                "id": "light",
                "title": "Chuyển BĐS trước",
                "actions": ["Tặng cho BĐS cho con (miễn thuế)", "Giữ chứng khoán, cổ phần đến khi có kế hoạch rõ"],
                "effect": [f"Tiết kiệm {vnd(tax)} thuế trước mắt"],
            },
            {
                "id": "heavy",
                "title": "Lập kế hoạch chuyển giao trọn gói",
                "actions": [
                    "Lập di chúc và thỏa thuận chia tài sản",
                    "Cân nhắc công ty nắm giữ cho phần cổ phần doanh nghiệp",
                ],
                "effect": ["Chuyển giao có trật tự, tránh tranh chấp"],
            },
        ],
    }


def business_cash(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    need = float(prm.get("need") or 5 * TY)
    ladder = [  # cheapest and fastest first
        ("Cầm cố tiền gửi (không mất lãi)", p.value("deposit") * 0.9, "lãi tiền gửi + 1%", "1 ngày"),
        ("Tiền thanh toán", p.value("cash"), "0", "ngay"),
        (
            "Bán quỹ trái phiếu / tiền tệ",
            sum(h["value"] for h in p.assets("fund") if h["liquid"]),
            "phí bán ~0,1%",
            "2 ngày",
        ),
        ("Vay cầm cố cổ phiếu", p.value("stock") * 0.5, "~12%/năm", "1 ngày"),
        ("Bán trái phiếu", p.value("bond") * 0.95, "chiết khấu ~5%", "1 – 2 tuần"),
        ("Vay thế chấp BĐS", p.value("real_estate") * 0.6, "~10%/năm", "2 – 4 tuần"),
    ]
    plan, left = [], need
    for name, avail, cost, when in ladder:
        if left <= 0 or avail <= 0:
            continue
        take = min(avail, left)
        plan.append({"source": name, "amount": take, "cost": cost, "time": when})
        left -= take
    return {
        "params": {"need": need},
        "summary": [
            line("Cần huy động", vnd(need)),
            *[
                line(f"{i + 1}. {x['source']}", f"{vnd(x['amount'])} · {x['cost']} · {x['time']}")
                for i, x in enumerate(plan)
            ],
            line("Còn thiếu", vnd(max(0.0, left)), "bad" if left > 0 else "good"),
        ],
        "before": p.state(),
        "after": {**p.state(), "liquid": max(0.0, p.liquid - need)},
        "options": [
            {
                "id": "light",
                "title": "Cầm cố, không bán",
                "actions": ["Cầm cố tiền gửi và cổ phiếu theo thứ tự trên", "Hoàn trả khi doanh nghiệp thu tiền về"],
                "effect": ["Giữ nguyên danh mục, chi phí lãi ngắn hạn"],
            },
            {
                "id": "heavy",
                "title": "Bán để không mang nợ",
                "actions": ["Bán cổ phiếu đang có lãi trước", "Bán trái phiếu doanh nghiệp còn lại"],
                "effect": ["Không phát sinh nợ", "Chốt lãi, có thể phát sinh thuế 0,1%"],
            },
        ],
    }


def medical(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    cost = float(prm.get("cost") or 1 * TY)
    insured = any(h["class"] == "insurance" and "sức khỏe" in h["name"].lower() for h in p.assets("insurance"))
    cover = float(prm.get("cover") if prm.get("cover") is not None else (0.6 if insured else 0.0))
    pocket = cost * (1 - cover)
    after = {**p.state(), "liquid": p.liquid - pocket}
    after["liquid_months"] = after["liquid"] / p.spending
    return {
        "params": {"cost": cost, "cover": cover},
        "summary": [
            line("Chi phí điều trị", vnd(cost)),
            line("Bảo hiểm chi trả", f"{pct(cover, digits=0)} · {vnd(cost * cover)}", "good" if cover else "bad"),
            line("Tự chi trả", vnd(pocket)),
            line(
                "Thanh khoản dự phòng sau đó",
                f"{after['liquid_months']:.0f} tháng chi tiêu".replace(".", ","),
                "bad" if after["liquid_months"] < 6 else "good",
            ),
        ],
        "before": p.state(),
        "after": after,
        "options": [
            {
                "id": "light",
                "title": "Dùng quỹ dự phòng",
                "actions": ["Chi từ tiền gửi không kỳ hạn", "Bổ sung lại quỹ trong 12 tháng"],
                "effect": ["Không bán tài sản đầu tư"],
            },
            {
                "id": "heavy",
                "title": "Nâng cấp bảo hiểm",
                "actions": ["Mua thêm bảo hiểm sức khỏe cao cấp cho cả gia đình", "Giữ riêng 12 tháng chi tiêu"],
                "effect": ["Giảm rủi ro chi phí y tế về sau"],
            },
        ],
    }


def emigrate(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    usd = float(prm.get("usd") or 200_000)
    rate = p.market["fx"]["USDVND"]["rate"]
    vnd_now, vnd_up = usd * rate, usd * rate * 1.05
    return {
        "params": {"usd": usd},
        "summary": [
            line("Số ngoại tệ cần", f"{usd:,.0f} USD".replace(",", ".")),
            line("Theo tỷ giá hôm nay", vnd(vnd_now)),
            line("Nếu tỷ giá +5%", vnd(vnd_up), "bad"),
            line(
                "Chiếm thanh khoản hiện có",
                pct(vnd_now / p.liquid if p.liquid else 1),
                "bad" if vnd_now > p.liquid * 0.5 else "neutral",
            ),
            line("Quy định", "Chuyển tiền du học / định cư theo hồ sơ chứng minh mục đích; kiểm tra hạn mức hiện hành"),
        ],
        "before": p.state(),
        "after": {**p.state(), "liquid": p.liquid - vnd_now},
        "options": [
            {
                "id": "light",
                "title": "Mua ngoại tệ dần",
                "actions": ["Mua mỗi tháng một phần trong 12 tháng", "Mở tài khoản ngoại tệ"],
                "effect": ["Trung bình giá, giảm rủi ro tỷ giá"],
            },
            {
                "id": "heavy",
                "title": "Khóa tỷ giá ngay",
                "actions": ["Mua kỳ hạn (forward) toàn bộ số cần", "Chuẩn bị hồ sơ chuyển tiền sớm"],
                "effect": [f"Chắc chắn chi phí {vnd(vnd_now)}"],
            },
        ],
    }


def wedding(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    amount = float(prm.get("amount") or 3 * TY)
    base = retire_early(p, {"retire_age": prm.get("retire_age") or 60})
    after = retire_early(p, {"retire_age": prm.get("retire_age") or 60}, withdraw=amount)
    drop = base["lasts"] - after["lasts"]
    return {
        "params": {"amount": amount},
        "summary": [
            line("Khoản rút ra", vnd(amount)),
            line("Tiền đủ dùng tới (trước)", "trên 100 tuổi" if base["lasts"] >= 100 else f"{base['lasts']} tuổi"),
            line(
                "Tiền đủ dùng tới (sau)",
                "trên 100 tuổi" if after["lasts"] >= 100 else f"{after['lasts']} tuổi",
                "bad" if drop > 0 else "good",
            ),
            line(
                "Ảnh hưởng mục tiêu nghỉ hưu",
                f"sớm hết tiền {drop} năm" if drop > 0 else "không đáng kể",
                "bad" if drop > 0 else "good",
            ),
        ],
        "before": p.state(),
        "after": {**p.state(), "liquid": p.liquid - amount, "net_worth": p.net_worth - amount},
        "options": [
            {
                "id": "light",
                "title": "Hỗ trợ một phần",
                "actions": [f"Hỗ trợ {vnd(amount * 0.5)}, phần còn lại con vay ưu đãi"],
                "effect": ["Giữ mục tiêu nghỉ hưu gần như nguyên vẹn"],
            },
            {
                "id": "heavy",
                "title": "Hỗ trợ toàn bộ",
                "actions": [f"Rút {vnd(amount)} từ tiền gửi và quỹ", "Tăng tích lũy sau đó để bù"],
                "effect": [f"Mục tiêu nghỉ hưu lùi khoảng {max(drop, 1)} năm"],
            },
        ],
    }


# ── market stress tests ─────────────────────────────────────────────────


def _stress(
    p: Pic,
    shock: Callable[[Dict[str, Any]], float],
    illiquid: Callable[[Dict[str, Any]], bool],
    extra_cost: float,
    limit: float,
) -> Dict[str, Any]:
    rows = []
    for h in p.assets():
        s = shock(h)
        if s:
            rows.append({"name": h["name"], "loss": h["value"] * s})
    loss = sum(r["loss"] for r in rows) - extra_cost
    nw = p.net_worth
    stuck = sum(h["value"] for h in p.assets() if illiquid(h))
    after = {"net_worth": nw + loss, "liquid": p.liquid, "liquid_months": p.liquid / p.spending}
    share = -loss / nw if nw else 0
    rows.sort(key=lambda r: r["loss"])
    return {
        "summary": [
            line("Tài sản ròng sau cú sốc", vnd(nw + loss)),
            line("Thay đổi", f"{vnd(loss, signed=True)} · {pct(-share, signed=True)}", "bad" if loss < 0 else "good"),
            line(
                "So với ngưỡng chấp nhận",
                f"{pct(limit, digits=0)} — " + ("vượt ngưỡng" if share > limit else "trong ngưỡng"),
                "bad" if share > limit else "good",
            ),
            line("Tài sản không bán được trong giai đoạn này", vnd(stuck), "bad" if stuck else "neutral"),
            *[line(f"Ảnh hưởng nhiều: {r['name']}", vnd(r["loss"], signed=True)) for r in rows[:3]],
        ],
        "before": p.state(),
        "after": after,
        "loss_share": share,
        "options": [
            {
                "id": "light",
                "title": "Giảm điểm nóng",
                "actions": [
                    f"Giảm 20% vị thế {rows[0]['name']}" if rows else "Giữ nguyên",
                    "Tăng tiền gửi lên 12 tháng chi tiêu",
                ],
                "effect": [f"Mức giảm còn khoảng {pct(share * 0.8)}"],
            },
            {
                "id": "heavy",
                "title": "Tái cân bằng theo hồ sơ rủi ro",
                "actions": [
                    "Đưa tỷ trọng cổ phiếu, trái phiếu DN về khung của hồ sơ",
                    "Thêm trái phiếu chính phủ / ngân hàng",
                ],
                "effect": [f"Mức giảm về dưới ngưỡng {pct(limit, digits=0)}"],
            },
        ],
    }


def bond_crisis(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    def shock(h):
        d = h["detail"]
        if h["class"] == "bond" and d.get("bond_kind") == "corporate":
            return -0.35
        if h["class"] == "stock":
            return -0.40 if d.get("sector") == "Bất động sản" else -0.25 * (d.get("beta") or 1)
        if h["class"] == "fund":
            return -0.10 if d.get("fund_type") == "bond" else -0.25 if d.get("fund_type") == "equity" else 0
        return -0.05 if h["class"] == "real_estate" else 0

    return {
        "params": {},
        **_stress(
            p,
            shock,
            lambda h: h["class"] == "bond" and h["detail"].get("bond_kind") == "corporate",
            0,
            p.profile["drawdown_limit"],
        ),
    }


def re_freeze(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    def shock(h):
        if h["class"] == "real_estate":
            return -0.15
        if h["class"] == "stock" and h["detail"].get("sector") in ("Bất động sản", "Ngân hàng"):
            return -0.30
        return 0

    return {"params": {}, **_stress(p, shock, lambda h: h["class"] == "real_estate", 0, p.profile["drawdown_limit"])}


def vni_30(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    def shock(h):
        if h["class"] == "stock":
            return -0.30 * (h["detail"].get("beta") or 1)
        if h["class"] == "fund" and h["detail"].get("fund_type") == "equity":
            return -0.28
        return -0.5 if h["class"] == "crypto" else 0

    return {"params": {}, **_stress(p, shock, lambda h: False, 0, p.profile["drawdown_limit"])}


def rates_up(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    floating = sum(
        h["value"] for h in p.holdings if h["kind"] == "liability" and h["detail"].get("rate_type") == "floating"
    )

    def shock(h):
        if h["class"] == "bond":
            return -(h["detail"].get("duration") or 1) * 0.02
        if h["class"] == "stock":
            return -0.10
        return -0.05 if h["class"] == "real_estate" else 0

    out = _stress(p, shock, lambda h: False, floating * 0.02, p.profile["drawdown_limit"])
    out["summary"].insert(
        3, line("Lãi vay thả nổi tăng thêm mỗi năm", vnd(floating * 0.02), "bad" if floating else "neutral")
    )
    return {"params": {}, **out}


def usd_up(p: Pic, prm: Dict[str, Any]) -> Dict[str, Any]:
    abroad = sum(
        e["amount"]
        for e in p.profile.get("events", [])
        if e.get("direction") == "out"
        and ("du học" in e["label"].lower() or "(mỹ)" in e["label"].lower() or "(úc)" in e["label"].lower())
    )

    def shock(h):
        return 0.05 * 0.3 if h["class"] == "gold" else 0  # gold follows the dollar, in part

    out = _stress(p, shock, lambda h: False, abroad * 0.05, p.profile["drawdown_limit"])
    out["summary"].insert(
        3, line("Khoản chi bằng ngoại tệ tăng thêm", vnd(abroad * 0.05), "bad" if abroad else "neutral")
    )
    return {"params": {}, **out}


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "tuition": {
        "kind": "life",
        "title": "Học phí cho con (trong nước / du học)",
        "question": "Cần bao nhiêu, mỗi tháng để dành bao nhiêu, tỷ giá tăng 5% thì sao?",
        "personas": ["Chuyên gia", "F1"],
        "run": tuition,
    },
    "retire_early": {
        "kind": "life",
        "title": "Nghỉ hưu sớm năm 55 tuổi",
        "question": "Dòng tiền thụ động có đủ chi không, tiền đủ dùng tới năm bao nhiêu tuổi?",
        "personas": ["Chuyên gia", "Nghỉ hưu"],
        "run": retire_early,
    },
    "sell_home": {
        "kind": "life",
        "title": "Bán căn nhà thứ hai",
        "question": "Thuế, phí, tiền thu về đầu tư vào đâu, so với giữ lại cho thuê?",
        "personas": ["F1", "Nghỉ hưu"],
        "run": sell_home,
    },
    "leverage_buy": {
        "kind": "life",
        "title": "Mua thêm BĐS bằng vốn vay",
        "question": "Áp lực trả nợ nếu lãi suất +2%, nếu tiền thuê không như kỳ vọng?",
        "personas": ["F1", "Mới chạm ngưỡng"],
        "run": leverage_buy,
    },
    "pass_on": {
        "kind": "life",
        "title": "Chuyển giao tài sản cho con",
        "question": "Chia thế nào, thuế, phí, cổ phần doanh nghiệp xử lý ra sao?",
        "personas": ["F1"],
        "run": pass_on,
    },
    "business_cash": {
        "kind": "life",
        "title": "Doanh nghiệp cần vốn gấp",
        "question": "Cầm cố tài sản nào trước, bán gì ít thiệt hại nhất?",
        "personas": ["F1"],
        "run": business_cash,
    },
    "medical": {
        "kind": "life",
        "title": "Chi phí y tế lớn",
        "question": "Thanh khoản dự phòng đủ không, bảo hiểm chi trả bao nhiêu?",
        "personas": ["Nghỉ hưu", "Chuyên gia"],
        "run": medical,
    },
    "emigrate": {
        "kind": "life",
        "title": "Định cư / con đi du học",
        "question": "Cần chuẩn bị bao nhiêu ngoại tệ, quy định chuyển tiền?",
        "personas": ["Chuyên gia", "F1"],
        "run": emigrate,
    },
    "wedding": {
        "kind": "life",
        "title": "Cưới hỏi / hỗ trợ con mua nhà",
        "question": "Rút một khoản lớn thì mục tiêu nghỉ hưu bị ảnh hưởng ra sao?",
        "personas": ["Nghỉ hưu", "F1"],
        "run": wedding,
    },
    "bond_crisis": {
        "kind": "stress",
        "title": "Chạy lại khủng hoảng trái phiếu DN 2022",
        "question": "Danh mục hiện tại sẽ ra sao?",
        "personas": [],
        "run": bond_crisis,
    },
    "re_freeze": {
        "kind": "stress",
        "title": "BĐS đóng băng như 2022–2023",
        "question": "Mất thanh khoản 18 tháng thì sao?",
        "personas": [],
        "run": re_freeze,
    },
    "vni_30": {
        "kind": "stress",
        "title": "VN-Index giảm 30%",
        "question": "Danh mục giảm bao nhiêu, có vượt ngưỡng không?",
        "personas": [],
        "run": vni_30,
    },
    "rates_up": {
        "kind": "stress",
        "title": "Lãi suất tăng 2%",
        "question": "Khoản vay, trái phiếu, cổ phiếu chịu ảnh hưởng thế nào?",
        "personas": [],
        "run": rates_up,
    },
    "usd_up": {
        "kind": "stress",
        "title": "USD/VND tăng 5%",
        "question": "Các khoản chi ngoại tệ tăng bao nhiêu?",
        "personas": [],
        "run": usd_up,
    },
}
