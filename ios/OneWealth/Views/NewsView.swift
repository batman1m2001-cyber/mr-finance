import SwiftUI

/// Tin tức: what the CIO-approved news does to the family (the website's Tác động tin, client view) — the expected
/// change, the range it may fall in, through which asset classes, and each event from its first news to effect.
struct NewsView: View {
    @Environment(AppModel.self) private var model
    @State private var horizon = "3m"

    static let horizons = ["1w", "3m", "12m"]
    static let horizonLabel = ["1w": "1 tuần", "3m": "3 tháng", "12m": "12 tháng"]

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    if let d = model.impact {
                        content(d).padding(.horizontal, 16).padding(.vertical, 8)
                            .task { try? await Task.sleep(for: .milliseconds(400)); screenshotScroll(proxy) }
                    } else {
                        Loading(error: model.impactError) { await model.loadImpact() }
                    }
                }
                .background(Theme.plane)
                .refreshable { await model.loadImpact() }
                .navigationTitle("Tin tức")
                .toolbar { ToolbarItem(placement: .topBarTrailing) { AccountMenu() } }
            }
        }
        .task { if model.impact == nil { await model.loadImpact() } }
    }

    @ViewBuilder
    private func content(_ d: Impact) -> some View {
        let effective = d.items.filter(\.effective)
        if d.items.isEmpty {
            ContentUnavailableView("Chưa có tin nào", systemImage: "newspaper",
                                   description: Text("Khi có tin đáng chú ý đã được kiểm duyệt, tác động lên tài sản của bạn sẽ hiện ở đây."))
                .padding(.top, 60)
        } else {
            VStack(spacing: 16) {
                Picker("Khoảng thời gian", selection: $horizon) {
                    ForEach(Self.horizons, id: \.self) { Text(Self.horizonLabel[$0] ?? $0).tag($0) }
                }
                .pickerStyle(.segmented)
                Hero(items: effective, horizon: horizon, label: Self.horizonLabel[horizon] ?? horizon,
                     responsible: d.labels?.responsible)
                ByClass(items: effective, horizon: horizon).id("classes")
                ForEach(d.items) { EventCard(item: $0, horizon: horizon) }
                if let note = d.labels?.note {
                    Text(note).font(.footnote).foregroundStyle(Theme.muted).frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }
}

private struct Hero: View {
    let items: [ImpactItem]
    let horizon: String
    let label: String
    let responsible: String?

    var body: some View {
        let total = items.reduce(0) { $0 + ($1.horizons[horizon]?.expected ?? 0) }
        let nw = items.first?.netWorth ?? 0
        Card {
            Text("Tác động tin · \(label) tới").font(.subheadline).foregroundStyle(Theme.ink2)
            Text(Fmt.vnd(total, signed: true)).font(.system(size: 36, weight: .bold, design: .rounded))
                .foregroundStyle(Theme.signed(total)).monospacedDigit()
            Text(items.isEmpty ? "Chưa có sự kiện nào đang hiệu lực."
                 : "\(items.count) sự kiện đang có hiệu lực · \(Fmt.pct(nw > 0 ? total / nw : 0, signed: true, digits: 2)) tài sản ròng")
                .font(.subheadline).foregroundStyle(Theme.ink2)
            Label("AI hỗ trợ · CIO duyệt", systemImage: "checkmark.seal")
                .font(.footnote.weight(.semibold)).foregroundStyle(Theme.accent)
                .padding(.horizontal, 10).padding(.vertical, 4).background(Theme.accentSoft, in: Capsule())
            Text("Kỳ vọng = trung bình theo xác suất các kịch bản CIO duyệt."
                 + (items.first?.priceDate.map { " Giá ngày \(Fmt.day($0))." } ?? "")
                 + (responsible.map { " \($0)." } ?? ""))
                .font(.footnote).foregroundStyle(Theme.muted)
        }
    }
}

private struct ByClass: View {
    let items: [ImpactItem]
    let horizon: String

    private struct Part: Identifiable {
        let cls: String
        let value: Double
        var id: String { cls }
    }

    var body: some View {
        // the classes' amounts are the 3-month ones (by_class); scaled to the horizon by its share of the 3-month total
        var sums: [String: Double] = [:]
        for i in items {
            let k = (i.horizons["3m"]?.expected ?? 0) == 0 ? 0 : (i.horizons[horizon]?.expected ?? 0) / (i.horizons["3m"]?.expected ?? 1)
            for (c, v) in i.byClass where v != 0 { sums[c, default: 0] += v * k }
        }
        let rows = sums.sorted { abs($0.value) > abs($1.value) }.prefix(6).map { Part(cls: $0.key, value: $0.value) }
        let top = rows.map { abs($0.value) }.max() ?? 1
        return Card(title: "Đến từ đâu") {
            Text("Theo nhóm tài sản").font(.footnote).foregroundStyle(Theme.muted)
            ForEach(rows) { r in
                let c = r.cls, v = r.value
                VStack(alignment: .leading, spacing: 6) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(classLabel(c)).foregroundStyle(Theme.ink)
                        Spacer()
                        Text(Fmt.vnd(v, signed: true)).fontWeight(.semibold).foregroundStyle(Theme.signed(v)).monospacedDigit()
                    }
                    .font(.subheadline)
                    GeometryReader { g in
                        let half = g.size.width / 2, w = max(3, half * abs(v) / top)
                        ZStack(alignment: .leading) {
                            Capsule().fill(Theme.surface2)
                            Capsule().fill(Theme.signed(v)).frame(width: w).offset(x: v >= 0 ? half : half - w)
                            Rectangle().fill(Theme.ink2).frame(width: 1).offset(x: half)
                        }
                    }
                    .frame(height: 6)
                    .accessibilityHidden(true)
                }
            }
        }
    }
}

private struct EventCard: View {
    let item: ImpactItem
    let horizon: String

    private static let when: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm dd/MM"
        f.timeZone = TimeZone(identifier: "Asia/Ho_Chi_Minh")
        return f
    }()

    var body: some View {
        Card {
            HStack(alignment: .firstTextBaseline) {
                Text(item.event.title).font(.headline).foregroundStyle(Theme.ink)
                Spacer()
                Text(item.statusLabel ?? item.status).font(.footnote.weight(.semibold))
                    .foregroundStyle(item.effective ? Theme.good : Theme.muted)
                    .padding(.horizontal, 10).padding(.vertical, 4)
                    .background((item.effective ? Theme.good : Theme.muted).opacity(0.12), in: Capsule())
            }
            if let b = item.horizons[horizon] {
                Row(label: "Kỳ vọng", value: Fmt.vnd(b.expected, signed: true), tint: Theme.signed(b.expected))
                RangeBar(band: b)
                Text("8 trên 10 kịch bản rơi vào khoảng \(Fmt.vnd(b.p10, signed: true)) đến \(Fmt.vnd(b.p90, signed: true))")
                    .font(.footnote).foregroundStyle(Theme.muted)
            }
            if let steps = item.timeline, !steps.isEmpty {
                DisclosureGroup("Từ tin đầu tiên tới khi có hiệu lực") {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(steps, id: \.self) { s in
                            HStack {
                                Text(s.label).font(.footnote).foregroundStyle(Theme.ink2)
                                Spacer()
                                Text(Self.when.string(from: Date(timeIntervalSince1970: s.at)))
                                    .font(.footnote).foregroundStyle(Theme.muted).monospacedDigit()
                            }
                        }
                        if let o = item.sources?.outlets, !o.isEmpty {
                            Text("Nguồn: \(o.joined(separator: ", "))").font(.footnote).foregroundStyle(Theme.muted)
                        }
                    }
                    .padding(.top, 6)
                }
                .font(.subheadline).tint(Theme.muted)
            }
        }
    }
}

/// P10 to P90 on a line through zero, the expected value as a dot.
private struct RangeBar: View {
    let band: Band

    var body: some View {
        GeometryReader { g in
            let lo = min(band.p10, 0), hi = max(band.p90, 0), span = max(hi - lo, 1)
            let x = { (v: Double) in g.size.width * (v - lo) / span }
            ZStack(alignment: .leading) {
                Capsule().fill(Theme.surface2).frame(height: 8)
                Capsule().fill(Theme.accent.opacity(0.35)).frame(width: max(4, x(band.p90) - x(band.p10)), height: 8)
                    .offset(x: x(band.p10))
                Rectangle().fill(Theme.ink2).frame(width: 1, height: 16).offset(x: x(0))
                Circle().fill(Theme.accent).frame(width: 12, height: 12).offset(x: x(band.expected) - 6)
            }
            .frame(maxHeight: .infinity)
        }
        .frame(height: 16)
        .accessibilityHidden(true)
    }
}
