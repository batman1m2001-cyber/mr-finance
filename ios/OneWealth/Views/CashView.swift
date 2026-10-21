import SwiftUI
import Charts

/// Dòng tiền: what is left each month, six months past and twelve ahead (POST /api/dashboard), last month's money by
/// category from the account's transactions (POST /api/flows), the large payments ahead and the recurring items.
struct CashView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    if let d = model.dashboard {
                        VStack(spacing: 16) {
                            NetChart(cash: d.cashflow)
                            if let f = model.flows {
                                MonthFlows(f: f).id("month")
                            } else if let e = model.flowsError {
                                Card(title: "Tháng trước") { Text(e).font(.subheadline).foregroundStyle(Theme.critical) }
                            }
                            if let large = d.cashflow.large, !large.isEmpty { LargeCard(items: large).id("large") }
                            if let rec = d.cashflow.recurring, !rec.isEmpty { RecurringCard(items: rec) }
                        }
                        .padding(.horizontal, 16).padding(.vertical, 8)
                        .task {
                            if model.flows == nil { await model.loadFlows() }
                            try? await Task.sleep(for: .milliseconds(400))
                            screenshotScroll(proxy)
                        }
                    } else {
                        Loading(error: model.error) { await model.refresh() }
                    }
                }
                .background(Theme.plane)
                .refreshable { await model.refresh(); await model.loadFlows() }
                .navigationTitle("Dòng tiền")
                .toolbar { ToolbarItem(placement: .topBarTrailing) { AccountMenu() } }
            }
        }
    }
}

/// MF_SCROLL=<card id> on the CI screenshot runs (docs/IOS_APP_PLAN.md)
func screenshotScroll(_ proxy: ScrollViewProxy) {
    #if targetEnvironment(simulator)
    if let id = ProcessInfo.processInfo.environment["MF_SCROLL"] { proxy.scrollTo(id, anchor: .top) }
    #endif
}

private struct NetChart: View {
    let cash: Cashflow

    private struct Bar: Identifiable {
        let month: String
        let net: Double
        let kind: String
        var id: String { month }
    }

    var body: some View {
        let past = cash.history.suffix(6).map { Bar(month: $0.month, net: $0.net / 1e6, kind: "Đã có") }
        let ahead = cash.months.map { Bar(month: $0.month, net: $0.net / 1e6, kind: "Dự kiến") }
        let bars = past + ahead
        let low = ahead.min { $0.net < $1.net }
        Card(title: "Còn lại mỗi tháng") {
            Text("Tiền vào trừ tiền ra, 6 tháng qua và 12 tháng tới").font(.footnote).foregroundStyle(Theme.muted)
            Chart(bars) { b in
                BarMark(x: .value("Tháng", b.month), y: .value("Còn lại", b.net), width: .ratio(0.7))
                    .foregroundStyle(by: .value("Loại", b.kind))
                    .cornerRadius(3)
                RuleMark(y: .value("0", 0)).foregroundStyle(Theme.ink2).lineStyle(StrokeStyle(lineWidth: 1))
            }
            .chartForegroundStyleScale(["Đã có": Theme.series, "Dự kiến": Theme.series.opacity(0.35)])
            .chartXAxis {
                AxisMarks(values: bars.enumerated().filter { $0.offset % 3 == 0 }.map(\.element.month)) { v in
                    AxisValueLabel { if let m = v.as(String.self) { Text(Fmt.month(m, short: true)) } }
                }
            }
            .chartYAxis {
                AxisMarks(position: .leading) { v in
                    AxisGridLine().foregroundStyle(Theme.hair)
                    AxisValueLabel { if let x = v.as(Double.self) { Text(Fmt.vn(x, 0)) } }
                }
            }
            .chartYAxisLabel("triệu đồng")
            .chartLegend(position: .top, alignment: .leading)
            .frame(height: 200)
            .accessibilityLabel("Còn lại mỗi tháng, 6 tháng qua và 12 tháng tới")
            if let low, low.net < 0 {
                Label("Tháng \(Fmt.month(low.month)) dự kiến thiếu \(Fmt.vnd(-low.net * 1e6))", systemImage: "exclamationmark.triangle.fill")
                    .font(.subheadline.weight(.semibold)).foregroundStyle(Theme.warning)
            }
            let tin = cash.months.reduce(0) { $0 + $1.inflow }, tout = cash.months.reduce(0) { $0 + $1.out }
            Row(label: "12 tháng tới: tiền vào", value: Fmt.vnd(tin), tint: Theme.good)
            Row(label: "12 tháng tới: tiền ra", value: Fmt.vnd(tout))
        }
    }
}

private struct MonthFlows: View {
    let f: Flows

    var body: some View {
        Card(title: "Tháng \(Fmt.month(f.month))") {
            Row(label: "Tiền vào", value: Fmt.vnd(f.totalIn), tint: Theme.good)
            Row(label: "Tiền ra", value: Fmt.vnd(f.totalOut))
            Row(label: "Còn lại", value: Fmt.vnd(f.left, signed: true), tint: Theme.signed(f.left))
            if !f.inflow.isEmpty { Categories(title: "Tiền vào", items: f.inflow) }
            if !f.outflow.isEmpty { Categories(title: "Tiền ra", items: f.outflow) }
            if let s = f.source { Text("Theo \(s)").font(.footnote).foregroundStyle(Theme.muted) }
        }
    }
}

private struct Categories: View {
    let title: String
    let items: [FlowCategory]

    var body: some View {
        Text(title).font(.footnote.weight(.semibold)).foregroundStyle(Theme.muted).padding(.top, 6)
        ForEach(items) { c in
            DisclosureGroup {
                ForEach(c.rows, id: \.self) { r in
                    HStack(alignment: .firstTextBaseline) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(r.desc ?? c.label).font(.footnote).foregroundStyle(Theme.ink2).lineLimit(2)
                            Text(Fmt.day(r.date)).font(.caption).foregroundStyle(Theme.muted)
                        }
                        Spacer(minLength: 12)
                        Text(Fmt.vnd(r.amount)).font(.footnote).foregroundStyle(Theme.ink2).monospacedDigit()
                    }
                    .padding(.vertical, 2)
                }
            } label: {
                HStack(alignment: .firstTextBaseline) {
                    Text(c.label).foregroundStyle(Theme.ink)
                    Spacer(minLength: 12)
                    Text(Fmt.vnd(c.amount)).fontWeight(.semibold).foregroundStyle(Theme.ink).monospacedDigit()
                }
                .font(.subheadline)
            }
            .tint(Theme.muted)
        }
    }
}

private struct LargeCard: View {
    let items: [CashItem]

    var body: some View {
        Card(title: "Khoản lớn sắp tới") {
            ForEach(Array(items.enumerated()), id: \.offset) { _, i in
                HStack(alignment: .firstTextBaseline) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(i.label).font(.subheadline).foregroundStyle(Theme.ink)
                        if let m = i.month { Text(Fmt.month(m)).font(.footnote).foregroundStyle(Theme.muted) }
                    }
                    Spacer(minLength: 12)
                    Text(Fmt.vnd(i.direction == "out" ? -i.amount : i.amount, signed: true))
                        .font(.subheadline.weight(.semibold)).monospacedDigit()
                        .foregroundStyle(i.direction == "out" ? Theme.ink : Theme.good)
                }
            }
        }
    }
}

private struct RecurringCard: View {
    let items: [Recurring]
    private static let cadence = ["monthly": "hằng tháng", "quarterly": "hằng quý", "yearly": "hằng năm", "annual": "hằng năm",
                                  "weekly": "hằng tuần"]

    var body: some View {
        Card(title: "Khoản định kỳ") {
            ForEach(items, id: \.self) { r in
                HStack(alignment: .firstTextBaseline) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(r.label).font(.subheadline).foregroundStyle(Theme.ink)
                        if let c = r.cadence { Text(Self.cadence[c] ?? c).font(.footnote).foregroundStyle(Theme.muted) }
                    }
                    Spacer(minLength: 12)
                    Text(Fmt.vnd(r.direction == "out" ? -r.amount : r.amount, signed: true))
                        .font(.subheadline.weight(.semibold)).monospacedDigit()
                        .foregroundStyle(r.direction == "out" ? Theme.ink : Theme.good)
                }
            }
        }
    }
}
