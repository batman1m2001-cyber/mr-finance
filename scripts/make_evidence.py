"""Write data/evidence.json: each factor's evidence (NEWS_EVIDENCE_BRD) — its event type, the labels it touches, and a
qualitative frame (§6: channels, mechanism, effect, time, what to watch, precedents) or the statistics branch (§5) —
plus the precedent calendar the statistics count. Also web/core/lang/en_evidence.js, the English of every phrase.

Precedents are the ones the BRD's examples name and ones whose outcome is in the market store (data/state.db: VN-Index,
SJC, USD/VND from 2020) or widely recorded; one without a source carries none, and only the CIO sees it marked.
Fed decisions verified against the FOMC statements (federalreserve.gov), 2020-01 → 2026-10.

    uv run python scripts/make_evidence.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "evidence.json"
EN = ROOT / "web" / "core" / "lang" / "en_evidence.js"

T = Tuple[str, str]  # (Vietnamese, English)

# the precedent calendar (§5): event type → the dates it happened (the day announced, US time for the Fed)
EVENTS = {
    "fed_cut": ["2020-03-03", "2020-03-15", "2024-09-18", "2024-11-07", "2024-12-18", "2025-09-17", "2025-10-29", "2025-12-10"],
    "fed_hike": [
        "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
        "2023-02-01", "2023-03-22", "2023-05-03", "2023-07-26", "2026-09-16",
    ],
    "sbv_rate_hike": ["2022-09-22", "2022-10-24"],
}  # fmt: skip


def P(event: T, outcome: T, difference: T, source: T = None) -> Dict[str, Any]:
    return {"event": event, "outcome": outcome, "difference": difference, "source": source}


FRAMES = {
    "P01": {
        "event_type": "second_property_tax",
        "channels": ["thuế/phí", "cung/cầu"],
        "mechanism": ("Thuế hằng năm với người có từ hai bất động sản làm tăng chi phí giữ nhà thứ hai, nhu cầu mua để giữ có thể giảm.",
                      "A yearly tax on owners of two or more properties raises the cost of holding a second home; demand to buy and hold may fall."),
        "targets": ["asset:real_estate"],
        "direction": "negative",
        "changes": ["chi phí", "giá"],
        "timeframe": ">3m",
        "watch": ("Dự thảo được trình Quốc hội và mức thuế suất cuối cùng.", "The draft going to the National Assembly, and the final rate."),
        "precedents": [
            P(("Singapore tăng thuế mua nhà thêm (ABSD) và siết tỷ lệ vay (01/2013)", "Singapore raises the extra buyer's stamp duty (ABSD) and tightens loan limits (01/2013)"),
              ("Chỉ số giá nhà tư nhân giảm liên tục khoảng bốn năm, đến giữa 2017.", "The private home price index fell for about four years, to mid-2017."),
              ("Thuế đánh khi mua, không phải hằng năm; đi kèm siết tín dụng.", "Taxed at purchase, not yearly; came with tighter credit.")),
        ],
    },
    "P02": {
        "event_type": "transfer_tax",
        "channels": ["thuế/phí"],
        "mechanism": ("Thuế tính trên phần lãi thay cho 2% giá bán: người bán có lãi lớn nộp nhiều hơn khi bán.",
                      "Tax on the gain instead of 2% of the price: a seller with a large gain pays more on sale."),
        "targets": ["asset:real_estate"],
        "direction": "negative",
        "changes": ["chi phí"],
        "timeframe": ">3m",
        "watch": ("Bản Luật Thuế TNCN được thông qua và cách xác định giá vốn.", "The personal income tax law as passed, and how the cost basis is set."),
        "precedents": [],
    },
    "P03": {
        "event_type": "land_price_table",
        "channels": ["thuế/phí"],
        "mechanism": ("Bảng giá đất sát giá thị trường hơn làm tăng tiền sử dụng đất, lệ phí và thuế tính theo bảng giá.",
                      "A land price table closer to market prices raises land-use fees, charges and taxes based on it."),
        "targets": ["asset:real_estate"],
        "direction": "negative",
        "changes": ["chi phí"],
        "timeframe": "3m",
        "watch": ("Bảng giá đất hằng năm của tỉnh, thành nơi có tài sản.", "The yearly land price table of the province where the property is."),
        "precedents": [
            P(("TP.HCM áp dụng bảng giá đất điều chỉnh (10/2024)", "Ho Chi Minh City applies its revised land price table (10/2024)"),
              ("Tiền sử dụng đất phải nộp tăng nhiều lần; nhiều hồ sơ chuyển mục đích sử dụng đất chậm lại.", "Land-use fees rose several times over; many land-use change applications slowed."),
              ("Lần đó điều chỉnh giữa kỳ; nay bảng giá đổi hằng năm theo luật.", "That was a mid-term revision; the table now changes yearly by law.")),
        ],
    },
    "P04": {
        "event_type": "sector_policy",
        "channels": ["lãi suất", "tín dụng"],
        "mechanism": ("Chính sách ảnh hưởng biên lợi nhuận ngân hàng, lợi nhuận ngành giảm thì giá cổ phiếu ngân hàng chịu áp lực.",
                      "A policy that squeezes bank margins: lower sector profits weigh on bank share prices."),
        "targets": ["sector:Ngân hàng"],
        "direction": "negative",
        "changes": ["giá"],
        "timeframe": "3m",
        "watch": ("Nội dung chính thức của dự thảo và lợi nhuận quý của các ngân hàng.", "The draft's official text and the banks' quarterly profits."),
        "precedents": [],
    },
    "P05": {
        "event_type": "ownership_cap",
        "channels": ["pháp lý", "dòng vốn"],
        "mechanism": ("Cá nhân không được sở hữu quá 2,5% vốn một ngân hàng: khoản nắm giữ lớn khó mua thêm, khó bán một lần.",
                      "No individual may own more than 2.5% of a bank: a large stake cannot grow and is harder to sell at once."),
        "targets": ["sector:Ngân hàng"],
        "direction": "negative",
        "changes": ["thanh khoản"],
        "timeframe": "1m",
        "watch": ("Hướng dẫn xử lý phần sở hữu vượt giới hạn.", "The guidance on holdings above the cap."),
        "precedents": [],
    },
    "P06": {
        "event_type": "bond_buyer_rule",
        "channels": ["pháp lý", "dòng vốn"],
        "mechanism": ("Ít nhà đầu tư đủ điều kiện mua trái phiếu doanh nghiệp riêng lẻ hơn, nên khó bán lại trước hạn.",
                      "Fewer investors may buy private corporate bonds, so selling before maturity gets harder."),
        "targets": ["asset:bond"],
        "direction": "negative",
        "changes": ["thanh khoản", "giá"],
        "timeframe": "1m",
        "watch": ("Khối lượng giao dịch trái phiếu doanh nghiệp trên thị trường thứ cấp.", "Corporate bond trading volume on the secondary market."),
        "precedents": [
            P(("Nghị định 65/2022 siết phát hành trái phiếu doanh nghiệp riêng lẻ (09/2022)", "Decree 65/2022 tightens private corporate bond issues (09/2022)"),
              ("Phát hành mới gần như dừng cuối 2022; nhiều trái phiếu khó bán lại, một số doanh nghiệp chậm trả.", "New issues almost stopped in late 2022; many bonds became hard to resell, some issuers paid late."),
              ("Năm 2022 có thêm các vụ vi phạm lớn làm mất niềm tin; lần này chỉ siết người mua.", "2022 also had large fraud cases that broke trust; this time only buyers are restricted.")),
        ],
    },
    "P07": {
        "event_type": "trading_tax",
        "channels": ["thuế/phí"],
        "mechanism": ("Thuế giao dịch chứng khoán thay đổi làm thay đổi chi phí mỗi lần bán.", "A change in the securities trading tax changes the cost of each sale."),
        "targets": ["asset:stock", "asset:fund"],
        "direction": "negative",
        "changes": ["chi phí"],
        "timeframe": ">3m",
        "watch": ("Phương án thuế trong bản Luật Thuế TNCN được thông qua.", "The tax option in the personal income tax law as passed."),
        "precedents": [],
    },
    "P08": {
        "event_type": "market_upgrade",
        "channels": ["dòng vốn", "tâm lý thị trường"],
        "mechanism": ("Quỹ theo chỉ số thị trường mới nổi mua cổ phiếu vốn hóa lớn khi nâng hạng có hiệu lực.",
                      "Emerging-market index funds buy large caps when the upgrade takes effect."),
        "targets": ["asset:stock", "asset:fund"],
        "direction": "positive",
        "changes": ["dòng tiền", "giá"],
        "timeframe": "1m",
        "watch": ("Dòng tiền khối ngoại ròng trên HOSE quanh ngày hiệu lực.", "Net foreign flows on HOSE around the effective date."),
        "precedents": [
            P(("Pakistan được MSCI nâng hạng lên thị trường mới nổi (hiệu lực 06/2017)", "MSCI upgrades Pakistan to emerging market (effective 06/2017)"),
              ("Chỉ số chứng khoán giảm mạnh trong năm sau ngày hiệu lực.", "The stock index fell sharply in the year after the effective date."),
              ("Pakistan có bất ổn chính trị và vĩ mô cùng lúc.", "Pakistan had political and economic turmoil at the same time.")),
            P(("Ả Rập Xê Út vào nhóm mới nổi của FTSE Russell và MSCI (2019)", "Saudi Arabia joins the FTSE Russell and MSCI emerging indexes (2019)"),
              ("Dòng vốn ngoại vào lớn trong các đợt đưa cổ phiếu vào chỉ số.", "Large foreign inflows during the inclusion steps."),
              ("Quy mô vốn hóa lớn hơn nhiều; đưa vào chỉ số theo nhiều đợt.", "A much larger market; included in several steps.")),
        ],
    },
    "P09": {
        "event_type": "gold_policy",
        "channels": ["pháp lý", "cung/cầu"],
        "mechanism": ("Nhà nước tăng cung vàng miếng, chênh lệch giá trong nước và thế giới có xu hướng thu hẹp.",
                      "The state adds to the supply of gold bars; the gap between domestic and world prices tends to narrow."),
        "targets": ["asset:gold"],
        "direction": "negative",
        "changes": ["giá"],
        "timeframe": "1-3m",
        "watch": ("Chênh lệch giá SJC so với giá thế giới, hằng tuần.", "The SJC price gap to the world price, weekly."),
        "precedents": [
            P(("NHNN bán vàng miếng bình ổn qua 4 ngân hàng quốc doanh (06/2024)", "The State Bank sells gold bars through 4 state-owned banks (06/2024)"),
              ("Giá vàng SJC giảm từ 85,95 triệu xuống 76,98 triệu/lượng trong tháng 6/2024; chênh lệch thu hẹp mạnh trong vài tuần.",
               "The SJC price fell from 85.95 mn to 76.98 mn per tael in June 2024; the gap narrowed sharply within weeks."),
              ("NHNN trực tiếp cung vàng; lần này là sửa nghị định.", "The State Bank sold directly; this time a decree is amended."),
              ("Chuỗi giá SJC trong kho dữ liệu thị trường", "The SJC price series in the market data store")),
            P(("Nghị định 24/2012 về quản lý kinh doanh vàng", "Decree 24/2012 on the gold trade"),
              ("Chênh lệch giá trong nước và thế giới nới rộng trong nhiều năm sau đó.", "The domestic–world gap widened for years after."),
              ("Chính sách lúc đó theo hướng siết cung.", "That policy restricted supply.")),
        ],
    },
    "P10": {
        "event_type": "crypto_framework",
        "channels": ["pháp lý"],
        "mechanism": ("Khung pháp lý mới mở kênh đầu tư hợp pháp: tài sản số đang tự giữ có thể chuyển sang sàn được cấp phép.",
                      "A new legal framework opens a lawful channel: self-held digital assets may move to a licensed exchange."),
        "targets": ["asset:crypto"],
        "direction": "positive",
        "changes": ["thủ tục", "thanh khoản"],
        "timeframe": "1-3m",
        "watch": ("Danh sách sàn được cấp phép và điều kiện mở tài khoản.", "The list of licensed exchanges and the account rules."),
        "precedents": [],
    },
    "P11": {
        "event_type": "fx_transfer_rule",
        "channels": ["tỷ giá", "pháp lý"],
        "mechanism": ("Hạn mức và thủ tục chuyển tiền cho du học sinh thay đổi, ảnh hưởng chi phí và thời điểm chuyển tiền.",
                      "Limits and steps for students' transfers change, affecting the cost and timing of transfers."),
        "targets": ["plan:study_abroad"],
        "direction": "negative",
        "changes": ["chi phí", "thủ tục"],
        "timeframe": "1-3m",
        "watch": ("Dự thảo thông tư ngoại hối của NHNN.", "The State Bank's draft foreign-exchange circular."),
        "precedents": [],
    },
    "P12": {
        "event_type": "pit_relief",
        "channels": ["thuế/phí"],
        "mechanism": ("Mức giảm trừ gia cảnh tăng làm giảm thuế thu nhập cá nhân phải nộp mỗi tháng.", "Higher family allowances cut the income tax due each month."),
        "targets": ["income:salary"],
        "direction": "positive",
        "changes": ["dòng tiền"],
        "timeframe": "1m",
        "watch": ("Bảng lương tháng đầu áp dụng mức mới.", "The first payslip at the new allowance."),
        "precedents": [
            P(("Nghị quyết 954/2020 nâng mức giảm trừ gia cảnh (kỳ tính thuế 2020)", "Resolution 954/2020 raises family allowances (tax year 2020)"),
              ("Mức giảm trừ bản thân tăng từ 9 lên 11 triệu, người phụ thuộc từ 3,6 lên 4,4 triệu; thuế phải nộp hằng tháng giảm tương ứng.",
               "The personal allowance rose from 9 to 11 mn and each dependant's from 3.6 to 4.4 mn; the monthly tax fell to match."),
              ("Mức tăng lần này lớn hơn.", "This rise is larger."),
              ("Nghị quyết 954/2020/UBTVQH14", "Resolution 954/2020/UBTVQH14")),
        ],
        "certain_from": ("từ kỳ tính thuế 2026", "from the 2026 tax year"),
    },
    "P13": {
        "event_type": "insurance_rule",
        "channels": ["pháp lý", "tâm lý thị trường"],
        "mechanism": ("Quy định chặt hơn về bán và hủy hợp đồng bảo hiểm liên kết đầu tư; giá trị hoàn lại khi hủy sớm có thể thấp.",
                      "Stricter rules on selling and cancelling unit-linked insurance; the surrender value on early exit may be low."),
        "targets": ["asset:insurance"],
        "direction": "negative",
        "changes": ["giá", "thủ tục"],
        "timeframe": "1-3m",
        "watch": ("Thông tư hướng dẫn và biểu phí hủy hợp đồng của hãng bảo hiểm.", "The guiding circular and the insurer's surrender charges."),
        "precedents": [
            P(("Khủng hoảng niềm tin bảo hiểm liên kết đầu tư sau kết luận thanh tra (2023)", "The loss of trust in unit-linked insurance after the 2023 inspection findings"),
              ("Doanh thu hợp đồng mới giảm mạnh; nhiều khách hủy hợp đồng và chịu phí hủy.", "New business fell sharply; many clients cancelled and paid surrender charges."),
              ("Lần đó là sự cố bán hàng; lần này là quy định mới.", "That was a mis-selling scandal; this is a new rule.")),
        ],
    },
    "P14": {
        "event_type": "global_min_tax",
        "channels": ["thuế/phí"],
        "mechanism": ("Doanh nghiệp thuộc tập đoàn đa quốc gia lớn nộp bổ sung đến mức 15%, lợi nhuận sau thuế giảm.",
                      "Firms in large multinational groups pay a top-up to 15%; after-tax profit falls."),
        "targets": ["asset:business"],
        "direction": "negative",
        "changes": ["dòng tiền"],
        "timeframe": ">3m",
        "watch": ("Tờ khai thuế bổ sung năm đầu áp dụng.", "The first year's top-up tax return."),
        "precedents": [],
    },
    "M01": {
        "event_type": "sbv_rate_hike",
        "channels": ["lãi suất", "tín dụng"],
        "mechanism": ("Lãi suất điều hành tăng làm lãi vay thả nổi tăng ở kỳ điều chỉnh tới và giá trái phiếu đang giữ giảm.",
                      "A higher policy rate raises floating loan rates at the next reset and lowers the price of bonds held."),
        "targets": ["loan:floating", "asset:bond"],
        "direction": "negative",
        "changes": ["chi phí", "giá"],
        "timeframe": "1m",
        "watch": ("Thông báo lãi suất của NHNN và lãi suất cơ sở của ngân hàng cho vay.", "The State Bank's rate notices and the lender's base rate."),
        "precedents": [
            P(("NHNN tăng lãi suất điều hành 1 điểm % (22/09/2022)", "The State Bank raises its policy rates by 1 point (22/09/2022)"),
              ("VN-Index từ 1.214,7 xuống 1.126,1 điểm sau một tuần; lãi vay mua nhà tăng trong các tháng sau.",
               "The VN-Index went from 1,214.7 to 1,126.1 a week later; mortgage rates rose in the following months."),
              ("Năm 2022 có thêm sức ép tỷ giá và khủng hoảng trái phiếu doanh nghiệp.", "2022 also had currency pressure and the corporate bond crisis."),
              ("Chuỗi VN-Index trong kho dữ liệu thị trường", "The VN-Index series in the market data store")),
            P(("NHNN tăng lãi suất điều hành lần hai, 1 điểm % (24/10/2022)", "The State Bank's second 1-point rise (24/10/2022)"),
              ("VN-Index tăng từ 986,2 lên 1.027,9 điểm sau một tuần, rồi xuống 911,9 điểm ngày 15/11/2022.",
               "The VN-Index rose from 986.2 to 1,027.9 a week later, then fell to 911.9 on 15/11/2022."),
              ("Thị trường đã giảm sâu trước đó.", "The market had already fallen a long way."),
              ("Chuỗi VN-Index trong kho dữ liệu thị trường", "The VN-Index series in the market data store")),
        ],
        "certain_from": ("từ kỳ điều chỉnh lãi tới", "from the next rate reset"),
    },
    "M02": {
        "event_type": "usd_vnd_rise",
        "channels": ["tỷ giá"],
        "mechanism": ("Tỷ giá USD/VND tăng làm khoản chi bằng ngoại tệ sắp tới tốn thêm tiền đồng.", "A higher USD/VND rate makes upcoming foreign-currency payments cost more dong."),
        "targets": ["plan:study_abroad", "plan:emigrate", "plan:support_abroad", "plan:invest_abroad", "plan:property_abroad"],
        "direction": "negative",
        "changes": ["chi phí"],
        "timeframe": "1w",
        "watch": ("Tỷ giá trung tâm và tỷ giá ngân hàng niêm yết.", "The central rate and the rate the bank posts."),
        "precedents": [
            P(("Tỷ giá USD/VND năm 2022", "USD/VND in 2022"),
              ("Từ 22.640 cuối 2021 lên đỉnh 24.660 ngày 11/11/2022, rồi về 23.410 cuối năm.", "From 22,640 at end-2021 to a 24,660 peak on 11/11/2022, then 23,410 at year end."),
              ("Năm 2022 Fed tăng lãi suất nhanh nhất trong nhiều thập kỷ.", "In 2022 the Fed raised rates at its fastest pace in decades."),
              ("Chuỗi USD/VND trong kho dữ liệu thị trường", "The USD/VND series in the market data store")),
        ],
    },
    "M03": {
        "event_type": "fed_hike",
        "branch": "statistics",
        "stat": {"series": "VNINDEX", "series_label": "VN-Index", "timeframe": "1w"},
        "channels": ["lãi suất", "dòng vốn"],
        "mechanism": ("Fed tăng lãi suất làm đồng USD mạnh lên, dòng vốn có xu hướng rút khỏi thị trường mới nổi.",
                      "A Fed hike strengthens the dollar; money tends to leave emerging markets."),
        "targets": ["asset:stock", "asset:fund"],
        "direction": "negative",
        "changes": ["giá"],
        "timeframe": "1w",
        "watch": ("Quyết định của FOMC và dòng tiền khối ngoại trên HOSE tuần sau đó.", "The FOMC decision and net foreign flows on HOSE the week after."),
        "precedents": [],
    },
    "I01": {
        "event_type": "metro_line",
        "channels": ["cung/cầu"],
        "mechanism": ("Tuyến metro vận hành làm căn hộ gần ga dễ cho thuê và dễ bán hơn: giá thuê tăng trước, giá bán sau.",
                      "A running metro line makes flats near stations easier to let and sell: rents rise first, prices later."),
        "targets": ["area:thao_dien"],
        "direction": "positive",
        "changes": ["giá", "thanh khoản"],
        "timeframe": ">3m",
        "watch": ("Giá thuê và lượng giao dịch quanh các ga.", "Rents and the number of deals around the stations."),
        "precedents": [
            P(("Tuyến Cát Linh – Hà Đông vận hành (Hà Nội, 11/2021)", "The Cat Linh – Ha Dong line opens (Hanoi, 11/2021)"),
              ("Mặt bằng giá căn hộ quanh các ga tăng sau khi tuyến chạy.", "Flat prices around the stations rose after the line opened."),
              ("Tuyến trên cao, đi qua khu đã đông dân.", "An elevated line through areas already crowded.")),
            P(("Bangkok: BTS (1999) và MRT (2004)", "Bangkok: BTS (1999) and MRT (2004)"),
              ("Căn hộ cách ga khoảng 500 m có giá bán và giá thuê cao hơn rõ rệt so với khu xa ga; dự án mới dồn về dọc tuyến.",
               "Flats within about 500 m of a station sell and let for clearly more than those further away; new projects cluster along the lines."),
              ("Thu nhập, mật độ dân và luật sở hữu nhà khác Việt Nam: chỉ tham khảo chiều hướng.", "Incomes, density and ownership law differ from Vietnam: the direction only.")),
        ],
    },
    "I02": {
        "event_type": "airport",
        "channels": ["cung/cầu"],
        "mechanism": ("Sân bay khai thác kéo việc làm và hạ tầng về khu vực, nhu cầu nhà đất quanh đó có thể tăng.",
                      "An operating airport brings jobs and roads to the area; demand for property around it may rise."),
        "targets": ["area:long_thanh"],
        "direction": "positive",
        "changes": ["giá", "thanh khoản"],
        "timeframe": ">3m",
        "watch": ("Ngày khai thác thương mại và số chuyến bay thực tế.", "The commercial opening date and the actual number of flights."),
        "precedents": [
            P(("Sân bay Vân Đồn khai thác (Quảng Ninh, 12/2018)", "Van Don airport opens (Quang Ninh, 12/2018)"),
              ("Giá đất quanh khu vực tăng nóng trước khi khai thác, rồi trầm lắng khi lượng khách thấp.", "Land prices around it jumped before opening, then went quiet when passenger numbers stayed low."),
              ("Long Thành là sân bay chính của vùng, quy mô lớn hơn nhiều.", "Long Thanh is the region's main airport, far larger.")),
        ],
    },
    "I03": {
        "event_type": "ring_road",
        "channels": ["cung/cầu"],
        "mechanism": ("Đường vành đai rút ngắn thời gian đi lại, khu dọc tuyến dễ cho thuê và dễ bán hơn.", "A ring road shortens trips; areas along it get easier to let and sell."),
        "targets": ["area:vinhomes_grand_park"],
        "direction": "positive",
        "changes": ["giá", "thanh khoản"],
        "timeframe": ">3m",
        "watch": ("Tiến độ thông xe từng đoạn.", "When each section opens."),
        "precedents": [],
    },
    # Ví dụ 4: the news is about money laundering; nothing the client or the RM reads may say so (FR-604)
    "P15": {
        "event_type": "outbound_transfer_control",
        "headline": ("Tin về rửa tiền qua kênh chuyển tiền ra nước ngoài", "News on money laundering through outbound transfers"),
        "channels": ["pháp lý"],
        "mechanism": ("Có thể dẫn đến thắt chặt thủ tục chuyển tiền ra nước ngoài.", "May lead to tighter steps for sending money abroad."),
        "targets": ["plan:study_abroad", "plan:emigrate", "plan:support_abroad"],
        "direction": "negative",
        "changes": ["thủ tục"],
        "timeframe": "1-3m",
        "watch": ("Dự thảo thông tư của NHNN về ngoại hối.", "The State Bank's draft foreign-exchange circular."),
        "precedents": [],
        "client_message": ("Việc chuyển tiền ra nước ngoài cho kế hoạch của gia đình có thể cần thêm thời gian và giấy tờ; nên chuẩn bị trước tháng {milestone}.",
                           "Sending money abroad for the family's plan may need more time and papers; best to prepare before {milestone}."),
        "rm_hint": ("Rà giấy tờ chứng minh mục đích chuyển tiền (thư nhập học, hóa đơn học phí) cùng khách.", "Go over the papers that prove the transfer's purpose (admission letter, tuition invoice) with the client."),
        "documents": [("Thư nhập học hoặc giấy tờ mục đích", "Admission letter or proof of purpose"), ("Hóa đơn học phí, chi phí", "Tuition or cost invoice")],
        "prep_weeks": 8,
    },
}

# phrases the page shows from the catalogue (src/evidence/catalogue.py)
CATALOGUE_EN = {
    "Fed tăng lãi suất": "Fed raises rates", "Fed giảm lãi suất": "Fed cuts rates", "NHNN tăng lãi suất điều hành": "State Bank raises policy rates",
    "NHNN giảm lãi suất điều hành": "State Bank cuts policy rates", "Loại mới": "New type", "Chính sách vàng miếng": "Gold bar policy",
    "lãi suất": "interest rates", "tín dụng": "credit", "tỷ giá": "exchange rate", "thuế/phí": "taxes/fees", "pháp lý": "legal",
    "cung/cầu": "supply/demand", "dòng vốn": "capital flows", "tâm lý thị trường": "market sentiment",
    "giá": "price", "dòng tiền": "cash flow", "chi phí": "cost", "thanh khoản": "liquidity", "thủ tục": "procedure",
    "Tích cực": "Positive", "Tiêu cực": "Negative", "Chưa rõ": "Unclear",
    "1–3 tháng": "1–3 months", "trên 3 tháng": "over 3 months", "Trên 3 tháng": "Over 3 months",
    # the event types
    "Thuế với người sở hữu nhiều bất động sản": "Tax on owners of several properties", "Thuế chuyển nhượng bất động sản": "Property transfer tax",
    "Bảng giá đất": "Land price table", "Chính sách riêng một ngành": "A single-sector policy", "Giới hạn sở hữu cổ phần": "Shareholding cap",
    "Điều kiện người mua trái phiếu doanh nghiệp": "Who may buy corporate bonds", "Thuế giao dịch chứng khoán": "Securities trading tax",
    "Khung pháp lý tài sản mã hóa": "Crypto-asset legal framework", "Quy định ngoại hối, chuyển tiền": "Foreign-exchange and transfer rules",
    "Giảm trừ thuế thu nhập cá nhân": "Personal income tax allowance", "Quy định bảo hiểm liên kết đầu tư": "Investment-linked insurance rules",
    "Thuế tối thiểu toàn cầu": "Global minimum tax", "Tỷ giá USD/VND tăng": "USD/VND rises", "Tuyến metro vận hành": "A metro line opens",
    "Sân bay mới khai thác": "A new airport opens", "Đường vành đai hoàn thành": "A ring road opens",
    "Kiểm soát chuyển tiền ra nước ngoài": "Controls on sending money abroad",
    # the target labels (§7): kinds and values
    "Kế hoạch: {0}": "Plan: {0}", "Khoản vay: {0}": "Loan: {0}", "Ngành: {=0}": "Sector: {0}", "Mã: {=0}": "Ticker: {0}",
    "Khu vực BĐS: {=0}": "Property area: {0}", "Thu nhập: {0}": "Income: {0}",
    "cổ phiếu": "shares", "chứng chỉ quỹ": "fund units", "trái phiếu": "bonds", "vàng": "gold", "tiền gửi": "deposits", "tiền mặt": "cash",
    "bất động sản": "property", "cổ phần tư nhân": "private equity", "bảo hiểm": "insurance", "tiền số": "crypto",
    "lãi thả nổi": "floating rate", "ngoại tệ": "foreign currency", "lương": "salary", "cổ tức": "dividends", "tiền thuê": "rent",
    # §8.2's evidence label
    "1 tiền lệ": "1 precedent", "{0} tiền lệ": "{0} precedents", "qua {0}": "via {0}", "{0}/{1} lần": "{0}/{1} times",
    # the statistics sentence (evidence/_stats.py) and the CIO's notes (evidence/frames.py, _check.py)
    "Trong {0} lần {1} từ {2}, {3} giảm trong {4} sau đó {5} lần ({6}), so với {7} ở {8} bất kỳ. Trung vị {9}, dao động {10} đến {11}.":
        "{1}: {0} times since {2}. {3} fell in the {4} after on {5} of them ({6}), against {7} in any {8}. Median {9}, range {10} to {11}.",
    "Trong {0} lần {1} từ {2}, {3} tăng trong {4} sau đó {5} lần ({6}), so với {7} ở {8} bất kỳ. Trung vị {9}, dao động {10} đến {11}.":
        "{1}: {0} times since {2}. {3} rose in the {4} after on {5} of them ({6}), against {7} in any {8}. Median {9}, range {10} to {11}.",
    "Chưa đo được lần {0} nào trên {1}.": "No {0} measured on {1} yet.",
    "Chỉ có {0} tiền lệ đo được (cần {1}): đi nhánh định tính.": "Only {0} precedents measured ({1} needed): the qualitative branch.",
    "Agent ghi {0}, thống kê cho {1}: giữ chiều hướng của thống kê.": "The agent wrote {0}, the statistics give {1}: the statistics' direction is kept.",
    # the alerts the two new rules write (impact/_rules.py: plans, stat) and their news (scripts/make_factors.py)
    "Kế hoạch chuyển tiền ra nước ngoài ({=0}): thủ tục có thể lâu hơn và cần thêm giấy tờ; không ảnh hưởng giá tài sản.":
        "Plan to send money abroad ({0}): the steps may take longer and need more papers; asset prices are not affected.",
    "{0} cổ phiếu, chứng chỉ quỹ: sau các lần Fed tăng lãi suất trước đây, VN-Index thường giảm trong tuần sau đó (xem bằng chứng).":
        "{0} in shares and fund units: after past Fed rate hikes, the VN-Index usually fell in the week after (see the evidence).",
    "Việc chuyển tiền ra nước ngoài cho kế hoạch của gia đình có thể cần thêm thời gian và giấy tờ; nên chuẩn bị trước tháng {0}.":
        "Sending money abroad for the family's plan may need more time and papers; best prepared before {0}.",
}  # fmt: skip


def _split(v: Any, en: Dict[str, str]) -> Any:
    """The Vietnamese of a (vi, en) pair, its English noted; lists and dicts walked."""
    if isinstance(v, tuple):
        en[v[0]] = v[1]
        return v[0]
    if isinstance(v, list):
        return [_split(x, en) for x in v]
    if isinstance(v, dict):
        return {k: _split(x, en) for k, x in v.items()}
    return v


# Each precedent's article or document, checked to load (business feedback 2026-10-29: a link to what was read, never
# a search); a precedent missing here has no link.
PRECEDENT_URLS = {
    "Singapore tăng thuế mua nhà thêm (ABSD) và siết tỷ lệ vay (01/2013)": "https://www.mas.gov.sg/news/media-releases/2013/additional-measures-to-ensure-a-stable-and-sustainable-property-market",
    "Pakistan được MSCI nâng hạng lên thị trường mới nổi (hiệu lực 06/2017)": "https://www.pakistantoday.com.pk/2016/06/15/msci-upgrades-pakistan-to-emerging-markets-status",
    "Ả Rập Xê Út vào nhóm mới nổi của FTSE Russell và MSCI (2019)": "https://oxfordbusinessgroup.com/articles-interviews/saudi-arabia-adds-securities-to-major-stock-market-indices",
    "Bangkok: BTS (1999) và MRT (2004)": "https://en.wikipedia.org/wiki/Rail_transport_in_Bangkok",
    "TP.HCM áp dụng bảng giá đất điều chỉnh (10/2024)": "https://vneconomy.vn/tp-hcm-cong-bo-bang-gia-dat-moi-ap-dung-den-het-nam-2025.htm",
    "Nghị định 65/2022 siết phát hành trái phiếu doanh nghiệp riêng lẻ (09/2022)": "https://vanban.chinhphu.vn/?pageid=27160&docid=206561",
    "NHNN bán vàng miếng bình ổn qua 4 ngân hàng quốc doanh (06/2024)": "https://www.sggp.org.vn/4-ngan-hang-va-1-doanh-nghiep-se-ban-vang-mieng-ra-thi-truong-tu-ngay-3-6-post742667.html",
    "Nghị định 24/2012 về quản lý kinh doanh vàng": "https://vanban.chinhphu.vn/?pageid=27160&docid=157073",
    "Nghị quyết 954/2020 nâng mức giảm trừ gia cảnh (kỳ tính thuế 2020)": "https://luatvietnam.vn/tin-van-ban-moi/tang-muc-giam-tru-gia-canh-thue-tncn-186-25423-article.html",
    "Khủng hoảng niềm tin bảo hiểm liên kết đầu tư sau kết luận thanh tra (2023)": "https://tuoitre.vn/bo-tai-chinh-da-co-ket-luan-thanh-tra-4-cong-ty-bao-hiem-nhan-tho-20230616144044099.htm",
    "NHNN tăng lãi suất điều hành 1 điểm % (22/09/2022)": "https://www.sggp.org.vn/ngan-hang-nha-nuoc-tang-lai-suat-dieu-hanh-post652216.html",
    "NHNN tăng lãi suất điều hành lần hai, 1 điểm % (24/10/2022)": "https://tuoitre.vn/plo/ngan-hang-nha-nuoc-tiep-tuc-tang-lai-suat-dieu-hanh-109704701.htm",
    "Tỷ giá USD/VND năm 2022": "https://www.vietnamplus.vn/nhin-lai-mot-nam-cstt-2022-ban-linh-duong-dau-voi-song-lon-post842246.vnp",
    "Tuyến Cát Linh – Hà Đông vận hành (Hà Nội, 11/2021)": "https://nhandan.vn/ngay-611-chinh-thuc-khai-thac-thuong-mai-tuyen-duong-sat-cat-linh-ha-dong-post672501.html",
    "Sân bay Vân Đồn khai thác (Quảng Ninh, 12/2018)": "https://diendandoanhnghiep.vn/khanh-thanh-san-bay-van-don-cang-hang-khong-bot-dau-tien-tai-viet-nam-10053836.html",
}  # fmt: skip


def main() -> None:
    en: Dict[str, str] = dict(CATALOGUE_EN)
    frames = {}
    for fid, f in FRAMES.items():
        frames[fid] = {"factor": fid, "branch": f.get("branch", "qualitative"), **_split(f, en)}
        for p in frames[fid].get("precedents") or []:
            p["url"] = PRECEDENT_URLS.get(p["event"])
    OUT.write_text(json.dumps({"as_of": "2026-10-28", "events": EVENTS, "frames": frames}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    body = ",\n".join(f"{json.dumps(k, ensure_ascii=False)}:{json.dumps(v, ensure_ascii=False)}" for k, v in sorted(en.items()))
    EN.write_text(
        "/* Vietnamese → English for the evidence frames (written by scripts/make_evidence.py; edit the script, not this). */\n"
        f"export default {{\n{body}\n}};\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
