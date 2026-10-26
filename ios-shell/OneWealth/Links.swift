import Foundation
import UIKit

/// The demo's server, and where a link the page opens should go.
enum Server {
    /// The public demo; MF_URL overrides it in the simulator runs.
    static let url = URL(string: ProcessInfo.processInfo.environment["MF_URL"] ?? "https://oneweath.ngrok.app/")!

    /// The first page: the server's own, or a route the simulator run names (MF_ROUTE, e.g. `#/admin`).
    static var start: URL {
        guard let route = ProcessInfo.processInfo.environment["MF_ROUTE"], !route.isEmpty else { return url }
        return URL(string: route, relativeTo: url)?.absoluteURL ?? url
    }
}

enum Links {
    enum Place: Equatable { case app, outside, cancel }

    /// Our server's pages stay in the app; another site, a phone number or a mail address goes to the system.
    static func place(_ url: URL?, server: URL = Server.url) -> Place {
        guard let url, let scheme = url.scheme?.lowercased() else { return .cancel }
        switch scheme {
        case "about", "blob", "data":
            return .app
        case "http", "https":
            return url.host?.lowercased() == server.host?.lowercased() ? .app : .outside
        default:
            return .outside  // tel:, mailto:, maps:
        }
    }

    /// The microphone and camera go to our own pages only (the system's own prompt still asks once).
    static func mayCapture(host: String, server: URL = Server.url) -> Bool {
        host.lowercased() == server.host?.lowercased()
    }

    /// The colour the page reports (`rgb(r, g, b)` or `rgba(r, g, b, a)`), or nil when it is not one.
    static func color(_ css: String) -> UIColor? {
        let parts = css.split(whereSeparator: { !"0123456789.".contains($0) }).compactMap { Double($0) }
        guard parts.count >= 3 else { return nil }
        return UIColor(red: parts[0] / 255, green: parts[1] / 255, blue: parts[2] / 255, alpha: 1)
    }

    /// Dark behind the status bar: its text is drawn light.
    static func isDark(_ color: UIColor) -> Bool {
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        color.getRed(&r, green: &g, blue: &b, alpha: &a)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.5
    }
}
