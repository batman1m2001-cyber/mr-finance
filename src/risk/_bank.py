"""The risk test: situational questions, each answer choosing the next question.

Tolerance (what the client *wants* to bear) comes from the answers. Capacity (what they *can*
bear) comes from their own data. The profile a client gets is the lower of the two, because a
portfolio must survive the client's life, not just their mood, and the gap between them is said
out loud. Rules, not a model: every point is explainable (docs/PLAN.md D3).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from wealth.money import vnd

# A question: its text (``{portfolio}`` is the client's own invested amount), options with the
# tolerance points they carry, and where each option leads. ``next`` names the next question,
# or a function of the answers so far.
Q = Dict[str, Any]

BANK: Dict[str, Q] = {
    "goal": {
        "text": "Mục tiêu chính của danh mục đầu tư của anh/chị là gì?",
        "options": [
            ("keep", "Giữ nguyên giá trị, không để mất vốn", 0),
            ("income", "Có thu nhập đều đặn (lãi, cổ tức, tiền thuê)", 3),
            ("grow", "Tăng trưởng ổn định trong dài hạn", 6),
            ("fast", "Tăng trưởng nhanh, chấp nhận biến động lớn", 10),
        ],
        "next": "horizon",
    },
    "horizon": {
        "text": "Bao lâu nữa anh/chị cần dùng phần lớn số tiền đang đầu tư?",
        "options": [
            ("lt2", "Dưới 2 năm", 0),
            ("2to5", "2 – 5 năm", 3),
            ("5to10", "5 – 10 năm", 7),
            ("gt10", "Trên 10 năm", 10),
        ],
        "next": "drop20",
    },
    "drop20": {
        "text": "Danh mục {portfolio} của anh/chị giảm còn {portfolio_80} chỉ trong 1 tháng. Anh/chị sẽ:",
        "options": [
            ("sell_all", "Bán hết để không mất thêm", 0),
            ("sell_some", "Bán bớt một phần", 3),
            ("hold", "Giữ nguyên, chờ thị trường hồi phục", 7),
            ("buy", "Mua thêm vì giá đang rẻ", 10),
        ],
        # fear here: ask about a smaller fall; calm: ask about a crash
        "next": lambda a: "drop5" if a.get("drop20") in ("sell_all", "sell_some") else "drop35",
    },
    "drop5": {
        "text": "Nếu danh mục chỉ giảm 5% trong 1 tháng, anh/chị sẽ:",
        "options": [("sell_all", "Vẫn bán hết", 0), ("sell_some", "Bán bớt", 2), ("hold", "Giữ nguyên", 5)],
        "next": "bet_safe",
    },
    "drop35": {
        "text": "Năm 2022 nhiều danh mục giảm 35% và mất hơn một năm để hồi phục. Nếu điều đó lặp lại, anh/chị sẽ:",
        "options": [
            ("sell_some", "Bán bớt để giữ phần còn lại", 3),
            ("hold", "Giữ nguyên, chờ hồi phục", 7),
            ("buy", "Mua thêm đều đặn khi thị trường giảm", 10),
        ],
        "next": "bet_bold",
    },
    "bet_safe": {
        "text": "Chọn một trong hai:",
        "options": [("a", "A: chắc chắn lãi 6%", 0), ("b", "B: 50% cơ hội lãi 10%, 50% cơ hội lỗ 1%", 5)],
        "next": "experience",
    },
    "bet_bold": {
        "text": "Chọn một trong hai:",
        "options": [
            ("a", "A: chắc chắn lãi 6%", 2),
            ("b", "B: 50% cơ hội lãi 15%, 50% cơ hội lỗ 3%", 6),
            ("c", "C: 50% cơ hội lãi 30%, 50% cơ hội lỗ 12%", 10),
        ],
        "next": "experience",
    },
    "experience": {
        "text": "Anh/chị đã tự đầu tư cổ phiếu hoặc trái phiếu doanh nghiệp bao lâu?",
        "options": [
            ("none", "Chưa từng", 0),
            ("lt3", "Dưới 3 năm", 4),
            ("3to10", "3 – 10 năm", 7),
            ("gt10", "Trên 10 năm", 10),
        ],
        "next": "leverage",
    },
    "leverage": {
        "text": "Khi thị trường giảm sâu, anh/chị có sẵn sàng vay thêm để mua vào không?",
        "options": [
            ("never", "Không bao giờ", 0),
            ("maybe", "Có thể, một khoản nhỏ", 6),
            ("yes", "Có, đó là cơ hội", 10),
        ],
        "next": "income",
    },
    "income": {
        "text": "Thu nhập của anh/chị trong 3 năm tới sẽ thế nào?",
        "options": [
            ("stable", "Rất ổn định (lương, lương hưu, tiền thuê)", 6),
            ("mostly", "Khá ổn định", 4),
            ("volatile", "Biến động theo kinh doanh", 3),
            ("unsure", "Không chắc chắn", 0),
        ],
        "next": lambda a, ctx: (
            "business"
            if ctx.get("owns_business")
            else "big_expense"
            if ctx.get("dependents")
            else "new_assets"
            if ctx.get("age", 99) < 40
            else None
        ),
    },
    "business": {
        "text": "Nếu doanh nghiệp của anh/chị cần vốn gấp, anh/chị sẽ lấy từ đâu trước?",
        "options": [
            ("portfolio", "Bán bớt danh mục đầu tư", 3),
            ("loan", "Vay ngân hàng", 6),
            ("reserve", "Quỹ dự phòng riêng của doanh nghiệp", 8),
        ],
        "next": lambda a, ctx: "big_expense" if ctx.get("dependents") else None,
    },
    "big_expense": {
        "text": "Khoản chi lớn sắp tới (học phí, mua nhà, chữa bệnh) có thể lùi lại nếu thị trường xấu không?",
        "options": [
            ("no", "Không thể lùi", 0),
            ("some", "Lùi được vài tháng", 4),
            ("yes", "Lùi được hoặc đã để riêng tiền", 8),
        ],
        "next": lambda a, ctx: "new_assets" if ctx.get("age", 99) < 40 else None,
    },
    "new_assets": {
        "text": "Anh/chị nghĩ gì về các kênh mới như tài sản số?",
        "options": [
            ("avoid", "Tránh hoàn toàn", 2),
            ("small", "Một phần nhỏ để thử", 6),
            ("core", "Là một phần chính của danh mục", 10),
        ],
        "next": None,
    },
}

FIRST = "goal"

# the five profiles: what each accepts losing, and where its money may sit
PROFILES = [
    {
        "level": 1,
        "name": "Bảo toàn",
        "drawdown_limit": 0.05,
        "mix": {"Tiền & tiền gửi": "50–70%", "Trái phiếu": "20–40%", "Cổ phiếu & quỹ cổ phiếu": "0–10%"},
    },
    {
        "level": 2,
        "name": "Thận trọng",
        "drawdown_limit": 0.08,
        "mix": {"Tiền & tiền gửi": "30–50%", "Trái phiếu": "30–40%", "Cổ phiếu & quỹ cổ phiếu": "10–25%"},
    },
    {
        "level": 3,
        "name": "Cân bằng",
        "drawdown_limit": 0.15,
        "mix": {"Tiền & tiền gửi": "15–30%", "Trái phiếu": "20–35%", "Cổ phiếu & quỹ cổ phiếu": "30–50%"},
    },
    {
        "level": 4,
        "name": "Tăng trưởng",
        "drawdown_limit": 0.25,
        "mix": {"Tiền & tiền gửi": "5–15%", "Trái phiếu": "10–25%", "Cổ phiếu & quỹ cổ phiếu": "50–70%"},
    },
    {
        "level": 5,
        "name": "Mạo hiểm",
        "drawdown_limit": 0.35,
        "mix": {
            "Tiền & tiền gửi": "0–10%",
            "Trái phiếu": "0–15%",
            "Cổ phiếu & quỹ cổ phiếu": "70–90%",
            "Tài sản số": "tối đa 10%",
        },
    },
]

PERSONAS = {
    "Chuyên gia": "Thu nhập cao từ chuyên môn, tích lũy đều, mục tiêu con cái và nghỉ hưu chủ động.",
    "F1": "Thế hệ tạo lập tài sản: chủ doanh nghiệp, nhiều bất động sản, quan tâm chuyển giao.",
    "F2": "Thế hệ kế thừa, trẻ: ưa công nghệ, chấp nhận biến động, quan tâm kênh mới.",
    "Nghỉ hưu": "Ưu tiên dòng tiền đều và giữ vốn, chi phí y tế tăng dần.",
    "Mới chạm ngưỡng": "Vừa đạt ngưỡng khách hàng ưu tiên, tài sản chủ yếu là nhà ở và tiền lương.",
}


def level_of(score: float) -> int:
    """A 0–100 score as a profile level 1–5."""
    return 1 + min(4, int(max(0.0, score) // 20))


def _options(q: Q) -> List[Tuple[str, str, int]]:
    return q["options"]


def next_id(answers: Dict[str, str], ctx: Dict[str, Any]) -> Optional[str]:
    """The next question to ask, or None when the test is done. Answers outside the path are
    ignored; a wrong option for a question on the path ends the walk there (it is asked again)."""
    qid: Optional[str] = FIRST
    while qid:
        if qid not in answers:
            return qid
        q = BANK[qid]
        if answers[qid] not in {o[0] for o in _options(q)}:
            return qid
        nxt = q["next"]
        if callable(nxt):
            qid = nxt(answers) if nxt.__code__.co_argcount == 1 else nxt(answers, ctx)
        else:
            qid = nxt
    return None


def path(answers: Dict[str, str], ctx: Dict[str, Any]) -> List[str]:
    """The questions this client was (or will be) asked, in order, as far as the answers go."""
    out, qid = [], FIRST
    while qid and qid in answers:
        out.append(qid)
        nxt = BANK[qid]["next"]
        qid = (nxt(answers) if nxt.__code__.co_argcount == 1 else nxt(answers, ctx)) if callable(nxt) else nxt
    return out


def question(qid: str, ctx: Dict[str, Any], answered: int) -> Dict[str, Any]:
    q = BANK[qid]
    p = ctx.get("portfolio") or 10_000_000_000
    text = q["text"].format(portfolio=vnd(p), portfolio_80=vnd(p * 0.8))
    return {
        "id": qid,
        "text": text,
        "options": [{"id": o[0], "text": o[1]} for o in _options(q)],
        "number": answered + 1,
        "of": f"{max(8, answered + 1)}–12",
    }


def tolerance(answers: Dict[str, str], ctx: Dict[str, Any]) -> float:
    """0–100: the points of the answers on this client's path, over the most that path allows."""
    got = most = 0
    for qid in path(answers, ctx):
        pts = {o[0]: o[2] for o in _options(BANK[qid])}
        got += pts[answers[qid]]
        most += max(pts.values())
    return round(100 * got / most, 1) if most else 0.0


def capacity(ctx: Dict[str, Any], answers: Dict[str, str]) -> Tuple[float, List[str]]:
    """0–100 from the client's own data, with the reasons that moved it."""
    score, why = 50.0, []
    months = ctx.get("liquidity_months", 0)
    if months >= 24:
        score += 15
        why.append(f"Dự phòng thanh khoản dồi dào ({months:.0f} tháng chi tiêu)")
    elif months >= 6:
        score += 5
        why.append(f"Dự phòng thanh khoản đủ ({months:.0f} tháng)")
    else:
        score -= 15
        why.append(f"Dự phòng thanh khoản mỏng ({months:.1f} tháng)")
    dsr = ctx.get("debt_service_ratio", 0)
    if dsr > 0.4:
        score -= 20
        why.append(f"Trả nợ chiếm {dsr:.0%} thu nhập")
    elif dsr > 0.2:
        score -= 8
        why.append(f"Trả nợ chiếm {dsr:.0%} thu nhập")
    lev = ctx.get("leverage", 0)
    if lev > 0.3:
        score -= 10
        why.append(f"Nợ bằng {lev:.0%} tài sản")
    kids = ctx.get("dependents", 0)
    if kids:
        score -= min(15, 5 * kids)
        why.append(f"{kids} người phụ thuộc")
    age = ctx.get("age", 45)
    if age < 40:
        score += 10
        why.append("Còn nhiều năm làm việc")
    elif age >= 60:
        score -= 15
        why.append("Đã nghỉ hưu: ít thời gian bù lỗ")
    when = answers.get("horizon")
    score += {"lt2": -15, "2to5": -5, "5to10": 0, "gt10": 5}.get(when, 0)
    if when == "lt2":
        why.append("Cần dùng tiền trong vòng 2 năm")
    inc = answers.get("income")
    score += {"stable": 10, "mostly": 5, "volatile": -5, "unsure": -15}.get(inc, 0)
    if inc in ("volatile", "unsure"):
        why.append("Thu nhập không ổn định")
    if answers.get("big_expense") == "no":
        score -= 10
        why.append("Có khoản chi lớn không thể lùi")
    if ctx.get("net_worth", 0) >= 50_000_000_000:
        score += 10
        why.append("Tài sản ròng lớn so với chi tiêu")
    return round(max(0.0, min(100.0, score)), 1), why


def persona(ctx: Dict[str, Any]) -> str:
    """Which of the five the client is, from their data."""
    if ctx.get("age", 0) >= 58 or ctx.get("pension"):
        return "Nghỉ hưu"
    if ctx.get("owns_business"):
        return "F1"
    if ctx.get("age", 99) < 35 and ctx.get("risky_share", 0) > 0.5:
        return "F2"
    if ctx.get("net_worth", 0) < 10_000_000_000:
        return "Mới chạm ngưỡng"
    return "Chuyên gia"


def says_vs_does(tol_level: int, behaviour: List[Dict[str, Any]]) -> Optional[str]:
    """A client who says they bear a lot, but sold when the market fell."""
    for b in behaviour:
        if b.get("action") in ("panic_sell", "sell") and tol_level >= 3:
            note = b["note"][:1].lower() + b["note"][1:]
            return (
                f"Anh/chị tự đánh giá chấp nhận rủi ro mức {PROFILES[tol_level - 1]['name']}, nhưng ngày "
                f"{b['date']} đã {note} (thị trường {b['market_move']:+.0%}): nói và làm chưa khớp."
            )
    return None
