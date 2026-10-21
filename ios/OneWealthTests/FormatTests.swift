import XCTest
@testable import OneWealth

/// The app writes money as the website does: the expectations are web/core/core.js's own outputs for these values.
final class FormatTests: XCTestCase {
    func testMoneyAsTheWebsite() {
        let cases: [(Double, Bool, String)] = [
            (43_526_000_000, false, "43,5 tỷ"), (980_500_000, true, "+981 triệu"), (-90_000_000, false, "−90 triệu"),
            (2_445_000_000, false, "2,44 tỷ"), (4_720_000_000, false, "4,72 tỷ"), (135_400_000, false, "135 triệu"),
            (15_284_000, false, "15,3 triệu"), (192_000, false, "192 nghìn"), (1_800_000_000, false, "1,8 tỷ"),
            (0, false, "0 đ"), (32_400_000_000, false, "32,4 tỷ"), (1_023_000_000, false, "1,02 tỷ"),
        ]
        for (a, signed, want) in cases { XCTAssertEqual(Fmt.vnd(a, signed: signed), want, "\(a)") }
        XCTAssertEqual(Fmt.vnd(nil), "—")
    }

    func testSharesAsTheWebsite() {
        XCTAssertEqual(Fmt.pct(0.023045915549235525, signed: true), "+2,3%")
        XCTAssertEqual(Fmt.pct(0.1183), "11,8%")
        XCTAssertEqual(Fmt.pct(0.08, digits: 0), "8%")
        XCTAssertEqual(Fmt.pct(-0.03295247305885603, signed: true), "−3,3%")
    }

    func testThousands() {
        XCTAssertEqual(Fmt.vn(1_234_567, 0), "1.234.567")
        XCTAssertEqual(Fmt.vn(123, 0), "123")
    }

    func testMonthsAndDays() {
        XCTAssertEqual(Fmt.month("2026-10"), "Th10/2026")
        XCTAssertEqual(Fmt.month("2026-03", short: true), "T3")
        XCTAssertEqual(Fmt.day("2026-10-09"), "09/10/2026")
        XCTAssertEqual(monthsText(41), "3 năm")
        XCTAssertEqual(monthsText(7.5), "7,5 tháng")
    }
}
