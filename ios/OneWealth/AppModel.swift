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
    var flows: Flows?
    var flowsError: String?
    var impact: Impact?
    var impactError: String?
    var chat = Chat()
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
        flows = nil
        impact = nil
        chat = Chat()
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

    func loadFlows() async {
        guard user != nil else { return }
        do { flows = try await api.flows(client); flowsError = nil } catch { flowsError = error.localizedDescription }
    }

    func loadImpact() async {
        guard user != nil else { return }
        do { impact = try await api.impact(client); impactError = nil } catch { impactError = error.localizedDescription }
    }

    // MARK: Trợ lý

    func ask(_ question: String) async {
        let q = question.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty, !chat.busy else { return }
        chat.messages.append(.init(mine: true, text: q))
        await turn { try await self.api.ask(self.client, message: q, conversation: self.chat.conversation) }
    }

    /// Xác nhận / Huỷ what a turn waits for (a write the assistant asks the client to confirm)
    func answer(_ m: Chat.Message, approve: Bool) async {
        guard let turnId = m.turnId, let i = chat.messages.firstIndex(where: { $0.id == m.id }) else { return }
        chat.messages[i].done = true
        chat.messages.append(.init(mine: true, text: approve ? "Xác nhận" : "Huỷ"))
        let answers = Dictionary(uniqueKeysWithValues: m.waits.map { ($0.id, approve ? "approve" : "deny") })
        await turn { try await self.api.ask(self.client, message: nil, conversation: self.chat.conversation, turn: turnId, approvals: answers) }
    }

    private func turn(_ call: @escaping () async throws -> AssistantTurn) async {
        chat.busy = true
        defer { chat.busy = false }
        do {
            let a = try await call()
            if let c = a.conversationId { chat.conversation = c }
            chat.messages.append(.init(mine: false, text: a.text ?? "", status: a.status, steps: a.steps ?? [],
                                       waits: a.waits ?? [], turnId: a.turnId))
            chat.suggest = a.suggest ?? []
        } catch {
            chat.messages.append(.init(mine: false, text: "Không gọi được trợ lý: \(error.localizedDescription)", status: "failed"))
        }
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

/// The conversation with the assistant, as the website's panel keeps it (web/copilot.js).
struct Chat {
    struct Message: Identifiable {
        let id = UUID()
        let mine: Bool
        let text: String
        var status: String? = nil
        var steps: [AssistantStep] = []
        var waits: [AssistantWait] = []
        var turnId: String? = nil
        var done = false
        var waiting: Bool { status == "pending" && !waits.isEmpty && turnId != nil && !done }
    }

    var messages: [Message] = []
    var conversation: String?
    var suggest = ["Tài sản của tôi thế nào?", "Dòng tiền tháng này?", "Có gì cần chú ý?", "Vì sao tin này ảnh hưởng tới tôi?"]
    var busy = false
}
