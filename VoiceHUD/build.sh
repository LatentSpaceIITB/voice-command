#!/bin/bash
# Build script for VoiceHUD SwiftUI app

set -e

echo "Building VoiceHUD..."
echo "===================="

cd "$(dirname "$0")"

# Build the Swift package
swift build -c release

# Create app bundle directory
APP_DIR="$HOME/Applications/VoiceHUD.app"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Copy executable
cp .build/release/VoiceHUD "$APP_DIR/Contents/MacOS/"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>VoiceHUD</string>
    <key>CFBundleIdentifier</key>
    <string>com.voicecommand.hud</string>
    <key>CFBundleName</key>
    <string>VoiceHUD</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSBackgroundOnly</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo ""
echo "Build complete!"
echo "App installed to: $APP_DIR"
echo ""
echo "To start VoiceHUD:"
echo "  open $APP_DIR"
echo ""
echo "To add to Login Items (start on boot):"
echo "  1. System Settings → General → Login Items"
echo "  2. Click + under 'Open at Login'"
echo "  3. Select VoiceHUD.app from ~/Applications"
