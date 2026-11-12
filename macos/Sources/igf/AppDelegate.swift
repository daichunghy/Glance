import AppKit

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private var appActivationObserver: Any?
    private var globalEventMonitor: Any?
    private var localEventMonitor: Any?
    
    // Known video conferencing and presentation bundle IDs
    private nonisolated static let videoCallBundleIDs: Set<String> = [
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
        
        // Start motion/camera tracking only if protection is enabled
        if AppModel.shared.isEnabled {
            if AppModel.shared.trackingSource == .camera {
                CameraTracker.shared.startTracking()
            } else {
                MotionTracker.shared.startTracking()
            }
        }
        
        // Monitor frontmost app changes to auto-pause during video calls & presentations
        setupAppSwitchMonitoring()
        
        // Setup global & local hotkey (Option + Shift + P / S)
        setupGlobalHotkey()
        
        print("[Glance] Started successfully.")
    }
    
    private func setupAppSwitchMonitoring() {
        let callBundleIDs = Self.videoCallBundleIDs
        appActivationObserver = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            queue: .main
        ) { notif in
            if let app = notif.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication,
               let bundleID = app.bundleIdentifier {
                let isVideoApp = callBundleIDs.contains(bundleID)
                let appName = app.localizedName ?? bundleID
                Task { @MainActor in
                    if AppModel.shared.isVideoCallActive != isVideoApp {
                        AppModel.shared.isVideoCallActive = isVideoApp
                        if isVideoApp {
                            print("[Glance] Video call app frontmost (\(appName)). Auto-pausing Glance.")
                        }
                    }
                }
            }
        }
    }
    
    private nonisolated static func matchesHotkeyAction(_ event: NSEvent) -> UInt16? {
        guard event.modifierFlags.contains([.option, .shift]) else { return nil }
        if event.keyCode == 35 || event.keyCode == 1 {
            return event.keyCode
        }
        return nil
    }

    private func triggerHotkey(keyCode: UInt16) {
        if keyCode == 35 {
            AppModel.shared.isEnabled.toggle()
            print("[Glance] Toggled protection via hotkey: \(AppModel.shared.isEnabled)")
        } else if keyCode == 1 {
            AppModel.shared.startShareMode()
            print("[Glance] Share mode on for 2 minutes")
        }
    }

    private func setupGlobalHotkey() {
        // Global monitor for Option + Shift + P (KeyCode 35 = 'P') and S (KeyCode 1 = 'S')
        globalEventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let keyCode = Self.matchesHotkeyAction(event) else { return }
            Task { @MainActor in
                self?.triggerHotkey(keyCode: keyCode)
            }
        }
        localEventMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let keyCode = Self.matchesHotkeyAction(event) else { return event }
            MainActor.assumeIsolated {
                self?.triggerHotkey(keyCode: keyCode)
            }
            return nil
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
        if let monitor = localEventMonitor {
            NSEvent.removeMonitor(monitor)
        }
    }
}
