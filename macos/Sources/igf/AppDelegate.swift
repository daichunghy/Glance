import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private var appActivationObserver: Any?
    private var globalEventMonitor: Any?
    
    // Known video conferencing and presentation bundle IDs
    private let videoCallBundleIDs: Set<String> = [
        "us.zoom.xos",
        "com.microsoft.teams",
        "com.microsoft.teams2",
        "com.apple.FaceTime",
        "com.cisco.webexmeetingsapp",
        "com.discord",
        "com.hnc.Discord",
        "com.apple.iWork.Keynote"
    ]
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Initialize overlays
        _ = BlurOverlayController.shared
        
        // Initialize menu bar item
        _ = MenuBarController.shared
        
        // Start motion/camera tracking
        if AppModel.shared.trackingSource == .camera {
            CameraTracker.shared.startTracking()
        } else {
            MotionTracker.shared.startTracking()
        }
        
        // Monitor frontmost app changes to auto-pause during video calls & presentations
        setupAppSwitchMonitoring()
        
        // Setup global hotkey (Option + Shift + P to quickly Pause/Resume)
        setupGlobalHotkey()
        
        print("[Glance] Started successfully.")
    }
    
    private func setupAppSwitchMonitoring() {
        appActivationObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { [weak self] notif in
            guard let self = self else { return }
            if let app = notif.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication,
               let bundleID = app.bundleIdentifier {
                let isVideoApp = self.videoCallBundleIDs.contains(bundleID)
                Task { @MainActor in
                    if AppModel.shared.isVideoCallActive != isVideoApp {
                        AppModel.shared.isVideoCallActive = isVideoApp
                        if isVideoApp {
                            print("[Glance] Video call app frontmost (\(app.localizedName ?? bundleID)). Auto-pausing Glance.")
                        }
                    }
                }
            }
        }
    }
    
    private func setupGlobalHotkey() {
        // Global monitor for Option + Shift + P (KeyCode 35 = 'P')
        globalEventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
            guard event.modifierFlags.contains([.option, .shift]) else { return }
            if event.keyCode == 35 {
                Task { @MainActor in
                    AppModel.shared.isEnabled.toggle()
                    print("[Glance] Toggled protection via hotkey: \(AppModel.shared.isEnabled)")
                }
            } else if event.keyCode == 1 {
                // Option + Shift + S: share the screen for 2 minutes
                Task { @MainActor in
                    AppModel.shared.startShareMode()
                    print("[Glance] Share mode on for 2 minutes")
                }
            }
        }
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        CameraTracker.shared.stopTracking()
        MotionTracker.shared.stopTracking()
        if let observer = appActivationObserver {
            NSWorkspace.shared.notificationCenter.removeObserver(observer)
        }
        if let monitor = globalEventMonitor {
            NSEvent.removeMonitor(monitor)
        }
    }
}
