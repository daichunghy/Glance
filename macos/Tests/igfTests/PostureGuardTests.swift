import Testing
@testable import igf

// Mirror of windows/tests/test_posture.py — same cases, same numbers.

private let baseSize = 0.30
private let baseY = 0.40
private let basePitch = 0.0

private func calibratedGuard(hold: Double = 10, release: Double = 3, cooldown: Double = 60) -> PostureGuard {
    let guard_ = PostureGuard(holdSeconds: hold, cooldownSeconds: cooldown, releaseSeconds: release)
    _ = guard_.update(now: 0, facePresent: true, faceSize: baseSize, centerY: baseY, pitch: basePitch)
    #expect(guard_.calibrate())
    return guard_
}

private func feed(_ g: PostureGuard, now: Double, size: Double = baseSize, y: Double = baseY, pitch: Double? = basePitch) -> PostureResult {
    var result = g.update(now: now, facePresent: true, faceSize: size, centerY: y, pitch: pitch)
    for _ in 0..<30 {
        result = g.update(now: now, facePresent: true, faceSize: size, centerY: y, pitch: pitch)
    }
    return result
}

@Test func postureUncalibratedNeverWarns() {
    let g = PostureGuard(holdSeconds: 1)
    _ = feed(g, now: 0, size: baseSize * 1.5, y: baseY + 0.2)
    let result = feed(g, now: 5, size: baseSize * 1.5, y: baseY + 0.2)
    #expect(result.status == .uncalibrated)
    #expect(!result.warning)
}

@Test func postureCalibrateWithoutFaceFails() {
    let g = PostureGuard()
    #expect(!g.calibrate())
    #expect(!g.isCalibrated)
}

@Test func postureGoodNeverWarns() {
    let g = calibratedGuard(hold: 1)
    let result = feed(g, now: 10)
    #expect(result.status == .good)
    #expect(!result.warning)
}

@Test func postureTurtleNeckWarnsOnlyAfterHold() {
    let g = calibratedGuard(hold: 10)
    _ = feed(g, now: 0, size: baseSize * 1.35, y: baseY + 0.05)
    var result = g.update(now: 9.9, facePresent: true, faceSize: baseSize * 1.35, centerY: baseY + 0.05, pitch: basePitch)
    #expect(!result.warning)
    result = g.update(now: 10, facePresent: true, faceSize: baseSize * 1.35, centerY: baseY + 0.05, pitch: basePitch)
    #expect(result.warning)
    #expect(result.justTriggered)
    #expect(result.kinds.contains(.turtleNeck))
}

@Test func postureHunchByDropAloneWithoutPitch() {
    let g = PostureGuard(holdSeconds: 5)
    _ = g.update(now: 0, facePresent: true, faceSize: baseSize, centerY: baseY, pitch: nil)
    #expect(g.calibrate())
    _ = feed(g, now: 0, size: baseSize, y: baseY + 0.15, pitch: nil)
    let result = g.update(now: 5, facePresent: true, faceSize: baseSize, centerY: baseY + 0.15, pitch: nil)
    #expect(result.warning)
    #expect(result.kinds.contains(.hunch))
}

@Test func postureKeyboardLookDownIsNotBad() {
    let g = calibratedGuard(hold: 1)
    let result = feed(g, now: 10, size: baseSize, y: baseY + 0.02, pitch: basePitch - 25)
    #expect(!result.warning)
    #expect(result.kinds.isEmpty)
}

@Test func postureNoFaceResetsBadTimer() {
    let g = calibratedGuard(hold: 5)
    _ = feed(g, now: 0, size: baseSize * 1.4, y: baseY + 0.06)
    _ = g.update(now: 4, facePresent: false)
    _ = feed(g, now: 4, size: baseSize * 1.4, y: baseY + 0.06)
    let result = g.update(now: 8, facePresent: true, faceSize: baseSize * 1.4, centerY: baseY + 0.06, pitch: basePitch)
    #expect(!result.warning)
}

@Test func postureWarningClearsAndCooldownBlocksRetrigger() {
    let g = calibratedGuard(hold: 1, release: 1, cooldown: 60)
    _ = feed(g, now: 0, size: baseSize * 1.4, y: baseY + 0.06)
    #expect(g.update(now: 1, facePresent: true, faceSize: baseSize * 1.4, centerY: baseY + 0.06, pitch: basePitch).warning)
    _ = feed(g, now: 2)
    _ = g.update(now: 3, facePresent: true, faceSize: baseSize, centerY: baseY, pitch: basePitch)
    _ = feed(g, now: 4, size: baseSize * 1.4, y: baseY + 0.06)
    #expect(!g.update(now: 10, facePresent: true, faceSize: baseSize * 1.4, centerY: baseY + 0.06, pitch: basePitch).warning)
    let again = g.update(now: 62, facePresent: true, faceSize: baseSize * 1.4, centerY: baseY + 0.06, pitch: basePitch)
    #expect(again.warning)
    #expect(again.justTriggered)
}

@Test func postureSnoozeSilencesThenRecovers() {
    let g = calibratedGuard(hold: 1)
    g.snooze(now: 0, seconds: 1800)
    let muted = g.update(now: 10, facePresent: true, faceSize: baseSize * 1.4, centerY: baseY + 0.06, pitch: basePitch)
    #expect(muted.status == .snoozed)
    #expect(!muted.warning)
    _ = feed(g, now: 1801, size: baseSize * 1.4, y: baseY + 0.06)
    #expect(g.update(now: 1802, facePresent: true, faceSize: baseSize * 1.4, centerY: baseY + 0.06, pitch: basePitch).warning)
}

@Test func postureDismissAsNotBadLoosensThresholds() {
    let g = calibratedGuard(hold: 1)
    _ = feed(g, now: 0, size: baseSize * 1.4, y: baseY + 0.06)
    #expect(g.update(now: 1, facePresent: true, faceSize: baseSize * 1.4, centerY: baseY + 0.06, pitch: basePitch).warning)
    let factor = g.dismissAsNotBad(now: 2)
    #expect(abs(factor - 1.10) < 0.0001)
    _ = feed(g, now: 70, size: baseSize * 1.30, y: baseY)
    #expect(!g.update(now: 71, facePresent: true, faceSize: baseSize * 1.30, centerY: baseY, pitch: basePitch).warning)
}
