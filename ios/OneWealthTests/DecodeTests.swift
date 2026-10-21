import XCTest
@testable import OneWealth

/// The real answers of the server (saved from https://oneweath.ngrok.app on 2026-10-21) decode into the app's models.
final class DecodeTests: XCTestCase {
    private func fixture<T: Decodable>(_ name: String, as: T.Type) throws -> T {
        let url = try XCTUnwrap(Bundle(for: Self.self).url(forResource: name, withExtension: "json"))
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return try d.decode(T.self, from: Data(contentsOf: url))
    }

    func testDashboard() throws {
        let d = try fixture("dashboard", as: DashboardReply.self).dashboard
        XCTAssertEqual(d.profile.name, "Nguyễn Minh Khoa")
        XCTAssertEqual(Fmt.vnd(d.netWorth.value), "43,5 tỷ")
        XCTAssertEqual(d.allocation.first?.group, "Bất động sản")
        XCTAssertEqual(d.risk.status, "over")
        XCTAssertEqual(d.cashflow.history.count, 12)
        XCTAssertEqual(d.cashflow.current?.inflow, 135_400_000)
        XCTAssertFalse(d.holdings.isEmpty)
        XCTAssertEqual(d.holdings.first?.cls, "real_estate")
    }

    func testSignIn() throws {
        XCTAssertEqual(try fixture("me", as: Me.self).user?.family, "C01")
        let clients = try fixture("accounts", as: Accounts.self).accounts.filter { $0.role == "client" }
        XCTAssertFalse(clients.isEmpty)
    }
}
