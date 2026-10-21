import Foundation

/// The server's answers, as the website reads them (app/web.py). Decoded with `.convertFromSnakeCase`;
/// every field the app does not need is left out, and those the server may omit are optional.

struct User: Codable, Equatable {
    let id: String
    let name: String
    let role: String
    let title: String?
    let family: String?
}

struct Me: Codable {
    let user: User?
    let auth: Bool?
    let demoAccounts: Bool?
}

struct Account: Codable, Identifiable {
    let id: String
    let name: String
    let role: String
    let title: String?
    let login: String?
}

struct Accounts: Codable { let accounts: [Account] }
struct SignedIn: Codable { let user: User? }
struct DashboardReply: Codable { let dashboard: Dashboard }

struct Dashboard: Codable {
    let asOf: String
    let profile: Profile
    let netWorth: NetWorth
    let allocation: [Slice]
    let performance: Performance?
    let risk: Risk
    let liquidity: Liquidity
    let cashflow: Cashflow
    let holdings: [Holding]
}

struct Profile: Codable {
    let name: String
    let age: Int?
    let occupation: String?
    let segment: String?
    let riskProfile: String?
}

struct NetWorth: Codable {
    let value: Double
    let assets: Double
    let liabilities: Double
    let prevValue: Double?
    let monthChange: Double?
    let monthChangePct: Double?
}

struct Slice: Codable, Identifiable {
    let group: String
    let value: Double
    let share: Double
    let pnl: Double?
    let ret: Double?
    var id: String { group }
    enum CodingKeys: String, CodingKey { case group, value, share, pnl, ret = "return" }
}

struct Performance: Codable {
    let realizedYtd: Double?
    let unrealized: Double?
    let unrealizedPct: Double?
    let ytdReturn: Double?
    let benchmarkName: String?
    let benchmarkYtd: Double?
    let vsBenchmark: Double?
}

struct Risk: Codable {
    let limit: Double
    let current: Double
    let stressLoss: Double?
    let status: String
}

struct Liquidity: Codable {
    let value: Double
    let spendingMonthly: Double?
    let months: Double
    let status: String
    let items: [Named]
}

struct Named: Codable, Identifiable {
    let name: String
    let value: Double
    var id: String { name }
}

struct Cashflow: Codable {
    let history: [CashMonth]
    let current: CashMonth?
    let months: [CashMonth]
    let large: [CashItem]?
}

struct CashMonth: Codable, Identifiable {
    let month: String
    let inflow: Double
    let out: Double
    let net: Double
    let items: [CashItem]?
    var id: String { month }
    enum CodingKeys: String, CodingKey { case month, inflow = "in", out, net, items }
}

struct CashItem: Codable, Identifiable, Hashable {
    let direction: String
    let amount: Double
    let label: String
    let kind: String?
    let month: String?
    var id: Int { hashValue }
}

struct Holding: Codable, Identifiable {
    let key: String?
    let cls: String
    let name: String
    let value: Double
    let prevValue: Double?
    let cost: Double?
    let source: String?
    let trust: String?
    let ownerName: String?
    var id: String { key ?? name }
    enum CodingKeys: String, CodingKey { case key, cls = "class", name, value, prevValue, cost, source, trust, ownerName }
}

/// The status words of the website (web/pages/detail.js STATUS).
enum Status {
    case good, warn, bad
    static func of(_ s: String) -> (Status, String) {
        switch s {
        case "ok": return (.good, "An toàn")
        case "near": return (.warn, "Gần ngưỡng")
        case "over": return (.bad, "Vượt ngưỡng")
        case "low": return (.warn, "Thấp")
        case "critical": return (.bad, "Rất thấp")
        default: return (.warn, s)
        }
    }
}

/// web/charts/money.js monthsText: "41 tháng", "3 năm"
func monthsText(_ m: Double) -> String {
    m >= 36 ? Fmt.vn(m / 12, 0) + " năm" : Fmt.vn(m, m >= 10 ? 0 : 1) + " tháng"
}
