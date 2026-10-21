import SwiftUI
import UIKit

/// The Techcombank-ecosystem look: black, white and greys, the brand red only on what is pressed or picked (buttons,
/// the selected tab, the client's own words). Figures never wear the red: a series is grey (`series`), a gain green,
/// a loss or a breach orange-red (`critical`), so a loss never reads as a button and a button never as a loss.
enum Theme {
    static let plane = dyn(0xf4f4f5, 0x0e0e10)
    static let surface = dyn(0xffffff, 0x1a1a1d)
    static let surface2 = dyn(0xf0f0f2, 0x26262a)
    static let ink = dyn(0x141414, 0xf2f2f3)
    static let ink2 = dyn(0x4a4a4f, 0xc7c7cc)
    static let muted = dyn(0x6f6f76, 0x8e8e95)
    static let hair = dyn(0xe4e4e7, 0x2e2e33)
    static let accent = dyn(0xe31b23, 0xff4d55)
    static let accentSoft = dyn(0xfdeced, 0x3a1517)
    static let series = dyn(0x3d3d42, 0xc9c9ce)
    static let good = dyn(0x0f7a3d, 0x4cc38a)
    static let warning = dyn(0xa16207, 0xf5c45e)
    static let critical = dyn(0xc2410c, 0xff8a4c)
    static let brandRed = Color(red: 227 / 255, green: 27 / 255, blue: 35 / 255)
    static let brandBlack = Color(red: 20 / 255, green: 20 / 255, blue: 20 / 255)

    static func status(_ s: Status) -> Color {
        switch s { case .good: good; case .warn: warning; case .bad: critical }
    }

    static func signed(_ x: Double?) -> Color { (x ?? 0) >= 0 ? good : critical }

    private static func dyn(_ light: UInt32, _ dark: UInt32) -> Color {
        Color(UIColor { t in rgb(t.userInterfaceStyle == .dark ? dark : light) })
    }

    private static func rgb(_ v: UInt32) -> UIColor {
        UIColor(red: CGFloat((v >> 16) & 0xff) / 255, green: CGFloat((v >> 8) & 0xff) / 255,
                blue: CGFloat(v & 0xff) / 255, alpha: 1)
    }
}

/// A white card on the page, as the website's panels.
struct Card<Content: View>: View {
    var title: String?
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let title {
                Text(title).font(.headline).foregroundStyle(Theme.ink)
            }
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Theme.hair, lineWidth: 1))
    }
}

/// A label and its figure on one line.
struct Row: View {
    let label: String
    let value: String
    var tint: Color = Theme.ink

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(label).foregroundStyle(Theme.ink2)
            Spacer(minLength: 12)
            Text(value).fontWeight(.semibold).foregroundStyle(tint).monospacedDigit()
        }
        .font(.subheadline)
    }
}

/// A status in words, with its icon, never by colour alone.
struct Pill: View {
    let status: String

    var body: some View {
        let (s, words) = Status.of(status)
        Label(words, systemImage: s == .good ? "checkmark.circle.fill" : s == .warn ? "exclamationmark.circle.fill" : "exclamationmark.triangle.fill")
            .font(.footnote.weight(.semibold))
            .foregroundStyle(Theme.status(s))
            .padding(.horizontal, 10).padding(.vertical, 4)
            .background(Theme.status(s).opacity(0.12), in: Capsule())
    }
}

/// A bar to a mark: the reading against its limit (risk) or its safe level (the reserve).
struct Meter: View {
    let value: Double
    let mark: Double
    let max: Double
    let status: Status

    var body: some View {
        GeometryReader { g in
            let w = g.size.width
            ZStack(alignment: .leading) {
                Capsule().fill(Theme.surface2)
                Capsule().fill(Theme.status(status)).frame(width: w * min(1, value / max))
                Rectangle().fill(Theme.ink).frame(width: 2, height: 16).offset(x: w * min(1, mark / max) - 1)
            }
        }
        .frame(height: 10)
        .accessibilityHidden(true)
    }
}
