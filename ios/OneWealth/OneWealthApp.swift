import SwiftUI

@main
struct OneWealthApp: App {
    @State private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(model)
                .tint(Theme.accent)
                .task { await model.start() }
        }
    }
}

struct RootView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        switch model.phase {
        case .starting:
            ProgressView().controlSize(.large).frame(maxWidth: .infinity, maxHeight: .infinity).background(Theme.plane)
        case .signedOut:
            SignInView()
        case .signedIn:
            MainTabs()
        }
    }
}

struct MainTabs: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var model = model
        TabView(selection: $model.tab) {
            OverviewView()
                .tabItem { Label("Tổng quan", systemImage: "house") }.tag(AppModel.Tab.overview)
            AssetsView()
                .tabItem { Label("Tài sản", systemImage: "chart.pie") }.tag(AppModel.Tab.assets)
            CashView()
                .tabItem { Label("Dòng tiền", systemImage: "arrow.left.arrow.right") }.tag(AppModel.Tab.cash)
            NewsView()
                .tabItem { Label("Tin tức", systemImage: "newspaper") }.tag(AppModel.Tab.news)
            AssistantView()
                .tabItem { Label("Trợ lý", systemImage: "bubble.left.and.bubble.right") }.tag(AppModel.Tab.assistant)
        }
    }
}
