import AppKit
import QuartzCore
import Combine

final class ScreenOverlayWindow: NSWindow {
    private let visualEffectView: NSVisualEffectView
    private let maskLayer = CAGradientLayer()
    
    init(screen: NSScreen) {
        // Essential: View bounds must always be (0, 0, width, height) relative to its window
        let bounds = NSRect(origin: .zero, size: screen.frame.size)
        visualEffectView = NSVisualEffectView(frame: bounds)
        visualEffectView.material = .fullScreenUI
        visualEffectView.blendingMode = .behindWindow
        visualEffectView.state = .active
        visualEffectView.wantsLayer = true
        visualEffectView.autoresizingMask = [.width, .height]
        
        super.init(
            contentRect: screen.frame,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        
        // Window level overlayWindow ensures overlay covers apps while letting context menus and popovers operate
        self.level = NSWindow.Level(Int(CGWindowLevelForKey(.overlayWindow)))
        self.isOpaque = false
        self.backgroundColor = .clear
        self.ignoresMouseEvents = true
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary, .ignoresCycle]
        self.alphaValue = 0.0
        
        self.contentView = visualEffectView
        self.orderFront(nil)
    }
    
    func updateProtection(side: ActiveProtectionSide, intensity: Double) {
        guard let layer = visualEffectView.layer else { return }
        
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        maskLayer.frame = layer.bounds
        CATransaction.commit()
        
        switch side {
        case .none:
            NSAnimationContext.runAnimationGroup { ctx in
                ctx.duration = 0.18
                ctx.timingFunction = CAMediaTimingFunction(name: .easeOut)
                self.animator().alphaValue = 0.0
            }
            return
            
        case .full:
            layer.mask = nil
            
        case .left:
            // Blur left side (opposite of looking right)
            maskLayer.startPoint = CGPoint(x: 0.0, y: 0.5)
            maskLayer.endPoint = CGPoint(x: 0.70, y: 0.5)
            maskLayer.colors = [
                NSColor.black.cgColor,
                NSColor.black.withAlphaComponent(0.6).cgColor,
                NSColor.clear.cgColor
            ]
            maskLayer.locations = [0.0, 0.45, 1.0]
            layer.mask = maskLayer
            
        case .right:
            // Blur right side (opposite of looking left)
            maskLayer.startPoint = CGPoint(x: 0.30, y: 0.5)
            maskLayer.endPoint = CGPoint(x: 1.0, y: 0.5)
            maskLayer.colors = [
                NSColor.clear.cgColor,
                NSColor.black.withAlphaComponent(0.6).cgColor,
                NSColor.black.cgColor
            ]
            maskLayer.locations = [0.0, 0.55, 1.0]
            layer.mask = maskLayer
        }
        
        NSAnimationContext.runAnimationGroup { ctx in
            ctx.duration = 0.20
            ctx.timingFunction = CAMediaTimingFunction(name: .easeOut)
            self.animator().alphaValue = CGFloat(intensity)
        }
    }
}

@MainActor
final class BlurOverlayController {
    static let shared = BlurOverlayController()
    
    private var windows: [ScreenOverlayWindow] = []
    private var cancellables = Set<AnyCancellable>()
    
    private init() {
        setupWindows()
        setupObservers()
    }
    
    func setupWindows() {
        windows.forEach { $0.close() }
        windows.removeAll()
        
        for screen in NSScreen.screens {
            let window = ScreenOverlayWindow(screen: screen)
            windows.append(window)
        }

        let side = AppModel.shared.activeSide
        let intensity = AppModel.shared.blurIntensity
        if side != .none {
            windows.forEach { $0.updateProtection(side: side, intensity: intensity) }
        }
    }
    
    private func setupObservers() {
        // Monitor screen configuration changes (e.g. plugging/unplugging external display)
        NotificationCenter.default.publisher(for: NSApplication.didChangeScreenParametersNotification)
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in
                MainActor.assumeIsolated {
                    self?.setupWindows()
                }
            }
            .store(in: &cancellables)
            
        // Monitor app model active protection side with deduplication
        Publishers.CombineLatest(AppModel.shared.$activeSide, AppModel.shared.$blurIntensity)
            .removeDuplicates { prev, curr in
                prev.0 == curr.0 && prev.1 == curr.1
            }
            .receive(on: RunLoop.main)
            .sink { [weak self] side, intensity in
                MainActor.assumeIsolated {
                    self?.windows.forEach { $0.updateProtection(side: side, intensity: intensity) }
                }
            }
            .store(in: &cancellables)
    }
}
