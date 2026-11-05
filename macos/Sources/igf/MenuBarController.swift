import AppKit
import SwiftUI
import Combine

@MainActor
final class MenuBarController: NSObject, NSPopoverDelegate {
    static let shared = MenuBarController()
    
    private var statusItem: NSStatusItem!
    private var popover: NSPopover!
    private var cancellables = Set<AnyCancellable>()
    
    override private init() {
        super.init()
        setupStatusItem()
        setupPopover()
        setupObservers()
    }
    
    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusItem.button {
            let image = NSImage(systemSymbolName: "shield.lefthalf.filled", accessibilityDescription: "Glance")
            image?.isTemplate = true
            button.image = image
            button.target = self
            button.action = #selector(togglePopover)
        }
    }
    
    private func setupPopover() {
        popover = NSPopover()
        popover.contentSize = NSSize(width: 270, height: 320)
        popover.behavior = .transient
        popover.delegate = self
        popover.contentViewController = NSHostingController(rootView: SettingsPopoverView())
    }
    
    private func setupObservers() {
        Publishers.CombineLatest3(AppModel.shared.$isLookingAway, AppModel.shared.$isEnabled, AppModel.shared.$isVideoCallActive)
            .receive(on: RunLoop.main)
            .sink { [weak self] isLookingAway, isEnabled, isVideoCall in
                guard let button = self?.statusItem.button else { return }
                
                let iconName: String
                if !isEnabled {
                    iconName = "shield.slash"
                } else if isVideoCall {
                    iconName = "video.slash.fill"
                } else if isLookingAway {
                    iconName = "shield.fill"
                } else {
                    iconName = "shield.lefthalf.filled"
                }
                
                let image = NSImage(systemSymbolName: iconName, accessibilityDescription: "Glance")
                image?.isTemplate = true
                button.image = image
            }
            .store(in: &cancellables)
    }
    
    @objc private func togglePopover() {
        guard let button = statusItem.button else { return }
        
        if popover.isShown {
            popover.performClose(nil)
            AppModel.shared.isPopoverOpen = false
        } else {
            AppModel.shared.isPopoverOpen = true
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            popover.contentViewController?.view.window?.makeKey()
        }
    }
    
    // MARK: - NSPopoverDelegate
    
    func popoverDidClose(_ notification: Notification) {
        AppModel.shared.isPopoverOpen = false
    }
}
