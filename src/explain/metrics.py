"""Every metric, grouped by the page that shows it; each formula is written from the function named in ``code``."""

from __future__ import annotations

from explain.catalogue import metric

# filled page by page (G1)

D = "src/dashboard/ops.py::"
# ── the dashboard: Toàn cảnh, Chi tiết, Bản đồ ───────────────────────────────────────────────────────────
metric(
    "holding.value",
    "Giá trị một khoản",
    "Giá trị hôm nay = số lượng × giá ngày định giá (cổ phiếu, quỹ, vàng, "
    "tiền số), diện tích × giá m² của khu vực (bất động sản), số dư (tiền, tiền gửi, nợ) — theo nguồn đã kết nối "
    "hoặc đã khai báo. Nợ là số còn phải trả.",
    "src/wealth/valuation.py::holding",
    source="Nguồn",
    price_date="Giá ngày",
    qty="Số lượng",
    price="Giá",
)
metric(
    "holding.share",
    "Tỷ trọng một khoản",
    "Tỷ trọng = giá trị khoản ÷ tổng tài sản (không gồm nợ).",
    "web/pages/pulse.js::openGroup",
    value="Giá trị khoản",
    assets="Tổng tài sản",
)
metric(
    "net_worth",
    "Tài sản ròng",
    "Tài sản ròng = tổng giá trị tài sản − tổng nợ, giá ngày định giá.",
    D + "net_worth",
    assets="Tổng tài sản",
    liabilities="Tổng nợ",
)
metric(
    "assets.total",
    "Tổng tài sản",
    "Tổng tài sản = cộng giá trị hôm nay của mọi khoản là tài sản (không trừ nợ).",
    D + "net_worth",
    count="Số khoản",
)
metric(
    "liabilities.total",
    "Tổng nợ",
    "Tổng nợ = cộng số còn phải trả của mọi khoản vay và dư nợ thẻ.",
    D + "net_worth",
    count="Số khoản",
)
metric(
    "net_worth.month_change",
    "Thay đổi tài sản ròng trong tháng",
    "Thay đổi = tài sản ròng hôm nay − tài sản ròng "
    "tháng trước; tháng trước = tổng giá trị tài sản một tháng trước − nợ hôm nay. Phần trăm = thay đổi ÷ tài sản "
    "ròng tháng trước.",
    D + "net_worth",
    now="Tài sản ròng hôm nay",
    prev="Tài sản ròng tháng trước",
)
metric(
    "class.month_change",
    "Thay đổi trong tháng của một nhóm",
    "Thay đổi của nhóm = Σ (giá trị hôm nay − giá trị "
    "một tháng trước) của các khoản trong nhóm; với nợ, nợ tăng làm tài sản ròng giảm.",
    "web/pages/pulse.js::render",
    group="Nhóm",
    count="Số khoản",
)
metric(
    "class.value",
    "Giá trị một nhóm tài sản",
    "Giá trị nhóm = cộng giá trị hôm nay các khoản thuộc nhóm (tiền mặt gộp với tiền gửi).",
    D + "allocation",
    count="Số khoản",
)
metric(
    "class.share",
    "Tỷ trọng một nhóm",
    "Tỷ trọng = giá trị nhóm ÷ tổng tài sản.",
    D + "allocation",
    value="Giá trị nhóm",
    assets="Tổng tài sản",
)
metric(
    "liquidity.value",
    "Thanh khoản dự phòng",
    "Thanh khoản = tiền mặt + tiền gửi + quỹ thị trường tiền tệ và quỹ "
    "trái phiếu rút được ngay + trái phiếu chính phủ: tiền có được trong vài ngày.",
    D + "liquidity",
    count="Số khoản",
)
metric(
    "liquidity.months",
    "Số tháng chi tiêu dự phòng",
    "Số tháng = thanh khoản ÷ chi tiêu mỗi tháng. Từ 6 tháng: an toàn; 3–6: thấp; dưới 3: rất thấp.",
    D + "liquidity",
    value="Thanh khoản",
    spending="Chi mỗi tháng",
)
metric(
    "liquidity.share",
    "Thanh khoản trên tổng tài sản",
    "Tỷ lệ = thanh khoản ÷ tổng tài sản.",
    "web/pages/pulse.js::render",
    value="Thanh khoản",
    assets="Tổng tài sản",
)
metric(
    "spending.monthly",
    "Chi tiêu mỗi tháng",
    "Chi tiêu mỗi tháng theo hồ sơ khách hàng (cộng các thành viên khi xem cả gia đình).",
    "src/wealth/profile.py::build",
)
metric(
    "risk.current",
    "Sụt giảm ước tính khi thị trường xấu",
    "Sụt giảm = Σ (giá trị khoản × mức giảm khi căng thẳng "
    "của loại khoản đó) ÷ tài sản ròng. Mức giảm: cổ phiếu = mức nền × beta; trái phiếu, bất động sản, vàng, quỹ, "
    "tiền số theo bảng căng thẳng của thị trường.",
    D + "drawdown",
    loss="Mất trong kịch bản xấu",
    net_worth="Tài sản ròng",
)
metric(
    "risk.loss",
    "Mất trong kịch bản xấu",
    "Mất = Σ giá trị khoản × mức giảm khi căng thẳng của khoản đó.",
    D + "drawdown",
)
metric(
    "risk.limit",
    "Ngưỡng sụt giảm chấp nhận",
    "Ngưỡng theo bài kiểm tra khẩu vị rủi ro gần nhất, nếu chưa có thì "
    "theo hồ sơ khách hàng (một thiết lập, không phải kết quả tính).",
    "src/wealth/profile.py::build",
)
metric(
    "flow.in",
    "Tiền vào trong tháng",
    "Tiền vào = cộng mọi giao dịch ghi có trong tháng (chỉ giao dịch tài khoản).",
    "src/flows/ops.py::month_flows",
    rows="Số giao dịch",
)
metric(
    "flow.out",
    "Tiền ra trong tháng",
    "Tiền ra = cộng mọi giao dịch ghi nợ trong tháng.",
    "src/flows/ops.py::month_flows",
    rows="Số giao dịch",
)
metric(
    "flow.left",
    "Còn lại / thiếu hụt trong tháng",
    "Còn lại = tiền vào − tiền ra trong tháng; âm là thiếu hụt.",
    "src/flows/ops.py::month_flows",
    total_in="Tiền vào",
    total_out="Tiền ra",
)
metric(
    "flow.band",
    "Một nhóm thu hoặc chi",
    "Nhóm = cộng các giao dịch cùng loại (lương, sinh hoạt, trả nợ…) trong "
    "tháng; bấm nhóm trên biểu đồ để xem từng giao dịch.",
    "src/flows/ops.py::_side",
    rows="Số giao dịch",
)
metric(
    "flow.saving_rate",
    "Tỷ lệ để dành",
    "Tỷ lệ = (tiền vào − tiền ra) ÷ tiền vào của tháng.",
    "web/pages/pulse.js::drawRatios",
    left="Còn lại",
    total_in="Tiền vào",
)
metric(
    "flow.out_in",
    "Tiền ra trên tiền vào",
    "Tỷ lệ = tiền ra ÷ tiền vào của tháng.",
    "web/pages/pulse.js::drawRatios",
    total_out="Tiền ra",
    total_in="Tiền vào",
)
metric(
    "transaction.amount",
    "Một giao dịch",
    "Số tiền của giao dịch như sao kê tài khoản ghi (không tính lại).",
    "src/flows/ops.py::month_flows",
    date="Ngày",
    source="Nguồn",
)
metric(
    "goal.need",
    "Số tiền mục tiêu cần",
    "Cần = chi phí của mục tiêu theo giả định của trang Kế hoạch (học phí, "
    "nghỉ hưu, mua nhà…), quy về thời điểm cần tiền.",
    "src/scenarios/_sim.py::goal",
)
metric(
    "goal.have",
    "Nguồn đã có cho mục tiêu",
    "Đã có = phần tài sản dành được cho mục tiêu theo quy tắc của mục tiêu "
    "đó (thanh khoản ngoài 6 tháng chi tiêu, dự phòng dùng được, hoặc dự kiến có lúc nghỉ hưu).",
    "src/scenarios/_sim.py::goal",
)
metric(
    "goal.gap",
    "Còn thiếu cho mục tiêu",
    "Còn thiếu = cần − đã có; âm là đã đủ.",
    "src/scenarios/_sim.py::goal",
    need="Cần",
    have="Đã có",
)
metric(
    "goal.progress",
    "Tiến độ mục tiêu",
    "Tiến độ = đã có ÷ cần, tối đa 100%.",
    "src/scenarios/_sim.py::goal",
    need="Cần",
    have="Đã có",
)
metric(
    "impact.expected_3m",
    "Tác động kỳ vọng 3 tháng",
    "Tác động kỳ vọng = Σ theo kịch bản CIO duyệt (xác suất × Σ "
    "theo khoản: giá trị × độ nhạy với từng yếu tố × biến động của yếu tố); mở “Cách tính” của sự kiện ở trang Tác "
    "động thị trường để xem từng kịch bản.",
    "src/apply/run.py::compute",
    event="Sự kiện",
)
metric(
    "impact.band",
    "Một mốc của dải kết quả",
    "Kỳ vọng = trung bình theo xác suất các kịch bản; P5, P10, P50, P90 = "
    "các mốc của phân bố kết quả (5%, 10%, 50%, 90% khả năng thấp hơn), tính từ độ biến động và tương quan giữa các "
    "yếu tố trong mô hình đã duyệt, cộng theo từng kịch bản.",
    "src/engine/scenario.py::evaluate",
    stat="Mốc",
    horizon="Kỳ hạn",
    event="Sự kiện",
)
metric(
    "impact.by_class",
    "Đóng góp của một phần",
    "Đóng góp = Σ theo kịch bản (xác suất × Σ các khoản thuộc phần này: "
    "giá trị × độ nhạy với từng yếu tố × biến động của yếu tố). Các phần cộng lại bằng tác động kỳ vọng.",
    "src/engine/scenario.py::evaluate",
    part="Phần",
    event="Sự kiện",
)
metric(
    "policy.impact",
    "Tác động ước tính của một chính sách",
    "Tác động = mức chịu tác động (giá trị các khoản bị "
    "chạm tới) × độ nhạy (phần giá trị dịch chuyển theo quy tắc của chính sách: thuế, phí, vùng dự án) × xác suất "
    "chính sách xảy ra; phần trăm = tác động ÷ tài sản ròng. Quy tắc riêng của từng chính sách, không phải bộ máy "
    "kịch bản (ADR-0007).",
    "src/impact/ops.py::score",
    exposure="Mức chịu tác động",
    sensitivity="Độ nhạy",
    probability="Xác suất",
)
metric(
    "policy.probability",
    "Xác suất của một chính sách",
    "Xác suất theo danh mục chính sách đang theo dõi (trạng "
    "thái dự thảo, lấy ý kiến, đã ban hành…), một thiết lập của danh mục, không phải kết quả tính.",
    "src/impact/ops.py::score",
)
metric(
    "concentration.value",
    "Giá trị tập trung",
    "Giá trị = cộng giá trị các khoản cùng khu vực bất động sản, cùng tổ "
    "chức phát hành hoặc cùng ngành; tỷ trọng = giá trị ÷ tổng tài sản, so với ngưỡng (khu vực 35%, tổ chức 10%, "
    "ngành 20%).",
    "src/dashboard/ops.py::concentration",
    share="Tỷ trọng",
    limit="Ngưỡng",
)
metric(
    "perf.realized_ytd",
    "Lãi/lỗ đã chốt từ đầu năm",
    "Đã chốt = lãi/lỗ của các lệnh bán từ 1/1 theo sao kê chứng khoán (TCBS), cộng các thành viên khi xem cả gia đình.",
    "src/consolidate/ops.py::tcbs",
)
metric(
    "perf.unrealized",
    "Lãi/lỗ chưa chốt",
    "Chưa chốt = Σ (giá trị hôm nay − giá vốn) của cổ phiếu, quỹ, trái "
    "phiếu có giá vốn; phần trăm = chưa chốt ÷ tổng giá vốn.",
    D + "performance",
    cost="Tổng giá vốn",
)
metric(
    "perf.ytd_return",
    "Lợi nhuận từ đầu năm",
    "Lợi nhuận = (giá trị hôm nay − giá trị ngày 1/1) ÷ giá trị ngày 1/1, trên các khoản có giá đầu năm.",
    D + "performance",
)
metric(
    "perf.benchmark_ytd",
    "Chỉ số so sánh từ đầu năm",
    "Mức tăng từ đầu năm của chỉ số khách hàng chọn làm chuẩn (theo dữ liệu thị trường ngày định giá).",
    D + "performance",
    benchmark="Chỉ số",
)
metric(
    "perf.vs_benchmark",
    "Chênh lệch với chỉ số",
    "Chênh lệch = lợi nhuận từ đầu năm của danh mục − mức tăng từ đầu năm của chỉ số.",
    D + "performance",
    mine="Danh mục",
    bench="Chỉ số",
)
metric(
    "perf.class",
    "Lãi/lỗ theo loại",
    "Theo loại = Σ (giá trị − giá vốn) của các khoản cùng loại có giá vốn; phần trăm = lãi/lỗ ÷ giá vốn của loại.",
    D + "performance",
    value="Giá trị",
    cost="Giá vốn",
)
metric(
    "class.return",
    "Lãi/lỗ của nhóm so với giá vốn",
    "Lãi/lỗ = (giá trị − giá vốn) ÷ giá vốn, trên các khoản của nhóm có giá vốn; “—” khi chưa có giá vốn.",
    D + "allocation",
    pnl="Lãi/lỗ",
)
metric(
    "tier.value",
    "Tài sản theo tầng nguồn",
    "Tầng = cộng tài sản của các nguồn cùng tầng (hệ sinh thái "
    "Techcombank, lưu ký bên ngoài, tự quản lý); tỷ trọng = tầng ÷ tổng tài sản.",
    "web/pages/detail.js::drawTiers",
    assets="Tổng tài sản",
)
metric(
    "source.net",
    "Giá trị ròng của một nguồn",
    "Ròng = tài sản − nợ mà nguồn này báo; tỷ trọng = tài sản của nguồn ÷ tổng tài sản.",
    "web/pages/detail.js::drawTiers",
)
metric(
    "cashflow.forecast",
    "Dự báo dòng tiền",
    "Dự báo = các khoản định kỳ tìm thấy trong giao dịch (lặp lại ít nhất "
    "3 tháng với số tiền ổn định) + các khoản theo sản phẩm (trả góp khoản vay, dư nợ thẻ trả tháng sau, tiền gửi "
    "đáo hạn, coupon trái phiếu, cổ tức, phí bảo hiểm) + các sự kiện khách hàng đã khai, trong các tháng tới.",
    "src/dashboard/_calendar.py::build",
    months="Số tháng",
)
metric(
    "cashflow.large",
    "Khoản phải trả lớn",
    "Khoản lớn = một khoản dự báo phải trả từ 500 triệu hoặc từ 3 tháng chi tiêu trở lên.",
    D + "cashflow",
    month="Tháng",
)
metric(
    "cashflow.recurring",
    "Khoản định kỳ",
    "Định kỳ = giao dịch cùng nội dung lặp lại ít nhất 3 tháng với số tiền "
    "ổn định; số tiền = mức điển hình của các lần đó.",
    "src/dashboard/_calendar.py::recurring",
)

# ── Tài sản: the book, the statement reader ───────────────────────────────────────────────────────────────
metric(
    "holding.price",
    "Giá ngày định giá",
    "Giá của một đơn vị (cổ phiếu, chứng chỉ quỹ, trái phiếu, lượng vàng) "
    "ngày định giá, từ dữ liệu thị trường; không tính lại.",
    "src/wealth/valuation.py::stock",
    price_date="Giá ngày",
)
metric(
    "holding.buy_price",
    "Giá mua bình quân",
    "Giá mua bình quân một đơn vị như nguồn báo (sao kê, công ty chứng "
    "khoán, quỹ) hoặc khách hàng khai; với bất động sản là số tiền đã bỏ ra khi mua.",
    "src/wealth/valuation.py::stock",
    source="Nguồn",
)
metric(
    "holding.cost",
    "Giá vốn",
    "Giá vốn = số lượng × giá mua bình quân (cổ phiếu, quỹ, trái phiếu), giá mua (bất "
    "động sản) hoặc số tiền gửi (tiền gửi); “—” khi nguồn không cho biết giá mua. Nhóm: cộng giá vốn các khoản có "
    "giá vốn.",
    "src/wealth/valuation.py::stock",
    qty="Số lượng",
    buy_price="Giá mua",
)
metric(
    "holding.pnl",
    "Lãi / lỗ so với giá vốn",
    "Lãi/lỗ = giá trị hôm nay − giá vốn; phần trăm = lãi/lỗ ÷ giá vốn. "
    "Tiền gửi: lãi dồn tích = số tiền gửi × lãi suất × số ngày từ ngày gửi đến ngày định giá ÷ 365. Chưa trừ thuế "
    "phí. Nhóm: cộng các khoản có giá vốn.",
    "web/pages/holdings.js::bookRow",
    value="Giá trị",
    cost="Giá vốn",
    rate="Lãi suất",
    days="Số ngày",
)
metric(
    "holding.terms",
    "Điều khoản của khoản",
    "Lãi suất, coupon, tiền thuê, trả góp, hạn mức, phí bảo hiểm như "
    "hợp đồng mà nguồn báo hoặc khách hàng khai; không tính lại.",
    "src/wealth/valuation.py::declared",
    source="Nguồn",
)
metric(
    "statement.total",
    "Tổng đọc được từ sao kê",
    "Tổng = cộng giá trị hôm nay các khoản đọc được từ tệp sao kê "
    "(giá theo dữ liệu thị trường ngày định giá khi sao kê có mã, số dư khi là tiền gửi).",
    "src/statements/ops.py::save_holdings",
    count="Số khoản",
    institution="Tổ chức",
)

# ── Kế hoạch: goals, decisions, stress tests ─────────────────────────────────────────────────────────────
S = "src/scenarios/_sim.py::"
metric(
    "goal.surplus",
    "Tiền dư mỗi tháng",
    "Tiền dư = thu nhập mỗi tháng − chi tiêu mỗi tháng theo hồ sơ khách hàng.",
    S + "surplus",
)
metric(
    "goals.total",
    "Mục tiêu đã đặt: đang có / cần có",
    "Tỷ lệ = Σ min(đã có, cần) ÷ Σ cần, trên các mục tiêu bạn đang theo dõi.",
    "web/pages/plan.js::drawMini",
    have="Đang có",
    need="Cần có",
    count="Số mục tiêu",
)
metric(
    "goals.saving",
    "Tổng cần để dành cho các mục tiêu",
    "Tổng = Σ mức cần để dành mỗi tháng của các mục tiêu "
    "đang theo dõi còn thiếu; còn dư / thiếu = tiền dư mỗi tháng − tổng đó.",
    "web/pages/plan.js::drawMini",
    surplus="Tiền dư mỗi tháng",
    count="Số mục tiêu còn thiếu",
)
metric(
    "cashflow.net_ahead",
    "Dòng tiền ròng 12 tháng tới",
    "Ròng = Σ tiền vào − Σ tiền ra của 12 tháng dự báo (các khoản định kỳ, theo sản phẩm và sự kiện đã khai).",
    "web/pages/plan.js::drawMini",
    total_in="Tiền vào",
    total_out="Tiền ra",
)
metric(
    "cashflow.past_net",
    "Dòng tiền ròng thực tế bình quân",
    "Bình quân = Σ (tiền vào − tiền ra) ÷ số tháng có giao dịch, trong 12 tháng qua.",
    "web/pages/plan.js::drawMini",
    months="Số tháng",
)
metric(
    "scenario.state",
    "Trước / sau kịch bản",
    "Trước = tài sản ròng, thanh khoản và số tháng đủ chi hôm nay; sau = "
    "các số đó sau khi áp kịch bản với các giả định đang chọn (khoản chi, khoản bán, mức giảm giá của stress test). "
    "Thay đổi = sau − trước.",
    "src/scenarios/ops.py::_run",
    scenario="Kịch bản",
)
metric(
    "scenario.line",
    "Một dòng của mô phỏng",
    "Do hàm mô phỏng của kịch bản tính trên chính tài sản của bạn với các "
    "giả định ở trên (đổi giả định rồi Chạy lại để thấy số thay đổi).",
    "src/scenarios/ops.py::_run",
    scenario="Kịch bản",
    line="Dòng",
)
metric(
    "goal.action_cut",
    "Mức giảm chênh lệch của một hành động",
    "Giảm chênh lệch = phần còn thiếu mà hành động này bù "
    "được nếu làm (tiền giải phóng, tiền để dành thêm đến mốc…), tối đa bằng phần còn thiếu.",
    S + "act",
)
metric(
    "track.actual",
    "Nguồn cho mục tiêu: thay đổi thực tế tháng này",
    "Thực tế = nguồn hôm nay − nguồn tháng trước; "
    "phần trăm ÷ nguồn tháng trước. Nguồn = thanh khoản ngoài 6 tháng chi tiêu, hoặc tài sản đầu tư trừ nợ với "
    "mục tiêu nghỉ hưu.",
    S + "track",
    pool="Nguồn",
)
metric(
    "track.expected",
    "Nguồn cho mục tiêu: kỳ vọng",
    "Kỳ vọng tháng = nguồn tháng trước × lãi năm ÷ 12 + để dành "
    "mỗi tháng theo kế hoạch; từ đầu năm = (1 + lãi)^(số tháng ÷ 12) − 1 + để dành × số tháng ÷ nguồn đầu năm.",
    S + "track",
    rate="Lãi năm",
    saving="Để dành mỗi tháng",
)
metric(
    "track.short",
    "Hụt / vượt so với kỳ vọng",
    "Hụt/vượt = thay đổi thực tế − kỳ vọng của tháng.",
    S + "track",
    actual="Thực tế",
    expected="Kỳ vọng",
)
metric(
    "track.point",
    "Nguồn và chênh lệch tại một mốc",
    "Nguồn và chênh lệch mục tiêu tính lại với giá trị tài sản tại "
    "mốc đó (đầu năm, tháng trước, hôm nay); thay đổi = chênh lệch mốc này − mốc trước.",
    S + "track",
    point="Mốc",
)
metric(
    "track.mover",
    "Biến động lớn trong nguồn",
    "Biến động = giá trị hôm nay − giá trị tháng trước của khoản; phần trăm ÷ giá trị tháng trước.",
    S + "track",
)

# ── Chi phí chính sách (client) ──────────────────────────────────────────────────────────────────────────
metric(
    "policy.exposure",
    "Mức chịu tác động",
    "Mức chịu tác động = cộng giá trị hôm nay các khoản mà chính sách chạm "
    "tới (theo loại tài sản, khu vực, ngành hoặc mã trong quy tắc của chính sách).",
    "src/impact/ops.py::score",
    count="Số khoản",
)
metric(
    "policy.sensitivity",
    "Độ nhạy",
    "Độ nhạy = phần giá trị dịch chuyển nếu chính sách xảy ra, theo quy tắc của "
    "chính sách (thuế, phí, chênh lệch giá, vùng dự án…); câu mô tả của mục nêu căn cứ.",
    "src/impact/ops.py::score",
)
metric(
    "policy.net",
    "Tổng tác động của một nhóm tin",
    "Tổng = cộng tác động ước tính (đã tính xác suất) của các mục trong nhóm đang hiển thị.",
    "web/pages/policy.js::drawSections",
    count="Số tin",
)
metric(
    "goals.gap_total",
    "Tổng còn thiếu của các mục tiêu cần chú ý",
    "Tổng = Σ phần còn thiếu của các mục tiêu đang theo dõi chưa đúng tiến độ.",
    "web/pages/policy.js::render",
    count="Số mục tiêu",
)
metric(
    "view.exposure",
    "Phần danh mục liên quan một góc nhìn",
    "Liên quan = cộng giá trị hôm nay các khoản thuộc mã, khu vực hoặc loại tài sản mà góc nhìn nói tới.",
    "web/pages/policy.js::touches",
    count="Số khoản",
)

# ── Tin tác động (client + RM) ───────────────────────────────────────────────────────────────────────────
G = "src/apply/goals.py::"
metric(
    "goal.funding",
    "Mức đáp ứng của mục tiêu",
    "Mức đáp ứng = nguồn dành được cho mục tiêu ÷ số tiền cần. Nguồn lấy "
    "theo thứ tự hạn từ tài sản tài chính (tiền, tiền gửi, quỹ, trái phiếu, cổ phiếu, vàng, tiền số); trước = giá trị "
    "hôm nay, sau = cộng thay đổi kỳ vọng 3 tháng của sự kiện. Mức Đạt / Theo dõi / Thiếu: tiền cần để dành mỗi tháng "
    "÷ thặng dư hằng tháng ≤ 0,6 / ≤ 1 / cao hơn.",
    G + "_fund",
    event="Sự kiện",
)
metric(
    "goal.event_impact",
    "Tác động của sự kiện lên một mục tiêu",
    "Tác động = tác động của cả nhóm tài sản tài chính "
    "(cùng bộ máy, cùng kỳ hạn, kỳ vọng và P5–P90) × phần mục tiêu này đang chiếm trong nhóm trước sự kiện; phần "
    "chưa gắn mục tiêu là phần còn lại.",
    G + "goal_impacts",
    event="Sự kiện",
    stat="Mốc",
)
metric(
    "goal.pool",
    "Nguồn tài sản tài chính cho mục tiêu",
    "Trước = cộng giá trị hôm nay của tiền, tiền gửi, quỹ, trái "
    "phiếu, cổ phiếu, vàng, tiền số; sau = trước + thay đổi kỳ vọng 3 tháng của các khoản đó theo sự kiện.",
    G + "goal_impacts",
    event="Sự kiện",
)
metric(
    "impact.holding",
    "Đóng góp của một vị thế",
    "Đóng góp = Σ theo kịch bản (xác suất × giá trị vị thế × độ nhạy "
    "với từng yếu tố × biến động của yếu tố), cộng các sự kiện đang hiệu lực; bấm để mở dấu vết tính.",
    "src/engine/scenario.py::evaluate",
)

# ── Hiệu quả tư vấn (RM): the advisory track record, sample data (data/advisory.json) ────────────────────
MOCK = " Số liệu là dữ liệu mẫu của bản demo (data/advisory.json), chưa tính từ kết quả thật."
A = "app/web.py::advisory_all"
metric(
    "advisory.hit_rate",
    "Tỷ lệ khuyến nghị đúng",
    "Tỷ lệ = số khuyến nghị đúng ÷ (đúng + sai), trên các khuyến nghị khách hàng đã thực hiện." + MOCK,
    "web/pages/performance.js::tiles",
    right="Đúng",
    wrong="Sai",
)
metric(
    "advisory.value",
    "Giá trị của khuyến nghị",
    "Giá trị = lãi/lỗ của khoản khuyến nghị từ ngày thực hiện đến khi "
    "chốt hoặc đến hôm nay; với khuyến nghị bị bỏ lỡ, là phần đã có thể thêm. Tổng của một nhóm = cộng các khuyến "
    "nghị trong nhóm (đúng, sai, bỏ lỡ)." + MOCK,
    A,
    count="Số khuyến nghị",
)
metric(
    "advisory.missed_news",
    "Tác động của tin bị bỏ lỡ",
    "Tác động = thay đổi giá trị các khoản của khách hàng do "
    "tin đó, khi đã có tín hiệu sớm mà hệ thống không cảnh báo; gộp theo tin trên mọi khách hàng." + MOCK,
    A,
)
metric(
    "advisory.agent_metric",
    "Chỉ số của một AI",
    "Điểm 0–100 và các chỉ số (độ chính xác, độ phủ, thời gian…) của "
    "từng AI trong 12 tháng; điểm chung = trung bình trên các khách hàng." + MOCK,
    A,
)
metric(
    "threshold.pre_review",
    "Ngưỡng RM xem trước",
    "Một thiết lập (Cấu hình → ngưỡng, CIO sửa, có phê duyệt): gia "
    "đình có kịch bản xấu 3 tháng (P10) bằng hoặc thấp hơn ngưỡng này, tính theo tài sản ròng, được đưa vào danh sách "
    "RM xem trước.",
    "src/apply/reads.py::rm_today",
)
metric(
    "impact.p10_3m",
    "Kịch bản xấu 3 tháng (P10)",
    "P10 = mốc 10% của phân bố tác động 3 tháng (10% khả năng thấp "
    "hơn), tính theo tài sản ròng; trong danh sách là sự kiện có P10 xấu nhất của gia đình.",
    "src/engine/scenario.py::evaluate",
    event="Sự kiện",
)
metric(
    "advisory.alerts_opened",
    "Cảnh báo khách hàng đã mở",
    "Tỷ lệ = số cảnh báo khách hàng đã mở ÷ số cảnh báo đã gửi trong 12 tháng." + MOCK,
    A,
)

# ── Đo lường, Agent (CIO, Tuân thủ, Admin) ──────────────────────────────────────────────────────────────
R = "src/measure/reports.py::"
metric(
    "measure.no_edit",
    "Tỷ lệ duyệt không sửa",
    "Tỷ lệ = số nhận định CIO duyệt mà không sửa gì ÷ số nhận định đã duyệt trong tháng, từ nhật ký duyệt.",
    R + "rubber_stamp",
    month="Tháng",
)
metric(
    "measure.on_time",
    "Tỷ lệ đạt thời hạn",
    "Tỷ lệ = số lần trong hạn ÷ số lần đo trong tháng: từ tin sớm nhất đến "
    "lần áp dụng có hiệu lực cho RM ≤ mục tiêu giờ (sự kiện CIO đánh dấu khẩn: ≤ 30 phút); tin → hộp tin và lần chạy "
    "agent CIO ≤ mục tiêu phút.",
    R + "speed",
    month="Tháng",
    step="Bước",
)
metric(
    "news.important_share",
    "Tỷ lệ tin quan trọng được thu thập",
    "Tỷ lệ = số câu chuyện quan trọng đã thu thập ÷ số câu chuyện quan trọng trong ngày. Quan trọng: tiêu đề nhắc một "
    "yếu tố của mô hình và nguồn đối chiếu (Google News, mục Kinh doanh) đưa từ ít nhất 2 báo. Đã thu thập: trong 36 "
    "giờ quanh câu chuyện, Hộp tin có tin có tiêu đề trùng ít nhất 40 % từ (Jaccard, bỏ số và từ đệm) với một tiêu đề "
    "của câu chuyện; chấm một lần, một ngày sau khi câu chuyện xuất hiện. Mục tiêu ≥ 95 %.",
    "src/news/reference.py::coverage",
    period="Ngày",
    important="Tin quan trọng",
    collected="Đã thu thập",
    followed="Có báo đang theo dõi",
)
metric(
    "measure.reviewed_share",
    "Khuyến nghị có người duyệt và nhật ký",
    "Tỷ lệ = khuyến nghị có người duyệt và có nhật ký ÷ khuyến nghị đã đưa ra trong tháng. Khuyến nghị (Đề xuất): lần "
    "áp dụng đã hiệu lực, bản tin đã duyệt, đề xuất của khách RM đã duyệt. Người duyệt là một người trong danh sách nhân "
    "viên, không phải agent hay hệ thống, khác người soạn; nhật ký là các dòng duyệt trong chuỗi nhật ký. Mục tiêu 100 %.",
    "src/measure/reviewed.py::rate",
    month="Tháng",
    recommendations="Khuyến nghị",
    ok="Đủ người duyệt và nhật ký",
)
metric(
    "measure.contact_signal_share",
    "Liên hệ bắt đầu từ tín hiệu hệ thống",
    "Tỷ lệ = số liên hệ RM ghi là bắt đầu từ một tín hiệu ÷ tổng số liên hệ RM ghi trong tháng. Tín hiệu: một dòng ở "
    "Hôm nay (gia đình cần xem trước sau một lần áp dụng, hoặc việc theo mục tiêu do quy định mới), được kiểm khi ghi. "
    "Mục tiêu ≥ 50 %.",
    "src/contacts/store.py::share",
    month="Tháng",
    contacts="Liên hệ",
    from_signal="Từ tín hiệu",
)
metric(
    "measure.alert_open_share",
    "Khách mở cảnh báo mức cao",
    "Tỷ lệ = số cảnh báo mức cao khách đã mở ÷ số cảnh báo mức cao đã đến khách, theo tháng đến. Đến: lần đầu mục mức "
    "cao có trong “Điều đáng chú ý” khi chính khách xem (chuông, Toàn cảnh). Mở: khách bấm mục trong chuông hoặc bằng "
    "chứng của nó. Mục tiêu ≥ 70 %.",
    "src/feed/opens.py::rate",
    month="Tháng gửi",
    delivered="Đã đến khách",
    opened="Khách đã mở",
)
metric(
    "measure.control_effect",
    "Hiệu quả kinh doanh: có và không có công cụ",
    "Chênh lệch = trung bình nhóm có công cụ − trung bình nhóm đối chứng, theo quý; khoảng tin cậy 90 % = chênh lệch ± "
    "1,645 × sai số chuẩn (Welch). Nhóm đối chứng: tỷ lệ gia đình do Tuân thủ cấu hình (mặc định 10 %), rút trong từng "
    "tầng (phân khúc × RM) theo seed; RM không nhận tín hiệu nào cho họ, khách vẫn được phục vụ đủ. Chỉ số: liên hệ "
    "mỗi gia đình mỗi tháng, tỷ lệ mục tiêu “Đạt” sau lần áp dụng cuối quý, khuyến nghị hành động được duyệt mỗi gia "
    "đình. Dưới hai gia đình một nhóm thì không tính khoảng.",
    "src/measure/control.py::effect",
    quarter="Quý",
    tool="Có công cụ",
    control="Đối chứng",
)
metric(
    "uptime.availability",
    "Sẵn sàng trong giờ làm việc",
    "Sẵn sàng = số phút làm việc có nhịp ÷ số phút làm việc trong tháng, từ nhịp đầu tiên đến phút hiện tại. Phút "
    "làm việc: thứ Hai–thứ Sáu, 08:00–17:30 giờ Việt Nam (ngày lễ vẫn tính). Một phút có nhịp khi máy chủ ghi được "
    "nhịp vào cơ sở dữ liệu trong phút đó (ba lần mỗi phút); khởi động lại khi triển khai tính là không sẵn sàng. "
    "Mục tiêu ≥ 99,5 %.",
    "src/control/uptime.py::measure",
    month="Tháng",
    business_minutes="Phút làm việc",
    up_minutes="Phút có nhịp",
)
metric(
    "agent.edited_share",
    "Tỷ lệ CIO sửa kịch bản",
    "Tỷ lệ = số nhận định CIO đã sửa kịch bản trước khi quyết ÷ số nhận định đã quyết, trong khoảng đang xem.",
    "src/views/catalogue.py::quality",
    period="Khoảng",
)
metric(
    "run.expected_3m",
    "Tổng kỳ vọng 3 tháng của một lần áp dụng",
    "Tổng = Σ tác động kỳ vọng 3 tháng của mọi gia "
    "đình trong lần áp dụng (mỗi gia đình: Σ theo kịch bản xác suất × Σ theo khoản giá trị × độ nhạy × biến động).",
    "src/apply/run.py::compute",
    families="Số gia đình",
)

# ── Dữ liệu thị trường, Cấu hình ─────────────────────────────────────────────────────────────────────────
metric(
    "market.value",
    "Giá trị mới nhất của một chuỗi thị trường",
    "Giá trị ngày gần nhất mà job dữ liệu thị trường "
    "đã lưu, như nguồn báo (không tính lại); nguồn đầu tiên trong danh sách là nguồn chính, các nguồn sau là dự "
    "phòng.",
    "app/web.py::market",
    date="Ngày",
    source="Nguồn",
)
metric(
    "setting.return",
    "Giả định lợi nhuận",
    "Một thiết lập, không phải kết quả tính: CIO đặt trong Cấu hình (giả định "
    "lợi nhuận), có hiệu lực sau khi người thứ hai duyệt; dùng cho mô phỏng Kế hoạch (lãi tiền gửi an toàn, tăng "
    "trưởng đầu tư…).",
    "src/scenarios/_sim.py::R",
    key="Khoản",
)
metric(
    "impact.by_factor",
    "Tác động qua một yếu tố",
    "Theo yếu tố = Σ theo kịch bản (xác suất × Σ theo khoản: giá trị × "
    "độ nhạy với yếu tố này × biến động của yếu tố); trên bản đồ nhiệt chia cho tài sản ròng của gia đình; tổng = "
    "cộng mọi gia đình. Các yếu tố cộng lại bằng tác động kỳ vọng.",
    "src/engine/scenario.py::evaluate",
    part="Yếu tố",
    family="Gia đình",
    exact="Giá trị chính xác",
)

# ── Mô hình · Tham số (CIO) ──────────────────────────────────────────────────────────────────────────────
metric(
    "model.parameter",
    "Tham số của mô hình",
    "Một tham số, không phải kết quả tính: tỷ lệ thể hiện theo kỳ hạn và "
    "cỡ cú sốc theo BRD, độ bất định cỡ cú sốc và hệ số co tương quan, trong phiên bản mô hình CIO đã duyệt.",
    "src/engine/model.py::default_model",
    version="Phiên bản",
)
metric(
    "model.coverage",
    "Tỷ lệ tháng nằm trong dải (ngoài mẫu)",
    "Tỷ lệ = số tháng mà biến động thật của yếu tố nằm "
    "trong dải P10–P90 mô hình dự báo ÷ số tháng chấm, với mô hình ước lượng trên dữ liệu đến ngày tách và chấm sau "
    "ngày đó. Kỳ vọng 80%, chấp nhận 70–90%. Chung = gộp mọi yếu tố.",
    "src/market/estimate.py::validate",
    split="Ngày tách",
)

# ── Đồ thị tác động, Độ chính xác (CIO) ─────────────────────────────────────────────────────────────────
metric(
    "scenario.probability",
    "Xác suất của một kịch bản",
    "Một thiết lập của nhận định, không phải kết quả tính: CIO đặt "
    "xác suất cho từng kịch bản (cơ sở, ngược chiều, căng thẳng…) khi duyệt; các xác suất cộng lại bằng 100%.",
    "src/apply/impact_graph.py::family_graph",
    event="Sự kiện",
)
metric(
    "impact.branch",
    "Tác động trong một kịch bản",
    "Trong kịch bản = Σ theo khoản (giá trị × độ nhạy với từng yếu tố "
    "× biến động của yếu tố trong kịch bản này), chưa nhân xác suất.",
    "src/engine/scenario.py::evaluate",
    branch="Kịch bản",
)
metric(
    "impact.edge",
    "Giá trị trên một cạnh của đồ thị",
    "Phần tác động kỳ vọng 3 tháng đi qua cạnh này: Σ theo kịch "
    "bản (xác suất × giá trị × độ nhạy × biến động) của các khoản ở đầu cạnh; với cạnh tài sản → gia đình là giá "
    "trị khoản.",
    "src/apply/impact_graph.py::family_graph",
)
B = "src/measure/backtest.py::"
metric(
    "accuracy.coverage",
    "Tỷ lệ nằm trong dải",
    "Tỷ lệ = số lần biến động thực tế của yếu tố nằm trong dải P10–P90 đã "
    "dự báo ÷ số lần chấm. Lịch sử: mô hình chạy lại, mỗi thời điểm chỉ ước lượng từ các tháng đã qua; nhận định: "
    "dự báo ghi lúc duyệt, chấm khi đến hạn (18:30 mỗi ngày). Gộp = mọi yếu tố.",
    B + "run",
    horizon="Kỳ hạn",
)
metric(
    "accuracy.direction",
    "Tỷ lệ đúng hướng",
    "Tỷ lệ = số lần dấu của dự báo kỳ vọng trùng dấu biến động thực tế ÷ số lần chấm có hướng.",
    B + "run",
    horizon="Kỳ hạn",
)
metric(
    "accuracy.threshold",
    "Ngưỡng chấm độ chính xác",
    "Một thiết lập, không phải kết quả tính: dải chấp nhận cho tỷ lệ "
    "nằm trong dải P10–P90 (kỳ vọng 80%) và mục tiêu đúng hướng VN-Index (KPI-03).",
    B + "verdict",
)
metric(
    "accuracy.forecast",
    "Dự báo và thực tế của một nhận định",
    "Kỳ vọng, P10, P90: dự báo biến động VN-Index (%) "
    "ghi lại lúc CIO duyệt nhận định; thực tế: biến động từ ngày duyệt đến hạn theo dữ liệu thị trường đã lưu.",
    "src/measure/forecasts.py::score",
    view="Nhận định",
)
metric(
    "scenario.move",
    "Biến động của một yếu tố trong kịch bản",
    "Yếu tố lõi: cú sốc theo cỡ CIO chọn (nhỏ / vừa / "
    "lớn theo BRD) × mức đã vào giá (chưa ×1, một phần ×0,5, hết ×0). Yếu tố khác: suy ra bằng kỳ vọng có điều kiện "
    "từ tương quan và độ biến động trong mô hình đã duyệt. Thanh: so với biến động 1 tháng thường thấy.",
    "src/engine/scenario.py::propagate",
    branch="Kịch bản",
)
