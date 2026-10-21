import SwiftUI
import UIKit

/// The website's colours (web/core/tokens.css), light and dark.
enum Theme {
    static let plane = dyn(0xf6f6fb, 0x16132b)
    static let surface = dyn(0xffffff, 0x211c3b)
    static let surface2 = dyn(0xf5f4fa, 0x2a2549)
    static let ink = dyn(0x1c1a2e, 0xecebf4)
    static let ink2 = dyn(0x4a4763, 0xc3c0d6)
    static let muted = dyn(0x6e6a86, 0x9a97b0)
    static let hair = dyn(0xe6e4ef, 0x332d57)
    static let accent = dyn(0x5b47d6, 0xb3a7ff)
    static let accentSoft = dyn(0xece9fd, 0x2f2858)
    static let good = dyn(0x0f7a3d, 0x5fd38d)
    static let warning = dyn(0xb37400, 0xf5c45e)
    static let critical = dyn(0xc0332b, 0xff8a7a)

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
