import Foundation

/// Posture policy (turtle neck / hunch), independent of camera and UI.
///
/// Shared spec: posture/POSTURE_SPEC.md in the repository root.
/// This mirrors windows/posture.py and linux/posture.py exactly (same
/// thresholds and state machine); the adapters on each platform normalise
/// camera geometry into the same inputs:
///   faceSize -- face width / frame width (proxy for head distance)
///   centerY  -- face centre Y, normalised, positive direction = head drops
///   pitch    -- optional head pitch in degrees (Vision, macOS only)
///
/// No frames are stored or sent anywhere; only these numbers live in RAM.
enum PostureKind: String, Equatable {
    case turtleNeck = "turtle_neck"
    case hunch = "hunch"
}

enum PostureStatus: Equatable {
    case uncalibrated
    case noFace
    case good
    case badPending
    case warning
    case snoozed
}

struct PostureResult: Equatable {
    let status: PostureStatus
    let kinds: [PostureKind]
    let warning: Bool
    let justTriggered: Bool
    let forward: Double
    let drop: Double
}

final class PostureGuard {
    let holdSeconds: Double
    let cooldownSeconds: Double
    let releaseSeconds: Double
    let forwardThreshold: Double = 0.18
    let forwardAlone: Double = 0.28
    let dropThreshold: Double = 0.07
    let dropAlone: Double = 0.12
    let supportingDrop: Double = 0.03
    let supportingForward: Double = 0.08
    let pitchDropThreshold: Double = 8.0
    let keyboardPitchDrop: Double = 20.0

    private(set) var baselineSize: Double?
    private(set) var baselineCenterY: Double?
    private(set) var baselinePitch: Double?

    private var smoothSize: Double?
    private var smoothCenterY: Double?
    private var smoothPitch: Double?
    private var badSince: Double?
    private var goodSince: Double?
    private var warningActive = false
    private var warningKinds: [PostureKind] = []
    private var cooldownUntil: Double?
    // Adaptive behaviour (research round 2), mirroring posture.py.
    private var warningTimes: [Double] = []
    private(set) var loosenFactor: Double = 1.0
    private var snoozedUntil: Double?

    init(holdSeconds: Double = 10, cooldownSeconds: Double = 60, releaseSeconds: Double = 3) {
        self.holdSeconds = holdSeconds
        self.cooldownSeconds = cooldownSeconds
        self.releaseSeconds = releaseSeconds
    }

    var isCalibrated: Bool { baselineSize != nil }

    /// Adopts the current smoothed measurements as the good baseline.
    /// Returns false when no face has been measured yet, so the UI can ask
    /// the user to look at the camera instead of saving an empty baseline.
    @discardableResult
    func calibrate() -> Bool {
        guard let size = smoothSize, let centerY = smoothCenterY else { return false }
        baselineSize = size
        baselineCenterY = centerY
        baselinePitch = smoothPitch
        loosenFactor = 1.0
        resetTimers()
        return true
    }

    /// 60s, then 120s, then 300s for repeat warnings within one hour.
    private func adaptiveCooldown(now: Double) -> Double {
        warningTimes = warningTimes.filter { now - $0 < 3600 }
        if warningTimes.count <= 1 { return cooldownSeconds }
        if warningTimes.count == 2 { return max(cooldownSeconds, 120) }
        return max(cooldownSeconds, 300)
    }

    /// Silence posture warnings for a while (default 30 minutes).
    func snooze(now: Double, seconds: Double = 1800) {
        snoozedUntil = now + seconds
        resetTimers(keepCooldown: true)
    }

    /// User tapped "not bad posture": clear this warning and loosen up.
    /// Thresholds grow 10% per tap (capped at x1.5).
    @discardableResult
    func dismissAsNotBad(now: Double) -> Double {
        loosenFactor = min(1.5, loosenFactor * 1.10)
        resetTimers()
        cooldownUntil = now + cooldownSeconds
        return loosenFactor
    }

    func reset() {
        baselineSize = nil
        baselineCenterY = nil
        baselinePitch = nil
        smoothSize = nil
        smoothCenterY = nil
        smoothPitch = nil
        warningTimes = []
        loosenFactor = 1.0
        snoozedUntil = nil
        resetTimers()
    }

    func resetTimers(keepCooldown: Bool = false) {
        badSince = nil
        goodSince = nil
        warningActive = false
        warningKinds = []
        if !keepCooldown { cooldownUntil = nil }
    }

    private func smoothed(_ current: Double?, _ value: Double?) -> Double? {
        guard let value else { return current }
        guard let current else { return value }
        return current * 0.70 + value * 0.30
    }

    func update(now: Double, facePresent: Bool, faceSize: Double? = nil, centerY: Double? = nil, pitch: Double? = nil) -> PostureResult {
        if let snoozedUntil {
            if now < snoozedUntil {
                return PostureResult(status: .snoozed, kinds: [], warning: false, justTriggered: false, forward: 0, drop: 0)
            }
            self.snoozedUntil = nil
        }
        guard facePresent else {
            // Away / looking elsewhere is the privacy guard's job, not ours.
            badSince = nil
            goodSince = nil
            return PostureResult(status: .noFace, kinds: [], warning: warningActive, justTriggered: false, forward: 0, drop: 0)
        }

        smoothSize = smoothed(smoothSize, faceSize)
        smoothCenterY = smoothed(smoothCenterY, centerY)
        smoothPitch = smoothed(smoothPitch, pitch)

        guard let baselineSize, let baselineCenterY, let size = smoothSize, let center = smoothCenterY else {
            return PostureResult(status: .uncalibrated, kinds: [], warning: false, justTriggered: false, forward: 0, drop: 0)
        }

        let forward = baselineSize != 0 ? size / baselineSize - 1.0 : 0.0
        let drop = center - baselineCenterY
        var pitchDrop = 0.0
        if pitch != nil, let baselinePitch, let smoothPitch {
            pitchDrop = baselinePitch - smoothPitch
        }

        let kinds = classify(forward: forward, drop: drop, pitchDrop: pitchDrop, pitchAvailable: pitch != nil)

        if !kinds.isEmpty {
            goodSince = nil
            if badSince == nil { badSince = now }
            if warningActive {
                warningKinds = kinds
                return PostureResult(status: .warning, kinds: kinds, warning: true, justTriggered: false, forward: forward, drop: drop)
            }
            if let badSince, now - badSince >= holdSeconds {
                if cooldownUntil == nil || now >= cooldownUntil! {
                    warningActive = true
                    warningKinds = kinds
                    warningTimes.append(now)
                    cooldownUntil = now + adaptiveCooldown(now: now)
                    return PostureResult(status: .warning, kinds: kinds, warning: true, justTriggered: true, forward: forward, drop: drop)
                }
                return PostureResult(status: .badPending, kinds: kinds, warning: false, justTriggered: false, forward: forward, drop: drop)
            }
            return PostureResult(status: .badPending, kinds: kinds, warning: false, justTriggered: false, forward: forward, drop: drop)
        }

        // Good posture this frame.
        badSince = nil
        if warningActive {
            if goodSince == nil { goodSince = now }
            if let goodSince, now - goodSince >= releaseSeconds {
                warningActive = false
                warningKinds = []
                self.goodSince = nil
                return PostureResult(status: .good, kinds: [], warning: false, justTriggered: false, forward: forward, drop: drop)
            }
            return PostureResult(status: .warning, kinds: warningKinds, warning: true, justTriggered: false, forward: forward, drop: drop)
        }
        return PostureResult(status: .good, kinds: [], warning: false, justTriggered: false, forward: forward, drop: drop)
    }

    private func classify(forward: Double, drop: Double, pitchDrop: Double, pitchAvailable: Bool) -> [PostureKind] {
        // Looking down at a keyboard / notes is not bad posture: the head
        // pitches far down but does not push forward or sink deeply.
        if pitchAvailable && pitchDrop >= keyboardPitchDrop && forward < supportingForward && drop < dropAlone {
            return []
        }
        var kinds: [PostureKind] = []
        let loosen = loosenFactor
        let turtle = forward >= forwardAlone * loosen
            || (forward >= forwardThreshold * loosen && (drop >= supportingDrop * loosen || pitchDrop >= pitchDropThreshold))
        let hunch = drop >= dropAlone * loosen
            || (drop >= dropThreshold * loosen && (pitchDrop >= pitchDropThreshold || forward >= supportingForward * loosen))
        if turtle { kinds.append(.turtleNeck) }
        if hunch { kinds.append(.hunch) }
        return kinds
    }
}
