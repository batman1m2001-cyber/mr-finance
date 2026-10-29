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
        "source": "Đề xuất trong quá trình sửa đổi chính sách thuế BĐS",
        "rule": {"type": "second_property", "annual_rate": 0.004},
    },
    {
        "id": "P02",
        "kind": "policy",
        "title": "Tính thuế chuyển nhượng BĐS theo lãi thực tế thay cho 2% giá bán",
        "status": "consultation",
        "source": "Dự thảo Luật Thuế TNCN (sửa đổi) — phương án thuế theo thu nhập",
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
        "source": "Luật Chứng khoán sửa đổi 2024 và các nghị định hướng dẫn",
        "rule": {"type": "bond_kind", "bond_kind": "corporate", "sensitivity": -0.05},
    },
    {
        "id": "P07",
        "kind": "policy",
        "title": "Thay đổi thuế chuyển nhượng chứng khoán",
        "status": "draft",
        "source": "Dự thảo Luật Thuế TNCN (sửa đổi) — phương án thuế giao dịch chứng khoán",
        "rule": {"type": "trading_cost", "turnover": 2.0, "rate": 0.001},
    },
    {
        "id": "P08",
        "kind": "policy",
        "title": "Nâng hạng thị trường chứng khoán",
        "status": "passed",
        "opportunity": True,
        "source": "FTSE Russell công bố nâng hạng Việt Nam lên thị trường mới nổi thứ cấp, hiệu lực 09/2026",
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
        "source": "Nghị định sửa đổi Nghị định 24/2012 về quản lý kinh doanh vàng",
        "rule": {"type": "gold"},
    },
    {
        "id": "P10",
        "kind": "policy",
        "title": "Thí điểm thị trường tài sản mã hóa",
        "status": "passed",
        "opportunity": True,
        "source": "Nghị quyết của Chính phủ về thí điểm thị trường tài sản mã hóa",
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
        "source": "Mức giảm trừ gia cảnh 15,5 triệu (bản thân) và 6,2 triệu (mỗi người phụ thuộc) từ 2026",
        "rule": {"type": "pit_relief", "self": 4_500_000, "dependent": 1_800_000, "marginal": 0.3},
    },
    {
        "id": "P13",
        "kind": "policy",
        "title": "Quy định bảo hiểm liên kết đầu tư",
        "status": "passed",
        "source": "Luật Kinh doanh bảo hiểm 2022 và văn bản hướng dẫn",
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
    {
        "id": "P15",
        "kind": "policy",
        "title": "Có thể thắt chặt thủ tục chuyển tiền ra nước ngoài",
        "status": "draft",
        "source": "Tin tổng hợp về kiểm soát chuyển tiền ra nước ngoài (giả định cho demo)",
        # no price moves: the plans that send money abroad take more steps (NEWS_EVIDENCE_BRD Ví dụ 4)
        "rule": {"type": "plans", "purposes": ["study_abroad", "emigrate", "support_abroad"]},
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
    {
        "id": "M03",
        "kind": "macro",
        "title": "Fed dự kiến tăng lãi suất thêm 0,25%",
        "status": "consultation",
        "source": "FOMC 16/09/2026: tăng lên 3,75–4%; dự báo trung vị thêm một lần tăng 0,25% trước cuối 2026",
        # the move is the median of what the VN-Index did after past hikes (src/evidence, the statistics branch)
        "rule": {"type": "stat", "classes": ["stock", "fund"]},
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
        "source": "Kế hoạch khai thác giai đoạn 1 năm 2026",
        "rule": {"type": "area", "area": "long_thanh", "sensitivity": 0.15},
    },
    {
        "id": "I03",
        "kind": "infrastructure",
        "title": "Đường Vành đai 3 TP.HCM hoàn thành",
        "status": "consultation",
        "opportunity": True,
        "source": "Kế hoạch thông xe 2026",
        "rule": {"type": "area", "area": "vinhomes_grand_park", "sensitivity": 0.06},
    },
]

# What the client reads on News and Prediction (business feedback 2026-10-29): the section the item sits in
# (global: world and macro news; local: Vietnam and its infrastructure; exclusive: laws at every stage and policy
# analysis), a three-line summary, why it matters to someone who holds what it touches, and the source's address
# — the article or document itself, checked to load; none when none was found (never a search).
NEWS = {
    "P01": {
        "section": "exclusive",
        "summary": [
            "Đề xuất đánh thuế hằng năm lên người sở hữu từ căn nhà thứ hai trở lên, đang ở giai đoạn dự thảo.",
            "Mục tiêu là hạn chế đầu cơ và nhà để trống.",
            "Mức thuế và ngưỡng áp dụng chưa được chốt.",
        ],
        "why": "Liên quan nếu gia đình bạn sở hữu nhiều hơn một bất động sản: chi phí nắm giữ có thể tăng.",
        "source_url": "https://vnexpress.net/bo-tai-chinh-se-nghien-cuu-danh-thue-nguoi-so-huu-nhieu-nha-dat-4797640.html",
    },
    "P02": {
        "section": "exclusive",
        "summary": [
            "Dự thảo Luật Thuế TNCN sửa đổi đề xuất tính thuế chuyển nhượng bất động sản theo lãi thực tế thay vì 2% giá bán.",
            "Phương án đang được lấy ý kiến.",
            "Bất động sản mua lâu và tăng giá mạnh sẽ chịu thuế cao hơn khi bán.",
        ],
        "why": "Liên quan tới bất động sản bạn đang nắm giữ: khoản lãi khi bán sau này có thể bị đánh thuế nhiều hơn.",
        "source_url": "https://vnexpress.net/de-xuat-tinh-thue-20-tren-lai-tung-lan-chuyen-nhuong-bat-dong-san-4916909.html",
    },
    "P03": {
        "section": "exclusive",
        "summary": [
            "Luật Đất đai 2024 yêu cầu bảng giá đất điều chỉnh hằng năm, sát giá thị trường.",
            "Bảng giá mới áp dụng từ 01/01/2026.",
            "Tiền sử dụng đất, lệ phí và thuế tính theo bảng giá sẽ tăng.",
        ],
        "why": "Liên quan tới bất động sản của bạn: phí và thuế khi chuyển nhượng, cấp sổ có thể cao hơn.",
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=211189&classid=1&typegroupid=3",
    },
    "P04": {
        "section": "exclusive",
        "summary": [
            "Giả định cho demo: một dự thảo chính sách làm giảm biên lợi nhuận nhóm ngân hàng.",
            "Lợi nhuận ngành giảm sẽ gây áp lực lên giá cổ phiếu ngân hàng.",
            "Mới ở giai đoạn dự thảo.",
        ],
        "why": "Liên quan nếu bạn nắm cổ phiếu ngân hàng hoặc quỹ có tỷ trọng ngân hàng.",
    },
    "P05": {
        "section": "exclusive",
        "summary": [
            "Luật Các TCTD 2024 giới hạn cá nhân sở hữu tối đa 2,5% và tổ chức tối đa 10% vốn điều lệ một ngân hàng.",
            "Luật đã có hiệu lực.",
            "Khoản nắm giữ lớn khó mua thêm và khó bán một lần.",
        ],
        "why": "Liên quan tới khoản cổ phiếu ngân hàng lớn trong danh mục của bạn.",
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=211190&classid=1&typegroupid=3",
    },
    "P06": {
        "section": "exclusive",
        "summary": [
            "Luật Chứng khoán sửa đổi 2024 siết điều kiện nhà đầu tư chuyên nghiệp được mua trái phiếu doanh nghiệp phát hành riêng lẻ.",
            "Ít người mua hơn làm thanh khoản trái phiếu doanh nghiệp giảm.",
            "Các nghị định hướng dẫn quy định mốc áp dụng cụ thể.",
        ],
        "why": "Liên quan tới trái phiếu doanh nghiệp bạn đang nắm: bán trước hạn có thể khó hơn.",
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=212484&classid=1&orggroupid=1",
    },
    "P07": {
        "section": "exclusive",
        "summary": [
            "Dự thảo Luật Thuế TNCN sửa đổi có phương án thay đổi cách đánh thuế giao dịch chứng khoán.",
            "Chi phí giao dịch có thể tăng với người mua bán thường xuyên.",
            "Đang ở giai đoạn dự thảo.",
        ],
        "why": "Liên quan tới cổ phiếu và chứng chỉ quỹ bạn giao dịch.",
        "source_url": "https://vneconomy.vn/bo-tai-chinh-rut-de-xuat-ap-thue-20-doi-voi-lai-rong-chung-khoan.htm",
    },
    "P08": {
        "section": "global",
        "summary": [
            "FTSE Russell nâng hạng Việt Nam lên thị trường mới nổi thứ cấp, hiệu lực từ 09/2026.",
            "Quỹ theo chỉ số thị trường mới nổi sẽ mua cổ phiếu vốn hóa lớn.",
            "Dòng vốn ngoại thường vào theo nhiều đợt quanh ngày hiệu lực.",
        ],
        "why": "Liên quan tới cổ phiếu vốn hóa lớn trong danh mục của bạn, nhóm hưởng lợi đầu tiên từ dòng vốn ngoại.",
        "source_url": "https://www.nst.com.my/amp/business/corporate/2025/10/1289826/vietnam-shares-hit-record-high-after-ftse-flags-upgrade-emerging",
    },
    "P09": {
        "section": "exclusive",
        "summary": [
            "Nghị định sửa đổi Nghị định 24/2012 thay đổi cách quản lý kinh doanh vàng miếng.",
            "Chênh lệch giá vàng trong nước và thế giới (khoảng 12%) có xu hướng thu hẹp.",
            "Giá vàng miếng SJC có thể giảm về gần giá thế giới.",
        ],
        "why": "Liên quan tới vàng miếng bạn đang giữ: giá trị có thể giảm khi chênh lệch thu hẹp.",
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=215074",
    },
    "P10": {
        "section": "exclusive",
        "summary": [
            "Chính phủ ban hành nghị quyết thí điểm thị trường tài sản mã hóa.",
            "Chỉ các sàn được cấp phép mới được hoạt động.",
            "Tài sản số có khung pháp lý rõ hơn.",
        ],
        "why": "Liên quan tới tài sản số bạn đang nắm giữ.",
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=215249",
    },
    "P11": {
        "section": "exclusive",
        "summary": [
            "Giả định cho demo: hạn mức và thủ tục chuyển tiền cho du học sinh thay đổi.",
            "Phí chuyển tiền có thể tăng và cần chuyển sớm hơn.",
            "Đang lấy ý kiến.",
        ],
        "why": "Liên quan tới kế hoạch học phí ở nước ngoài của gia đình bạn.",
    },
    "P12": {
        "section": "exclusive",
        "summary": [
            "Mức giảm trừ gia cảnh tăng lên 15,5 triệu đồng cho bản thân và 6,2 triệu đồng cho mỗi người phụ thuộc.",
            "Áp dụng từ kỳ tính thuế 2026.",
            "Thuế thu nhập cá nhân phải nộp hằng tháng giảm.",
        ],
        "why": "Liên quan tới thu nhập từ lương của bạn và số người phụ thuộc bạn khai.",
        "source_url": "https://tuoitre.vn/chinh-thuc-nang-giam-tru-gia-canh-len-15-5-trieu-thang-ap-dung-tu-ky-tinh-thue-2026-20251017103939942.htm",
    },
    "P13": {
        "section": "exclusive",
        "summary": [
            "Luật Kinh doanh bảo hiểm 2022 và văn bản hướng dẫn siết quy định bán bảo hiểm liên kết đầu tư.",
            "Hợp đồng phải minh bạch hơn về phí và rủi ro.",
            "Giá trị hoàn lại của một số hợp đồng có thể bị ảnh hưởng.",
        ],
        "why": "Liên quan tới hợp đồng bảo hiểm bạn đang có.",
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=206242",
    },
    "P14": {
        "section": "exclusive",
        "summary": [
            "Quốc hội áp dụng thuế tối thiểu toàn cầu 15% từ 2024.",
            "Doanh nghiệp thuộc tập đoàn đa quốc gia lớn phải nộp bổ sung đến mức 15%.",
            "Một số ưu đãi đầu tư cũ bị thay đổi.",
        ],
        "why": "Liên quan tới cổ phần doanh nghiệp bạn sở hữu: lợi nhuận sau thuế có thể giảm.",
        "source_url": "https://vanban.chinhphu.vn/?pageid=27160&docid=209231",
    },
    "P15": {
        "section": "exclusive",
        "summary": [
            "Tin tổng hợp cho thấy thủ tục chuyển tiền ra nước ngoài có thể bị thắt chặt.",
            "Chưa có văn bản chính thức.",
            "Giả định cho demo.",
        ],
        "why": "Liên quan tới kế hoạch chi tiêu ở nước ngoài của gia đình bạn: du học, định cư, hỗ trợ người thân.",
    },
    "M01": {
        "section": "local",
        "summary": [
            "Kịch bản giả định: Ngân hàng Nhà nước tăng lãi suất điều hành 0,5 điểm.",
            "Lãi vay thả nổi tăng theo ở kỳ điều chỉnh tới.",
            "Lãi tiền gửi mới cũng có thể tăng.",
        ],
        "why": "Liên quan tới khoản vay lãi suất thả nổi và tiền gửi của bạn.",
    },
    "M02": {
        "section": "global",
        "summary": [
            "Kịch bản giả định: tỷ giá USD/VND tăng 3%.",
            "Đồng USD mạnh lên khi Fed giữ lãi suất cao lâu hơn.",
            "Các khoản chi bằng ngoại tệ tính ra tiền đồng sẽ tăng.",
        ],
        "why": "Liên quan tới các khoản chi bằng ngoại tệ của gia đình bạn, như học phí ở nước ngoài.",
    },
    "M03": {
        "section": "global",
        "summary": [
            "Ngày 16/09/2026, FOMC tăng lãi suất lên 3,75–4%.",
            "Dự báo trung vị cho thấy thêm một lần tăng 0,25% trước cuối 2026.",
            "Lãi suất Mỹ cao thường kéo dòng vốn rời thị trường mới nổi.",
        ],
        "why": "Liên quan tới cổ phiếu và chứng chỉ quỹ bạn đang nắm.",
        "source_url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm",
    },
    "I01": {
        "section": "local",
        "summary": [
            "Tuyến Metro số 1 Bến Thành – Suối Tiên đưa vào khai thác cuối 2024.",
            "Nhà ở gần ga được hưởng lợi về giá bán và giá thuê.",
            "Dự án mới có xu hướng dồn về dọc tuyến.",
        ],
        "why": "Liên quan tới bất động sản của bạn nằm gần tuyến Metro.",
        "source_url": "https://vnexpress.net/metro-ben-thanh-suoi-tien-van-hanh-4830508.html",
    },
    "I02": {
        "section": "local",
        "summary": [
            "Sân bay Long Thành dự kiến đưa giai đoạn 1 vào khai thác trong năm 2026.",
            "Hạ tầng kết nối giúp đất vùng ven tăng giá.",
            "Tiến độ thực tế còn cần theo dõi.",
        ],
        "why": "Liên quan tới bất động sản của bạn ở khu vực Long Thành.",
        "source_url": "https://www.vietnamplus.vn/de-xuat-phuong-an-phan-chia-va-lo-trinh-khai-thac-san-bay-long-thanh-post1123930.vnp",
    },
    "I03": {
        "section": "local",
        "summary": [
            "Đường Vành đai 3 TP.HCM dự kiến thông xe trong năm 2026.",
            "Thời gian di chuyển giữa các khu ven đô được rút ngắn.",
            "Bất động sản dọc tuyến được hưởng lợi.",
        ],
        "why": "Liên quan tới bất động sản của bạn dọc tuyến Vành đai 3.",
        "source_url": "https://tuoitre.vn/pho-chu-tich-ubnd-tphcm-hoang-nguyen-dinh-yeu-cau-thong-xe-17km-doan-tren-cao-vanh-dai-3-vao-thang-11-100261002162541363.htm",
    },
}

STATUS_LABEL = {"draft": "Dự thảo", "consultation": "Đang lấy ý kiến / dự kiến", "passed": "Đã thông qua / đã diễn ra"}

# How soon each item's impact lands: the time in its evidence frame (data/evidence.json, scripts/make_evidence.py);
# the chart filters 1–3 months under 3 months.
EVIDENCE = Path(__file__).resolve().parents[1] / "data" / "evidence.json"
TIMEFRAMES = {"1w": "1 tuần", "1m": "1 tháng", "1-3m": "1–3 tháng", "3m": "3 tháng", ">3m": "trên 3 tháng"}
HORIZON = {"1w": "1w", "1m": "1m", "1-3m": "3m", "3m": "3m", ">3m": ">3m"}


def main() -> None:
    frames = json.loads(EVIDENCE.read_text(encoding="utf-8"))["frames"]
    for f in FACTORS:
        tf = frames[f["id"]]["timeframe"]
        f["probability"] = STATUS[f["status"]]
        f["status_label"] = STATUS_LABEL[f["status"]]
        f["horizon"] = HORIZON[tf]
        f["horizon_label"] = TIMEFRAMES[tf]
        f.setdefault("opportunity", False)
        f.update(NEWS[f["id"]])
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
