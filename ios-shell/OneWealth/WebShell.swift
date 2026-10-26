import os
import SwiftUI
import WebKit

let log = Logger(subsystem: "app.onewealth.demo", category: "shell")

/// The website in a WKWebView: its sign-in kept (the default data store), its links to other sites sent to Safari,
/// its downloads handed to the share sheet, its alerts shown as iOS alerts, its colours behind the status bar.
struct WebShell: UIViewRepresentable {
    let shell: Shell

    func makeCoordinator() -> Coordinator { Coordinator(shell: shell) }

    func makeUIView(context: Context) -> WKWebView {
        let env = ProcessInfo.processInfo.environment
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()
        config.applicationNameForUserAgent = "Mobile/15E148 OneWealthApp/1.0"
        config.allowsInlineMediaPlayback = true
        let content = config.userContentController
        content.add(context.coordinator, name: "shell")
        content.addUserScript(WKUserScript(source: Self.colours, injectionTime: .atDocumentEnd, forMainFrameOnly: true))
        if let theme = env["MF_THEME"], ["light", "dark"].contains(theme) {  // the simulator runs: the site's own theme setting
            content.addUserScript(WKUserScript(source: "try { localStorage.setItem('mf.theme', '\(theme)') } catch (_) {}",
                                               injectionTime: .atDocumentStart, forMainFrameOnly: true))
        }

        let web = WKWebView(frame: .zero, configuration: config)
        web.navigationDelegate = context.coordinator
        web.uiDelegate = context.coordinator
        web.allowsBackForwardNavigationGestures = true
        web.isOpaque = false
        web.backgroundColor = .clear
        web.scrollView.backgroundColor = .clear
        #if DEBUG
        if #available(iOS 16.4, *) { web.isInspectable = true }
        #endif
        let refresh = UIRefreshControl()
        refresh.addTarget(context.coordinator, action: #selector(Coordinator.pulled(_:)), for: .valueChanged)
        web.scrollView.refreshControl = refresh

        shell.retry = { [weak web] in
            guard let web else { return }
            if web.url == nil { web.load(URLRequest(url: Server.start)) } else { web.reload() }
        }
        context.coordinator.web = web
        context.coordinator.open(web, env: env)
        return web
    }

    func updateUIView(_ web: WKWebView, context: Context) {}

    /// The colours at the page's top and bottom edges (its header, its plane): the first element there with a
    /// background, walking up to the page's own. Sent when they change: a theme switch, another page.
    static let colours = """
    (function () {
      // any CSS colour (color-mix, color(srgb …), oklch) as rgb(r, g, b), through a 1×1 canvas; null when see-through
      const cx = document.createElement("canvas").getContext("2d", {willReadFrequently: true});
      function rgb(c) {
        cx.clearRect(0, 0, 1, 1); cx.fillStyle = "#000"; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1);
        const [r, g, b, a] = cx.getImageData(0, 0, 1, 1).data;
        return a < 26 ? null : `rgb(${r}, ${g}, ${b})`;
      }
      function at(x, y) {
        for (let e = document.elementFromPoint(x, y); e; e = e.parentElement) {
          const c = rgb(getComputedStyle(e).backgroundColor);
          if (c) return c;
        }
        return null;
      }
      let last = "";
      function post() {
        const m = {top: at(4, 4), bottom: at(4, innerHeight - 4)}, s = JSON.stringify(m);
        if (s !== last) { last = s; window.webkit.messageHandlers.shell.postMessage(m); }
      }
      addEventListener("hashchange", () => setTimeout(post, 80));
      addEventListener("load", post);
      new MutationObserver(() => setTimeout(post, 40)).observe(document.documentElement, {attributes: true, attributeFilter: ["data-theme", "class"]});
      setInterval(post, 1500);
      post();
    })();
    """

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler, WKDownloadDelegate {
        let shell: Shell
        weak var web: WKWebView?
        private var downloads: [ObjectIdentifier: URL] = [:]

        init(shell: Shell) { self.shell = shell }

        /// The first page. The simulator runs sign out first (MF_SIGNOUT=1), or sign in as a demo account (MF_DEMO=C01)
        /// the way the sign-in page's demo buttons do, the session cookie copied into the web view's store.
        func open(_ web: WKWebView, env: [String: String]) {
            let store = web.configuration.websiteDataStore
            Task { @MainActor in
                if env["MF_SIGNOUT"] == "1" {
                    await store.removeData(ofTypes: WKWebsiteDataStore.allWebsiteDataTypes(), modifiedSince: .distantPast)
                }
                if let id = env["MF_DEMO"], !id.isEmpty {
                    var request = URLRequest(url: Server.url.appendingPathComponent("api/auth/demo"))
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    request.httpBody = try? JSONSerialization.data(withJSONObject: ["id": id])
                    _ = try? await URLSession.shared.data(for: request)
                    for cookie in HTTPCookieStorage.shared.cookies(for: Server.url) ?? [] {
                        await store.httpCookieStore.setCookie(cookie)
                    }
                }
                log.notice("open \(Server.start.absoluteString, privacy: .public)")
                web.load(URLRequest(url: Server.start))
            }
        }

        @objc func pulled(_ refresh: UIRefreshControl) {
            guard let web else { refresh.endRefreshing(); return }
            web.reload()
        }

        // MARK: the page's colours

        func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
            guard let m = message.body as? [String: Any] else { return }
            log.notice("page colours \(String(describing: m), privacy: .public)")
            if let css = m["top"] as? String, let c = Links.color(css) { shell.top = c }
            if let css = m["bottom"] as? String, let c = Links.color(css) { shell.bottom = c }
        }

        // MARK: navigation

        func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if action.shouldPerformDownload { decisionHandler(.download); return }
            if action.targetFrame?.isMainFrame == false { decisionHandler(.allow); return }  // an embed keeps its own page
            switch Links.place(action.request.url) {
            case .app:
                decisionHandler(.allow)
            case .outside:
                if let url = action.request.url { UIApplication.shared.open(url) }
                decisionHandler(.cancel)
            case .cancel:
                decisionHandler(.cancel)
            }
        }

        func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse,
                     decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
            let http = response.response as? HTTPURLResponse
            let disposition = http?.value(forHTTPHeaderField: "Content-Disposition")?.lowercased() ?? ""
            if !response.canShowMIMEType || disposition.hasPrefix("attachment") { decisionHandler(.download); return }
            // the tunnel's own error page (the demo server is down): our retry instead
            if response.isForMainFrame, let http, http.statusCode >= 500 || http.value(forHTTPHeaderField: "ngrok-error-code") != nil {
                shell.phase = .offline("Máy chủ demo chưa chạy (HTTP \(http.statusCode)).")
                decisionHandler(.cancel)
                return
            }
            decisionHandler(.allow)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            webView.scrollView.refreshControl?.endRefreshing()
            if case .offline = shell.phase { return }
            shell.phase = .ready
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            failed(webView, error)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            failed(webView, error)
        }

        private func failed(_ webView: WKWebView, _ error: Error) {
            webView.scrollView.refreshControl?.endRefreshing()
            let e = error as NSError
            if e.domain == NSURLErrorDomain && e.code == NSURLErrorCancelled { return }
            if e.domain == "WebKitErrorDomain" && e.code == 102 { return }  // interrupted: a download, a link sent outside
            log.notice("load failed \(e.domain, privacy: .public) \(e.code): \(e.localizedDescription, privacy: .public)")
            shell.phase = .offline(e.localizedDescription)
        }

        func webViewWebContentProcessDidTerminate(_ webView: WKWebView) { webView.reload() }

        // MARK: downloads: a statement export, a report

        func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
            download.delegate = self
        }

        func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
            download.delegate = self
        }

        func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String,
                      completionHandler: @escaping (URL?) -> Void) {
            let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let file = dir.appendingPathComponent(suggestedFilename.isEmpty ? "OneWealth" : suggestedFilename)
            downloads[ObjectIdentifier(download)] = file
            completionHandler(file)
        }

        func downloadDidFinish(_ download: WKDownload) {
            guard let file = downloads.removeValue(forKey: ObjectIdentifier(download)), let web = download.webView else { return }
            let share = UIActivityViewController(activityItems: [file], applicationActivities: nil)
            share.popoverPresentationController?.sourceView = web
            present(share, over: web)
        }

        func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
            downloads.removeValue(forKey: ObjectIdentifier(download))
        }

        // MARK: new windows and the page's alerts

        func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                     for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
            guard let url = action.request.url else { return nil }
            switch Links.place(url) {
            case .app: webView.load(action.request)  // target=_blank on our own page: here, not a second window
            case .outside: UIApplication.shared.open(url)
            case .cancel: break
            }
            return nil
        }

        func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                     initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
            let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler() })
            if !present(alert, over: webView) { completionHandler() }
        }

        func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                     initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
            let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "Huỷ", style: .cancel) { _ in completionHandler(false) })
            alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) })
            if !present(alert, over: webView) { completionHandler(false) }
        }

        func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String, defaultText: String?,
                     initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
            let alert = UIAlertController(title: nil, message: prompt, preferredStyle: .alert)
            alert.addTextField { $0.text = defaultText }
            alert.addAction(UIAlertAction(title: "Huỷ", style: .cancel) { _ in completionHandler(nil) })
            alert.addAction(UIAlertAction(title: "OK", style: .default) { [weak alert] _ in completionHandler(alert?.textFields?.first?.text) })
            if !present(alert, over: webView) { completionHandler(nil) }
        }

        func webView(_ webView: WKWebView, requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                     initiatedByFrame frame: WKFrameInfo, type: WKMediaCaptureType,
                     decisionHandler: @escaping (WKPermissionDecision) -> Void) {
            log.info("capture \(origin.host, privacy: .public)")
            decisionHandler(Links.mayCapture(host: origin.host) ? .grant : .deny)  // the page asks each time without this
        }

        /// Shown over whatever is on screen; false when nothing is (the answer then goes back at once).
        @discardableResult
        private func present(_ controller: UIViewController, over view: UIView) -> Bool {
            guard var top = view.window?.rootViewController else { return false }
            while let next = top.presentedViewController { top = next }
            top.present(controller, animated: true)
            return true
        }
    }
}
