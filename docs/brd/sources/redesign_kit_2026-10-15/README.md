# OneWealth Redesign & Product Evolution Kit

Bộ tài liệu này dùng để giao coding assistant thực hiện redesign UI/UX, đối chiếu BRD, refactor codebase, xây dựng Financial Intelligence Graph và tích hợp OneWealth Copilot.

## Nội dung

- `PROMPT_MASTER.md` — prompt chính để chạy trong coding assistant ở repository.
- `PROMPT_FINANCIAL_INTELLIGENCE_GRAPH.md` — định hướng graph, dòng tiền và animation có mục đích.
- `PROMPT_ONEWEALTH_COPILOT.md` — yêu cầu assistant hỏi đáp theo ngữ cảnh và thực hiện task qua tool thật.
- `BRD_COVERAGE_AND_ACCEPTANCE.md` — quy tắc bắt buộc về traceability, bảo toàn tính năng và nghiệm thu.
- `CHANGE_PROPOSAL.md` — mô tả thay đổi, phạm vi, thứ tự triển khai và tiêu chí đánh giá.
- `assets/current_dashboard_reference.png` — screenshot dashboard hiện tại do người dùng cung cấp (nếu có trong gói).
- `assets/onewealth_redesign_concept_board.png` — ảnh concept tham khảo được tạo để truyền đạt định hướng thị giác; không phải bản thiết kế pixel-perfect hoặc nguồn dữ liệu thật.

## Cách dùng

1. Giải nén thư mục này.
2. Mở coding assistant tại repository thực tế, ví dụ `/home/thanglq/mr-finance`.
3. Đảm bảo file BRD tồn tại tại:
   `/home/thanglq/mr-finance/Đặc tả bộ agent tác động tin tức - Yêu cầu kinh doanh và nền tảng công nghệ.docx`
4. Đưa `PROMPT_MASTER.md` cho coding assistant. Có thể đính kèm/cho xem các ảnh trong `assets/`.
5. Nếu agent hỗ trợ tham chiếu file, yêu cầu nó đọc các file prompt bổ sung và acceptance criteria trong gói.
6. Yêu cầu nó tạo báo cáo coverage thực tế dựa trên BRD và repository. Không coi các con số trong ảnh concept là dữ liệu thật.

## Nguyên tắc quan trọng

- BRD gốc là nguồn yêu cầu nghiệp vụ có thẩm quyền.
- Không được bỏ tính năng chỉ để giao diện gọn hơn.
- Ảnh concept chỉ mô tả hướng thiết kế, không phải đặc tả nghiệp vụ.
- Không giả lập dữ liệu, API, agent capability, kết quả test hoặc task execution.
- 100% requirements phải được kiểm kê và truy vết; các mục chưa làm phải được báo rõ, không được tuyên bố hoàn thành giả tạo.
