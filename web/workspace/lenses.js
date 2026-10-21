/* The Customer workspace's lenses and addresses (FEAT-40, ADR-0035). A lens is a view of the one graph: which kinds
   show, which classes open, what the inspector says first. `#/client/xem/<lens>` is a lens alone; every older
   Customer address still names its page, which opens as a sheet over the graph, with the lens that page belongs to —
   so the server's links (citations, search, the bell) need no change. A lens's pages are buttons under its title, and
   its numbers a section of the Bảng số liệu (part); Toàn cảnh and Chi tiết are that dashboard now (UX_TOOLBAR_PLAN
   T3+T4), so their addresses open it. */

export const LENSES = [
  {id: "tong-quan", label: "Tổng quan", icon: "map", tip: "Tổng quan: toàn bộ bức tranh tài chính", sub: "Tài sản, dòng tiền, mục tiêu, rủi ro và tin tức quanh bạn",
    kinds: ["family", "class", "flow", "liquidity", "goal", "risk", "event"], sheets: [], part: "cash"},
  {id: "tai-san", label: "Tài sản", icon: "wallet", tip: "Tài sản: từng khoản và nguồn dữ liệu", sub: "Từng loại tài sản, khoản nợ và nguồn dữ liệu của chúng",
    kinds: ["family", "class", "holding", "source"], sheets: ["tai-san"], part: "alloc"},
  {id: "dong-tien", label: "Dòng tiền", icon: "flow", tip: "Dòng tiền: thu nhập, chi tiêu, thanh khoản", sub: "Thu nhập và chi tiêu của tháng, và tiền dự phòng",
    kinds: ["family", "flow", "category", "liquidity", "class"], sheets: [], part: "cash"},
  {id: "muc-tieu", label: "Mục tiêu & kịch bản", short: "Mục tiêu", icon: "target", tip: "Mục tiêu và kịch bản giả định", sub: "Mục tiêu của bạn và các kịch bản giả định",
    kinds: ["family", "goal", "scenario"], sheets: ["ke-hoach"]},
  {id: "tin", label: "Tin tức", icon: "news", tip: "Tin tức, sự kiện và chính sách có thể tác động", sub: "Tin tức, sự kiện và chính sách có thể tác động tới tài sản của bạn",
    kinds: ["family", "event", "alert", "class"], sheets: ["thi-truong", "do-thi", "chinh-sach"]},
  {id: "rui-ro", label: "Rủi ro", icon: "alert", tip: "Rủi ro: mức lỗ khi căng thẳng, tập trung, dự phòng", sub: "Mức lỗ khi thị trường xấu, mức tập trung và tiền dự phòng",
    kinds: ["family", "risk", "liquidity", "class"], sheets: ["khau-vi"], part: "risk"},
];
export const LENS = Object.fromEntries(LENSES.map(l => [l.id, l]));

// the dedicated views: each an existing page module, at its old address (ADR-0035 §3)
export const SHEETS = {
  "tai-san": {page: "holdings", label: "Tài sản", route: "#/client/tai-san", lens: "tai-san", nav: ["tai-san"]},
  "ke-hoach": {page: "plan", label: "Kế hoạch", route: "#/client/muc-tieu/ke-hoach", lens: "muc-tieu", nav: ["muc-tieu", "ke-hoach"]},
  "khau-vi": {page: "risktest", label: "Khẩu vị rủi ro", route: "#/client/rui-ro/khau-vi", lens: "rui-ro", nav: ["rui-ro", "khau-vi"]},
  "thi-truong": {page: "impact", label: "Tác động tin", route: "#/client/tin/thi-truong", lens: "tin", nav: ["tin", "thi-truong"]},
  "do-thi": {page: "graph", label: "Đồ thị tác động", route: "#/client/tin/do-thi", lens: "tin", nav: ["tin", "do-thi"]},
  "chinh-sach": {page: "policy", label: "Chi phí chính sách", route: "#/client/tin/chinh-sach", lens: "tin", nav: ["tin", "chinh-sach"]},
  "chuyen-gia": {page: "advisor", label: "Chuyên gia", route: "#/client/chuyen-gia", lens: null, nav: ["chuyen-gia"]},
  "bo-nho": {page: "memory", label: "Bộ nhớ", route: "#/client/bo-nho", lens: null, nav: ["bo-nho"]},
};
// the toolbar: the lenses, then Chuyên gia (OWN-GW-05: Experts may stay a separate view). Bộ nhớ is not on it
// (UX_TOOLBAR_PLAN T2): the header and the assistant's panel open it, and its address still works.
export const TOOLBAR = [...LENSES.map(l => ({...l, href: lensRoute(l.id)})),
  {id: "chuyen-gia", label: "Chuyên gia", icon: "users", tip: "Chuyên gia: liên hệ đội ngũ tư vấn", href: SHEETS["chuyen-gia"].route, sheet: true}];

export function lensRoute(id) { return `#/client/xem/${id}`; }

// the dashboard's sections, for a link that names one
export const PARTS = {cash: "Dòng tiền", alloc: "Phân bổ", pnl: "Lãi / lỗ", month: "Tiền vào và ra trong tháng", nw: "Tài sản ròng", risk: "Rủi ro", liq: "Thanh khoản"};
// Toàn cảnh and Chi tiết, the client's former pages: the dashboard, at the section each led with
const BOARD = {"tong-quan/toan-canh": "month", "tong-quan/chi-tiet": "nw"};

// the old addresses: [first, second] → sheet id; a bare first segment with subpages opens its first one
const OLD = {
  "tai-san": "tai-san",
  "muc-tieu": "ke-hoach", "muc-tieu/ke-hoach": "ke-hoach", "muc-tieu/khau-vi": "khau-vi", "rui-ro": "khau-vi", "rui-ro/khau-vi": "khau-vi",
  "tin": "thi-truong", "tin/thi-truong": "thi-truong", "tin/do-thi": "do-thi", "tin/chinh-sach": "chinh-sach",
  "chuyen-gia": "chuyen-gia", "bo-nho": "bo-nho",
};

/* The address's parts after the role → {lens (or null: keep the current one), sheet (or null), param}, and a
   dashboard section to open (part) for Toàn cảnh's and Chi tiết's addresses. */
export function resolve(parts) {
  const [a, b, c] = parts;
  if (BOARD[`${a}/${b}`]) return {lens: "tong-quan", sheet: null, param: null, part: BOARD[`${a}/${b}`]};
  if (!a || a === "tong-quan" && (!b || b === "ban-do")) return {lens: a ? "tong-quan" : null, sheet: null, param: null};
  if (a === "xem") return {lens: LENS[b] ? b : "tong-quan", sheet: null, param: null};
  const two = b && OLD[`${a}/${b}`];
  const id = two || OLD[a];
  if (!id) return {lens: "tong-quan", sheet: null, param: null};
  const s = SHEETS[id];
  return {lens: s.lens, sheet: id, param: two ? c || null : b || null};
}

/* A page module's ctx.href(nav, sub, param) inside the workspace: the same old addresses (they open sheets). */
export function href(nav, sub, param) {
  return `#/client/${[nav, sub, param].filter(Boolean).map(encodeURIComponent).join("/")}`;
}
