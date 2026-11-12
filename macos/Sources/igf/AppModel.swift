import SwiftUI
import Combine
import AppKit
import QuartzCore
import ServiceManagement

enum TrackingSource: String, CaseIterable, Identifiable {
    case camera = "Camera"
    case airpods = "AirPods"
    
    var id: String { rawValue }
}

enum BlurMode: String, CaseIterable, Identifiable {
    case directional = "Side Blur"
    case fullScreen = "Full Screen"
    
    var id: String { rawValue }
}

enum Sensitivity: String, CaseIterable, Identifiable {
    case low = "Low"
    case medium = "Medium"
    case high = "High"
    
    var id: String { rawValue }
    
    var thresholdDegrees: Double {
        switch self {
        case .high: return 14.0
        case .medium: return 20.0
        case .low: return 28.0
        }
    }
}

enum ActiveProtectionSide: Equatable {
    case none
    case left
    case right
    case full
}

@MainActor
final class AppModel: ObservableObject {
    static let shared = AppModel()
    
    // Preferences (automatically persisted)
    @Published var isEnabled: Bool = true {
        didSet {
            UserDefaults.standard.set(isEnabled, forKey: "glance_isEnabled")
            if !isEnabled {
                clearProtection()
                // Off means the camera really stops (LED off) — the toggle
                // is also the kill switch (Option+Shift+P).
                CameraTracker.shared.stopTracking()
                MotionTracker.shared.stopTracking()
                isTrackingActive = false
                isCameraCoveredOrDark = false
            } else if oldValue == false {
                handleTrackingSourceChange()
            }
        }
    }

    // Share mode: deliberately show the screen to someone next to you for
    // 2 minutes without switching Glance off; protection resumes by itself.
    @Published var shareUntil: Date?
    private var shareExpiryTask: Task<Void, Never>?

    var isSharing: Bool {
        guard let shareUntil else { return false }
        return Date() < shareUntil
    }

    func startShareMode() {
        shareExpiryTask?.cancel()
        shareUntil = Date().addingTimeInterval(120)
        clearProtection()
        shareExpiryTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 120_000_000_000)
            guard !Task.isCancelled else { return }
            self?.shareUntil = nil
        }
    }
    @Published var trackingSource: TrackingSource = .camera {
        didSet {
            UserDefaults.standard.set(trackingSource.rawValue, forKey: "glance_trackingSource")
            handleTrackingSourceChange()
        }
    }
    @Published var blurMode: BlurMode = .directional {
        didSet {
            UserDefaults.standard.set(blurMode.rawValue, forKey: "glance_blurMode")
            if isLookingAway && activeSide != .none && !isAwayFromDesk {
                if blurMode == .fullScreen {
                    activeSide = .full
                } else {
                    activeSide = (currentYawDegrees > 0) ? .left : .right
                }
            }
        }
    }
    @Published var sensitivity: Sensitivity = .medium {
        didSet {
            UserDefaults.standard.set(sensitivity.rawValue, forKey: "glance_sensitivity")
        }
    }
    @Published var blurIntensity: Double = 0.95 {
        didSet {
            UserDefaults.standard.set(blurIntensity, forKey: "glance_blurIntensity")
        }
    }
    @Published var autoBlurWhenAway: Bool = true {
        didSet {
            UserDefaults.standard.set(autoBlurWhenAway, forKey: "glance_autoBlurWhenAway")
            if !autoBlurWhenAway && isAwayFromDesk {
                clearProtection()
            }
        }
    }
    // Posture Guard (turtle neck / hunch) — opt-in, off by default.
    // Shares the camera frames with privacy tracking; never blurs the
    // screen and never affects protection when off. See POSTURE_SPEC.md.
    @Published var postureEnabled: Bool = false {
        didSet {
            if !postureEnabled {
                postureGuard.resetTimers()
                postureStatus = .good
                postureWarningKinds = []
            }
        }
    }
    @Published var postureStatus: PostureStatus = .good
    @Published var postureWarningKinds: [PostureKind] = []
    @Published var postureSuggestBreak: Bool = false
    let postureGuard = PostureGuard()

    var postureNeedsCalibration: Bool { postureEnabled && !postureGuard.isCalibrated }

    /// Feed one camera observation into the posture guard.
    /// `centerY` must already be normalised so larger = head dropped lower
    /// (the Vision adapter in CameraTracker flips the y axis).
    func processPosture(now: Double, facePresent: Bool, faceSize: Double? = nil, centerY: Double? = nil, pitch: Double? = nil) {
        guard postureEnabled, trackingSource == .camera, !isVideoCallActive else { return }
        let result = postureGuard.update(now: now, facePresent: facePresent, faceSize: faceSize, centerY: centerY, pitch: pitch)
        postureStatus = result.status
        postureWarningKinds = result.warning ? result.kinds : []
        postureSuggestBreak = result.warning && result.suggestBreak
        if !result.warning { postureSuggestBreak = false }
    }

    @discardableResult
    func calibratePosture() -> Bool {
        let ok = postureGuard.calibrate()
        if ok { savePostureProfile() }
        return ok
    }

    // Calibration persists across relaunches (UserDefaults, numbers only).
    private func savePostureProfile() {
        guard let profile = postureGuard.exportProfile() else { return }
        let defaults = UserDefaults.standard
        defaults.set(profile["size"] ?? nil, forKey: "postureProfileSize")
        defaults.set(profile["centerY"] ?? nil, forKey: "postureProfileCenterY")
        defaults.set(profile["loosen"] ?? nil, forKey: "postureProfileLoosen")
        if let pitch = profile["pitch"] ?? nil {
            defaults.set(pitch, forKey: "postureProfilePitch")
            defaults.set(true, forKey: "postureProfileHasPitch")
        } else {
            defaults.set(false, forKey: "postureProfileHasPitch")
        }
    }

    private func loadPostureProfile() {
        let defaults = UserDefaults.standard
        guard defaults.object(forKey: "postureProfileSize") != nil else { return }
        var data: [String: Double?] = [
            "size": defaults.double(forKey: "postureProfileSize"),
            "centerY": defaults.double(forKey: "postureProfileCenterY"),
            "loosen": defaults.double(forKey: "postureProfileLoosen"),
        ]
        if defaults.bool(forKey: "postureProfileHasPitch") {
            data["pitch"] = defaults.double(forKey: "postureProfilePitch")
        }
        postureGuard.importProfile(data)
    }

    func dismissPostureAsNotBad() {
        postureGuard.dismissAsNotBad(now: CACurrentMediaTime())
        savePostureProfile()
        postureStatus = .good
        postureWarningKinds = []
    }

    func snoozePosture() {
        postureGuard.snooze(now: CACurrentMediaTime())
        postureStatus = .snoozed
        postureWarningKinds = []
    }

    private var isSyncingLaunchAtLogin = false
    @Published var launchAtLogin: Bool = false {
        didSet {
            guard !isSyncingLaunchAtLogin else { return }
            if #available(macOS 13.0, *) {
                do {
                    if launchAtLogin {
                        if SMAppService.mainApp.status != .enabled {
                            try SMAppService.mainApp.register()
                        }
                    } else {
                        if SMAppService.mainApp.status == .enabled {
                            try SMAppService.mainApp.unregister()
                        }
                    }
                } catch {
                    print("[Glance] Failed to update launchAtLogin: \(error)")
                    isSyncingLaunchAtLogin = true
                    launchAtLogin = (SMAppService.mainApp.status == .enabled)
                    isSyncingLaunchAtLogin = false
                }
            }
            UserDefaults.standard.set(launchAtLogin, forKey: "glance_launchAtLogin")
        }
    }
    // Smart Context Detection (Video calls, Meetings, Fullscreen Presentation)
    @Published var isVideoCallActive: Bool = false {
        didSet {
            if isVideoCallActive {
                clearProtection()
            }
        }
    }
    @Published var isPopoverOpen: Bool = false {
        didSet {
            if isPopoverOpen {
                clearProtection()
            }
        }
    }
    
    // Live Tracking Status
    @Published var isLookingAway: Bool = false
    @Published var isAwayFromDesk: Bool = false
    @Published var activeSide: ActiveProtectionSide = .none
    @Published var currentYawDegrees: Double = 0.0
    @Published var isTrackingActive: Bool = false
    @Published var isFaceDetected: Bool = false
    @Published var isAirPodsConnected: Bool = false
    @Published var cameraPermissionDenied: Bool = false
    @Published var cameraUnavailableMessage: String? = nil
    @Published var isCameraCoveredOrDark: Bool = false

    var isAirPodsSupportedOnOS: Bool {
        MotionTracker.shared.isSupportedOnCurrentOS
    }
    
    private init() {
        loadPostureProfile()
        let defaults = UserDefaults.standard
        if defaults.object(forKey: "glance_isEnabled") != nil {
            self.isEnabled = defaults.bool(forKey: "glance_isEnabled")
        }
        if let source = defaults.string(forKey: "glance_trackingSource"), let s = TrackingSource(rawValue: source) {
            self.trackingSource = (s == .airpods && !MotionTracker.shared.isSupportedOnCurrentOS) ? .camera : s
        }
        if let mode = defaults.string(forKey: "glance_blurMode"), let m = BlurMode(rawValue: mode) {
            self.blurMode = m
        }
        if let sens = defaults.string(forKey: "glance_sensitivity"), let s = Sensitivity(rawValue: sens) {
            self.sensitivity = s
        }
        if defaults.object(forKey: "glance_autoBlurWhenAway") != nil {
            self.autoBlurWhenAway = defaults.bool(forKey: "glance_autoBlurWhenAway")
        }
        if defaults.object(forKey: "glance_blurIntensity") != nil {
            self.blurIntensity = defaults.double(forKey: "glance_blurIntensity")
        }
        isSyncingLaunchAtLogin = true
        if #available(macOS 13.0, *) {
            self.launchAtLogin = (SMAppService.mainApp.status == .enabled)
        } else {
            self.launchAtLogin = defaults.bool(forKey: "glance_launchAtLogin")
        }
        isSyncingLaunchAtLogin = false
    }
    
    func clearProtection() {
        isLookingAway = false
        isAwayFromDesk = false
        activeSide = .none
    }

    func handleDarkCameraFrame() {
        isCameraCoveredOrDark = true
        isFaceDetected = false
        clearProtection()
    }
    
    private func handleTrackingSourceChange() {
        isCameraCoveredOrDark = false
        guard isEnabled else {
            CameraTracker.shared.stopTracking()
            MotionTracker.shared.stopTracking()
            isTrackingActive = false
            return
        }
        cameraUnavailableMessage = nil
        if trackingSource == .camera {
            MotionTracker.shared.stopTracking()
            CameraTracker.shared.startTracking()
        } else {
            CameraTracker.shared.stopTracking()
            cameraPermissionDenied = false
            MotionTracker.shared.startTracking()
        }
    }
    
    // Robust state machine with dual-direction switching, hysteresis and meeting guard
    func processFaceState(angleDegrees: Double?, isPresent: Bool) {
        isCameraCoveredOrDark = false
        // Guard against blurring during video calls, settings tweaking, share mode or when disabled
        guard isEnabled, !isVideoCallActive, !isPopoverOpen, !isSharing else {
            if isLookingAway || activeSide != .none {
                clearProtection()
            }
            return
        }
        
        if isPresent, let angle = angleDegrees {
            isFaceDetected = true
            if isAwayFromDesk {
                clearProtection()
            }
            currentYawDegrees = angle
            
            let threshold = sensitivity.thresholdDegrees
            let releaseThreshold = max(5.0, threshold - 6.0)
            
            if isLookingAway {
                if abs(angle) < releaseThreshold {
                    // Head returned to center safe zone
                    clearProtection()
                } else {
                    // Head still turned away: handle swinging between left and right seamlessly
                    if angle > threshold {
                        // Looking right -> blur left
                        activeSide = (blurMode == .directional) ? .left : .full
                    } else if angle < -threshold {
                        // Looking left -> blur right
                        activeSide = (blurMode == .directional) ? .right : .full
                    }
                }
            } else {
                // Head was centered: trigger blur if angle exceeds threshold
                if angle > threshold {
                    // Looking right -> blur left
                    isLookingAway = true
                    activeSide = (blurMode == .directional) ? .left : .full
                } else if angle < -threshold {
                    // Looking left -> blur right
                    isLookingAway = true
                    activeSide = (blurMode == .directional) ? .right : .full
                }
            }
        } else {
            // Face not in frame (user turned head extreme angle or walked away)
            isFaceDetected = false
            
            if autoBlurWhenAway {
                isAwayFromDesk = true
                isLookingAway = true
                activeSide = .full
            }
        }
    }
    
    // Fallback for AirPods motion updates
    func processAngle(_ angleDegrees: Double) {
        processFaceState(angleDegrees: angleDegrees, isPresent: true)
    }
}
