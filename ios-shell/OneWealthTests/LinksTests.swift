import XCTest
@testable import OneWealth

final class LinksTests: XCTestCase {
    let server = URL(string: "https://oneweath.ngrok.app/")!

    func testOurPagesStayInTheApp() {
        XCTAssertEqual(Links.place(URL(string: "https://oneweath.ngrok.app/#/rm/ban"), server: server), .app)
        XCTAssertEqual(Links.place(URL(string: "https://ONEWEATH.ngrok.app/api/x"), server: server), .app)
        XCTAssertEqual(Links.place(URL(string: "about:blank"), server: server), .app)
        XCTAssertEqual(Links.place(URL(string: "blob:https://oneweath.ngrok.app/1f2e"), server: server), .app)
    }

    func testOtherSitesAndSchemesGoOutside() {
        XCTAssertEqual(Links.place(URL(string: "https://vnexpress.net/tin"), server: server), .outside)
        XCTAssertEqual(Links.place(URL(string: "tel:+84901234567"), server: server), .outside)
        XCTAssertEqual(Links.place(URL(string: "mailto:rm@onewealth.vn"), server: server), .outside)
    }

    func testNoLinkIsCancelled() {
        XCTAssertEqual(Links.place(nil, server: server), .cancel)
    }

    func testOnlyOurSiteMayRecord() {
        XCTAssertTrue(Links.mayCapture(host: "OneWeath.ngrok.app", server: server))
        XCTAssertFalse(Links.mayCapture(host: "vnexpress.net", server: server))
    }

    func testThePageColours() {
        XCTAssertTrue(Links.isDark(Links.color("rgb(17, 13, 11)")!))
        XCTAssertFalse(Links.isDark(Links.color("rgba(241, 241, 241, 1)")!))
        XCTAssertNil(Links.color("transparent"))
    }
}
