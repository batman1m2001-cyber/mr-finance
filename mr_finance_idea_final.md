# Plan v2: Tập trung vào selling point Consolidate + Dashboard tổng thể

**Thông điệp chính:** *"KH có tài sản ở nhiều sản phẩm, nhiều kênh, nhiều nền tảng nhưng không ai cho họ thấy bức tranh toàn cảnh. Chúng tôi làm việc đó và cho biết điều gì đang tác động tới bức tranh ấy."*

---

## 1. Thu thập dữ liệu: 3 tầng nguồn

| Tầng | Nguồn | Dữ liệu lấy được | Cách lấy |
|---|---|---|---|
| **1. Hệ sinh thái Techcombank** (tự động, không cần KH thao tác) | Techcombank | Tiền gửi, thẻ, khoản vay, lương về, chi tiêu định kỳ | Nội bộ |
| | TCBS | Cổ phiếu, trái phiếu, giá vốn, lãi lỗ | Nội bộ |
| | Techcom Capital | Chứng chỉ quỹ | Nội bộ |
| | One Mount / OneHousing | Định giá nhà, giá theo khu vực, thanh khoản BĐS | Nội bộ |
| **2. Ngoài hệ sinh thái** (KH đồng ý chia sẻ) | Ngân hàng khác, công ty CK khác (SSI, VPS…) | Số dư, danh mục | **Open API** (theo khung Open API của NHNN) hoặc **tải sao kê PDF/Excel**, AI đọc và tự bóc tách |
| **3. KH tự khai** | Hồ sơ cá nhân | Thu nhập, số con và tuổi các con, người phụ thuộc, BĐS ngoài hệ thống, vàng, bảo hiểm, nợ cá nhân, cổ phần DN | Form thông minh hoặc **chat với AI** ("Tôi có 1 căn ở Thảo Điền mua 2019 giá 8 tỷ") |

**Điểm nhấn khi pitch:**
- **Tầng 1 không cần KH làm gì:** đây là lợi thế riêng mà chỉ Techcombank có, đối thủ không sao chép được.
- **Tải sao kê lên là AI đọc được:** KH không phải nhập tay từng dòng.
- **Độ tin cậy dữ liệu:** mỗi tài sản được gắn nhãn *đã xác thực* (từ API/hệ sinh thái), *từ sao kê*, hoặc *KH tự khai*. Mức độ chắc chắn của các phân tích phía sau được tính theo nhãn này.
- **Gia đình:** liên kết tài khoản vợ/chồng/con (cần sự đồng ý của từng người) để xem tài sản theo cá nhân hoặc cả hộ.

---

## 2. Bài test khẩu vị rủi ro bằng AI (tham khảo bài test của SSI)

Điểm khác so với bài test tĩnh của SSI:

1. **Hỏi thích ứng:** câu sau phụ thuộc vào câu trả lời trước, khoảng 8–12 câu thay vì 20 câu cố định.
2. **Câu hỏi tình huống thay vì chấm điểm 1–5:**
   - *"Danh mục 10 tỷ của anh giảm còn 8 tỷ trong 1 tháng. Anh sẽ: bán hết / giữ nguyên / mua thêm?"*
   - *"Chọn A: chắc chắn lãi 6%, hay B: 50% cơ hội lãi 15%, 50% cơ hội lỗ 3%?"*
3. **Tách 2 khái niệm** (đây là điểm ghi điểm về mặt chuyên môn):
   - **Mức chấp nhận rủi ro (risk tolerance):** KH *muốn* chịu bao nhiêu, lấy từ bài test.
   - **Khả năng chịu rủi ro (risk capacity):** KH *có thể* chịu bao nhiêu, AI tự tính từ dữ liệu dòng tiền, nợ và người phụ thuộc.
   - Khi hai chỉ số lệch nhau, hệ thống cảnh báo. Ví dụ: KH muốn rủi ro cao nhưng dòng tiền yếu, 3 con đang đi học.
4. **Tự cập nhật:** hệ thống hỏi lại khi có thay đổi lớn trong đời (sinh con, nghỉ hưu), khi thị trường biến động mạnh, hoặc theo định kỳ 6 tháng. Nó cũng so *KH nói gì* với *KH thực sự làm gì* (ví dụ tự khai là chấp nhận rủi ro cao nhưng bán tháo khi thị trường giảm 5%).
5. **Kết quả:** gán KH vào 1 trong 5 chân dung, kèm một risk profile cụ thể.

---

## 3. Dashboard tổng thể (selling point chính)

```
┌──────────────────────────────────────────────────────────────┐
│ TÀI SẢN RÒNG: 45,2 tỷ  ▲ +3,1% tháng   [Cá nhân | Gia đình]   │
├───────────────────┬──────────────────┬───────────────────────┤
│ PHÂN BỔ TÀI SẢN   │ LÃI/LỖ DANH MỤC  │ RỦI RO                │
│ BĐS 55%           │ Đã chốt: +1,2 tỷ │ Ngưỡng: 15% sụt giảm  │
│ CP 15% · TP 12%   │ Chưa chốt: +0,8 tỷ│ Hiện tại: 9% ●       │
│ Tiền 10% · Vàng 8%│ So benchmark: +2%│ Tập trung: BĐS Q2 ⚠   │
├───────────────────┴──────────────────┴───────────────────────┤
│ THANH KHOẢN DỰ PHÒNG: 3,4 tỷ = đủ chi 14 tháng ●              │
├──────────────────────────────────────────────────────────────┤
│ DÒNG TIỀN 12 THÁNG TỚI (lịch)                                │
│ ▲ Inflow: lương, cổ tức, coupon TP, tiền thuê nhà, đáo hạn TG │
│ ▼ Outflow: trả nợ vay, học phí, phí BH, thuế                  │
│ ⚠ Khoản phải trả lớn: T3/2027 học phí du học 1,8 tỷ           │
├──────────────────────────────────────────────────────────────┤
│ CẢNH BÁO TÁC ĐỘNG (3)  → xem mục 5                            │
└──────────────────────────────────────────────────────────────┘
```

**Các chỉ số chính:**
- **Lãi/lỗ toàn danh mục:** đã chốt và chưa chốt, so với benchmark mà KH tự đặt.
- **Ngưỡng rủi ro:** mức sụt giảm tối đa KH chấp nhận, so với mức rủi ro hiện tại; cảnh báo khi tài sản quá tập trung vào một ngành, một khu vực hoặc một tổ chức phát hành.
- **Thanh khoản dự phòng:** lượng tài sản thanh khoản cao, quy đổi thành *số tháng chi tiêu đủ trang trải*.
- **Dòng tiền tương lai:** các khoản phải trả, tiền vào và tiền ra được dựng thành **lịch 12–36 tháng**. AI tự phát hiện khoản định kỳ từ sao kê (lương, tiền thuê, học phí).

---

## 4. Các kịch bản mô phỏng (giữ 3 kịch bản cũ, bổ sung thêm)

**A. Kịch bản theo các mốc trong đời (KH chủ động thử):**

| Kịch bản | Câu hỏi AI trả lời | Phù hợp chân dung |
|---|---|---|
| Học phí cho con (trong nước / du học) | Cần bao nhiêu, từ bây giờ phải để dành bao nhiêu mỗi tháng, tỷ giá USD tăng 5% thì sao | Chuyên gia, F1 |
| Nghỉ hưu sớm năm 55 tuổi | Dòng tiền thụ động có đủ chi không, tiền đủ dùng tới năm bao nhiêu tuổi | Chuyên gia, nghỉ hưu |
| Bán căn nhà thứ 2 | Thuế, phí, tiền thu về thì đầu tư vào đâu, so với giữ lại cho thuê | F1, nghỉ hưu |
| **Mua thêm BĐS bằng vốn vay** | Áp lực trả nợ nếu lãi suất +2%, nếu tiền thuê không như kỳ vọng | F1, mới chạm ngưỡng |
| **Chuyển giao tài sản cho con / thừa kế** | Chia thế nào, thuế/phí, cổ phần DN xử lý ra sao | F1 |
| **DN cần vốn gấp** | Cầm cố tài sản nào trước, bán gì ít thiệt hại nhất | F1 |
| **Chi phí y tế lớn hoặc biến cố sức khỏe** | Thanh khoản dự phòng đủ không, bảo hiểm chi trả bao nhiêu | Nghỉ hưu, chuyên gia |
| **Định cư / con đi du học** | Quy định chuyển tiền ra nước ngoài, cần chuẩn bị ngoại tệ bao nhiêu | Chuyên gia, F1 |
| **Cưới hỏi / hỗ trợ con mua nhà** | Rút một khoản lớn thì ảnh hưởng mục tiêu nghỉ hưu ra sao | Nghỉ hưu, F1 |

**B. Stress test thị trường** (AI tự chạy, KH xem kết quả):
- Chạy lại **khủng hoảng trái phiếu DN 2022**: danh mục hiện tại sẽ ra sao.
- **Thị trường BĐS đóng băng như 2022–2023:** mất thanh khoản trong 18 tháng.
- **VN-Index giảm 30%**, **lãi suất tăng 2%**, **USD/VND tăng 5%**.

Với mỗi kịch bản, AI đưa ra 2 hướng **heavy / light**. Nội dung chỉ là mô phỏng; khuyến nghị cụ thể phải qua RM duyệt.

---

## 5. Đo mức độ tác động lên tài sản KH

**Công thức tính điểm tác động (minh bạch, giải thích được):**

```
Tác động (VND) = Mức nắm giữ × Độ nhạy × Xác suất xảy ra
```
- **Mức nắm giữ (exposure):** KH đang có bao nhiêu tiền trong tài sản bị ảnh hưởng.
- **Độ nhạy (sensitivity):** mức biến động của tài sản khi sự kiện xảy ra. Cách tính theo loại tài sản:
  - Trái phiếu: theo **duration**.
  - Cổ phiếu: theo **beta ngành**.
  - BĐS: theo dữ liệu giá từng khu vực của OneHousing.
  - Khoản vay: theo lãi suất thả nổi.
- **Xác suất xảy ra:** mới là dự thảo (thấp), đang lấy ý kiến (trung bình), đã thông qua (cao).
- **Kết quả hiển thị:** số tiền VND, % tài sản ròng và mức độ 🔴 cao / 🟡 trung bình / 🟢 thấp, kèm **nguồn trích dẫn**.

**Tác động vĩ mô và vi mô lên tài sản của KH:**

| Yếu tố | Kênh tác động lên tài sản KH |
|---|---|
| Lãi suất điều hành tăng/giảm | Giá trái phiếu, chi phí khoản vay, lãi tiền gửi, cổ phiếu ngân hàng và BĐS |
| Tỷ giá USD/VND | Chi phí du học, cổ phiếu xuất khẩu, khoản nợ bằng USD |
| Giá vàng, chênh lệch vàng trong nước và thế giới | Vàng KH đang giữ |
| Room tín dụng / siết cho vay BĐS | Thanh khoản BĐS, cổ phiếu nhà phát triển BĐS |
| **Vi mô: hạ tầng địa phương** (metro, cao tốc, sân bay Long Thành, cầu mới) | BĐS gần dự án **tăng giá**. Cảnh báo không chỉ báo tin xấu mà cả **cơ hội** |
| **Vi mô: sáp nhập tỉnh, quy hoạch mới, bảng giá đất địa phương** | Giá BĐS và thuế, phí theo từng khu vực |

---

## 6. Cảnh báo sớm về chính sách (mở rộng thêm nhiều trường hợp)

| # | Chính sách / dự thảo | KH bị ảnh hưởng | Nội dung cảnh báo |
|---|---|---|---|
| 1 | **Thuế với người sở hữu từ 2 BĐS trở lên** | KH có ≥ 2 BĐS | "Ước tính thuế phải nộp tăng thêm X triệu/năm cho căn ở Q7" |
| 2 | **Đổi cách tính thuế chuyển nhượng BĐS** (từ 2% giá bán sang tính theo lãi thực tế hoặc thời gian nắm giữ) | KH dự định bán nhà | "Nếu bán trước hoặc sau khi luật có hiệu lực, chênh lệch thuế là Y" |
| 3 | **Bảng giá đất điều chỉnh hằng năm** (Luật Đất đai 2024) | KH có đất, sắp làm thủ tục chuyển nhượng | Phí trước bạ, thuế, tiền sử dụng đất tăng |
| 4 | **Dự thảo ảnh hưởng ngân hàng quốc doanh** | KH nắm nhiều trái phiếu, cổ phiếu ngân hàng | Mức nắm giữ và tác động lan sang toàn ngành ngân hàng |
| 5 | **Giới hạn sở hữu cổ phần ngân hàng** (Luật Các TCTD 2024) | KH nắm nhiều cổ phiếu một ngân hàng | Rủi ro bị bán giải chấp hoặc buộc thoái vốn của cổ đông lớn |
| 6 | **Siết điều kiện nhà đầu tư chuyên nghiệp mua trái phiếu DN** | KH đang mua trái phiếu DN | Có thể không mua tiếp được, thanh khoản thứ cấp giảm |
| 7 | **Thay đổi thuế chuyển nhượng chứng khoán** | KH giao dịch nhiều | Chi phí giao dịch tăng |
| 8 | **Nâng hạng thị trường chứng khoán** | KH nắm cổ phiếu vốn hóa lớn | **Cơ hội:** dòng vốn ngoại chảy vào nhóm cổ phiếu này |
| 9 | **Chính sách quản lý vàng miếng** | KH giữ nhiều vàng | Chênh lệch giá vàng trong nước và thế giới thu hẹp, giá trị vàng đang giữ thay đổi |
| 10 | **Thí điểm thị trường tài sản số / crypto** | Chân dung F2 | Khung pháp lý mới, kênh đầu tư hợp pháp |
| 11 | **Quy định ngoại hối, chuyển tiền du học** | KH có con du học | Hạn mức và thủ tục chuyển tiền thay đổi |
| 12 | **Thuế thu nhập cá nhân sửa đổi** (giảm trừ gia cảnh, biểu thuế) | Chuyên gia thu nhập cao | Thu nhập thực nhận thay đổi Z/tháng |
| 13 | **Quy định bảo hiểm liên kết đầu tư** | KH có hợp đồng bảo hiểm liên kết đầu tư | Quyền lợi và phí hủy hợp đồng thay đổi |
| 14 | **Thuế tối thiểu toàn cầu, ưu đãi đầu tư** | F1 có DN | Lợi nhuận của DN ảnh hưởng tới giá trị cổ phần |

**Lưu ý khi demo:** trước khi đưa vào slide, cần kiểm tra lại trạng thái pháp lý mới nhất của từng mục (đã ban hành hay còn là dự thảo). Mình đã gom danh sách theo hiểu biết hiện có, nhưng các quy định này thay đổi nhanh. Nên chọn **3–4 trường hợp mạnh nhất** để demo kỹ (gợi ý #1, #4, #8, cộng 1 trường hợp hạ tầng), còn lại đưa vào slide để cho thấy hệ thống mở rộng được.

---

## 7. Luồng demo tập trung vào selling point

1. **Kết nối dữ liệu (30 giây):** liên kết Techcombank, TCBS, OneHousing tự động; tải lên 1 sao kê của VPS và AI tự đọc; chat để khai thêm 1 mảnh đất và thông tin 2 con.
2. **Bài test AI (30 giây):** trả lời 3 câu tình huống, hệ thống báo *"Anh muốn rủi ro cao nhưng khả năng chịu rủi ro chỉ ở mức trung bình"*.
3. **Dashboard tổng thể (1 phút):** bấm chuyển giữa cá nhân và gia đình; lịch dòng tiền hiện ra khoản học phí lớn sắp tới.
4. **Có cảnh báo (1 phút):** dự thảo thuế BĐS thứ 2 → *"−120 triệu/năm"*; hạ tầng metro → *"Căn Q9 +8%"*.
5. **Kịch bản (1 phút):** KH thử bán 1 căn và xem dòng tiền thay đổi.
6. **RM duyệt (30 giây):** chứng minh vẫn đáp ứng compliance theo đề bài.

---

**Việc nên làm tiếp:**
- **Dữ liệu mock:** dựng 5 portfolio mẫu, sao kê giả và lịch dòng tiền.
- **Bài test:** viết bộ câu hỏi AI risk test.
- **Wireframe:** vẽ chi tiết dashboard.

Bạn muốn bắt đầu từ phần nào?