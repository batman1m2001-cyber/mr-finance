/* Each staff role's desk (FEAT-41): its title, its centre module (desk/<view>.js) and the rail's groups of its
   menu's pages (web/shell.js ids, unchanged). A group links to its first page; its pages show as tabs on the sheet.
   The map of every page to its group: docs/brd/ux/role_desks.md. */
export const DESKS = {
  cio: {
    title: "Bàn quyết định", view: "cio",
    groups: [
      {id: "ban", label: "Bàn quyết định", short: "Bàn", icon: "target", tip: "Bàn quyết định: việc chờ bạn, dòng tin đến gia đình", desk: true, nav: ["ban"]},
      {id: "tin", label: "Tin tức", icon: "news", tip: "Tin tức: hộp tin, sự kiện, nhận định", nav: ["hop-tin", "nhan-dinh"]},
      {id: "tac-dong", label: "Tác động", icon: "zap", tip: "Tác động: lần áp dụng, phơi nhiễm, đồ thị", nav: ["ap-dung", "phoi-nhiem", "do-thi"]},
      {id: "noi-dung", label: "Nội dung", icon: "file", tip: "Nội dung: nghiên cứu, bản tin, chính sách", nav: ["nghien-cuu", "ban-tin", "chinh-sach"]},
      {id: "mo-hinh", label: "Mô hình", icon: "sliders", tip: "Mô hình: tham số, dữ liệu, độ chính xác, đo lường", nav: ["mo-hinh", "do-luong"]},
      {id: "ai", label: "AI & cấu hình", short: "AI", icon: "bot", tip: "AI & cấu hình: bản đồ agent, việc nền, cấu hình theo phiên bản", nav: ["agent", "viec-nen", "cau-hinh"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
  admin: {
    title: "Vận hành", view: "admin",
    groups: [
      {id: "ban", label: "Vận hành", icon: "activity", tip: "Vận hành: bản đồ hệ thống, cảnh báo, việc lỗi, cấu hình chờ", desk: true, nav: ["ban"]},
      {id: "he-thong", label: "Hệ thống", icon: "settings", tip: "Hệ thống: lịch chạy, nguồn tin, agent, người dùng, nạp lịch sử", nav: ["he-thong"]},
      {id: "du-lieu", label: "Dữ liệu thị trường", short: "Dữ liệu", icon: "stock", tip: "Dữ liệu thị trường: nguồn, lịch lấy, chuỗi", nav: ["du-lieu"]},
      {id: "cau-hinh", label: "Cấu hình", icon: "sliders", tip: "Cấu hình theo phiên bản, hai người duyệt", nav: ["cau-hinh"]},
      {id: "tai-khoan", label: "Tài khoản", icon: "users", tip: "Tài khoản và vai trò: thêm, đổi vai trò, khoá, đặt lại mật khẩu; hai Quản trị", nav: ["tai-khoan"]},
      {id: "agent", label: "Agent & việc nền", short: "Agent", icon: "bot", tip: "Agent & việc nền: bản đồ agent, lịch chạy, chạy ngay", nav: ["agent", "viec-nen"]},
      {id: "nhat-ky", label: "Nhật ký", icon: "history", tip: "Nhật ký kiểm toán: chuỗi băm, xuất", nav: ["nhat-ky"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
  compliance: {
    title: "Bàn kiểm soát", view: "compliance",
    groups: [
      {id: "ban", label: "Bàn kiểm soát", short: "Bàn", icon: "shield", tip: "Bàn kiểm soát: các chốt kiểm soát và việc chờ Tuân thủ", desk: true, nav: ["ban"]},
      {id: "giu", label: "Tin bị giữ", icon: "lock", tip: "Tin bị giữ vì danh sách hạn chế", nav: ["giu"]},
      {id: "noi-dung", label: "Nội dung", icon: "file", tip: "Nội dung: nghiên cứu, bản tin, chính sách", nav: ["nghien-cuu", "ban-tin", "chinh-sach"]},
      {id: "do-luong", label: "Đo lường", icon: "activity", tip: "Đo lường: báo cáo hằng tháng", nav: ["do-luong"]},
      {id: "nhat-ky", label: "Nhật ký", icon: "history", tip: "Nhật ký kiểm toán: chuỗi băm, xuất", nav: ["nhat-ky"]},
      {id: "ai", label: "AI & cấu hình", short: "AI", icon: "bot", tip: "Agent, việc nền và cấu hình theo phiên bản", nav: ["agent", "viec-nen", "cau-hinh"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
  specialist: {
    title: "Bàn chuyên gia", view: "specialist",
    groups: [
      {id: "ban", label: "Bàn chuyên gia", short: "Bàn", icon: "scale", tip: "Bàn chuyên gia: khuyến nghị chờ bạn bên cạnh bức tranh của gia đình", desk: true, nav: ["ban"]},
      {id: "duyet", label: "Duyệt khuyến nghị", short: "Duyệt", icon: "check", tip: "Duyệt khuyến nghị: chờ bạn và đã xử lý", nav: ["duyet"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
  rm: {
    title: "Sổ khách hàng", view: "rm",
    groups: [
      {id: "ban", label: "Sổ khách hàng", short: "Sổ khách", icon: "users", tip: "Sổ khách hàng: gia đình của bạn, ai cần bạn trước", desk: true, nav: ["ban"]},
      {id: "hom-nay", label: "Hôm nay", icon: "calendar", tip: "Hôm nay: cần xem trước, việc theo mục tiêu, nhật ký liên hệ", nav: ["hom-nay"]},
      {id: "khach-hang", label: "Khách hàng", icon: "user", tip: "Khách hàng đang chọn: Wealth view, Wealth planning advisor, Headline news, Advisory performance", nav: ["khach-hang"]},
      {id: "hieu-qua", label: "Advisory performance", short: "Hiệu quả", icon: "activity", tip: "Advisory performance: khách hàng này và tất cả khách hàng của bạn", nav: ["hieu-qua"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "archive", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
};
