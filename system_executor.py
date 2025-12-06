"""System executor - controls macOS applications."""

import subprocess
from typing import Optional

# Common app name mappings (what user says → actual app name)
APP_ALIASES = {
    # Browsers
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "browser": "Google Chrome",
    "safari": "Safari",
    "arc": "Arc",
    "arc browser": "Arc",
    "firefox": "Firefox",
    "brave": "Brave Browser",
    # System
    "finder": "Finder",
    "files": "Finder",
    "terminal": "Terminal",
    "iterm": "iTerm",
    "warp": "Warp",
    # Dev
    "code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "cursor": "Cursor",
    # Media
    "spotify": "Spotify",
    "music": "Music",
    "apple music": "Music",
    # Communication
    "slack": "Slack",
    "discord": "Discord",
    "zoom": "zoom.us",
    "teams": "Microsoft Teams",
    "whatsapp": "WhatsApp",
    "whats app": "WhatsApp",
    "what's app": "WhatsApp",
    "telegram": "Telegram",
    "messages": "Messages",
    "imessage": "Messages",
    "facetime": "FaceTime",
    "mail": "Mail",
    # Office
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "notes": "Notes",
    "reminders": "Reminders",
    "calendar": "Calendar",
    # Productivity
    "notion": "Notion",
    "obsidian": "Obsidian",
    "figma": "Figma",
    "photoshop": "Adobe Photoshop",
    "illustrator": "Adobe Illustrator",
    "premiere": "Adobe Premiere Pro",
    # System
    "system preferences": "System Preferences",
    "settings": "System Settings",
    "system settings": "System Settings",
    "activity monitor": "Activity Monitor",
    "app store": "App Store",
    "preview": "Preview",
    "photos": "Photos",
    # Other
    "raycast": "Raycast",
    "1password": "1Password",
}


class SystemExecutor:
    """Executes system-level commands on macOS."""

    def __init__(self):
        print("System executor ready.")

    def execute(self, intent: dict) -> bool:
        """Execute system action based on intent."""
        action = intent.get("action")

        if action == "open_app":
            return self.open_app(intent.get("app_name", ""))
        elif action == "close_app":
            return self.close_app(intent.get("app_name", ""))
        elif action == "switch_app":
            return self.switch_app(intent.get("app_name", ""))
        elif action == "open_url":
            return self.open_url(intent.get("url", ""))
        else:
            print(f"❌ Unknown system action: {action}")
            return False

    def _resolve_app_name(self, name: str) -> str:
        """Resolve user-friendly name to actual app name."""
        name_lower = name.lower().strip()
        return APP_ALIASES.get(name_lower, name)

    def open_app(self, app_name: str) -> bool:
        """Open an application."""
        if not app_name:
            print("❌ No app name provided")
            return False

        resolved_name = self._resolve_app_name(app_name)
        print(f"🚀 Opening {resolved_name}...")

        try:
            result = subprocess.run(
                ["open", "-a", resolved_name],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ {resolved_name} opened!")
                return True
            else:
                # Try with original name if resolved name failed
                if resolved_name != app_name:
                    result = subprocess.run(
                        ["open", "-a", app_name],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"✅ {app_name} opened!")
                        return True

                print(f"❌ Could not open {app_name}: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error opening app: {e}")
            return False

    def close_app(self, app_name: str) -> bool:
        """Close an application using AppleScript."""
        if not app_name:
            print("❌ No app name provided")
            return False

        resolved_name = self._resolve_app_name(app_name)
        print(f"🛑 Closing {resolved_name}...")

        script = f'tell application "{resolved_name}" to quit'

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ {resolved_name} closed!")
                return True
            else:
                print(f"❌ Could not close {resolved_name}: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error closing app: {e}")
            return False

    def switch_app(self, app_name: str) -> bool:
        """Bring an application to the front."""
        if not app_name:
            print("❌ No app name provided")
            return False

        resolved_name = self._resolve_app_name(app_name)
        print(f"🔄 Switching to {resolved_name}...")

        script = f'tell application "{resolved_name}" to activate'

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ Switched to {resolved_name}!")
                return True
            else:
                print(f"❌ Could not switch to {resolved_name}: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error switching app: {e}")
            return False

    def open_url(self, url: str) -> bool:
        """Open a URL in the default browser."""
        if not url:
            print("❌ No URL provided")
            return False

        # Add https:// if no protocol specified
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        print(f"🌐 Opening {url}...")

        try:
            result = subprocess.run(
                ["open", url],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ URL opened!")
                return True
            else:
                print(f"❌ Could not open URL: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error opening URL: {e}")
            return False


if __name__ == "__main__":
    executor = SystemExecutor()

    print("\n=== Testing System Executor ===\n")

    # Test open
    print("Test 1: Open Finder")
    executor.open_app("Finder")

    print("\nTest 2: Open Chrome (alias)")
    executor.execute({"action": "open_app", "app_name": "chrome"})

    print("\nTest 3: Switch to Finder")
    executor.execute({"action": "switch_app", "app_name": "finder"})
