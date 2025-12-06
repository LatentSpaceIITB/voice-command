"""Context Capture - Layer 1: "The Now"

Captures the current context (selected text, clipboard, window content, or screenshot)
following a priority hierarchy for optimal speed and privacy.
"""

import subprocess
import pyperclip
import time
from typing import Optional, Tuple
from dataclasses import dataclass
from context_detector import ContextDetector


@dataclass
class CapturedContext:
    """Captured context with metadata."""
    content: str  # Text content or base64 image
    source: str  # "selection", "clipboard", "window", "screenshot"
    app_name: str  # Active application
    window_title: str  # Active window title
    timestamp: float
    is_image: bool = False


class ContextCapture:
    """Captures current context following the grab hierarchy.

    Priority:
    1. Selected Text (via AppleScript/Accessibility)
    2. Clipboard (recent copy)
    3. Active Window Content (via Accessibility API)
    4. Visual Screenshot (last resort, requires vision model)
    """

    # Privacy-sensitive apps that should block context capture
    SENSITIVE_APPS = {
        "1Password",
        "Bitwarden",
        "KeyChain Access",
        "Keychain Access",
        "password",
        "bank",
        "banking",
    }

    # Apps that don't support text extraction well
    SCREENSHOT_PREFERRED_APPS = {
        "Preview",
        "Photos",
        "Figma",
        "Sketch",
    }

    def __init__(self):
        """Initialize context capture."""
        self.context_detector = ContextDetector()
        self.last_clipboard_time = 0
        self.last_clipboard_content = ""
        print("Context capture ready.")

    def capture(self, force_screenshot: bool = False) -> Optional[CapturedContext]:
        """Capture current context following the grab hierarchy.

        Args:
            force_screenshot: If True, skip text extraction and go straight to screenshot

        Returns:
            CapturedContext or None if capture failed or was blocked
        """
        # Get active app context
        context = self.context_detector.get_context()
        app_name = context.get("app_name", "Unknown")
        window_title = context.get("window_title", "")

        # Privacy check: block sensitive apps
        if self._is_sensitive(app_name, window_title):
            print(f"🔒 Context capture blocked for sensitive app: {app_name}")
            return None

        timestamp = time.time()

        # If screenshot is forced or app prefers screenshots, skip text extraction
        if force_screenshot or app_name in self.SCREENSHOT_PREFERRED_APPS:
            print("📸 Forcing screenshot capture...")
            return self._capture_screenshot(app_name, window_title, timestamp)

        # Priority 1: Selected Text
        selected = self._get_selected_text()
        if selected:
            print(f"✂️  Captured selected text ({len(selected)} chars)")
            return CapturedContext(
                content=selected,
                source="selection",
                app_name=app_name,
                window_title=window_title,
                timestamp=timestamp,
            )

        # Priority 2: Clipboard (if recent)
        clipboard = self._get_recent_clipboard()
        if clipboard:
            print(f"📋 Captured clipboard ({len(clipboard)} chars)")
            return CapturedContext(
                content=clipboard,
                source="clipboard",
                app_name=app_name,
                window_title=window_title,
                timestamp=timestamp,
            )

        # Priority 3: Active Window Content
        window_content = self._get_window_content()
        if window_content:
            print(f"🪟 Captured window content ({len(window_content)} chars)")
            return CapturedContext(
                content=window_content,
                source="window",
                app_name=app_name,
                window_title=window_title,
                timestamp=timestamp,
            )

        # Priority 4: Screenshot (fallback)
        print("📸 Falling back to screenshot...")
        return self._capture_screenshot(app_name, window_title, timestamp)

    def _is_sensitive(self, app_name: str, window_title: str) -> bool:
        """Check if app/window is privacy-sensitive."""
        app_lower = app_name.lower()
        title_lower = window_title.lower()

        for sensitive in self.SENSITIVE_APPS:
            if sensitive.lower() in app_lower or sensitive.lower() in title_lower:
                return True

        return False

    def _get_selected_text(self) -> Optional[str]:
        """Get currently selected text via AppleScript.

        Strategy: Simulate Cmd+C to copy selection, then restore original clipboard.
        """
        try:
            # Save original clipboard
            original_clipboard = pyperclip.paste()

            # Clear clipboard
            pyperclip.copy("")

            # Simulate Cmd+C to copy selection
            script = '''
            tell application "System Events"
                keystroke "c" using command down
            end tell
            '''
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=1
            )

            # Small delay for clipboard update
            time.sleep(0.05)

            # Get new clipboard content
            selected = pyperclip.paste()

            # Restore original clipboard
            pyperclip.copy(original_clipboard)

            # If clipboard changed, we captured a selection
            if selected and selected != original_clipboard:
                return selected.strip()

            return None

        except Exception as e:
            print(f"Failed to get selected text: {e}")
            return None

    def _get_recent_clipboard(self, max_age_seconds: float = 5.0) -> Optional[str]:
        """Get clipboard content if it was copied recently.

        Args:
            max_age_seconds: Only return clipboard if copied within this time
        """
        try:
            clipboard = pyperclip.paste()

            # Check if clipboard has changed recently
            if clipboard != self.last_clipboard_content:
                self.last_clipboard_content = clipboard
                self.last_clipboard_time = time.time()

            # Only return if clipboard is recent
            age = time.time() - self.last_clipboard_time
            if age <= max_age_seconds and clipboard:
                return clipboard.strip()

            return None

        except Exception as e:
            print(f"Failed to get clipboard: {e}")
            return None

    def _get_window_content(self) -> Optional[str]:
        """Get text content from active window via Accessibility API.

        This uses AppleScript to get the window's text content.
        """
        try:
            # Try to get window value (works for text editors, browsers, etc.)
            script = '''
            tell application "System Events"
                set frontApp to name of first process whose frontmost is true
                tell process frontApp
                    try
                        set windowContent to value of text area 1 of scroll area 1 of window 1
                        return windowContent
                    on error
                        try
                            set windowContent to value of text field 1 of window 1
                            return windowContent
                        on error
                            return ""
                        end try
                    end try
                end tell
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0 and result.stdout.strip():
                content = result.stdout.strip()
                # Limit to reasonable size
                if len(content) > 10000:
                    content = content[:10000] + "...\n[truncated]"
                return content

            return None

        except Exception as e:
            print(f"Failed to get window content: {e}")
            return None

    def _capture_screenshot(
        self,
        app_name: str,
        window_title: str,
        timestamp: float
    ) -> Optional[CapturedContext]:
        """Capture screenshot of active window.

        Returns base64-encoded image for vision model processing.
        """
        try:
            import tempfile
            import base64
            from pathlib import Path

            # Create temp file for screenshot
            temp_dir = Path(tempfile.gettempdir())
            screenshot_path = temp_dir / f"voice_cmd_screenshot_{int(timestamp)}.png"

            # Capture active window using screencapture
            # -w flag captures only the active window
            result = subprocess.run(
                ["screencapture", "-w", "-x", str(screenshot_path)],
                capture_output=True,
                timeout=3
            )

            if result.returncode != 0 or not screenshot_path.exists():
                print("Screenshot capture failed")
                return None

            # Read and encode as base64
            with open(screenshot_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Clean up temp file
            screenshot_path.unlink()

            print(f"📸 Screenshot captured ({len(image_data)} bytes)")

            return CapturedContext(
                content=image_data,
                source="screenshot",
                app_name=app_name,
                window_title=window_title,
                timestamp=timestamp,
                is_image=True,
            )

        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            return None

    def update_clipboard_tracking(self):
        """Update clipboard tracking. Call this periodically to track clipboard changes."""
        try:
            clipboard = pyperclip.paste()
            if clipboard != self.last_clipboard_content:
                self.last_clipboard_content = clipboard
                self.last_clipboard_time = time.time()
        except Exception:
            pass


# Global instance
context_capture = ContextCapture()


if __name__ == "__main__":
    print("Testing Context Capture")
    print("=" * 50)

    capturer = ContextCapture()

    print("\nTest 1: Capture current context")
    print("(Try selecting some text before running)")
    print()

    context = capturer.capture()

    if context:
        print(f"\nCaptured Context:")
        print(f"  Source: {context.source}")
        print(f"  App: {context.app_name}")
        print(f"  Window: {context.window_title}")
        print(f"  Is Image: {context.is_image}")
        if not context.is_image:
            preview = context.content[:200]
            if len(context.content) > 200:
                preview += "..."
            print(f"  Content: {preview}")
        else:
            print(f"  Content: [Image data, {len(context.content)} bytes]")
    else:
        print("\nNo context captured (or blocked)")

    print("\nTest 2: Force screenshot")
    screenshot_context = capturer.capture(force_screenshot=True)
    if screenshot_context:
        print(f"Screenshot captured: {screenshot_context.source}")
