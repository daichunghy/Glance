import SwiftUI
import Combine
import AppKit

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
    
    // Preferences
    @Published var isEnabled: Bool = true {
        didSet {
            if !isEnabled {
                clearProtection()
            }
        }
    }
    @Published var trackingSource: TrackingSource = .camera {
        didSet {
            handleTrackingSourceChange()
        }
    }
    @Published var blurMode: BlurMode = .directional {
        didSet {
            if isLookingAway && activeSide != .none && !isAwayFromDesk {
                if blurMode == .fullScreen {
                    activeSide = .full
                } else {
                    activeSide = (currentYawDegrees > 0) ? .left : .right
                }
            }
        }
    }
    @Published var sensitivity: Sensitivity = .medium
    @Published var blurIntensity: Double = 0.95
    @Published var autoBlurWhenAway: Bool = true {
        didSet {
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
    }

    @discardableResult
    func calibratePosture() -> Bool {
        postureGuard.calibrate()
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
    
    private init() {}
    
    func clearProtection() {
        isLookingAway = false
        isAwayFromDesk = false
        activeSide = .none
    }
    
    private func handleTrackingSourceChange() {
        if trackingSource == .camera {
            MotionTracker.shared.stopTracking()
            CameraTracker.shared.startTracking()
        } else {
            CameraTracker.shared.stopTracking()
            MotionTracker.shared.startTracking()
        }
    }
    
    // Robust state machine with dual-direction switching, hysteresis and meeting guard
    func processFaceState(angleDegrees: Double?, isPresent: Bool) {
        // Guard against blurring during video calls, settings tweaking or when disabled
        guard isEnabled, !isVideoCallActive, !isPopoverOpen else {
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
