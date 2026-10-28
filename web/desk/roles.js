/* Each staff role's desk (FEAT-41): its title, its centre module (desk/<view>.js) and the rail's groups of its
   menu's pages (web/shell.js ids, unchanged). A group links to its first page; its pages show as tabs on the sheet.
   The map of every page to its group: docs/brd/ux/role_desks.md. */
export const DESKS = {
  cio: {
    title: "Decision board", view: "cio",
    groups: [
      {id: "ban", label: "Decision board", short: "Board", icon: "target", tip: "Decision board: việc chờ bạn, dòng tin đến gia đình, hộp tin", desk: true, nav: ["ban", "nhan-dinh", "giu", "mo-hinh", "do-luong", "agent", "viec-nen", "cau-hinh"]},  // Admin's pages: old links open here
      {id: "tac-dong", label: "Tác động", icon: "zap", tip: "Tác động: tác động danh mục, phân bổ chờ duyệt, đồ thị lần áp dụng", nav: ["phoi-nhiem", "phan-bo", "do-thi", "ap-dung"]},
      {id: "noi-dung", label: "Nội dung", icon: "file", tip: "Nội dung: bài viết cho khách Private, bằng chứng tin", nav: ["ban-tin", "nghien-cuu", "chinh-sach", "bang-chung"]},
      {id: "hieu-qua", label: "Hiệu quả", icon: "activity", tip: "Hiệu quả: bao nhiêu tin, dự báo đúng sai", nav: ["hieu-qua"]},
      {id: "nhat-ky", label: "Nhật ký", icon: "history", tip: "Nhật ký kiểm toán: chuỗi băm, xuất", nav: ["nhat-ky"]},  // OWN-FB-18: Compliance's chain
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
  admin: {
    title: "Vận hành", view: "admin",
    groups: [
      {id: "ban", label: "Vận hành", icon: "activity", tip: "Vận hành: bản đồ hệ thống, cảnh báo, việc lỗi, cấu hình chờ", desk: true, nav: ["ban"]},
      {id: "he-thong", label: "Hệ thống", icon: "settings", tip: "Hệ thống: lịch chạy, nguồn tin, agent, người dùng, nạp lịch sử", nav: ["he-thong"]},
      {id: "du-lieu", label: "Dữ liệu thị trường", short: "Dữ liệu", icon: "stock", tip: "Dữ liệu thị trường: nguồn, lịch lấy, chuỗi", nav: ["du-lieu"]},
      {id: "nguon-tin", label: "Nguồn tin", icon: "news", tip: "Nguồn tin: thêm, sửa, tắt, xoá, thử; gửi đề xuất rồi duyệt", nav: ["nguon-tin"]},  // N1
      {id: "cau-hinh", label: "Cấu hình", icon: "sliders", tip: "Cấu hình theo phiên bản, hai người duyệt", nav: ["cau-hinh"]},
      {id: "tai-khoan", label: "Tài khoản", icon: "users", tip: "Tài khoản và vai trò: thêm, đổi vai trò, khoá, đặt lại mật khẩu; hai Quản trị", nav: ["tai-khoan"]},
      {id: "mo-hinh", label: "Mô hình", icon: "layers", tip: "Mô hình: tham số, độ chính xác, thử nghiệm hằng ngày, đo lường", nav: ["mo-hinh", "do-luong"]},
      {id: "agent", label: "Agent & việc nền", short: "Agent", icon: "bot", tip: "Agent & việc nền: bản đồ agent, lịch chạy, chạy ngay", nav: ["agent", "viec-nen"]},
      {id: "nhat-ky", label: "Nhật ký", icon: "history", tip: "Nhật ký kiểm toán: chuỗi băm, xuất", nav: ["nhat-ky"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
  rm: {
    title: "Tổng quan", view: "rm",
    groups: [
      {id: "ban", label: "Tổng quan", icon: "users", tip: "Tổng quan: khách hàng đang quản lý, ai cần bạn trước, ghi liên hệ", desk: true, nav: ["ban"]},  // OWN-FB-25, -21
      {id: "khach-hang", label: "Khách hàng", icon: "user", tip: "Khách hàng đang chọn: Wealth view, Wealth planning advisor, Headline news, Advisory performance", nav: ["khach-hang"]},
      {id: "hieu-qua", label: "Advisory performance", short: "Hiệu quả", icon: "activity", tip: "Advisory performance: khách hàng này và tất cả khách hàng của bạn", nav: ["hieu-qua"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
};
