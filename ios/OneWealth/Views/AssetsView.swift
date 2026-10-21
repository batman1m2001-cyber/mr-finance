import SwiftUI

/// Tài sản: every holding of the dashboard, grouped by class as the website's Tài sản page — value, cost and profit,
/// where the figure comes from; the debts under them.
struct AssetsView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        NavigationStack {
            ScrollView {
                if let d = model.dashboard {
                    let assets = d.holdings.filter { !Self.debts.contains($0.cls) }
                    let debts = d.holdings.filter { Self.debts.contains($0.cls) }
                    VStack(spacing: 16) {
                        Card {
                            Row(label: "Tổng tài sản", value: Fmt.vnd(d.netWorth.assets))
                            Row(label: "Khoản nợ", value: Fmt.vnd(d.netWorth.liabilities))
                            Divider()
                            Row(label: "Tài sản ròng", value: Fmt.vnd(d.netWorth.value))
                            if let p = d.performance, let ytd = p.ytdReturn {
                                Row(label: "Lợi nhuận đầu tư từ đầu năm", value: Fmt.pct(ytd, signed: true), tint: Theme.signed(ytd))
                                if let b = p.benchmarkYtd, let name = p.benchmarkName {
                                    Row(label: "\(name) cùng kỳ", value: Fmt.pct(b, signed: true))
                                }
                            }
                        }
                        ForEach(Self.groups(assets)) { g in
                            HoldingGroup(title: classLabel(g.cls), items: g.items)
                        }
                        if !debts.isEmpty { HoldingGroup(title: "Khoản nợ", items: debts, debt: true) }
                        Text("Số liệu đến \(Fmt.day(d.asOf))").font(.footnote).foregroundStyle(Theme.muted)
                    }
                    .padding(.horizontal, 16).padding(.vertical, 8)
                } else {
                    Loading(error: model.error) { await model.refresh() }
                }
            }
            .background(Theme.plane)
            .refreshable { await model.refresh() }
            .navigationTitle("Tài sản")
            .toolbar { ToolbarItem(placement: .topBarTrailing) { AccountMenu() } }
        }
    }

    static let debts: Set<String> = ["loan", "card"]

    struct Group: Identifiable {
        let cls: String
        let items: [Holding]
        var id: String { cls }
        var total: Double { items.reduce(0) { $0 + $1.value } }
    }

    /// classes by their total, largest first
    static func groups(_ items: [Holding]) -> [Group] {
        Dictionary(grouping: items, by: \.cls)
            .map { Group(cls: $0.key, items: $0.value.sorted { $0.value > $1.value }) }
            .sorted { $0.total > $1.total }
    }
}

private struct HoldingGroup: View {
    let title: String
    let items: [Holding]
    var debt = false

    var body: some View {
        Card {
            HStack(alignment: .firstTextBaseline) {
                Text(title).font(.headline).foregroundStyle(Theme.ink)
                Spacer()
                Text(Fmt.vnd(items.reduce(0) { $0 + $1.value })).font(.headline).foregroundStyle(Theme.ink).monospacedDigit()
            }
            ForEach(Array(items.enumerated()), id: \.offset) { i, h in
                if i > 0 { Divider() }
                VStack(alignment: .leading, spacing: 4) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(h.name).foregroundStyle(Theme.ink)
                        Spacer(minLength: 12)
                        Text(Fmt.vnd(h.value)).fontWeight(.semibold).foregroundStyle(Theme.ink).monospacedDigit()
                    }
                    .font(.subheadline)
                    HStack(alignment: .firstTextBaseline) {
                        Text(sourceLabel(h.source)).foregroundStyle(Theme.muted)
                        Spacer(minLength: 12)
                        if !debt, let cost = h.cost, cost > 0 {
                            let pnl = h.value - cost
                            Text("\(Fmt.vnd(pnl, signed: true)) (\(Fmt.pct(pnl / cost, signed: true)))")
                                .foregroundStyle(Theme.signed(pnl)).monospacedDigit()
                        }
                    }
                    .font(.footnote)
                }
            }
        }
    }
}

/// While a screen's figures load, or why they did not, with a way to try again.
struct Loading: View {
    let error: String?
    let retry: () async -> Void

    var body: some View {
        if let error {
            ContentUnavailableView {
                Label("Chưa tải được", systemImage: "wifi.exclamationmark")
            } description: { Text(error) } actions: {
                Button("Thử lại") { Task { await retry() } }.buttonStyle(PrimaryButton())
            }
            .padding(.top, 80)
        } else {
            ProgressView().controlSize(.large).padding(.top, 120)
        }
    }
}
