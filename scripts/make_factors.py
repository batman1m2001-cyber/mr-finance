"""Write data/factors.json: the policies, macro moves and infrastructure projects the alerts watch.

Each factor has a status (dự thảo / lấy ý kiến / đã thông qua → a probability), a source line,
and a rule (src/impact/_rules.py) that finds which holdings it touches and how much. Statuses and
numbers are a snapshot for the demo: the brief says to re-check every item's legal status before
showing it, and the UI says so too. Items marked (giả định) are assumptions, not news.

    uv run python scripts/make_factors.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "factors.json"

STATUS = {"draft": 0.2, "consultation": 0.5, "passed": 0.9}

FACTORS = [
    # ── policies (the brief's list) ─────────────────────────────────────
    {
        "id": "P01",
        "kind": "policy",
        "title": "Thuế với người sở hữu từ 2 bất động sản trở lên",
        "status": "draft",
        "source": "Đề xuất trong quá trình sửa đổi chính sách thuế BĐS (cần kiểm tra trạng thái)",
        "rule": {"type": "second_property", "annual_rate": 0.004},
    },
    {
        "id": "P02",
        "kind": "policy",
        "title": "Tính thuế chuyển nhượng BĐS theo lãi thực tế thay cho 2% giá bán",
        "status": "consultation",
        "source": "Dự thảo Luật Thuế TNCN (sửa đổi) — phương án thuế theo thu nhập (cần kiểm tra trạng thái)",
        "rule": {"type": "transfer_tax", "old_rate": 0.02, "gain_rate": 0.2},
    },
    {
        "id": "P03",
        "kind": "policy",
        "title": "Bảng giá đất điều chỉnh hằng năm (Luật Đất đai 2024)",
        "status": "passed",
        "source": "Luật Đất đai 2024, hiệu lực 01/08/2024; bảng giá đất áp dụng từ 01/01/2026",
        "rule": {"type": "land_fees", "rate": 0.006},
    },
    {
        "id": "P04",
        "kind": "policy",
        "title": "Dự thảo ảnh hưởng nhóm ngân hàng quốc doanh (giả định)",
        "status": "draft",
        "source": "Giả định cho demo: chính sách tác động biên lợi nhuận ngành ngân hàng",
        "rule": {"type": "sector", "sector": "Ngân hàng", "sensitivity": -0.08},
    },
    {
        "id": "P05",
        "kind": "policy",
        "title": "Giới hạn sở hữu cổ phần ngân hàng (Luật Các TCTD 2024)",
        "status": "passed",
        "source": "Luật Các tổ chức tín dụng 2024: cá nhân tối đa 2,5%, tổ chức tối đa 10% vốn điều lệ",
        "rule": {
            "type": "issuer_concentration",
            "sector": "Ngân hàng",
            "min_value": 1_000_000_000,
            "sensitivity": -0.06,
        },
    },
    {
        "id": "P06",
        "kind": "policy",
        "title": "Siết điều kiện nhà đầu tư chuyên nghiệp mua trái phiếu DN",
        "status": "passed",
        "source": "Luật Chứng khoán sửa đổi 2024 và các nghị định hướng dẫn (cần kiểm tra mốc áp dụng)",
        "rule": {"type": "bond_kind", "bond_kind": "corporate", "sensitivity": -0.05},
    },
    {
        "id": "P07",
        "kind": "policy",
        "title": "Thay đổi thuế chuyển nhượng chứng khoán",
        "status": "draft",
        "source": "Dự thảo Luật Thuế TNCN (sửa đổi) — phương án thuế giao dịch chứng khoán (cần kiểm tra)",
        "rule": {"type": "trading_cost", "turnover": 2.0, "rate": 0.001},
    },
    {
        "id": "P08",
        "kind": "policy",
        "title": "Nâng hạng thị trường chứng khoán",
        "status": "passed",
        "opportunity": True,
        "source": "FTSE Russell công bố nâng hạng Việt Nam lên thị trường mới nổi thứ cấp, hiệu lực 09/2026 (cần kiểm tra)",
        "rule": {
            "type": "large_caps",
            "tickers": ["FPT", "TCB", "VCB", "MBB", "VNM", "HPG", "VHM", "MWG", "SSI"],
            "sensitivity": 0.08,
        },
    },
    {
        "id": "P09",
        "kind": "policy",
        "title": "Chính sách quản lý vàng miếng",
        "status": "passed",
        "source": "Nghị định sửa đổi Nghị định 24/2012 về quản lý kinh doanh vàng (cần kiểm tra)",
        "rule": {"type": "gold"},
    },
    {
        "id": "P10",
        "kind": "policy",
        "title": "Thí điểm thị trường tài sản mã hóa",
        "status": "passed",
        "opportunity": True,
        "source": "Nghị quyết của Chính phủ về thí điểm thị trường tài sản mã hóa (cần kiểm tra)",
        "rule": {"type": "crypto", "sensitivity": 0.05},
    },
    {
        "id": "P11",
        "kind": "policy",
        "title": "Quy định ngoại hối, chuyển tiền du học",
        "status": "consultation",
        "source": "Giả định cho demo: hạn mức và thủ tục chuyển tiền cho du học sinh thay đổi (phí, chuyển sớm)",
        "rule": {"type": "study_abroad", "fx_move": 0.01},
    },
    {
        "id": "P12",
        "kind": "policy",
        "title": "Thuế thu nhập cá nhân: tăng mức giảm trừ gia cảnh",
        "status": "passed",
        "opportunity": True,
        "source": "Mức giảm trừ gia cảnh 15,5 triệu (bản thân) và 6,2 triệu (mỗi người phụ thuộc) từ 2026 (cần kiểm tra)",
        "rule": {"type": "pit_relief", "self": 4_500_000, "dependent": 1_800_000, "marginal": 0.3},
    },
    {
        "id": "P13",
        "kind": "policy",
        "title": "Quy định bảo hiểm liên kết đầu tư",
        "status": "passed",
        "source": "Luật Kinh doanh bảo hiểm 2022 và văn bản hướng dẫn (cần kiểm tra)",
        "rule": {"type": "insurance", "sensitivity": -0.03},
    },
    {
        "id": "P14",
        "kind": "policy",
        "title": "Thuế tối thiểu toàn cầu, thay đổi ưu đãi đầu tư",
        "status": "passed",
        "source": "Nghị quyết của Quốc hội về thuế tối thiểu toàn cầu, áp dụng từ 2024",
        "rule": {"type": "business", "sensitivity": -0.04},
    },
    # ── macro ───────────────────────────────────────────────────────────
    {
        "id": "M01",
        "kind": "macro",
        "title": "Lãi suất điều hành tăng 0,5%",
        "status": "consultation",
        "source": "Kịch bản giả định cho demo",
        "rule": {"type": "rates", "move": 0.005},
    },
    {
        "id": "M02",
        "kind": "macro",
        "title": "Tỷ giá USD/VND tăng 3%",
        "status": "consultation",
        "source": "Kịch bản giả định cho demo",
        "rule": {"type": "study_abroad", "fx_move": 0.03},
    },
    # ── infrastructure (micro, often good news) ─────────────────────────
    {
        "id": "I01",
        "kind": "infrastructure",
        "title": "Metro số 1 Bến Thành – Suối Tiên vận hành",
        "status": "passed",
        "opportunity": True,
        "source": "Tuyến Metro số 1 TP.HCM đưa vào khai thác cuối 2024",
        "rule": {"type": "area", "area": "thao_dien", "sensitivity": 0.06},
    },
    {
        "id": "I02",
        "kind": "infrastructure",
        "title": "Sân bay Long Thành đưa giai đoạn 1 vào khai thác",
        "status": "consultation",
        "opportunity": True,
        "source": "Kế hoạch khai thác giai đoạn 1 năm 2026 (cần kiểm tra tiến độ)",
        "rule": {"type": "area", "area": "long_thanh", "sensitivity": 0.15},
    },
    {
        "id": "I03",
        "kind": "infrastructure",
        "title": "Đường Vành đai 3 TP.HCM hoàn thành",
        "status": "consultation",
        "opportunity": True,
        "source": "Kế hoạch thông xe 2026 (cần kiểm tra tiến độ)",
        "rule": {"type": "area", "area": "vinhomes_grand_park", "sensitivity": 0.06},
    },
]

STATUS_LABEL = {"draft": "Dự thảo", "consultation": "Đang lấy ý kiến / dự kiến", "passed": "Đã thông qua / đã diễn ra"}


def main() -> None:
    for f in FACTORS:
        f["probability"] = STATUS[f["status"]]
        f["status_label"] = STATUS_LABEL[f["status"]]
        f.setdefault("opportunity", False)
    OUT.write_text(
        json.dumps(
            {
                "as_of": "2026-10-09",
                "note": "Ảnh chụp cho demo: kiểm tra lại trạng thái pháp lý từng mục trước khi trình bày.",
                "factors": FACTORS,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
