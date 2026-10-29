# Business feedback 6 — the staff desks (2026-10-24)

Received as two annotated PDFs of screenshots ("Các lỗi ver 2.pdf", "Các lỗi ver 2-2.pdf", 13 pages, the RM's and
the CIO's desks, and one page of the Customer's) and, the same day, a screenshot of the sign-in page. The notes are
written on the screenshots; quoted as written, the English is ours. The PDFs are kept out of git (they show demo
data only, but they are the owner's working files).

| Their words | What it asks |
|---|---|
| "tại màn hình của RM, bỏ phần graph này đi nhé" | RM · Sổ khách hàng: remove the drawing of the families around the RM; keep the cards below |
| "Bỏ tab tác động tin này đi" · same on Toàn cảnh and Bản đồ tài chính | RM · Khách hàng: remove the tabs Tác động tin, Toàn cảnh, Bản đồ tài chính |
| "đổi tên Chi phí chính sách thành Headline news, gồm 2 tab: News and prediction, Đồ thị tác động" | RM · Khách hàng: Chi phí chính sách becomes Headline news, two inner tabs |
| "Kế hoạch → Wealth planning advisor" | rename the tab |
| "Chi tiết tài sản và Tài sản gộp thành Wealth view, 2 tab: Tổng quan, Dữ liệu chi tiết tài sản" | one tab Wealth view, two inner tabs |
| "Bỏ tab Duyệt đề xuất, và ở tab Hiệu quả → đổi tên thành Advisory performance → Tách thành 2 tab (1 tab là chỉ Khách hàng này, 1 tab là Tất cả khách hàng) giống như hình ở bên dưới" | the RM's Advisory performance with two inner tabs, laid out as the mock: an internal banner, six figures, the AI pipeline of four agents with arrows, the log of recommendations, the important news missed |
| "Tại màn hình của CIO: Thôi đừng đổi tên thành News approval → mà đổi tên thành Decision board" | CIO: Bàn quyết định is called Decision board |
| "bỏ Sự kiện" · "Gia đình và RM để riêng một khung màu khác" | the flow drops its Sự kiện stage; Gia đình and RM sit in their own coloured frame |
| "mỗi dòng hiển thị mức độ tác động và nhóm tin" | each decision row shows its impact level and its news group |
| "thêm bộ lọc như Hộp tin … hiện 20 dòng, xem thêm" | the decisions get the inbox's filters (source, domestic or international, relevance, search); 20 rows, then Xem thêm |
| "đưa Hộp tin vào Decision board, bỏ nhóm Tin tức" | the inbox's tools (source health, filters, Lấy tin ngay, Bỏ tin, Gom thành sự kiện) move into the Decision board; the Tin tức group goes |
| "Phơi nhiễm → Tổng quan tác động tới tài sản, bỏ Sự kiện gần đây, kéo rộng ra" · "viết lại cho dễ hiểu" · "thêm chọn kịch bản và bảng xếp hạng gia đình" | the desk's exposure card renamed, full width, plain words (no raw ids; a run is a "kịch bản"), a picker of the scenario and the families ranked (Gia đình, Kỳ vọng, % tài sản ròng, P10) |
| "bỏ Mô hình và dữ liệu, Agent dưới bàn" | the desk's two technical cards go |
| "bỏ phần này" (the sheet's header) · "Phơi nhiễm → Tác động danh mục" · "bỏ Lần áp dụng, giữ Đồ thị lần áp dụng" · "viết lại cho dễ hiểu", "P10 là gì?" | CIO · Tác động: no repeated title and back link above the tabs; Phơi nhiễm is Tác động danh mục; Lần áp dụng is no tab; plain words and a plain P10 |
| "bỏ Nghiên cứu; Bản tin và Chính sách gộp lại, tập trung vào viết bài … CIO tự viết tin tức, thông tin chính sách độc quyền cho khách Private" | CIO · Nội dung: one tab to write articles, the CIO's own news and policy notes, for Private clients only |
| "chuyển Mô hình và AI sang Admin" · "CIO chỉ cần một tab Hiệu quả đơn giản (bao nhiêu tin, độ chính xác), không kỹ thuật" | the Mô hình and AI groups move to Admin; the CIO gets one simple Hiệu quả tab |
| (Customer · Headline News) "Tác động lên tài sản ròng: mỗi dòng là thanh chồng theo loại tài sản (bđs, chứng khoán, trái phiếu, chứng chỉ quỹ, vàng…), di chuột hiện tên và số tiền" | the client's impact bars split by asset class, each part named with its amount on hover |
| (sign-in page) "Xoá account này đi" on Tuân thủ (Đỗ Minh Châu, Vũ Hải Nam) and Chuyên gia (duyệt khuyến nghị) (Phan Đức Thịnh, Lâm Bảo Ngọc, Đặng Thu Trang, Vũ Hoàng Long, Trịnh Khánh Linh) | delete the Compliance and Expert accounts |

**What was decided** (ours, the owner gave no rule for it): the duties of the two removed roles move to the CIO, and
every four-eyes rule stays — a second CIO (Lê Thu Hà) approves what the first wrote; an RM decides a recommendation
alone, as for a family with no expert today. The audit trail keeps the old roles' names for what they did. Plan:
[`docs/BUSINESS_FEEDBACK_6_PLAN.md`](../../../BUSINESS_FEEDBACK_6_PLAN.md).
