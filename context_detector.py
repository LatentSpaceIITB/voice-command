"""Context detector - detects the currently active application on macOS."""

import subprocess
from typing import Optional


class ContextDetector:
    """Detects the currently active/frontmost application on macOS."""

    def __init__(self):
        pass

    def get_active_app(self) -> str:
        """Get the name of the currently active (frontmost) application."""
        script = 'tell application "System Events" to get name of first process whose frontmost is true'

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "Unknown"

        except Exception as e:
            print(f"Error detecting active app: {e}")
            return "Unknown"

    def get_active_window_title(self) -> Optional[str]:
        """Get the title of the active window (if available)."""
        script = '''
        tell application "System Events"
            set frontApp to first process whose frontmost is true
            set appName to name of frontApp
            try
                tell frontApp
                    set windowTitle to name of front window
                end tell
                return windowTitle
            on error
                return ""
            end try
        end tell
        '''

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None

        except Exception:
            return None

    def get_context(self) -> dict:
        """Get full context including app name and window title."""
        app_name = self.get_active_app()
        window_title = self.get_active_window_title()

        return {
            "app_name": app_name,
            "window_title": window_title,
            "is_browser": app_name in ["Google Chrome", "Safari", "Firefox", "Arc", "Brave Browser"],
            "is_editor": app_name in ["Visual Studio Code", "Sublime Text", "Atom", "TextEdit", "Notes"],
            "is_notion": app_name == "Notion",
            "is_terminal": app_name in ["Terminal", "iTerm2", "iTerm"],
        }

    def is_app_active(self, app_name: str) -> bool:
        """Check if a specific app is currently active."""
        current = self.get_active_app().lower()
        return app_name.lower() in current


if __name__ == "__main__":
    detector = ContextDetector()

    print("=== Context Detector Test ===\n")

    print(f"Active app: {detector.get_active_app()}")
    print(f"Window title: {detector.get_active_window_title()}")
    print()

    context = detector.get_context()
    print("Full context:")
    for key, value in context.items():
        print(f"  {key}: {value}")
