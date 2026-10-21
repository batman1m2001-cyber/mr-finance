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
    let recurring: [Recurring]?
}

struct Recurring: Codable, Hashable {
    let direction: String
    let label: String
    let amount: Double
    let cadence: String?
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

// MARK: Dòng tiền — POST /api/flows: last month's money by category, from the account's transactions

struct FlowsReply: Codable { let flows: Flows }

struct Flows: Codable {
    let month: String
    let inflow: [FlowCategory]
    let outflow: [FlowCategory]
    let totalIn: Double
    let totalOut: Double
    let left: Double
    let source: String?
}

struct FlowCategory: Codable, Identifiable {
    let category: String
    let label: String
    let amount: Double
    let rows: [FlowRow]
    var id: String { category + label }
}

struct FlowRow: Codable, Hashable {
    let date: String
    let amount: Double
    let desc: String?
}

// MARK: Tin tức — GET /api/families/<id>/impact?role=client: what the CIO-approved news does to the family

struct Impact: Codable {
    let items: [ImpactItem]
    let effectiveExpected3m: Double?
    let effectiveCount: Int?
    let labels: ImpactLabels?
}

struct ImpactLabels: Codable {
    let note: String?
    let responsible: String?
}

struct ImpactItem: Codable, Identifiable {
    let runId: String
    let status: String
    let statusLabel: String?
    let event: ImpactEvent
    let priceDate: String?
    let netWorth: Double?
    /// "1w", "3m", "12m"
    let horizons: [String: Band]
    /// by asset class; the decoder camel-cases these keys too ("real_estate" → "realEstate")
    let byClass: [String: Double]
    let timeline: [ImpactStep]?
    let sources: ImpactSources?
    var id: String { runId }
    var effective: Bool { status == "EFFECTIVE" }
}

struct ImpactEvent: Codable { let id: String; let title: String }
struct Band: Codable { let expected: Double; let p10: Double; let p50: Double; let p90: Double }
struct ImpactStep: Codable, Hashable { let at: Double; let step: String; let label: String }
struct ImpactSources: Codable { let outlets: [String]?; let count: Int? }

// MARK: Trợ lý — POST /api/assistant

struct AssistantReply: Codable { let assistant: AssistantTurn }

struct AssistantTurn: Codable {
    let text: String?
    let status: String?
    let steps: [AssistantStep]?
    let conversationId: String?
    let suggest: [String]?
    let turnId: String?
    let waits: [AssistantWait]?
}

struct AssistantStep: Codable, Hashable { let label: String?; let tool: String?; let status: String? }
struct AssistantWait: Codable, Hashable { let id: String; let label: String? }

/// src/wealth/labels.py CLASSES, under both spellings of a key (see ImpactItem.byClass)
func classLabel(_ key: String) -> String {
    let labels = [
        "cash": "Tiền mặt & thanh toán", "deposit": "Tiền gửi", "stock": "Cổ phiếu", "bond": "Trái phiếu",
        "fund": "Chứng chỉ quỹ", "real_estate": "Bất động sản", "realEstate": "Bất động sản", "gold": "Vàng",
        "business": "Cổ phần doanh nghiệp", "insurance": "Bảo hiểm", "crypto": "Tài sản số", "loan": "Khoản vay",
        "card": "Dư nợ thẻ",
    ]
    return labels[key] ?? key
}

/// src/wealth/labels.py SOURCES
func sourceLabel(_ key: String?) -> String {
    let labels = [
        "techcombank": "Techcombank", "tcbs": "TCBS", "techcom_capital": "Techcom Capital", "onehousing": "OneHousing",
        "declared": "Bạn tự khai", "statement": "Sao kê tải lên", "open_api": "Open API (ngân hàng / CTCK khác)",
    ]
    guard let key else { return "" }
    return labels[key] ?? key
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
