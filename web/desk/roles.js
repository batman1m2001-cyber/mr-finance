/* Each staff role's desk (FEAT-41): its title, its centre module (desk/<view>.js) and the rail's groups of its
   menu's pages (web/shell.js ids, unchanged). A group links to its first page; its pages show as tabs on the sheet.
   The map of every page to its group: docs/brd/ux/role_desks.md. */
export const DESKS = {
  cio: {
    title: "Bàn quyết định", view: "cio",
    groups: [
      {id: "ban", label: "Bàn quyết định", icon: "target", tip: "Bàn quyết định: việc chờ bạn, dòng tin đến gia đình", desk: true, nav: ["ban"]},
      {id: "tin", label: "Tin & sự kiện", icon: "news", tip: "Tin & sự kiện: hộp tin, sự kiện, nhận định", nav: ["hop-tin", "nhan-dinh"]},
      {id: "tac-dong", label: "Tác động", icon: "zap", tip: "Tác động: lần áp dụng, phơi nhiễm, đồ thị", nav: ["ap-dung", "phoi-nhiem", "do-thi"]},
      {id: "noi-dung", label: "Nội dung", icon: "file", tip: "Nội dung: nghiên cứu, bản tin, chính sách", nav: ["nghien-cuu", "ban-tin", "chinh-sach"]},
      {id: "mo-hinh", label: "Mô hình", icon: "sliders", tip: "Mô hình: tham số, dữ liệu, độ chính xác, đo lường", nav: ["mo-hinh", "do-luong"]},
      {id: "ai", label: "AI & cấu hình", icon: "bot", tip: "AI & cấu hình: bản đồ agent, cấu hình theo phiên bản", nav: ["agent", "cau-hinh"]},
      {id: "bo-nho", label: "Bộ nhớ", icon: "history", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", nav: ["bo-nho"], foot: true},
    ],
  },
};
