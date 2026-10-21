import Foundation
import Observation

/// What the app knows: who is signed in and the dashboard of their family, read from the server.
@MainActor @Observable
final class AppModel {
    enum Phase { case starting, signedOut, signedIn }

    let api: API
    var phase: Phase = .starting
    var user: User?
    var demoAccounts: [Account] = []
    var dashboard: Dashboard?
    var error: String?
    var loading = false
    var tab: Tab = .overview

    enum Tab: String, CaseIterable { case overview, assets, cash, news, assistant }

    init() {
        let env = ProcessInfo.processInfo.environment
        api = API(server: UserDefaults.standard.string(forKey: "server") ?? env["MF_SERVER"] ?? API.defaultServer)
        if let s = env["MF_SCREEN"], let t = Tab(rawValue: s) { tab = t }
    }

    var client: String { user?.family ?? user?.id ?? "" }

    func start() async {
        #if targetEnvironment(simulator)
        // the screenshot runs on CI (docs/IOS_APP_PLAN.md): MF_SIGNOUT=1 opens on sign-in, MF_DEMO=C01 signs in as C01
        let env = ProcessInfo.processInfo.environment
        if env["MF_SIGNOUT"] == "1" { await api.logout() }
        if let id = env["MF_DEMO"], !id.isEmpty { await demo(id); if user != nil { return } }
        #endif
        do {
            let me = try await api.me()
            if let u = me.user { await signedIn(u) } else { await signedOut(demo: me.demoAccounts ?? false) }
        } catch {
            self.error = error.localizedDescription
            await signedOut(demo: true)
        }
    }

    private func signedOut(demo: Bool) async {
        user = nil
        dashboard = nil
        phase = .signedOut
        demoAccounts = demo ? ((try? await api.accounts()) ?? []).filter { $0.role == "client" } : []
    }

    private func signedIn(_ u: User) async {
        user = u
        error = nil
        phase = .signedIn
        await refresh()
    }

    func demo(_ id: String) async {
        await run { if let u = try await self.api.demo(id) { await self.signedIn(u) } }
    }

    func login(_ login: String, _ password: String) async {
        await run { if let u = try await self.api.login(login, password) { await self.signedIn(u) } }
    }

    func logout() async {
        await api.logout()
        await signedOut(demo: true)
    }

    func refresh() async {
        guard user != nil else { return }
        await run { self.dashboard = try await self.api.dashboard(self.client) }
    }

    private func run(_ work: @escaping () async throws -> Void) async {
        loading = true
        defer { loading = false }
        do {
            try await work()
            error = nil
        } catch let e as APIError where e.signedOut && phase == .signedIn {
            await signedOut(demo: true)
            error = "Phiên đăng nhập đã hết. Xin đăng nhập lại."
        } catch {
            self.error = error.localizedDescription
        }
    }
}
