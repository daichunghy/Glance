# Contributing to Glance

Thanks for helping. Glance is a small project, so every clear bug report and focused pull request matters.

## Before you start

- **Status check:** macOS is the most complete platform. Windows and Linux are still being verified on real hardware — reports from real machines are the most valuable contribution right now.
- **Privacy is a hard rule.** Any change must keep these guarantees: 100% on-device processing, no frames saved, nothing uploaded, no face recognition, no identity verification. A pull request that breaks one of these will not be merged.
- **Posture Guard** is in active development and is not a medical device — please do not add medical claims, diagnoses, or treatment language.

## Reporting a bug

Open an issue and include:

1. Your OS and version (for example: macOS, Windows, or your Linux distribution).
2. Which Glance build / source folder you ran (`macos/`, `windows/`, or `linux/`).
3. What you expected, what actually happened, and the steps to reproduce it.
4. Whether a meeting app was using the camera, and whether the room was dark or the camera covered — these cases are handled on purpose, so the detail helps.

Do **not** attach webcam images of yourself or anyone else to a public issue.

## Submitting a change

1. Fork the repository and create a branch for one change.
2. Keep the change small and focused. One fix or one feature per pull request.
3. Run from source on your platform before submitting:
   - **macOS:** `./build_app.sh`
   - **Windows:** `pip install -r requirements.txt`, then `python glance_windows.py`
   - **Linux:** `pip install -r requirements.txt`, then run the Linux entry point.
4. If your change touches posture, guard, or screen-cover logic on Windows or Linux, run the existing tests and say so in the pull request (current baseline: Windows 28 passing, Linux 19 passing).
5. Describe in the pull request: what changed, why, and how you tested it — including the camera-busy, camera-covered, and dark-room cases if your change touches detection.

## Style

- Keep it simple. The project motto is **“Simple. yet powerful.”**
- Match the style of the file you are editing (Swift on macOS, Python on Windows / Linux).
- Prefer clear names and short functions over clever code.
- Documentation changes are welcome — clarity in the README is a feature.

## Security and privacy issues

Do not open a public issue for a privacy or security problem. Follow [SECURITY.md](SECURITY.md) instead.
