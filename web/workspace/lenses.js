/* The Customer workspace's lenses and addresses (FEAT-40, ADR-0035). A lens is a view of the one graph: which kinds
   show, which classes open, what the inspector says first. `#/client/xem/<lens>` is a lens alone; every older
   Customer address still names its page, which opens as a sheet over the graph, with the lens that page belongs to —
   so the server's links (citations, search, the bell) need no change. A lens's pages are buttons under its title, and
   its numbers a section of the Bảng số liệu (part); Toàn cảnh and Chi tiết are that dashboard now (UX_TOOLBAR_PLAN
   T3+T4), so their addresses open it.
   The classic app (BUSINESS_FEEDBACK_1021_PLAN B3.1): the bar leads to each section's page, Toàn cảnh is the home
   page. The bank's names (WEALTH_NAMES_PLAN, ADR-0037): four sections — Wealth View, Wealth Planning Advisor, Headline
   News, Relationship specialist — and no graph for the client: every address that opened it opens its section's
   page, and every older address still opens its page. The lenses stay as the graph's views (the code is kept). */

export const LENSES = [
  {id: "tong-quan", label: "Tổng quan", icon: "map", tip: "Tổng quan: toàn bộ bức tranh tài chính", sub: "Tài sản, dòng tiền, mục tiêu, rủi ro và tin tức quanh bạn",
    kinds: ["family", "class", "flow", "liquidity", "goal", "risk", "event"], sheets: [], part: "cash"},
  {id: "tai-san", label: "Tài sản", icon: "wallet", tip: "Tài sản: từng khoản và nguồn dữ liệu", sub: "Từng loại tài sản, khoản nợ và nguồn dữ liệu của chúng",
    kinds: ["family", "class", "holding"], sheets: ["tai-san"], part: "alloc"},  // its sources: in Thông tin (T6)
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
  "tai-san": {page: "holdings", label: "Dữ liệu chi tiết tài sản", route: "#/client/tai-san", lens: "tong-quan", nav: ["tai-san"]},
  "ke-hoach": {page: "plan", label: "Wealth planning advisor", route: "#/client/muc-tieu/ke-hoach", lens: "muc-tieu", nav: ["muc-tieu", "ke-hoach"]},
  "khau-vi": {page: "risktest", label: "Risk profile test", route: "#/client/rui-ro/khau-vi", lens: "muc-tieu", nav: ["rui-ro", "khau-vi"]},
  "thi-truong": {page: "impact", label: "Tác động tin", route: "#/client/tin/thi-truong", lens: "tin", nav: ["tin", "thi-truong"]},
  "do-thi": {page: "graph", label: "Đồ thị tác động", route: "#/client/tin/do-thi", lens: "tin", nav: ["tin", "do-thi"]},
  "chinh-sach": {page: "policy", label: "Chi phí chính sách", route: "#/client/tin/chinh-sach", lens: "tin", nav: ["tin", "chinh-sach"]},
  "chuyen-gia": {page: "advisor", label: "Relationship specialist", route: "#/client/chuyen-gia", lens: null, nav: ["chuyen-gia"]},
  "bo-nho": {page: "memory", label: "Bộ nhớ", route: "#/client/bo-nho", lens: null, nav: ["bo-nho"]},
};
// each section's page and its tabs (B3.1; the names: WEALTH_NAMES_PLAN): [label, address, the view a tab opens]
export const SECTIONS = {
  "tong-quan": {home: "#/client/tong-quan", tabs: [["Wealth view", "#/client/tong-quan", "money"], [SHEETS["tai-san"].label, SHEETS["tai-san"].route]]},
  "muc-tieu": {home: SHEETS["ke-hoach"].route, tabs: ["ke-hoach", "khau-vi"].map(id => [SHEETS[id].label, SHEETS[id].route])},
  "tin": {home: SHEETS["thi-truong"].route, tabs: ["thi-truong", "do-thi", "chinh-sach"].map(id => [SHEETS[id].label, SHEETS[id].route])},
  "chuyen-gia": {home: SHEETS["chuyen-gia"].route, tabs: [[SHEETS["chuyen-gia"].label, SHEETS["chuyen-gia"].route]]},
};
// the toolbar: the bank's four sections (business feedback 2, 2026-10-22). Bộ nhớ is not on it (UX_TOOLBAR_PLAN T2):
// the header and the assistant's panel open it, and its address still works.
export const TOOLBAR = [
  {id: "tong-quan", label: "Wealth View", icon: "map", tip: "Wealth View: tài sản ròng, phân bổ, dòng tiền và từng khoản", href: SECTIONS["tong-quan"].home},
  {id: "muc-tieu", label: "Wealth Planning Advisor", icon: "target", tip: "Wealth Planning Advisor: kế hoạch theo mục tiêu và bài test rủi ro", href: SECTIONS["muc-tieu"].home},
  {id: "tin", label: "Headline News", icon: "news", tip: "Headline News: tin, sự kiện và chính sách tác động tới tài sản", href: SECTIONS["tin"].home},
  {id: "chuyen-gia", label: "Relationship specialist", icon: "users", tip: "Relationship specialist: chuyên viên phụ trách bạn", href: SECTIONS["chuyen-gia"].home, sheet: true},
];
export const SECTION_NAME = Object.fromEntries(TOOLBAR.map(t => [t.id, t.label]));

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
// the graph's addresses (no graph for the client, ADR-0037): each lens → its section's page; Dòng tiền's own page
// is the dashboard's cash part
const GRAPH = {"tong-quan": {home: true}, "dong-tien": {part: "cash"}, "rui-ro": {part: "risk"},
  "tai-san": {sheet: "tai-san"}, "muc-tieu": {sheet: "ke-hoach"}, "tin": {sheet: "thi-truong"}};

/* The address's parts after the role → {lens (or null: keep the current one), sheet (or null), param}, and a
   dashboard section to open (part) for Toàn cảnh's and Chi tiết's addresses, and the home (B3.1): the dashboard at
   its top. */
export function resolve(parts) {
  const [a, b, c] = parts;
  const home = {lens: "tong-quan", sheet: null, param: null, home: true};
  if (BOARD[`${a}/${b}`]) return {lens: "tong-quan", sheet: null, param: null, part: BOARD[`${a}/${b}`]};
  if (!a || a === "tong-quan" && (!b || b === "ban-do")) return home;
  const g = a === "xem" ? GRAPH[b] || GRAPH["tong-quan"] : a === "dong-tien" ? GRAPH["dong-tien"] : null;
  if (g && g.part) return {lens: "tong-quan", sheet: null, param: null, part: g.part};
  const two = b && OLD[`${a}/${b}`];
  const id = g ? g.sheet : two || OLD[a];
  if (!id) return home;
  const s = SHEETS[id];
  return {lens: s.lens, sheet: id, param: g ? null : two ? c || null : b || null};
}

/* A page module's ctx.href(nav, sub, param) inside the workspace: the same old addresses (they open sheets). */
export function href(nav, sub, param) {
  return `#/client/${[nav, sub, param].filter(Boolean).map(encodeURIComponent).join("/")}`;
}
