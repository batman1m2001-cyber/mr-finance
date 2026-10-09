/* Money and percentages as a Vietnamese reader says them (the twin of src/wealth/money.py). */
(function (g) {
  "use strict";
  const TY = 1e9, TR = 1e6;
  const vn = (x, d) => {
    let s = x.toFixed(d).replace(".", ",");
    if (s.includes(",")) s = s.replace(/0+$/, "").replace(/,$/, "");
    const [int, frac] = s.split(",");
    return int.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + (frac ? "," + frac : "");
  };
  function vnd(a, signed) {
    const sign = signed && a > 0 ? "+" : a < 0 ? "-" : "";
    const x = Math.abs(a);
    if (x >= TY) return sign + vn(x / TY, x < 10 * TY ? 2 : 1) + " tỷ";
    if (x >= TR) return sign + vn(x / TR, x >= 100 * TR ? 0 : 1) + " triệu";
    return sign + vn(x, 0) + " đ";
  }
  function pct(x, signed, digits) {
    const sign = signed && x > 0 ? "+" : x < 0 ? "-" : "";
    return sign + vn(Math.abs(x) * 100, digits == null ? 1 : digits) + "%";
  }
  function months(m) { return m >= 36 ? vn(m / 12, 0) + " năm" : vn(m, m >= 10 ? 0 : 1) + " tháng"; }
  function monthName(ym) { return "T" + Number(ym.slice(5, 7)) + "/" + ym.slice(2, 4); }
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  g.Fmt = {vnd, pct, months, monthName, esc};
})(window);
