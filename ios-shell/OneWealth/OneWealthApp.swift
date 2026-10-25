import SwiftUI

@main
struct OneWealthApp: App {
    @State private var shell = Shell()

    var body: some Scene {
        WindowGroup {
            RootView().environment(shell)
        }
    }
}

/// What the app shows over the page: the mark while the first page loads, a retry when the server cannot be reached.
@Observable
final class Shell {
    enum Phase: Equatable { case loading, ready, offline(String) }

    var phase: Phase = .loading
    /// the colours at the page's top (its header) and bottom, behind the status bar and the home indicator
    var top = UIColor(red: 1, green: 1, blue: 1, alpha: 1)
    var bottom = UIColor(red: 0xf1 / 255, green: 0xf1 / 255, blue: 0xf1 / 255, alpha: 1)
    @ObservationIgnored var retry: () -> Void = {}
}

struct RootView: View {
    @Environment(Shell.self) private var shell

    var body: some View {
        ZStack {
            VStack(spacing: 0) { Color(shell.top); Color(shell.bottom) }.ignoresSafeArea()
            WebShell(shell: shell)
            switch shell.phase {
            case .loading:
                Splash { ProgressView().controlSize(.large).tint(Mark.gold) }
            case .offline(let why):
                Splash {
                    VStack(spacing: 12) {
                        Text("Không mở được OneWealth").font(.headline).foregroundStyle(.white)
                        Text(why).font(.footnote).foregroundStyle(.white.opacity(0.75)).multilineTextAlignment(.center)
                        Button("Thử lại") { shell.phase = .loading; shell.retry() }
                            .buttonStyle(.borderedProminent).tint(Mark.gold).foregroundStyle(Mark.brown)
                        Text(Server.url.host ?? "").font(.caption2).foregroundStyle(.white.opacity(0.5))
                    }
                }
            case .ready:
                EmptyView()
            }
        }
        .preferredColorScheme(Links.isDark(shell.top) ? .dark : .light)
        .animation(.easeOut(duration: 0.25), value: shell.phase)
    }
}

/// The website's mark: a brown square, the gold ring, the white point.
enum Mark {
    static let brown = Color(red: 0x59 / 255, green: 0x39 / 255, blue: 0x2c / 255)
    static let gold = Color(red: 0xc8 / 255, green: 0xa4 / 255, blue: 0x5d / 255)
    /// the app icon's square, a step lighter than the splash behind it
    static let tile = Color(red: 0x68 / 255, green: 0x45 / 255, blue: 0x36 / 255)
}

struct Splash<Below: View>: View {
    @ViewBuilder var below: Below

    var body: some View {
        VStack(spacing: 28) {
            ZStack {
                Circle().stroke(Mark.gold, lineWidth: 11).frame(width: 56, height: 56)
                Circle().fill(.white).frame(width: 18, height: 18)
            }
            .frame(width: 104, height: 104)
            .background(Mark.tile, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
            Text("OneWealth").font(.title2.weight(.semibold)).foregroundStyle(.white)
            below
        }
        .padding(32)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Mark.brown)
        .transition(.opacity)
    }
}
