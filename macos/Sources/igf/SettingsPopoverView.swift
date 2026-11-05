import SwiftUI

struct SettingRow<Content: View>: View {
    let icon: String
    let iconColor: Color
    let title: String
    @ViewBuilder let control: () -> Content
    
    var body: some View {
        HStack(spacing: 8) {
            ZStack {
                RoundedRectangle(cornerRadius: 5, style: .continuous)
                    .fill(iconColor)
                    .frame(width: 20, height: 20)
                Image(systemName: icon)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white)
            }
            
            Text(title)
                .font(.system(size: 12, weight: .regular))
                .foregroundColor(.primary)
            
            Spacer()
            
            control()
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 7)
    }
}

struct SettingsPopoverView: View {
    @ObservedObject var model = AppModel.shared
    
    var body: some View {
        VStack(spacing: 11) {
            // Header: App icon badge + Title + Master Switch
            HStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 7, style: .continuous)
                        .fill(model.isLookingAway ? Color.orange : (model.isEnabled ? Color.blue : Color.secondary.opacity(0.3)))
                        .frame(width: 28, height: 28)
                    Image(systemName: model.isLookingAway ? "shield.fill" : "shield.lefthalf.filled")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.white)
                }
                
                VStack(alignment: .leading, spacing: 1) {
                    Text("Glance")
                        .font(.system(size: 13, weight: .bold))
                    Text(headerSubtitle)
                        .font(.system(size: 10.5))
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Toggle("", isOn: $model.isEnabled)
                    .toggleStyle(.switch)
                    .labelsHidden()
            }
            .padding(.horizontal, 2)
            
            // Section 1: Live Status & Alignment Card
            VStack(spacing: 8) {
                HStack {
                    HStack(spacing: 5) {
                        Circle()
                            .fill(statusIndicatorColor)
                            .frame(width: 6, height: 6)
                        Text(statusTitle)
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(.primary)
                    }
                    
                    Spacer()
                    
                    Text(statusDetailText)
                        .font(.system(size: 11, weight: .medium, design: .monospaced))
                        .foregroundColor(model.isLookingAway ? .orange : .secondary)
                }
                
                // Sleek Level Gauge
                GeometryReader { geo in
                    let width = geo.size.width
                    let clamped = min(max(model.currentYawDegrees, -45), 45)
                    let pointerX = ((clamped + 45.0) / 90.0) * width
                    let threshold = model.sensitivity.thresholdDegrees
                    let leftX = ((-threshold + 45.0) / 90.0) * width
                    let rightX = ((threshold + 45.0) / 90.0) * width
                    
                    ZStack(alignment: .leading) {
                        // Track
                        Capsule()
                            .fill(Color(NSColor.separatorColor).opacity(0.25))
                            .frame(height: 5)
                        
                        // Safe zone
                        Capsule()
                            .fill(Color.green.opacity(0.35))
                            .frame(width: max(0, rightX - leftX), height: 5)
                            .offset(x: leftX)
                        
                        // Center reference notch
                        Rectangle()
                            .fill(Color.secondary.opacity(0.5))
                            .frame(width: 1.5, height: 9)
                            .offset(x: width / 2 - 0.75)
                        
                        // Current angle indicator dot
                        Circle()
                            .fill(model.isLookingAway ? Color.orange : Color.blue)
                            .frame(width: 11, height: 11)
                            .shadow(color: (model.isLookingAway ? Color.orange : Color.blue).opacity(0.35), radius: 2, y: 1)
                            .offset(x: pointerX - 5.5)
                    }
                }
                .frame(height: 11)
                
                // Calibrate Button
                Button(action: {
                    if model.trackingSource == .camera {
                        CameraTracker.shared.calibrateCenter()
                    } else {
                        MotionTracker.shared.calibrateCenter()
                    }
                }) {
                    HStack(spacing: 5) {
                        Image(systemName: "scope")
                            .font(.system(size: 10, weight: .semibold))
                        Text("Calibrate Center")
                            .font(.system(size: 11, weight: .medium))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 3)
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
            .padding(9)
            .background(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .fill(Color(NSColor.controlBackgroundColor).opacity(0.6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 10, style: .continuous)
                            .stroke(Color(NSColor.separatorColor).opacity(0.18), lineWidth: 0.5)
                    )
            )
            
            // Section 2: Inset Grouped Settings Card
            VStack(spacing: 0) {
                // Row 1: Tracking Source
                SettingRow(
                    icon: "camera.fill",
                    iconColor: .purple,
                    title: "Source"
                ) {
                    Picker("", selection: $model.trackingSource) {
                        Text("Camera").tag(TrackingSource.camera)
                        Text("AirPods").tag(TrackingSource.airpods)
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 130)
                }
                
                Divider()
                    .padding(.leading, 36)
                
                // Row 2: Blur Mode
                SettingRow(
                    icon: "rectangle.split.2x1.fill",
                    iconColor: .blue,
                    title: "Blur Style"
                ) {
                    Picker("", selection: $model.blurMode) {
                        ForEach(BlurMode.allCases) { mode in
                            Text(mode.rawValue).tag(mode)
                        }
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 130)
                }
                
                Divider()
                    .padding(.leading, 36)
                
                // Row 3: Sensitivity
                SettingRow(
                    icon: "gauge.with.needle.fill",
                    iconColor: .orange,
                    title: "Sensitivity"
                ) {
                    Picker("", selection: $model.sensitivity) {
                        ForEach(Sensitivity.allCases) { s in
                            Text(s.rawValue).tag(s)
                        }
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 130)
                }
                
                Divider()
                    .padding(.leading, 36)
                
                // Row 4: Away Protection Toggle
                SettingRow(
                    icon: "person.fill.badge.shield.checkmark",
                    iconColor: .green,
                    title: "Away Blur"
                ) {
                    Toggle("", isOn: $model.autoBlurWhenAway)
                        .toggleStyle(.switch)
                        .controlSize(.mini)
                        .labelsHidden()
                }
            }
            .background(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .fill(Color(NSColor.controlBackgroundColor).opacity(0.6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 10, style: .continuous)
                            .stroke(Color(NSColor.separatorColor).opacity(0.18), lineWidth: 0.5)
                    )
            )
            
            // Footer: Hotkey hint & Quit button
            HStack {
                Text("⌥⇧P to toggle")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(.secondary.opacity(0.8))
                
                Spacer()
                
                Button(action: {
                    NSApplication.shared.terminate(nil)
                }) {
                    Text("Quit Glance")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
            .padding(.top, 1)
            .padding(.horizontal, 2)
        }
        .padding(13)
        .frame(width: 270)
    }
    
    // MARK: - Computed Status Helpers
    
    private var headerSubtitle: String {
        if !model.isEnabled { return "Protection Paused" }
        if model.isVideoCallActive { return "Paused for Video Call" }
        if model.isAwayFromDesk { return "Screen Protected (Away)" }
        if model.isLookingAway { return "Screen Protected" }
        return "Glance Protection Active"
    }
    
    private var statusIndicatorColor: Color {
        if !model.isEnabled { return .secondary }
        if model.isVideoCallActive { return .yellow }
        if model.isAwayFromDesk || model.isLookingAway { return .orange }
        if model.trackingSource == .camera {
            return model.isFaceDetected ? .green : .orange
        } else {
            return model.isAirPodsConnected ? .green : .orange
        }
    }
    
    private var statusTitle: String {
        if !model.isEnabled { return "Disabled" }
        if model.isVideoCallActive { return "In Video Call" }
        if model.isAwayFromDesk { return "Desk Empty" }
        if model.isLookingAway {
            return model.activeSide == .full ? "Full Blur" : (model.activeSide == .left ? "Left Blur" : "Right Blur")
        }
        if model.trackingSource == .camera {
            return model.isFaceDetected ? "Face Tracked" : "Searching..."
        } else {
            return model.isAirPodsConnected ? "AirPods Active" : "No AirPods"
        }
    }
    
    private var statusDetailText: String {
        if !model.isEnabled { return "--" }
        if model.isVideoCallActive { return "Paused" }
        if model.isAwayFromDesk { return "Away" }
        let deg = model.currentYawDegrees
        if abs(deg) < 4 {
            return "Center"
        } else if deg > 0 {
            return String(format: "+%.0f° R", deg)
        } else {
            return String(format: "%.0f° L", deg)
        }
    }
}
