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
            VStack(spacing: 10) {
                Text("Tài sản ròng của \(d.profile.name)").font(.subheadline).foregroundStyle(Theme.ink2)
                GoldCoin(value: Fmt.vnd(nw.value)).frame(width: 170, height: 170)
                    .accessibilityLabel("Tài sản ròng \(Fmt.vnd(nw.value))")
                if let ch = nw.monthChange {
                    HStack(spacing: 6) {
                        Image(systemName: ch >= 0 ? "arrow.up.right" : "arrow.down.right")
                        Text("\(Fmt.vnd(ch, signed: true)) (\(Fmt.pct(nw.monthChangePct, signed: true))) so với tháng trước")
                    }
                    .font(.subheadline.weight(.semibold)).foregroundStyle(Theme.signed(ch))
                }
            }
            .frame(maxWidth: .infinity)
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

/// The net worth as the website's graph shows it: a polished gold coin — raised rim with a milled edge, a ring of
/// beads, a glint now and then — its one figure struck in a dark bronze serif over the lit lower edge of the cut.
struct GoldCoin: View {
    let value: String
    @Environment(\.accessibilityReduceMotion) private var still
    @State private var glint = false

    private static let hi = Color(red: 1, green: 246 / 255, blue: 207 / 255)
    private static let mid = Color(red: 230 / 255, green: 178 / 255, blue: 62 / 255)
    private static let deep = Color(red: 122 / 255, green: 78 / 255, blue: 8 / 255)
    private static let ink = Color(red: 28 / 255, green: 18 / 255, blue: 2 / 255)
    private static let lit = Color(red: 1, green: 243 / 255, blue: 196 / 255)

    var body: some View {
        GeometryReader { g in
            let w = min(g.size.width, g.size.height), r = w / 2
            ZStack {
                Circle().fill(RadialGradient(stops: [.init(color: Self.hi, location: 0), .init(color: Self.mid, location: 0.55),
                                                     .init(color: Self.deep, location: 1)],
                                             center: UnitPoint(x: 0.5, y: 0.34), startRadius: 0, endRadius: r * 1.44))
                    .shadow(color: Self.mid.opacity(0.45), radius: w * 0.08)  // the glow around it, as the website's aura
                Circle().fill(RadialGradient(colors: [Color(red: 1, green: 240 / 255, blue: 191 / 255).opacity(0.62), .clear],
                                             center: UnitPoint(x: 0.5, y: 0.46), startRadius: 0, endRadius: r * 0.9))
                Circle().strokeBorder(LinearGradient(stops: [.init(color: Self.hi, location: 0), .init(color: Self.mid, location: 0.22),
                                                            .init(color: Self.hi, location: 0.42), .init(color: Self.deep, location: 0.68),
                                                            .init(color: Self.mid, location: 0.86), .init(color: Self.hi, location: 1)],
                                                     startPoint: .topLeading, endPoint: .bottomTrailing), lineWidth: w * 0.056)
                Circle().stroke(Self.deep.opacity(0.5), style: StrokeStyle(lineWidth: 1.4, dash: [0.9, 1.6]))
                    .padding(0.7)  // the milled edge
                Circle().stroke(LinearGradient(colors: [Self.deep, Self.mid, Self.hi], startPoint: .topLeading, endPoint: .bottomTrailing),
                                lineWidth: 1.6).padding(w * 0.06)  // the bevel into the field
                Circle().stroke(Self.deep.opacity(0.55), style: StrokeStyle(lineWidth: 2, lineCap: .round, dash: [0, w * 0.035]))
                    .padding(w * 0.097)  // the ring of beads
                Rectangle().fill(LinearGradient(colors: [.clear, .white.opacity(0.7), .clear], startPoint: .leading, endPoint: .trailing))
                    .frame(width: w * 0.18, height: w * 1.4).rotationEffect(.degrees(28))
                    .offset(x: glint ? w : -w)
                    .mask(Circle())
                ZStack {
                    Text(value).foregroundStyle(Self.lit.opacity(0.9)).offset(x: 0.6, y: 0.8)
                    Text(value).foregroundStyle(Self.ink)
                }
                .font(.custom("Georgia-Bold", size: w * 0.2, relativeTo: .largeTitle))
                .monospacedDigit()
                .lineLimit(1).minimumScaleFactor(0.5)
                .frame(width: w * 0.7)  // inside the beads
            }
            .frame(width: w, height: w)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .task {  // a glint every six seconds, as the website's coin; none when the phone asks for less motion
            guard !still else { return }
            while !Task.isCancelled {
                glint = false
                try? await Task.sleep(for: .milliseconds(50))
                withAnimation(.easeInOut(duration: 1.8)) { glint = true }
                try? await Task.sleep(for: .seconds(6))
            }
        }
        .accessibilityElement(children: .ignore)
    }
}
