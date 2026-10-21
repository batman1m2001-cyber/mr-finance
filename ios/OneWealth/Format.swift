import Foundation

/// Money, shares and months written as the website writes them (web/core/core.js `vnd`, `pct`):
/// "43,5 tỷ", "−90 triệu", "+2,3%", "Th10/2026".
enum Fmt {
    private static let ty = 1e9, tr = 1e6

    /// `x` with `d` decimals, a comma for the decimal point, dots between thousands, no trailing zeros.
    static func vn(_ x: Double, _ d: Int) -> String {
        let f = pow(10, Double(d))  // half away from zero, as JavaScript's toFixed: 980,5 triệu → "981 triệu"
        var s = String(format: "%.\(d)f", (x * f).rounded(.toNearestOrAwayFromZero) / f).replacingOccurrences(of: ".", with: ",")
        if s.contains(",") {
            while s.hasSuffix("0") { s.removeLast() }
            if s.hasSuffix(",") { s.removeLast() }
        }
        let parts = s.split(separator: ",", maxSplits: 1).map(String.init)
        var int = parts[0], grouped = ""
        while int.count > 3 {
            grouped = "." + int.suffix(3) + grouped
            int = String(int.dropLast(3))
        }
        return int + grouped + (parts.count > 1 ? "," + parts[1] : "")
    }

    static func vnd(_ a: Double?, signed: Bool = false) -> String {
        guard let a, !a.isNaN else { return "—" }
        let sign = signed && a > 0 ? "+" : a < 0 ? "−" : ""
        let x = abs(a)
        if x >= ty { return sign + vn(x / ty, x < 10 * ty ? 2 : 1) + " tỷ" }
        if x >= tr { return sign + vn(x / tr, x >= 100 * tr ? 0 : 1) + " triệu" }
        if x >= 1e3 { return sign + vn(x / 1e3, x >= 1e5 ? 0 : 1) + " nghìn" }
        return sign + vn(x, 0) + " đ"
    }

    static func pct(_ x: Double?, signed: Bool = false, digits: Int = 1) -> String {
        guard let x, !x.isNaN else { return "—" }
        let sign = signed && x > 0 ? "+" : x < 0 ? "−" : ""
        return sign + vn(abs(x) * 100, digits) + "%"
    }

    /// "2026-10" → "Th10/2026"; "2026-10" with `short` → "T10"
    static func month(_ ym: String, short: Bool = false) -> String {
        let p = ym.split(separator: "-")
        guard p.count >= 2, let m = Int(p[1]) else { return ym }
        return short ? "T\(m)" : "Th\(m)/\(p[0])"
    }

    /// "2026-10" → "10/2026", after the word "tháng"
    static func monthNumber(_ ym: String) -> String {
        let p = ym.split(separator: "-")
        guard p.count >= 2, let m = Int(p[1]) else { return ym }
        return "\(m)/\(p[0])"
    }

    /// "2026-10-09" → "09/10/2026"
    static func day(_ iso: String) -> String {
        let p = iso.prefix(10).split(separator: "-")
        guard p.count == 3 else { return iso }
        return "\(p[2])/\(p[1])/\(p[0])"
    }
}
