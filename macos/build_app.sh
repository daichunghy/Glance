#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "===> Building igf (Release)..."
swift build -c release

APP_NAME="Glance"
APP_BUNDLE="$DIR/$APP_NAME.app"
BIN_SRC="$DIR/.build/release/igf"

echo "===> Creating $APP_NAME.app bundle..."
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Copy binary
cp "$BIN_SRC" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# Copy Icon
if [ -f "$DIR/AppIcon.icns" ]; then
    cp "$DIR/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"
fi

# Create Info.plist
cat << 'EOF' > "$APP_BUNDLE/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Glance</string>
    <key>CFBundleIdentifier</key>
    <string>com.glance.app</string>
    <key>CFBundleName</key>
    <string>Glance</string>
    <key>CFBundleDisplayName</key>
    <string>Glance</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.1</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>Glance uses the built-in camera for real-time on-device head tracking to protect your screen privacy when you look away, and — only if you enable Posture Guard — to remind you about turtle neck and slouching. Video is processed on this Mac and never saved or sent.</string>
    <key>NSMotionUsageDescription</key>
    <string>Glance uses AirPods headphone motion to detect when you turn your head away to automatically protect your screen privacy.</string>
</dict>
</plist>
EOF

echo "===> Ad-hoc Code Signing..."
codesign -s - --force --deep "$APP_BUNDLE"

echo "===> Done! App created at: $APP_BUNDLE"
