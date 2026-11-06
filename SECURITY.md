# Security & Privacy — Glance

Glance is a privacy app, so its security model starts with a simple promise:

- Presence detection runs **100% on-device**.
- **No webcam frames are saved** to disk.
- **Nothing is uploaded** — there is no Glance server receiving images.
- There is **no face recognition and no identity verification**. Glance checks presence, not identity.
- Turning Glance **off truly turns the camera off**.

If you find anything that breaks — or looks like it could break — one of those promises, please treat it as a security issue.

## Reporting a vulnerability

**Please do not open a public issue, and do not post exploit details, screenshots of real people, or webcam captures in public.**

Instead:

1. Use GitHub's **private vulnerability reporting** for this repository, if it is enabled (repository page → **Security** → **Report a vulnerability**).
2. If private reporting is not available, open a minimal public issue that says only that you have a privacy/security report and would like a private channel — with **no technical details** — and wait for the maintainer to respond before sharing more.

Please include, in the private report:

- Affected platform (`macos/`, `windows/`, or `linux/`) and OS version.
- A clear description of the issue and its privacy/security impact.
- Steps to reproduce, using your own device and your own test setup only.
- Any suggested fix, if you have one.

## What counts as in scope

- Any code path that saves, transmits, or exposes webcam frames or derived face data.
- Camera staying on after Glance is turned off or quit.
- The screen cover failing open (screen left visible) in a case Glance claims to handle.
- Posture Guard data (calibration profiles) being shared or stored outside the user's own machine.
- Dependency or build-script issues that could compromise a user building from source.

## What is out of scope

- Another person physically looking at an uncovered screen before Glance reacts, or after the user disables Glance or enables “Show screen for 2 minutes” share mode.
- Issues in the operating system, webcam drivers, or meeting apps themselves.
- Posture accuracy disagreements — Posture Guard is a reminder tool, **not a medical device**.

## Response

This is a small, maintainer-run project, so there is no formal SLA. Genuine privacy and security reports are the highest priority and will be acknowledged as soon as reasonably possible. Please give the maintainer a reasonable chance to fix an issue before disclosing it publicly.
