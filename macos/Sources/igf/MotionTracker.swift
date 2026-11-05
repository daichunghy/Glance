import Foundation
import CoreMotion

@MainActor
final class MotionTracker: NSObject, CMHeadphoneMotionManagerDelegate {
    static let shared = MotionTracker()
    
    private let motionManager = CMHeadphoneMotionManager()
    private var baselineYaw: Double?
    private var smoothedAngle: Double = 0.0
    private let smoothingFactor: Double = 0.35 // 0 to 1, higher = more responsive
    
    override init() {
        super.init()
        motionManager.delegate = self
    }
    
    func startTracking() {
        guard motionManager.isDeviceMotionAvailable else {
            print("[igf] Headphone motion is not available on this device.")
            AppModel.shared.isAirPodsConnected = false
            return
        }
        
        AppModel.shared.isAirPodsConnected = true
        
        motionManager.startDeviceMotionUpdates(to: .main) { [weak self] motion, error in
            guard let self = self, let motion = motion, error == nil else {
                if let error = error {
                    print("[igf] Motion update error: \(error.localizedDescription)")
                }
                return
            }
            
            AppModel.shared.isAirPodsConnected = true
            
            let rawYaw = motion.attitude.yaw
            
            // Set initial baseline if not set yet
            if self.baselineYaw == nil {
                self.baselineYaw = rawYaw
            }
            
            guard let baseline = self.baselineYaw else { return }
            
            // Calculate relative angle with wrap-around handling (-pi to pi)
            var delta = rawYaw - baseline
            while delta > .pi { delta -= 2 * .pi }
            while delta < -.pi { delta += 2 * .pi }
            
            let degrees = delta * 180.0 / .pi
            
            // Smooth out jitter
            self.smoothedAngle = (self.smoothedAngle * (1.0 - self.smoothingFactor)) + (degrees * self.smoothingFactor)
            
            AppModel.shared.processAngle(self.smoothedAngle)
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
    
    // MARK: - CMHeadphoneMotionManagerDelegate
    
    nonisolated func headphoneMotionManagerDidConnect(_ manager: CMHeadphoneMotionManager) {
        Task { @MainActor in
            print("[igf] AirPods connected with motion support.")
            AppModel.shared.isAirPodsConnected = true
            self.startTracking()
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
