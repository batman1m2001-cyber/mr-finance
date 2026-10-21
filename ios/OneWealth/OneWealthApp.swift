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
            Soon(title: "Tài sản", icon: "chart.pie")
                .tabItem { Label("Tài sản", systemImage: "chart.pie") }.tag(AppModel.Tab.assets)
            Soon(title: "Dòng tiền", icon: "arrow.left.arrow.right")
                .tabItem { Label("Dòng tiền", systemImage: "arrow.left.arrow.right") }.tag(AppModel.Tab.cash)
            Soon(title: "Tin tức", icon: "newspaper")
                .tabItem { Label("Tin tức", systemImage: "newspaper") }.tag(AppModel.Tab.news)
            Soon(title: "Trợ lý", icon: "bubble.left.and.bubble.right")
                .tabItem { Label("Trợ lý", systemImage: "bubble.left.and.bubble.right") }.tag(AppModel.Tab.assistant)
        }
    }
}

/// A tab not built yet (docs/IOS_APP_PLAN.md I2, I3).
struct Soon: View {
    let title: String
    let icon: String

    var body: some View {
        NavigationStack {
            ContentUnavailableView(title, systemImage: icon, description: Text("Màn hình này có trong bản tiếp theo."))
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Theme.plane)
                .navigationTitle(title)
        }
    }
}
