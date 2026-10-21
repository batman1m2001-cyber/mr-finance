import Foundation

/// The OneWealth server, as the website calls it: JSON over HTTPS, the session in the HttpOnly cookie
/// `mf_session` that sign-in sets (kept by the shared cookie store across launches).
struct APIError: LocalizedError {
    let status: Int
    let message: String
    var errorDescription: String? { message }
    var signedOut: Bool { status == 401 }
}

final class API {
    static let defaultServer = "https://oneweath.ngrok.app"

    var server: URL
    private let session: URLSession
    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()

    init(server: String = API.defaultServer) {
        self.server = URL(string: server) ?? URL(string: API.defaultServer)!
        let config = URLSessionConfiguration.default
        config.httpCookieStorage = .shared
        config.httpShouldSetCookies = true
        config.timeoutIntervalForRequest = 60
        session = URLSession(configuration: config)
    }

    func get<T: Decodable>(_ path: String) async throws -> T {
        try await send(path, method: "GET", body: nil)
    }

    func post<T: Decodable>(_ path: String, _ body: [String: Any]) async throws -> T {
        try await send(path, method: "POST", body: try JSONSerialization.data(withJSONObject: body))
    }

    private func send<T: Decodable>(_ path: String, method: String, body: Data?) async throws -> T {
        var req = URLRequest(url: server.appendingPathComponent(path))
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        if let body {
            req.httpBody = body
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: req)
        } catch {
            throw APIError(status: 0, message: "Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.")
        }
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            throw APIError(status: status, message: Self.detail(data) ?? "Máy chủ trả lỗi \(status).")
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError(status: status, message: "Không đọc được trả lời của máy chủ (\(path)).")
        }
    }

    /// The server's `{"detail": "..."}`, the last line of it as the website shows it.
    private static func detail(_ data: Data) -> String? {
        guard let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let d = obj["detail"] as? String, !d.isEmpty else { return nil }
        return d.split(separator: "\n").last.map(String.init)
    }

    // MARK: sign-in

    func me() async throws -> Me { try await get("api/auth/me") }
    func accounts() async throws -> [Account] { (try await get("api/auth/accounts") as Accounts).accounts }
    func demo(_ id: String) async throws -> User? { (try await post("api/auth/demo", ["id": id]) as SignedIn).user }
    func login(_ login: String, _ password: String) async throws -> User? {
        (try await post("api/auth/login", ["login": login, "password": password]) as SignedIn).user
    }
    func logout() async {
        _ = try? await post("api/auth/logout", [:]) as Empty
        for c in HTTPCookieStorage.shared.cookies(for: server) ?? [] { HTTPCookieStorage.shared.deleteCookie(c) }
    }

    // MARK: the client's money

    func dashboard(_ client: String) async throws -> Dashboard {
        (try await post("api/dashboard", ["client_id": client, "scope": "personal", "months": 12]) as DashboardReply).dashboard
    }
}

struct Empty: Decodable {}
