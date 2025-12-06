import SwiftUI
import AppKit
import Starscream

// MARK: - Main App

@main
struct VoiceHUDApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}

// MARK: - App Delegate

class AppDelegate: NSObject, NSApplicationDelegate {
    var hudWindow: HUDWindow?
    var wsClient: HUDWebSocketClient?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Hide from dock
        NSApp.setActivationPolicy(.accessory)

        // Create the HUD window
        hudWindow = HUDWindow()

        // Connect to Python backend
        wsClient = HUDWebSocketClient(hudWindow: hudWindow!)
        wsClient?.connect()

        print("VoiceHUD started - connecting to ws://localhost:8765")
    }

    func applicationWillTerminate(_ notification: Notification) {
        wsClient?.disconnect()
    }
}

// MARK: - HUD View Model

class HUDViewModel: ObservableObject {
    @Published var title: String = ""
    @Published var content: String = ""
    @Published var contentType: String = "text"
    @Published var actions: [String] = ["copy"]
    @Published var isStreaming: Bool = false
    @Published var showClarification: Bool = false
    @Published var clarificationQuestion: String = ""
    @Published var clarificationOptions: [[String: String]] = []

    var onAction: (String) -> Void = { _ in }
    var onDismiss: () -> Void = {}
}

// MARK: - HUD Window (Floating Panel)

class HUDWindow: NSPanel {
    var viewModel: HUDViewModel
    var hostingView: NSHostingView<HUDContentView>?

    init() {
        self.viewModel = HUDViewModel()

        super.init(
            contentRect: NSRect(x: 0, y: 0, width: 600, height: 400),
            styleMask: [.nonactivatingPanel, .titled, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )

        // Window appearance
        self.isFloatingPanel = true
        self.level = .floating
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        self.isMovableByWindowBackground = true
        self.titlebarAppearsTransparent = true
        self.titleVisibility = .hidden
        self.backgroundColor = .clear
        self.isOpaque = false
        self.hasShadow = true

        // Set up callbacks
        viewModel.onAction = { [weak self] action in
            self?.handleAction(action)
        }
        viewModel.onDismiss = { [weak self] in
            self?.hide()
        }

        // Create SwiftUI view
        let contentView = HUDContentView(viewModel: viewModel)
        hostingView = NSHostingView(rootView: contentView)
        self.contentView = hostingView

        // Center on screen
        if let screen = NSScreen.main {
            let screenRect = screen.visibleFrame
            let windowRect = self.frame
            let x = screenRect.midX - windowRect.width / 2
            let y = screenRect.midY - windowRect.height / 2
            self.setFrameOrigin(NSPoint(x: x, y: y))
        }
    }

    func show() {
        self.alphaValue = 0
        self.orderFrontRegardless()

        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.15
            self.animator().alphaValue = 1
        }
    }

    func hide() {
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.15
            self.animator().alphaValue = 0
        } completionHandler: {
            self.orderOut(nil)
        }
    }

    func updateContent(title: String, content: String, contentType: String, actions: [String]) {
        DispatchQueue.main.async {
            self.viewModel.title = title
            self.viewModel.content = content
            self.viewModel.contentType = contentType
            self.viewModel.actions = actions
            self.viewModel.showClarification = false
        }
    }

    func appendContent(_ chunk: String) {
        DispatchQueue.main.async {
            self.viewModel.content += chunk
        }
    }

    func setStreaming(_ streaming: Bool) {
        DispatchQueue.main.async {
            self.viewModel.isStreaming = streaming
        }
    }

    func showClarification(question: String, options: [[String: String]]) {
        DispatchQueue.main.async {
            self.viewModel.clarificationQuestion = question
            self.viewModel.clarificationOptions = options
            self.viewModel.showClarification = true
        }
    }

    private func handleAction(_ action: String) {
        // Send action back to Python via WebSocket
        NotificationCenter.default.post(
            name: .hudAction,
            object: nil,
            userInfo: ["action": action, "content": viewModel.content]
        )
    }

    // Click outside to dismiss
    override func resignKey() {
        super.resignKey()
        hide()
    }
}

// MARK: - HUD Content View

struct HUDContentView: View {
    @ObservedObject var viewModel: HUDViewModel

    var body: some View {
        VStack(spacing: 0) {
            // Title bar
            HStack {
                Text(viewModel.title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.primary)

                Spacer()

                if viewModel.isStreaming {
                    ProgressView()
                        .scaleEffect(0.6)
                        .frame(width: 16, height: 16)
                }

                Button(action: viewModel.onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                        .font(.system(size: 16))
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)

            Divider()

            // Content area
            ScrollView {
                if viewModel.showClarification {
                    ClarificationView(
                        question: viewModel.clarificationQuestion,
                        options: viewModel.clarificationOptions,
                        onSelect: { value in
                            viewModel.onAction("select:\(value)")
                        }
                    )
                } else {
                    ContentDisplayView(
                        content: viewModel.content,
                        contentType: viewModel.contentType
                    )
                }
            }
            .frame(maxHeight: 300)

            Divider()

            // Action buttons
            HStack(spacing: 12) {
                ForEach(viewModel.actions, id: \.self) { action in
                    ActionButton(action: action) {
                        viewModel.onAction(action)
                    }
                }

                Spacer()

                // Keyboard shortcut hints
                Text("⌘C Copy  ⎋ Dismiss")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .frame(width: 600)
        .background(VisualEffectBlur())
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.primary.opacity(0.1), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.2), radius: 20, x: 0, y: 10)
    }
}

// MARK: - Content Display View (Renders text/code/markdown)

struct ContentDisplayView: View {
    let content: String
    let contentType: String

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            if contentType == "code" {
                CodeBlockView(code: content)
            } else {
                Text(content)
                    .font(.system(size: 14))
                    .foregroundColor(.primary)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(16)
    }
}

// MARK: - Code Block View

struct CodeBlockView: View {
    let code: String

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(code)
                .font(.system(size: 13, design: .monospaced))
                .foregroundColor(.primary)
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(Color.primary.opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }
}

// MARK: - Clarification View

struct ClarificationView: View {
    let question: String
    let options: [[String: String]]
    let onSelect: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(question)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.primary)

            ForEach(Array(options.enumerated()), id: \.offset) { index, option in
                Button(action: { onSelect(option["value"] ?? "") }) {
                    HStack {
                        Text("\(index + 1).")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.secondary)
                            .frame(width: 20)

                        Text(option["label"] ?? "")
                            .font(.system(size: 14))
                            .foregroundColor(.primary)

                        Spacer()
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color.primary.opacity(0.05))
                    .clipShape(RoundedRectangle(cornerRadius: 6))
                }
                .buttonStyle(.plain)
            }
        }
        .padding(16)
    }
}

// MARK: - Action Button

struct ActionButton: View {
    let action: String
    let onTap: () -> Void

    var icon: String {
        switch action {
        case "copy": return "doc.on.doc"
        case "insert": return "text.insert"
        case "run": return "play.fill"
        case "send": return "paperplane.fill"
        default: return "circle"
        }
    }

    var label: String {
        switch action {
        case "copy": return "Copy"
        case "insert": return "Insert"
        case "run": return "Run"
        case "send": return "Send"
        default: return action.capitalized
        }
    }

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                Text(label)
                    .font(.system(size: 12, weight: .medium))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color.accentColor.opacity(0.1))
            .foregroundColor(.accentColor)
            .clipShape(RoundedRectangle(cornerRadius: 6))
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Frosted Glass Effect

struct VisualEffectBlur: NSViewRepresentable {
    func makeNSView(context: Context) -> NSVisualEffectView {
        let view = NSVisualEffectView()
        view.blendingMode = .behindWindow
        view.state = .active
        view.material = .hudWindow
        return view
    }

    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {}
}

// MARK: - WebSocket Client

extension Notification.Name {
    static let hudAction = Notification.Name("hudAction")
}

class HUDWebSocketClient: WebSocketDelegate {
    private var socket: WebSocket?
    private weak var hudWindow: HUDWindow?
    private var isConnected = false
    private var reconnectTimer: Timer?

    init(hudWindow: HUDWindow) {
        self.hudWindow = hudWindow

        // Listen for actions from HUD
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleHUDAction),
            name: .hudAction,
            object: nil
        )
    }

    func connect() {
        guard let url = URL(string: "ws://localhost:8765") else { return }

        var request = URLRequest(url: url)
        request.timeoutInterval = 5

        socket = WebSocket(request: request)
        socket?.delegate = self
        socket?.connect()
    }

    func disconnect() {
        reconnectTimer?.invalidate()
        socket?.disconnect()
    }

    @objc private func handleHUDAction(_ notification: Notification) {
        guard let action = notification.userInfo?["action"] as? String,
              let content = notification.userInfo?["content"] as? String else { return }

        // Handle local actions
        switch action {
        case "copy":
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(content, forType: .string)

        case "insert":
            // Copy and simulate paste
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(content, forType: .string)

            // Hide HUD first
            hudWindow?.hide()

            // Small delay then paste
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                self.simulatePaste()
            }

        default:
            break
        }

        // Send action to Python backend
        let message: [String: Any] = [
            "action": action,
            "content": content
        ]

        if let data = try? JSONSerialization.data(withJSONObject: message),
           let json = String(data: data, encoding: .utf8) {
            socket?.write(string: json)
        }
    }

    private func simulatePaste() {
        let src = CGEventSource(stateID: .hidSystemState)

        let keyDown = CGEvent(keyboardEventSource: src, virtualKey: 0x09, keyDown: true) // V key
        keyDown?.flags = .maskCommand
        keyDown?.post(tap: .cghidEventTap)

        let keyUp = CGEvent(keyboardEventSource: src, virtualKey: 0x09, keyDown: false)
        keyUp?.flags = .maskCommand
        keyUp?.post(tap: .cghidEventTap)
    }

    // MARK: - WebSocketDelegate

    func didReceive(event: WebSocketEvent, client: any Starscream.WebSocketClient) {
        switch event {
        case .connected:
            print("WebSocket connected")
            isConnected = true
            reconnectTimer?.invalidate()

        case .disconnected(let reason, let code):
            print("WebSocket disconnected: \(reason) (code: \(code))")
            isConnected = false
            scheduleReconnect()

        case .text(let text):
            handleMessage(text)

        case .error(let error):
            print("WebSocket error: \(String(describing: error))")
            isConnected = false
            scheduleReconnect()

        case .cancelled:
            isConnected = false
            scheduleReconnect()

        default:
            break
        }
    }

    private func scheduleReconnect() {
        reconnectTimer?.invalidate()
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: false) { [weak self] _ in
            self?.connect()
        }
    }

    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String else { return }

        DispatchQueue.main.async { [weak self] in
            switch type {
            case "show_hud":
                let title = json["title"] as? String ?? ""
                let content = json["content"] as? String ?? ""
                let contentType = json["content_type"] as? String ?? "text"
                let actions = json["actions"] as? [String] ?? ["copy"]

                self?.hudWindow?.updateContent(
                    title: title,
                    content: content,
                    contentType: contentType,
                    actions: actions
                )
                self?.hudWindow?.setStreaming(true)
                self?.hudWindow?.show()

            case "stream":
                let chunk = json["content"] as? String ?? ""
                self?.hudWindow?.appendContent(chunk)

            case "complete":
                self?.hudWindow?.setStreaming(false)

            case "hide_hud":
                self?.hudWindow?.hide()

            case "error":
                let content = json["content"] as? String ?? "An error occurred"
                self?.hudWindow?.updateContent(
                    title: "Error",
                    content: content,
                    contentType: "text",
                    actions: []
                )
                self?.hudWindow?.show()

            case "clarify":
                let question = json["content"] as? String ?? ""
                let options = json["options"] as? [[String: String]] ?? []
                self?.hudWindow?.showClarification(question: question, options: options)
                self?.hudWindow?.show()

            default:
                break
            }
        }
    }
}
