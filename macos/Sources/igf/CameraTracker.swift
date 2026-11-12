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
    private var hasConfiguredInput: Bool = false
    
    override init() {
        super.init()
        setupSession()
        setupInterruptionAndSleepObservers()
    }
    
    private func setupSession() {
        sessionQueue.async { [weak self] in
            _ = self?.configureSessionLocked()
        }
    }

    private func configureSessionLocked() -> Bool {
        if hasConfiguredInput {
            return true
        }

        captureSession.beginConfiguration()

        // Remove any previous inputs/outputs before reconfiguring
        for input in captureSession.inputs {
            captureSession.removeInput(input)
        }
        for output in captureSession.outputs {
            captureSession.removeOutput(output)
        }

        // Using .low preset drastically minimizes buffer allocations and RAM footprint (~75% reduction)
        if captureSession.canSetSessionPreset(.low) {
            captureSession.sessionPreset = .low
        } else if captureSession.canSetSessionPreset(.vga640x480) {
            captureSession.sessionPreset = .vga640x480
        }

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) ?? AVCaptureDevice.default(for: .video),
              let input = try? AVCaptureDeviceInput(device: device),
              captureSession.canAddInput(input) else {
            hasConfiguredInput = false
            captureSession.commitConfiguration()
            Task { @MainActor in
                AppModel.shared.cameraUnavailableMessage = "No camera found"
                AppModel.shared.isTrackingActive = false
            }
            return false
        }

        captureSession.addInput(input)

        // Limit hardware camera sensor frame rate safely within supported range
        do {
            try device.lockForConfiguration()
            if let range = device.activeFormat.videoSupportedFrameRateRanges.first,
               range.minFrameRate > 0 {
                let targetRate = min(max(15.0, range.minFrameRate), range.maxFrameRate)
                let timescale = CMTimeScale(max(1, Int32((targetRate * 1000).rounded())))
                let duration = CMTime(value: 1000, timescale: timescale)
                device.activeVideoMinFrameDuration = duration
                device.activeVideoMaxFrameDuration = duration
            }
            device.unlockForConfiguration()
        } catch {
            print("[Glance] Camera frame rate config skipped: \(error)")
        }

        videoOutput.alwaysDiscardsLateVideoFrames = true
        videoOutput.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange)
        ]
        videoOutput.setSampleBufferDelegate(self, queue: sessionQueue)

        if captureSession.canAddOutput(videoOutput) {
            captureSession.addOutput(videoOutput)
        }

        captureSession.commitConfiguration()
        hasConfiguredInput = true
        return true
    }
    
    private func setupInterruptionAndSleepObservers() {
        // 1. Camera interruption by video call apps (Zoom, Google Meet, Teams, FaceTime)
        NotificationCenter.default.addObserver(
            forName: .AVCaptureSessionWasInterrupted,
            object: captureSession,
            queue: .main
        ) { [weak self] notif in
            print("[Glance] Camera interrupted by another app (e.g. Video Call). Pausing privacy blur.")
            self?.sessionQueue.async {
                self?.noFaceFramesCount = 0
            }
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

        // 2. Camera hot-plug (external webcams, Studio Display, Continuity Camera)
        NotificationCenter.default.addObserver(
            forName: AVCaptureDevice.wasConnectedNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            guard let self = self else { return }
            self.sessionQueue.async {
                let configured = self.configureSessionLocked()
                guard configured && !self.isRunning else { return }
                Task { @MainActor in
                    if AppModel.shared.isEnabled && AppModel.shared.trackingSource == .camera {
                        self.startTracking()
                    }
                }
            }
        }

        NotificationCenter.default.addObserver(
            forName: AVCaptureDevice.wasDisconnectedNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            guard let self = self else { return }
            self.sessionQueue.async {
                let stillConnected = self.captureSession.inputs
                    .compactMap { ($0 as? AVCaptureDeviceInput)?.device }
                    .contains { $0.isConnected }
                guard !stillConnected else { return }
                if self.captureSession.isRunning {
                    self.captureSession.stopRunning()
                }
                self.isRunning = false
                self.hasConfiguredInput = false
                self.noFaceFramesCount = 0
                if !self.configureSessionLocked() {
                    Task { @MainActor in
                        AppModel.shared.isTrackingActive = false
                        AppModel.shared.isFaceDetected = false
                        AppModel.shared.clearProtection()
                    }
                } else {
                    Task { @MainActor in
                        if AppModel.shared.isEnabled && AppModel.shared.trackingSource == .camera {
                            self.startTracking()
                        }
                    }
                }
            }
        }
        
        // 3. System Sleep & Wake Lifecycle
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

    private func meanLuma(of pixelBuffer: CVPixelBuffer) -> Double? {
        guard CVPixelBufferGetPlaneCount(pixelBuffer) > 0 else { return nil }
        let width = CVPixelBufferGetWidthOfPlane(pixelBuffer, 0)
        let height = CVPixelBufferGetHeightOfPlane(pixelBuffer, 0)
        guard width > 0, height > 0 else { return nil }
        CVPixelBufferLockBaseAddress(pixelBuffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(pixelBuffer, .readOnly) }
        guard let baseAddress = CVPixelBufferGetBaseAddressOfPlane(pixelBuffer, 0) else { return nil }
        let bytesPerRow = CVPixelBufferGetBytesPerRowOfPlane(pixelBuffer, 0)
        let buffer = baseAddress.assumingMemoryBound(to: UInt8.self)

        let stepX = max(1, width / 16)
        let stepY = max(1, height / 12)
        var total = 0
        var count = 0
        var y = 0
        while y < height {
            let rowOffset = y * bytesPerRow
            var x = 0
            while x < width {
                total += Int(buffer[rowOffset + x])
                count += 1
                x += stepX
            }
            y += stepY
        }
        return count > 0 ? Double(total) / Double(count) : nil
    }
    
    func startTracking() {
        sessionQueue.async { [weak self] in
            guard let self = self, !self.isRunning else { return }
            guard self.configureSessionLocked() else {
                Task { @MainActor in
                    AppModel.shared.isTrackingActive = false
                    AppModel.shared.cameraUnavailableMessage = "No camera found"
                }
                return
            }

            let status = AVCaptureDevice.authorizationStatus(for: .video)
            if status == .notDetermined {
                AVCaptureDevice.requestAccess(for: .video) { granted in
                    if granted {
                        Task { @MainActor in
                            guard AppModel.shared.isEnabled, AppModel.shared.trackingSource == .camera else { return }
                            self.sessionQueue.async {
                                guard !self.isRunning, self.configureSessionLocked() else { return }
                                self.captureSession.startRunning()
                                self.isRunning = true
                                Task { @MainActor in
                                    AppModel.shared.cameraPermissionDenied = false
                                    AppModel.shared.cameraUnavailableMessage = nil
                                    AppModel.shared.isTrackingActive = true
                                }
                            }
                        }
                    } else {
                        Task { @MainActor in
                            AppModel.shared.cameraPermissionDenied = true
                            AppModel.shared.cameraUnavailableMessage = "Camera access denied"
                            AppModel.shared.isTrackingActive = false
                        }
                    }
                }
            } else if status == .authorized {
                self.captureSession.startRunning()
                self.isRunning = true
                Task { @MainActor in
                    AppModel.shared.cameraPermissionDenied = false
                    AppModel.shared.cameraUnavailableMessage = nil
                    AppModel.shared.isTrackingActive = true
                }
            } else {
                Task { @MainActor in
                    AppModel.shared.cameraPermissionDenied = true
                    AppModel.shared.cameraUnavailableMessage = "Camera access denied"
                    AppModel.shared.isTrackingActive = false
                }
            }
        }
    }
    
    func stopTracking() {
        sessionQueue.async { [weak self] in
            guard let self = self, self.isRunning else { return }
            self.captureSession.stopRunning()
            self.isRunning = false
            self.noFaceFramesCount = 0
            Task { @MainActor in
                AppModel.shared.isTrackingActive = false
                AppModel.shared.isFaceDetected = false
                AppModel.shared.isCameraCoveredOrDark = false
                AppModel.shared.clearProtection()
            }
        }
    }
    
    func calibrateCenter() {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            self.baselineAngle = self.smoothedAngle + self.baselineAngle
            self.smoothedAngle = 0.0
            Task { @MainActor in
                AppModel.shared.processFaceState(angleDegrees: 0.0, isPresent: true)
            }
        }
    }
    
    // MARK: - AVCaptureVideoDataOutputSampleBufferDelegate
    
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        autoreleasepool {
            let currentTime = CACurrentMediaTime()
            guard currentTime - lastProcessTime >= processInterval else { return }
            lastProcessTime = currentTime
            
            guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }

            if let luma = meanLuma(of: pixelBuffer), luma < 15.0 {
                self.noFaceFramesCount = 0
                Task { @MainActor in
                    AppModel.shared.handleDarkCameraFrame()
                }
                return
            }
            
            do {
                // Orientation .up is the true native orientation on macOS FaceTime HD cameras
                try sequenceHandler.perform([faceRequest], on: pixelBuffer, orientation: .up)
                
                if let observation = faceRequest.results?.first {
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

                    // Convert to degrees: positive = looking right, negative = looking left.
                    // If Vision omits yaw (Intel Macs or extreme angles), fall back to horizontal bbox position
                    // so a visible face never falsely triggers "Desk Empty".
                    let degrees: Double
                    if let rawYaw = observation.yaw?.floatValue {
                        degrees = -Double(rawYaw) * (180.0 / .pi)
                    } else {
                        degrees = -(Double(bbox.midX) - 0.5) * 70.0
                    }
                    
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
