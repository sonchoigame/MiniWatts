import AppIntents
import SwiftUI

@main
struct MiniWattsApp: App {
    @State private var monitor: PowerMonitor
    /// One per process, and alive for as long as the app is: the layer Picture in
    /// Picture draws from cannot come and go with a settings sheet.
    @State private var floatingMeter = FloatingMeterController()

    @AppStorage("nsmodWelcomeShown") private var nsmodWelcomeShown = false
    @State private var showNSMODWelcome = false

    init() {
        let monitor = PowerMonitor()
        _monitor = State(initialValue: monitor)
        // The Shortcuts action runs in this process — launched in the background, with
        // no scene, when the app is not already running — and has to read through this
        // monitor's sensors rather than open its own: a process gets one working HID
        // client, and a second one reads NaN. Registered here because `init` is the
        // one place that runs on every launch, scene or no scene.
        AppDependencyManager.shared.add(dependency: monitor)
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(monitor)
                .environment(floatingMeter)
                .onAppear {
                    if !nsmodWelcomeShown {
                        showNSMODWelcome = true
                    }
                }
                .fullScreenCover(isPresented: $showNSMODWelcome) {
                    NSMODWelcomeView {
                        nsmodWelcomeShown = true
                        showNSMODWelcome = false
                    }
                    .interactiveDismissDisabled()
                }
        }
    }
}

private struct NSMODWelcomeView: View {
    @Environment(\.openURL) private var openURL
    let onTelegramOpened: () -> Void

    private let telegramURL = URL(string: "https://t.me/sonchoigame23")!

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color.black,
                    Color(red: 0.08, green: 0.02, blue: 0.16),
                    Color(red: 0.02, green: 0.03, blue: 0.10)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 24) {
                Spacer()

                ZStack {
                    Circle()
                        .fill(.white.opacity(0.08))
                        .frame(width: 108, height: 108)

                    Circle()
                        .stroke(.purple.opacity(0.65), lineWidth: 2)
                        .frame(width: 108, height: 108)

                    Image(systemName: "bolt.fill")
                        .font(.system(size: 48, weight: .bold))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [.purple, .cyan],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .shadow(color: .purple.opacity(0.8), radius: 18)
                }

                VStack(spacing: 8) {
                    Text("VIETSUB BY NSMOD")
                        .font(.system(size: 30, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                        .multilineTextAlignment(.center)

                    Text("MiniWatts • Bản Việt hóa")
                        .font(.headline)
                        .foregroundStyle(.cyan)
                }

                Text("Tham gia kênh Telegram để nhận bản cập nhật Việt hóa mới nhất từ NSMOD.")
                    .font(.body)
                    .foregroundStyle(.white.opacity(0.75))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 34)

                Button {
                    openURL(telegramURL)
                    onTelegramOpened()
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "paperplane.fill")
                        Text("VÀO KÊNH TELEGRAM")
                            .fontWeight(.bold)
                    }
                    .font(.headline)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(
                        LinearGradient(
                            colors: [.purple, .blue],
                            startPoint: .leading,
                            endPoint: .trailing
                        ),
                        in: RoundedRectangle(cornerRadius: 18, style: .continuous)
                    )
                    .shadow(color: .purple.opacity(0.45), radius: 16, y: 6)
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 28)

                Text("@sonchoigame23")
                    .font(.footnote.monospaced())
                    .foregroundStyle(.white.opacity(0.5))

                Spacer()
            }
        }
    }
}
