import Foundation
import AppKit
import AVFoundation
import Vision
import CoreGraphics

final class CameraTracker: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate, @unchecked Sendable {
    static let shared = CameraTracker()
    
    private let captureSession = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "com.glance.camera.queue", qos: .userInteractive)
    private var isRunning = false
    
    // Persistent Vision sequence handler & request for maximum performance and stability
    private let sequenceHandler = VNSequenceRequestHandler()
    private lazy var faceRequest: VNDetectFaceRectanglesRequest = {
        let req = VNDetectFaceRectanglesRequest()
        req.revision = VNDetectFaceRectanglesRequestRevision3
        return req
    }()
    
    private var lastProcessTime: TimeInterval = 0
    private let processInterval: TimeInterval = 0.12 // ~8 FPS
    
    private var baselineAngle: Double = 0.0
    private var smoothedAngle: Double = 0.0
    private var noFaceFramesCount: Int = 0
    
    override init() {
        super.init()
        setupSession()
        setupInterruptionAndSleepObservers()
    }
    
    private func setupSession() {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            
            self.captureSession.beginConfiguration()
            
            // Using .low preset drastically minimizes buffer allocations and RAM footprint (~75% reduction)
            if self.captureSession.canSetSessionPreset(.low) {
                self.captureSession.sessionPreset = .low
            } else {
                self.captureSession.sessionPreset = .vga640x480
            }
            
            guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) ?? AVCaptureDevice.default(for: .video),
                  let input = try? AVCaptureDeviceInput(device: device),
                  self.captureSession.canAddInput(input) else {
                self.captureSession.commitConfiguration()
                return
            }
            
            self.captureSession.addInput(input)
            
            // Limit hardware camera sensor frame rate to supported range (15 FPS)
            do {
                try device.lockForConfiguration()
                if let range = device.activeFormat.videoSupportedFrameRateRanges.first {
                    let minRate = range.minFrameRate
                    device.activeVideoMinFrameDuration = CMTime(value: 1000, timescale: CMTimeScale(minRate * 1000))
                    device.activeVideoMaxFrameDuration = CMTime(value: 1000, timescale: CMTimeScale(minRate * 1000))
                }
                device.unlockForConfiguration()
            } catch {
                print("[Glance] Camera frame rate config skipped: \(error)")
            }
            
            self.videoOutput.alwaysDiscardsLateVideoFrames = true
            self.videoOutput.videoSettings = [
                kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange)
            ]
            self.videoOutput.setSampleBufferDelegate(self, queue: self.sessionQueue)
            
            if self.captureSession.canAddOutput(self.videoOutput) {
                self.captureSession.addOutput(self.videoOutput)
            }
            
            self.captureSession.commitConfiguration()
        }
    }
    
    private func setupInterruptionAndSleepObservers() {
        // 1. Camera interruption by video call apps (Zoom, Google Meet, Teams, FaceTime)
        NotificationCenter.default.addObserver(
            forName: .AVCaptureSessionWasInterrupted,
            object: captureSession,
            queue: .main
        ) { [weak self] notif in
            print("[Glance] Camera interrupted by another app (e.g. Video Call). Pausing privacy blur.")
            self?.noFaceFramesCount = 0
            Task { @MainActor in
                AppModel.shared.isVideoCallActive = true
                AppModel.shared.clearProtection()
            }
        }
        
        NotificationCenter.default.addObserver(
            forName: .AVCaptureSessionInterruptionEnded,
            object: captureSession,
            queue: .main
        ) { notif in
            print("[Glance] Camera interruption ended (Video Call closed). Resuming protection.")
            Task { @MainActor in
                AppModel.shared.isVideoCallActive = false
            }
        }
        
        // 2. System Sleep & Wake Lifecycle
        NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didWakeNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.sessionQueue.async { [weak self] in
                guard let self = self, self.isRunning else { return }
                if !self.captureSession.isRunning {
                    self.captureSession.startRunning()
                    print("[Glance] Camera resumed after system wake.")
                }
            }
        }
    }
    
    // Checks if the user is actively typing or moving the mouse in the last 2.5 seconds
    private func isUserTypingOrUsingMouse() -> Bool {
        if let eventType = CGEventType(rawValue: ~0) {
            let idleSeconds = CGEventSource.secondsSinceLastEventType(.hidSystemState, eventType: eventType)
            return idleSeconds < 2.5
        }
        return false
    }
    
    func startTracking() {
        sessionQueue.async { [weak self] in
            guard let self = self, !self.isRunning else { return }
            
            let status = AVCaptureDevice.authorizationStatus(for: .video)
            if status == .notDetermined {
                AVCaptureDevice.requestAccess(for: .video) { granted in
                    if granted {
                        self.sessionQueue.async {
                            self.captureSession.startRunning()
                            self.isRunning = true
                            Task { @MainActor in
                                AppModel.shared.isTrackingActive = true
                            }
                        }
                    }
                }
            } else if status == .authorized {
                self.captureSession.startRunning()
                self.isRunning = true
                Task { @MainActor in
                    AppModel.shared.isTrackingActive = true
                }
            }
        }
    }
    
    func stopTracking() {
        sessionQueue.async { [weak self] in
            guard let self = self, self.isRunning else { return }
            self.captureSession.stopRunning()
            self.isRunning = false
            Task { @MainActor in
                AppModel.shared.isTrackingActive = false
                AppModel.shared.isFaceDetected = false
                AppModel.shared.clearProtection()
            }
        }
    }
    
    func calibrateCenter() {
        baselineAngle = smoothedAngle + baselineAngle
        smoothedAngle = 0.0
        Task { @MainActor in
            AppModel.shared.processFaceState(angleDegrees: 0.0, isPresent: true)
        }
    }
    
    // MARK: - AVCaptureVideoDataOutputSampleBufferDelegate
    
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        autoreleasepool {
            let currentTime = CACurrentMediaTime()
            guard currentTime - lastProcessTime >= processInterval else { return }
            lastProcessTime = currentTime
            
            guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
            
            do {
                // Orientation .up is the true native orientation on macOS FaceTime HD cameras
                try sequenceHandler.perform([faceRequest], on: pixelBuffer, orientation: .up)
                
                if let observation = faceRequest.results?.first,
                   let rawYaw = observation.yaw?.floatValue {

                    self.noFaceFramesCount = 0

                    // Posture Guard shares this observation (no extra camera
                    // work). Vision y is bottom-up, so flip it: the posture
                    // adapter expects larger centerY = head dropped lower.
                    let bbox = observation.boundingBox
                    let posturePitch = observation.pitch.map { Double($0.floatValue) * (180.0 / .pi) }
                    let postureNow = currentTime
                    Task { @MainActor in
                        AppModel.shared.processPosture(
                            now: postureNow, facePresent: true,
                            faceSize: Double(bbox.width),
                            centerY: 1.0 - Double(bbox.midY),
                            pitch: posturePitch)
                    }
                    
                    // Convert to degrees: positive = looking right, negative = looking left
                    let degrees = -Double(rawYaw) * (180.0 / .pi)
                    
                    // If user is tilting head down to look at keyboard/desk, ignore small yaw jitters
                    if let rawPitch = observation.pitch?.floatValue {
                        let pitchDegrees = Double(rawPitch) * (180.0 / .pi)
                        if pitchDegrees < -15.0 && abs(degrees) < 16.0 {
                            // User is looking down at keyboard/notes in front of them -> Keep clear
                            Task { @MainActor in
                                AppModel.shared.processFaceState(angleDegrees: 0.0, isPresent: true)
                            }
                            return
                        }
                    }
                    
                    let relative = degrees - self.baselineAngle
                    
                    // Exponential moving average for smooth, jitter-free angle changes
                    self.smoothedAngle = (self.smoothedAngle * 0.70) + (relative * 0.30)
                    
                    Task { @MainActor in
                        AppModel.shared.processFaceState(angleDegrees: self.smoothedAngle, isPresent: true)
                    }
                } else {
                    Task { @MainActor in
                        AppModel.shared.processPosture(now: currentTime, facePresent: false)
                    }
                    // If no face was seen, check if user is actively typing or clicking mouse
                    if self.isUserTypingOrUsingMouse() {
                        // User is at desk typing or moving mouse! Do NOT trigger away blur
                        self.noFaceFramesCount = 0
                        Task { @MainActor in
                            AppModel.shared.processFaceState(angleDegrees: 0.0, isPresent: true)
                        }
                        return
                    }
                    
                    self.noFaceFramesCount += 1
                    
                    // Only trigger away protection after ~0.9s (7 frames) of NO face AND NO typing/mouse input
                    if self.noFaceFramesCount == 7 {
                        Task { @MainActor in
                            AppModel.shared.processFaceState(angleDegrees: nil, isPresent: false)
                        }
                    }
                }
            } catch {
                // Drop errors gracefully
            }
        }
    }
}
