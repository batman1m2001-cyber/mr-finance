import SwiftUI
import Charts

/// Tổng quan: the website's Toàn cảnh on a phone — net worth, this month's money, the last six months,
/// allocation, risk against the limit, the reserve. Every figure from POST /api/dashboard.
struct OverviewView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    if let d = model.dashboard {
                        VStack(spacing: 16) {
                            NetWorthCard(d: d)
                            MonthCard(d: d)
                            AllocationCard(d: d).id("allocation")
                            RiskCard(d: d).id("risk")
                            ReserveCard(d: d)
                            Text("Số liệu đến \(Fmt.day(d.asOf))").font(.footnote).foregroundStyle(Theme.muted)
                        }
                        .padding(.horizontal, 16).padding(.vertical, 8)
                        .task { try? await Task.sleep(for: .milliseconds(400)); screenshotScroll(proxy) }
                    } else {
                        Loading(error: model.error) { await model.refresh() }
                    }
                }
                .background(Theme.plane)
                .refreshable { await model.refresh() }
                .navigationTitle("Tổng quan")
                .toolbar { ToolbarItem(placement: .topBarTrailing) { AccountMenu() } }
            }
        }
    }
}

struct AccountMenu: View {
    @Environment(AppModel.self) private var model
    @AppStorage("theme") private var theme = "light"

    var body: some View {
        Menu {
            if let u = model.user {
                Text(u.name)
                if let t = u.title { Text(t) }
            }
            Toggle(isOn: Binding(get: { theme == "dark" }, set: { theme = $0 ? "dark" : "light" })) {
                Label("Giao diện tối", systemImage: "moon")
            }
            Button(role: .destructive) { Task { await model.logout() } } label: {
                Label("Đăng xuất", systemImage: "rectangle.portrait.and.arrow.right")
            }
        } label: {
            Image(systemName: "person.crop.circle").font(.title3)
        }
        .accessibilityLabel("Tài khoản")
    }
}

private struct NetWorthCard: View {
    let d: Dashboard

    var body: some View {
        let nw = d.netWorth
        Card {
            VStack(alignment: .leading, spacing: 6) {
                Text("Tài sản ròng của \(d.profile.name)").font(.subheadline).foregroundStyle(Theme.ink2)
                Text(Fmt.vnd(nw.value)).font(.system(size: 40, weight: .bold, design: .rounded))
                    .foregroundStyle(Theme.navy).monospacedDigit()
                Capsule().fill(Theme.gold).frame(width: 44, height: 3).accessibilityHidden(true)
                if let ch = nw.monthChange {
                    HStack(spacing: 6) {
                        Image(systemName: ch >= 0 ? "arrow.up.right" : "arrow.down.right")
                        Text("\(Fmt.vnd(ch, signed: true)) (\(Fmt.pct(nw.monthChangePct, signed: true))) so với tháng trước")
                    }
                    .font(.subheadline.weight(.semibold)).foregroundStyle(Theme.signed(ch))
                }
            }
            Divider()
            Row(label: "Tài sản", value: Fmt.vnd(nw.assets))
            Row(label: "Khoản nợ", value: Fmt.vnd(nw.liabilities))
        }
    }
}

private struct MonthCard: View {
    let d: Dashboard

    var body: some View {
        let past = Array(d.cashflow.history.suffix(6))
        Card(title: d.cashflow.current.map { "Dòng tiền \(Fmt.month($0.month))" } ?? "Dòng tiền") {
            if let c = d.cashflow.current {
                Row(label: "Tiền vào", value: Fmt.vnd(c.inflow), tint: Theme.good)
                Row(label: "Tiền ra", value: Fmt.vnd(c.out))
                Row(label: "Còn lại", value: Fmt.vnd(c.net, signed: true), tint: Theme.signed(c.net))
            }
            if !past.isEmpty {
                Text("6 tháng qua").font(.footnote.weight(.semibold)).foregroundStyle(Theme.muted).padding(.top, 4)
                Chart {
                    ForEach(past) { m in
                        BarMark(x: .value("Tháng", Fmt.month(m.month, short: true)), y: .value("Số tiền", m.inflow / 1e6))
                            .foregroundStyle(by: .value("Loại", "Tiền vào"))
                            .position(by: .value("Loại", "Tiền vào"))
                            .cornerRadius(4)
                        BarMark(x: .value("Tháng", Fmt.month(m.month, short: true)), y: .value("Số tiền", m.out / 1e6))
                            .foregroundStyle(by: .value("Loại", "Tiền ra"))
                            .position(by: .value("Loại", "Tiền ra"))
                            .cornerRadius(4)
                    }
                }
                .chartForegroundStyleScale(["Tiền vào": Theme.good, "Tiền ra": Theme.series])
                .chartYAxis {
                    AxisMarks(position: .leading) { v in
                        AxisGridLine().foregroundStyle(Theme.hair)
                        AxisValueLabel { if let x = v.as(Double.self) { Text(Fmt.vn(x, 0)) } }
                    }
                }
                .chartYAxisLabel("triệu đồng")
                .chartLegend(position: .top, alignment: .leading)
                .frame(height: 180)
                .accessibilityLabel("Tiền vào và tiền ra 6 tháng qua")
            }
        }
    }
}

private struct AllocationCard: View {
    let d: Dashboard

    var body: some View {
        Card(title: "Phân bổ tài sản") {
            ForEach(d.allocation.filter { $0.value > 0 }) { s in
                VStack(alignment: .leading, spacing: 6) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(s.group).foregroundStyle(Theme.ink)
                        Spacer()
                        Text(Fmt.vnd(s.value)).fontWeight(.semibold).foregroundStyle(Theme.ink).monospacedDigit()
                        Text(Fmt.pct(s.share, digits: 0)).foregroundStyle(Theme.muted).monospacedDigit()
                            .frame(minWidth: 44, alignment: .trailing)
                    }
                    .font(.subheadline)
                    GeometryReader { g in
                        Capsule().fill(Theme.surface2)
                            .overlay(alignment: .leading) {
                                Capsule().fill(Theme.series).frame(width: max(4, g.size.width * s.share))
                            }
                    }
                    .frame(height: 6)
                    .accessibilityHidden(true)
                }
            }
        }
    }
}

private struct RiskCard: View {
    let d: Dashboard

    var body: some View {
        let r = d.risk
        Card(title: "Rủi ro") {
            Row(label: "Ngưỡng sụt giảm chấp nhận", value: Fmt.pct(r.limit, digits: 0))
            Row(label: "Sụt giảm ước tính khi thị trường xấu", value: Fmt.pct(r.current))
            Meter(value: r.current, mark: r.limit, max: Swift.max(r.limit * 1.6, r.current * 1.1), status: Status.of(r.status).0)
                .padding(.vertical, 4)
            HStack(spacing: 8) {
                Pill(status: r.status)
                if let loss = r.stressLoss {
                    Text("mất \(Fmt.vnd(loss)) trong kịch bản xấu").font(.footnote).foregroundStyle(Theme.muted)
                }
            }
        }
    }
}

private struct ReserveCard: View {
    let d: Dashboard

    var body: some View {
        let l = d.liquidity
        let top = Swift.max(12, Swift.min(l.months, 36))
        Card(title: "Thanh khoản dự phòng") {
            Row(label: "Tiền và tài sản rút được ngay", value: Fmt.vnd(l.value))
            Row(label: "Đủ chi", value: monthsText(l.months))
            Meter(value: Swift.min(l.months, top), mark: 6, max: top, status: Status.of(l.status).0)
                .padding(.vertical, 4)
            HStack(spacing: 8) {
                Pill(status: l.status)
                if let s = l.spendingMonthly {
                    Text("chi tiêu \(Fmt.vnd(s))/tháng · mốc an toàn 6 tháng").font(.footnote).foregroundStyle(Theme.muted)
                }
            }
        }
    }
}
