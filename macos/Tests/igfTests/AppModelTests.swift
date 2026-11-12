import Testing
@testable import igf

@Test @MainActor func darkCameraFrameClearsProtectionAndMarksCovered() {
    let model = AppModel.shared
    let prevEnabled = model.isEnabled
    let prevCall = model.isVideoCallActive
    let prevPopover = model.isPopoverOpen
    defer {
        model.isVideoCallActive = prevCall
        model.isPopoverOpen = prevPopover
        model.isEnabled = prevEnabled
        model.clearProtection()
        model.isCameraCoveredOrDark = false
    }

    model.isEnabled = true
    model.isVideoCallActive = false
    model.isPopoverOpen = false
    model.shareUntil = nil

    model.processFaceState(angleDegrees: 30.0, isPresent: true)
    #expect(model.isLookingAway)
    #expect(model.activeSide != .none)

    model.handleDarkCameraFrame()
    #expect(model.isCameraCoveredOrDark)
    #expect(!model.isLookingAway)
    #expect(!model.isAwayFromDesk)
    #expect(model.activeSide == .none)
}

@Test @MainActor func shareModeTemporarilySuspendsBlur() {
    let model = AppModel.shared
    let prevEnabled = model.isEnabled
    defer {
        model.shareUntil = nil
        model.isEnabled = prevEnabled
        model.clearProtection()
    }

    model.isEnabled = true
    model.isVideoCallActive = false
    model.isPopoverOpen = false

    model.processFaceState(angleDegrees: nil, isPresent: false)
    #expect(model.activeSide == .full)

    model.startShareMode()
    #expect(model.isSharing)
    #expect(model.activeSide == .none)

    model.processFaceState(angleDegrees: 32.0, isPresent: true)
    #expect(model.activeSide == .none)
}
