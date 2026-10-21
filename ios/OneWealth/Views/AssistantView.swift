import SwiftUI

/// Trợ lý: the website's assistant (POST /api/assistant) as a chat — the question, the answer and the steps it took,
/// Xác nhận / Huỷ when it waits for the client, and the suggested next questions.
struct AssistantView: View {
    @Environment(AppModel.self) private var model
    @State private var question = ""
    @FocusState private var typing: Bool

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        if model.chat.messages.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Hỏi về tài sản, dòng tiền, tin tức của bạn").font(.title3.weight(.semibold))
                                    .foregroundStyle(Theme.ink)
                                Text("Trợ lý đọc số liệu của bạn trên OneWealth, nói rõ các bước đã làm và hỏi trước khi ghi điều gì.")
                                    .font(.subheadline).foregroundStyle(Theme.ink2)
                            }
                            .padding(.top, 8)
                        }
                        ForEach(model.chat.messages) { m in
                            Bubble(m: m).id(m.id)
                        }
                        if model.chat.busy {
                            HStack(spacing: 8) {
                                ProgressView()
                                Text("Đang trả lời…").font(.subheadline).foregroundStyle(Theme.muted)
                            }
                            .id("busy")
                        }
                        if !model.chat.busy && !model.chat.suggest.isEmpty {
                            Suggestions(items: model.chat.suggest) { q in Task { await model.ask(q) } }.id("suggest")
                        }
                    }
                    .padding(16)
                }
                .scrollDismissesKeyboard(.interactively)
                .background(Theme.plane)
                .onChange(of: model.chat.messages.count) {
                    withAnimation { proxy.scrollTo(model.chat.busy ? "busy" : "suggest", anchor: .bottom) }
                }
                .onChange(of: model.chat.busy) {
                    withAnimation { proxy.scrollTo(model.chat.busy ? "busy" : "suggest", anchor: .bottom) }
                }
                .safeAreaInset(edge: .bottom) { composer }
                .navigationTitle("Trợ lý")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .topBarTrailing) { AccountMenu() } }
            }
        }
        .task { await screenshotAsk() }
    }

    private var composer: some View {
        HStack(alignment: .bottom, spacing: 8) {
            TextField("Hỏi trợ lý…", text: $question, axis: .vertical)
                .lineLimit(1...4)
                .focused($typing)
                .padding(.horizontal, 14).padding(.vertical, 10)
                .background(Theme.surface, in: RoundedRectangle(cornerRadius: 20))
                .overlay(RoundedRectangle(cornerRadius: 20).stroke(Theme.hair, lineWidth: 1))
                .submitLabel(.send)
                .onSubmit(send)
            Button(action: send) {
                Image(systemName: "arrow.up.circle.fill").font(.system(size: 34))
            }
            .disabled(question.trimmingCharacters(in: .whitespaces).isEmpty || model.chat.busy)
            .accessibilityLabel("Gửi")
        }
        .padding(.horizontal, 16).padding(.vertical, 8)
        .background(.bar)
    }

    private func send() {
        let q = question
        question = ""
        Task { await model.ask(q) }
    }

    /// The CI screenshot of an answer (docs/IOS_APP_PLAN.md): MF_ASK=<question>, asked once on launch.
    private func screenshotAsk() async {
        #if targetEnvironment(simulator)
        if let q = ProcessInfo.processInfo.environment["MF_ASK"], model.chat.messages.isEmpty { await model.ask(q) }
        #endif
    }
}

private struct Bubble: View {
    @Environment(AppModel.self) private var model
    let m: Chat.Message

    var body: some View {
        if m.mine {
            HStack {
                Spacer(minLength: 48)
                Text(m.text).foregroundStyle(Theme.accentInk)
                    .padding(.horizontal, 14).padding(.vertical, 10)
                    .background(Theme.accent, in: RoundedRectangle(cornerRadius: 18))
            }
        } else {
            VStack(alignment: .leading, spacing: 10) {
                Prose(text: m.text)
                if !m.steps.isEmpty {
                    FlowLayout(spacing: 6) {
                        ForEach(m.steps, id: \.self) { s in
                            Text("\(s.label ?? s.tool ?? "") \(s.status == "ok" ? "✓" : s.status == "declined" ? "–" : s.status == nil ? "" : "✕")")
                                .font(.caption).foregroundStyle(s.status == nil || s.status == "ok" ? Theme.ink2 : Theme.critical)
                                .padding(.horizontal, 8).padding(.vertical, 3)
                                .background(Theme.surface2, in: Capsule())
                        }
                    }
                }
                if m.waiting {
                    HStack(spacing: 8) {
                        Button("Xác nhận") { Task { await model.answer(m, approve: true) } }.buttonStyle(PrimaryButton())
                        Button("Huỷ") { Task { await model.answer(m, approve: false) } }.buttonStyle(.bordered)
                    }
                    .controlSize(.large)
                }
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.surface, in: RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Theme.hair, lineWidth: 1))
        }
    }
}

/// The answer's text as the website draws it (web/copilot.js prose): paragraphs, "- " lists, **bold**.
struct Prose: View {
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            ForEach(Array(text.split(separator: "\n", omittingEmptySubsequences: true).enumerated()), id: \.offset) { _, raw in
                let line = String(raw)
                if let item = Self.listItem(line) {
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Text("•").foregroundStyle(Theme.muted)
                        Text(Self.inline(item))
                    }
                } else {
                    let t = line.replacingOccurrences(of: #"^#+\s*"#, with: "", options: .regularExpression)
                        .trimmingCharacters(in: .whitespaces)
                    if !t.isEmpty { Text(Self.inline(t)) }
                }
            }
        }
        .font(.body)
        .foregroundStyle(Theme.ink)
        .textSelection(.enabled)
    }

    static func listItem(_ line: String) -> String? {
        guard let r = line.range(of: #"^\s*(?:[-*•]|\d+[.)])\s+"#, options: .regularExpression) else { return nil }
        return String(line[r.upperBound...])
    }

    static func inline(_ s: String) -> AttributedString {
        (try? AttributedString(markdown: s, options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)))
            ?? AttributedString(s)
    }
}

private struct Suggestions: View {
    let items: [String]
    let pick: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Gợi ý").font(.footnote.weight(.semibold)).foregroundStyle(Theme.muted)
            FlowLayout(spacing: 8) {
                ForEach(items.prefix(5), id: \.self) { q in
                    Button { pick(q) } label: {
                        Text(q).font(.subheadline).foregroundStyle(Theme.ink)
                            .padding(.horizontal, 12).padding(.vertical, 8)
                            .background(Theme.surface, in: Capsule())
                            .overlay(Capsule().stroke(Theme.hair, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(.top, 4)
    }
}

/// Chips that wrap onto the next line.
struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let rows = arrange(proposal.width ?? .infinity, subviews)
        return CGSize(width: proposal.width ?? rows.map(\.width).max() ?? 0,
                      height: rows.reduce(0) { $0 + $1.height } + spacing * CGFloat(max(0, rows.count - 1)))
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var y = bounds.minY
        for row in arrange(bounds.width, subviews) {
            var x = bounds.minX
            for i in row.items {
                let s = subviews[i].sizeThatFits(.unspecified)
                subviews[i].place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(width: min(s.width, bounds.width), height: s.height))
                x += min(s.width, bounds.width) + spacing
            }
            y += row.height + spacing
        }
    }

    private struct Line { var items: [Int] = []; var width: CGFloat = 0; var height: CGFloat = 0 }

    private func arrange(_ width: CGFloat, _ subviews: Subviews) -> [Line] {
        var rows: [Line] = [], cur = Line()
        for i in subviews.indices {
            let s = subviews[i].sizeThatFits(.unspecified)
            let w = min(s.width, width)
            if !cur.items.isEmpty && cur.width + spacing + w > width {
                rows.append(cur)
                cur = Line()
            }
            cur.width += (cur.items.isEmpty ? 0 : spacing) + w
            cur.height = max(cur.height, s.height)
            cur.items.append(i)
        }
        if !cur.items.isEmpty { rows.append(cur) }
        return rows
    }
}
