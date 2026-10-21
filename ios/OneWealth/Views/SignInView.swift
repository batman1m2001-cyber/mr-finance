import SwiftUI

/// Đăng nhập: email and password, or one of the demo clients when the server offers them (GET /api/auth/accounts).
struct SignInView: View {
    @Environment(AppModel.self) private var model
    @State private var login = ""
    @State private var password = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Image(systemName: "leaf.circle.fill")
                        .font(.system(size: 48)).foregroundStyle(Theme.accent).accessibilityHidden(true)
                    Text("OneWealth").font(.largeTitle.bold()).foregroundStyle(Theme.ink)
                    Text("Toàn bộ tài sản và dòng tiền của gia đình bạn, ở một nơi.")
                        .font(.body).foregroundStyle(Theme.ink2)
                }
                .padding(.top, 32)

                Card(title: "Đăng nhập") {
                    TextField("Email", text: $login)
                        .textContentType(.username).keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                        .padding(12).background(Theme.surface2, in: RoundedRectangle(cornerRadius: 10))
                    SecureField("Mật khẩu", text: $password)
                        .textContentType(.password)
                        .padding(12).background(Theme.surface2, in: RoundedRectangle(cornerRadius: 10))
                    Button {
                        Task { await model.login(login, password) }
                    } label: {
                        Text("Đăng nhập").font(.headline).frame(maxWidth: .infinity, minHeight: 44)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(login.isEmpty || password.isEmpty || model.loading)
                }

                if let e = model.error {
                    Label(e, systemImage: "exclamationmark.triangle.fill")
                        .font(.subheadline).foregroundStyle(Theme.critical)
                }

                if !model.demoAccounts.isEmpty {
                    Card(title: "Tài khoản mẫu") {
                        Text("Dữ liệu mẫu, không cần mật khẩu.").font(.footnote).foregroundStyle(Theme.muted)
                        ForEach(model.demoAccounts) { a in
                            Button {
                                Task { await model.demo(a.id) }
                            } label: {
                                HStack(spacing: 12) {
                                    Text(initials(a.name))
                                        .font(.subheadline.bold()).foregroundStyle(Theme.accent)
                                        .frame(width: 40, height: 40).background(Theme.accentSoft, in: Circle())
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(a.name).font(.body.weight(.semibold)).foregroundStyle(Theme.ink)
                                        if let t = a.title { Text(t).font(.footnote).foregroundStyle(Theme.muted) }
                                    }
                                    Spacer()
                                    Image(systemName: "chevron.right").foregroundStyle(Theme.muted)
                                }
                                .frame(minHeight: 44)
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            .disabled(model.loading)
                        }
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 32)
        }
        .background(Theme.plane)
        .overlay { if model.loading { ProgressView().controlSize(.large) } }
    }

    private func initials(_ name: String) -> String {
        let w = name.split(separator: " ")
        return ((w.dropLast().first.map { String($0.prefix(1)) } ?? "") + (w.last.map { String($0.prefix(1)) } ?? "")).uppercased()
    }
}
