import Foundation
import CoreMotion

@available(macOS 14.0, *)
@MainActor
private final class HeadphoneMotionAdapter: NSObject, CMHeadphoneMotionManagerDelegate {
    private let motionManager = CMHeadphoneMotionManager()
    private var baselineYaw: Double?
    private var smoothedAngle: Double = 0.0
    private let smoothingFactor: Double = 0.35

    override init() {
        super.init()
        motionManager.delegate = self
    }

    func startTracking() {
        guard motionManager.isDeviceMotionAvailable else {
            print("[igf] Headphone motion is not available on this device.")
            AppModel.shared.isAirPodsConnected = false
            AppModel.shared.cameraUnavailableMessage = "AirPods motion not available. Connect supported AirPods."
            return
        }

        AppModel.shared.cameraUnavailableMessage = nil
        AppModel.shared.isAirPodsConnected = true
        AppModel.shared.isTrackingActive = true

        motionManager.startDeviceMotionUpdates(to: .main) { [weak self] motion, error in
            MainActor.assumeIsolated {
                guard let self = self, let motion = motion, error == nil else {
                    if let error = error {
                        print("[igf] Motion update error: \(error.localizedDescription)")
                    }
                    return
                }

                AppModel.shared.isAirPodsConnected = true

                let rawYaw = motion.attitude.yaw
                if self.baselineYaw == nil {
                    self.baselineYaw = rawYaw
                }
                guard let baseline = self.baselineYaw else { return }

                var delta = rawYaw - baseline
                while delta > .pi { delta -= 2 * .pi }
                while delta < -.pi { delta += 2 * .pi }

                let degrees = delta * 180.0 / .pi
                self.smoothedAngle = (self.smoothedAngle * (1.0 - self.smoothingFactor)) + (degrees * self.smoothingFactor)
                AppModel.shared.processAngle(self.smoothedAngle)
            }
        }
    }

    func stopTracking() {
        motionManager.stopDeviceMotionUpdates()
    }

    func calibrateCenter() {
        if let currentMotion = motionManager.deviceMotion {
            baselineYaw = currentMotion.attitude.yaw
            smoothedAngle = 0.0
            AppModel.shared.processAngle(0.0)
            print("[igf] Calibrated center reference angle.")
        } else {
            baselineYaw = nil
            smoothedAngle = 0.0
        }
    }

    nonisolated func headphoneMotionManagerDidConnect(_ manager: CMHeadphoneMotionManager) {
        Task { @MainActor in
            print("[igf] AirPods connected with motion support.")
            AppModel.shared.isAirPodsConnected = true
            if AppModel.shared.isEnabled && AppModel.shared.trackingSource == .airpods {
                self.startTracking()
            }
        }
    }

    nonisolated func headphoneMotionManagerDidDisconnect(_ manager: CMHeadphoneMotionManager) {
        Task { @MainActor in
            print("[igf] AirPods disconnected.")
            AppModel.shared.isAirPodsConnected = false
            self.stopTracking()
        }
    }
}

@MainActor
final class MotionTracker: NSObject {
    static let shared = MotionTracker()

    private var adapterStorage: AnyObject?

    var isSupportedOnCurrentOS: Bool {
        if #available(macOS 14.0, *) {
            return true
        }
        return false
    }

    @available(macOS 14.0, *)
    private var adapter: HeadphoneMotionAdapter {
        if let existing = adapterStorage as? HeadphoneMotionAdapter {
            return existing
        }
        let created = HeadphoneMotionAdapter()
        adapterStorage = created
        return created
    }

    func startTracking() {
        if #available(macOS 14.0, *) {
            adapter.startTracking()
        } else {
            AppModel.shared.isAirPodsConnected = false
            AppModel.shared.isTrackingActive = false
            AppModel.shared.cameraUnavailableMessage = "AirPods tracking requires macOS 14 or later."
        }
    }

    func stopTracking() {
        if #available(macOS 14.0, *) {
            (adapterStorage as? HeadphoneMotionAdapter)?.stopTracking()
        }
    }

    func calibrateCenter() {
        if #available(macOS 14.0, *) {
            adapter.calibrateCenter()
        }
    }
}
