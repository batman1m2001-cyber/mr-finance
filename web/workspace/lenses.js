/* The Customer workspace's lenses and addresses (FEAT-40, ADR-0035). A lens is a view of the one graph: which kinds
   show, which classes open, what the inspector says first. `#/client/xem/<lens>` is a lens alone; every older
   Customer address still names its page, which opens as a sheet over the graph, with the lens that page belongs to —
   so the server's links (citations, search, the bell) need no change. */

export const LENSES = [
  {id: "tong-quan", label: "Tổng quan", icon: "map", tip: "Tổng quan: toàn bộ bức tranh tài chính",
    kinds: ["family", "class", "flow", "liquidity", "goal", "risk", "event"], sheets: ["toan-canh", "chi-tiet"]},
  {id: "tai-san", label: "Tài sản", icon: "wallet", tip: "Tài sản: từng khoản và nguồn dữ liệu",
    kinds: ["family", "class", "holding", "source"], sheets: ["tai-san"]},
  {id: "dong-tien", label: "Dòng tiền", icon: "flow", tip: "Dòng tiền: thu nhập, chi tiêu, thanh khoản",
    kinds: ["family", "flow", "category", "liquidity", "class"], sheets: ["toan-canh"]},
  {id: "muc-tieu", label: "Mục tiêu & kịch bản", icon: "target", tip: "Mục tiêu và kịch bản giả định",
    kinds: ["family", "goal", "scenario"], sheets: ["ke-hoach"]},
  {id: "tin", label: "Tin & sự kiện", icon: "news", tip: "Tin tức, sự kiện và chính sách có thể tác động",
    kinds: ["family", "event", "alert", "class"], sheets: ["thi-truong", "do-thi", "chinh-sach"]},
  {id: "rui-ro", label: "Rủi ro", icon: "alert", tip: "Rủi ro: mức lỗ khi căng thẳng, tập trung, dự phòng",
    kinds: ["family", "risk", "liquidity", "class"], sheets: ["khau-vi", "chi-tiet"]},
];
export const LENS = Object.fromEntries(LENSES.map(l => [l.id, l]));

// the dedicated views: each an existing page module, at its old address (ADR-0035 §3)
export const SHEETS = {
  "toan-canh": {page: "pulse", label: "Toàn cảnh", route: "#/client/tong-quan/toan-canh", lens: "tong-quan", nav: ["tong-quan", "toan-canh"]},
  "chi-tiet": {page: "detail", label: "Chi tiết tài sản", route: "#/client/tong-quan/chi-tiet", lens: "tong-quan", nav: ["tong-quan", "chi-tiet"]},
  "tai-san": {page: "holdings", label: "Tài sản", route: "#/client/tai-san", lens: "tai-san", nav: ["tai-san"]},
  "ke-hoach": {page: "plan", label: "Kế hoạch", route: "#/client/muc-tieu/ke-hoach", lens: "muc-tieu", nav: ["muc-tieu", "ke-hoach"]},
  "khau-vi": {page: "risktest", label: "Khẩu vị rủi ro", route: "#/client/muc-tieu/khau-vi", lens: "rui-ro", nav: ["muc-tieu", "khau-vi"]},
  "thi-truong": {page: "impact", label: "Tác động thị trường", route: "#/client/tin/thi-truong", lens: "tin", nav: ["tin", "thi-truong"]},
  "do-thi": {page: "graph", label: "Đồ thị tác động", route: "#/client/tin/do-thi", lens: "tin", nav: ["tin", "do-thi"]},
  "chinh-sach": {page: "policy", label: "Chi phí chính sách", route: "#/client/tin/chinh-sach", lens: "tin", nav: ["tin", "chinh-sach"]},
  "chuyen-gia": {page: "advisor", label: "Chuyên gia", route: "#/client/chuyen-gia", lens: null, nav: ["chuyen-gia"]},
  "bo-nho": {page: "memory", label: "Bộ nhớ", route: "#/client/bo-nho", lens: null, nav: ["bo-nho"]},
};
// the toolbar: the lenses, then the two dedicated views (OWN-GW-05: Experts may stay a separate view)
export const TOOLBAR = [...LENSES.map(l => ({...l, href: lensRoute(l.id)})),
  {id: "chuyen-gia", label: "Chuyên gia", icon: "users", tip: "Chuyên gia: liên hệ đội ngũ tư vấn", href: SHEETS["chuyen-gia"].route, sheet: true},
  {id: "bo-nho", label: "Bộ nhớ", icon: "history", tip: "Bộ nhớ: điều trợ lý ghi nhớ về bạn", href: SHEETS["bo-nho"].route, sheet: true}];

export function lensRoute(id) { return `#/client/xem/${id}`; }

// the old addresses: [first, second] → sheet id; a bare first segment with subpages opens its first one
const OLD = {
  "tong-quan/toan-canh": "toan-canh", "tong-quan/chi-tiet": "chi-tiet", "tai-san": "tai-san",
  "muc-tieu": "ke-hoach", "muc-tieu/ke-hoach": "ke-hoach", "muc-tieu/khau-vi": "khau-vi",
  "tin": "thi-truong", "tin/thi-truong": "thi-truong", "tin/do-thi": "do-thi", "tin/chinh-sach": "chinh-sach",
  "chuyen-gia": "chuyen-gia", "bo-nho": "bo-nho",
};

/* The address's parts after the role → {lens (or null: keep the current one), sheet (or null), param}. */
export function resolve(parts) {
  const [a, b, c] = parts;
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
