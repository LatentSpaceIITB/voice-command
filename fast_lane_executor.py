"""Fast Lane Executor - Extended local command execution.

Handles all Fast Lane commands that can be executed locally without cloud APIs.
Uses AppleScript and subprocess for macOS system control.
"""

import subprocess
import time
import threading
from typing import Optional

from system_executor import SystemExecutor, APP_ALIASES


class FastLaneExecutor(SystemExecutor):
    """Executes Fast Lane commands locally using AppleScript/subprocess."""

    # All supported Fast Lane actions
    FAST_LANE_ACTIONS = {
        # Media controls
        "media_play_pause",
        "media_next",
        "media_previous",
        # Volume controls
        "volume_up",
        "volume_down",
        "volume_mute",
        "volume_unmute",
        # System controls
        "lock_screen",
        "sleep_display",
        "screenshot",
        "screenshot_selection",
        # System toggles
        "wifi_on",
        "wifi_off",
        "dnd_on",
        "dnd_off",
        "dark_mode_on",
        "dark_mode_off",
        # Window management
        "window_maximize",
        "window_minimize",
        "window_fullscreen",
        "window_snap_left",
        "window_snap_right",
        "window_close",
        # Timer/Alarm
        "set_timer",
        "set_alarm",
        # Inherited from SystemExecutor
        "open_app",
        "close_app",
        "switch_app",
        "open_url",
    }

    def __init__(self):
        """Initialize the Fast Lane executor."""
        super().__init__()
        print("Fast Lane executor ready.")

    def execute(self, intent: dict) -> bool:
        """Execute Fast Lane action based on intent.

        Args:
            intent: Dict with 'action' key and relevant parameters

        Returns:
            True if execution succeeded, False otherwise
        """
        action = intent.get("action")

        if not action:
            print("No action specified in intent")
            return False

        # Existing system actions (from parent)
        if action in ("open_app", "close_app", "switch_app", "open_url"):
            return super().execute(intent)

        # Media controls
        if action == "media_play_pause":
            return self._media_play_pause()
        elif action == "media_next":
            return self._media_next()
        elif action == "media_previous":
            return self._media_previous()

        # Volume controls
        elif action == "volume_up":
            return self._volume_up(intent.get("level"))
        elif action == "volume_down":
            return self._volume_down(intent.get("level"))
        elif action == "volume_mute":
            return self._volume_mute()
        elif action == "volume_unmute":
            return self._volume_unmute()

        # System controls
        elif action == "lock_screen":
            return self._lock_screen()
        elif action == "sleep_display":
            return self._sleep_display()
        elif action == "screenshot":
            return self._screenshot()
        elif action == "screenshot_selection":
            return self._screenshot_selection()

        # System toggles
        elif action == "wifi_on":
            return self._wifi_on()
        elif action == "wifi_off":
            return self._wifi_off()
        elif action == "dnd_on":
            return self._dnd_on()
        elif action == "dnd_off":
            return self._dnd_off()
        elif action == "dark_mode_on":
            return self._dark_mode_on()
        elif action == "dark_mode_off":
            return self._dark_mode_off()

        # Window management
        elif action == "window_maximize":
            return self._window_maximize()
        elif action == "window_minimize":
            return self._window_minimize()
        elif action == "window_fullscreen":
            return self._window_fullscreen()
        elif action == "window_snap_left":
            return self._window_snap_left()
        elif action == "window_snap_right":
            return self._window_snap_right()
        elif action == "window_close":
            return self._window_close()

        # Timers and Alarms
        elif action == "set_timer":
            return self._set_timer(intent.get("duration_seconds", 300))
        elif action == "set_alarm":
            return self._set_alarm(intent.get("time"))

        else:
            print(f"Unknown Fast Lane action: {action}")
            return False

    def _run_applescript(self, script: str) -> bool:
        """Run AppleScript and return success status."""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("AppleScript timed out")
            return False
        except Exception as e:
            print(f"AppleScript error: {e}")
            return False

    def _run_command(self, cmd: list) -> bool:
        """Run a shell command and return success status."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Command timed out")
            return False
        except Exception as e:
            print(f"Command error: {e}")
            return False

    # =========================================================================
    # MEDIA CONTROLS
    # =========================================================================

    def _media_play_pause(self) -> bool:
        """Toggle play/pause for media playback."""
        # Try Spotify first (most common)
        if self._run_applescript('tell application "Spotify" to playpause'):
            print("Toggled Spotify playback")
            return True

        # Try Apple Music
        if self._run_applescript('tell application "Music" to playpause'):
            print("Toggled Music playback")
            return True

        # Try system-wide media key
        script = '''
        tell application "System Events"
            key code 49
        end tell
        '''
        return self._run_applescript(script)

    def _media_next(self) -> bool:
        """Skip to next track."""
        # Try Spotify
        if self._run_applescript('tell application "Spotify" to next track'):
            print("Skipped to next track (Spotify)")
            return True

        # Try Apple Music
        if self._run_applescript('tell application "Music" to next track'):
            print("Skipped to next track (Music)")
            return True

        return False

    def _media_previous(self) -> bool:
        """Go to previous track."""
        # Try Spotify
        if self._run_applescript('tell application "Spotify" to previous track'):
            print("Went to previous track (Spotify)")
            return True

        # Try Apple Music
        if self._run_applescript('tell application "Music" to previous track'):
            print("Went to previous track (Music)")
            return True

        return False

    # =========================================================================
    # VOLUME CONTROLS
    # =========================================================================

    def _volume_up(self, level: Optional[int] = None) -> bool:
        """Increase system volume."""
        if level is not None:
            script = f'set volume output volume {level}'
        else:
            script = 'set volume output volume ((output volume of (get volume settings)) + 10)'
        if self._run_applescript(script):
            print("Volume increased")
            return True
        return False

    def _volume_down(self, level: Optional[int] = None) -> bool:
        """Decrease system volume."""
        if level is not None:
            script = f'set volume output volume {level}'
        else:
            script = 'set volume output volume ((output volume of (get volume settings)) - 10)'
        if self._run_applescript(script):
            print("Volume decreased")
            return True
        return False

    def _volume_mute(self) -> bool:
        """Mute system volume."""
        if self._run_applescript('set volume with output muted'):
            print("Volume muted")
            return True
        return False

    def _volume_unmute(self) -> bool:
        """Unmute system volume."""
        if self._run_applescript('set volume without output muted'):
            print("Volume unmuted")
            return True
        return False

    # =========================================================================
    # SYSTEM CONTROLS
    # =========================================================================

    def _lock_screen(self) -> bool:
        """Lock the screen."""
        # Use keyboard shortcut: Ctrl+Cmd+Q
        script = '''
        tell application "System Events"
            keystroke "q" using {command down, control down}
        end tell
        '''
        if self._run_applescript(script):
            print("Screen locked")
            return True
        return False

    def _sleep_display(self) -> bool:
        """Put display to sleep."""
        if self._run_command(["pmset", "displaysleepnow"]):
            print("Display sleeping")
            return True
        return False

    def _screenshot(self) -> bool:
        """Take full screen screenshot (saved to Desktop)."""
        # Use keyboard shortcut: Cmd+Shift+3
        script = '''
        tell application "System Events"
            keystroke "3" using {command down, shift down}
        end tell
        '''
        if self._run_applescript(script):
            print("Screenshot captured")
            return True
        return False

    def _screenshot_selection(self) -> bool:
        """Take screenshot of selection."""
        # Use keyboard shortcut: Cmd+Shift+4
        script = '''
        tell application "System Events"
            keystroke "4" using {command down, shift down}
        end tell
        '''
        if self._run_applescript(script):
            print("Screenshot selection mode activated")
            return True
        return False

    # =========================================================================
    # SYSTEM TOGGLES
    # =========================================================================

    def _wifi_on(self) -> bool:
        """Turn WiFi on."""
        if self._run_command(["networksetup", "-setairportpower", "en0", "on"]):
            print("WiFi turned on")
            return True
        return False

    def _wifi_off(self) -> bool:
        """Turn WiFi off."""
        if self._run_command(["networksetup", "-setairportpower", "en0", "off"]):
            print("WiFi turned off")
            return True
        return False

    def _dnd_on(self) -> bool:
        """Enable Do Not Disturb / Focus mode."""
        # Try using shortcuts app (macOS Monterey+)
        if self._run_command(["shortcuts", "run", "Turn On Do Not Disturb"]):
            print("Do Not Disturb enabled")
            return True

        # Fallback: Try Focus menu
        script = '''
        tell application "System Events"
            tell process "Control Center"
                click menu bar item "Focus" of menu bar 1
            end tell
        end tell
        '''
        return self._run_applescript(script)

    def _dnd_off(self) -> bool:
        """Disable Do Not Disturb / Focus mode."""
        if self._run_command(["shortcuts", "run", "Turn Off Do Not Disturb"]):
            print("Do Not Disturb disabled")
            return True
        return False

    def _dark_mode_on(self) -> bool:
        """Enable dark mode."""
        script = '''
        tell application "System Events"
            tell appearance preferences
                set dark mode to true
            end tell
        end tell
        '''
        if self._run_applescript(script):
            print("Dark mode enabled")
            return True
        return False

    def _dark_mode_off(self) -> bool:
        """Disable dark mode."""
        script = '''
        tell application "System Events"
            tell appearance preferences
                set dark mode to false
            end tell
        end tell
        '''
        if self._run_applescript(script):
            print("Dark mode disabled")
            return True
        return False

    # =========================================================================
    # WINDOW MANAGEMENT
    # =========================================================================

    def _window_maximize(self) -> bool:
        """Maximize the current window (green button)."""
        script = '''
        tell application "System Events"
            set frontApp to name of first process whose frontmost is true
            tell process frontApp
                try
                    click button 2 of window 1
                end try
            end tell
        end tell
        '''
        if self._run_applescript(script):
            print("Window maximized")
            return True
        return False

    def _window_minimize(self) -> bool:
        """Minimize the current window (yellow button)."""
        script = '''
        tell application "System Events"
            set frontApp to name of first process whose frontmost is true
            tell process frontApp
                try
                    click button 3 of window 1
                end try
            end tell
        end tell
        '''
        if self._run_applescript(script):
            print("Window minimized")
            return True
        return False

    def _window_fullscreen(self) -> bool:
        """Toggle fullscreen for current window."""
        # Use keyboard shortcut: Ctrl+Cmd+F
        script = '''
        tell application "System Events"
            keystroke "f" using {command down, control down}
        end tell
        '''
        if self._run_applescript(script):
            print("Fullscreen toggled")
            return True
        return False

    def _window_snap_left(self) -> bool:
        """Snap window to left half of screen."""
        # Try Rectangle/Spectacle keyboard shortcut first
        script = '''
        tell application "System Events"
            keystroke (ASCII character 28) using {control down, option down}
        end tell
        '''
        if self._run_applescript(script):
            print("Window snapped left")
            return True

        # Fallback: Manual positioning
        return self._manual_snap_left()

    def _window_snap_right(self) -> bool:
        """Snap window to right half of screen."""
        # Try Rectangle/Spectacle keyboard shortcut first
        script = '''
        tell application "System Events"
            keystroke (ASCII character 29) using {control down, option down}
        end tell
        '''
        if self._run_applescript(script):
            print("Window snapped right")
            return True

        # Fallback: Manual positioning
        return self._manual_snap_right()

    def _manual_snap_left(self) -> bool:
        """Manually position window to left half of screen."""
        script = '''
        tell application "Finder"
            set screenBounds to bounds of window of desktop
            set screenWidth to item 3 of screenBounds
            set screenHeight to item 4 of screenBounds
        end tell

        tell application "System Events"
            set frontApp to name of first process whose frontmost is true
            tell process frontApp
                try
                    set position of window 1 to {0, 25}
                    set size of window 1 to {screenWidth / 2, screenHeight - 25}
                end try
            end tell
        end tell
        '''
        return self._run_applescript(script)

    def _manual_snap_right(self) -> bool:
        """Manually position window to right half of screen."""
        script = '''
        tell application "Finder"
            set screenBounds to bounds of window of desktop
            set screenWidth to item 3 of screenBounds
            set screenHeight to item 4 of screenBounds
        end tell

        tell application "System Events"
            set frontApp to name of first process whose frontmost is true
            tell process frontApp
                try
                    set position of window 1 to {screenWidth / 2, 25}
                    set size of window 1 to {screenWidth / 2, screenHeight - 25}
                end try
            end tell
        end tell
        '''
        return self._run_applescript(script)

    def _window_close(self) -> bool:
        """Close the current window."""
        # Use keyboard shortcut: Cmd+W
        script = '''
        tell application "System Events"
            keystroke "w" using command down
        end tell
        '''
        if self._run_applescript(script):
            print("Window closed")
            return True
        return False

    # =========================================================================
    # TIMERS AND ALARMS
    # =========================================================================

    def _set_timer(self, duration_seconds: int) -> bool:
        """Set a timer with notification when complete.

        Args:
            duration_seconds: Timer duration in seconds
        """
        if duration_seconds <= 0:
            print("Invalid timer duration")
            return False

        minutes = duration_seconds // 60
        seconds = duration_seconds % 60

        # Show immediate notification that timer was set
        if minutes > 0:
            duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            if seconds > 0:
                duration_str += f" {seconds} second{'s' if seconds != 1 else ''}"
        else:
            duration_str = f"{seconds} second{'s' if seconds != 1 else ''}"

        # Notify user
        notify_script = f'''
        display notification "Timer set for {duration_str}" with title "Voice Command" sound name "Pop"
        '''
        self._run_applescript(notify_script)

        # Start background timer
        def timer_complete():
            time.sleep(duration_seconds)
            # Play notification when done
            complete_script = '''
            display notification "Timer complete!" with title "Voice Command" sound name "Glass"
            '''
            self._run_applescript(complete_script)

        thread = threading.Thread(target=timer_complete, daemon=True)
        thread.start()

        print(f"Timer set for {duration_str}")
        return True

    def _set_alarm(self, time_str: Optional[str]) -> bool:
        """Set an alarm using Reminders app.

        Args:
            time_str: Time string like "7:00 AM"
        """
        if not time_str:
            print("No time specified for alarm")
            return False

        # Create a reminder with the specified time
        script = f'''
        tell application "Reminders"
            set newReminder to make new reminder with properties {{name:"Alarm - {time_str}", remind me date:date "{time_str}"}}
        end tell
        '''

        if self._run_applescript(script):
            print(f"Alarm set for {time_str}")
            # Notify user
            notify_script = f'''
            display notification "Alarm set for {time_str}" with title "Voice Command" sound name "Pop"
            '''
            self._run_applescript(notify_script)
            return True

        return False


# Global instance
fast_executor = FastLaneExecutor()


if __name__ == "__main__":
    import sys

    executor = FastLaneExecutor()

    print("Fast Lane Executor Test")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("\nUsage: python fast_lane_executor.py <action> [params]")
        print("\nAvailable actions:")
        for action in sorted(executor.FAST_LANE_ACTIONS):
            print(f"  - {action}")
        print("\nExamples:")
        print("  python fast_lane_executor.py media_play_pause")
        print("  python fast_lane_executor.py volume_mute")
        print("  python fast_lane_executor.py open_app chrome")
        print("  python fast_lane_executor.py set_timer 60")
        exit(0)

    action = sys.argv[1]

    # Build intent based on action
    intent = {"action": action}

    if action in ("open_app", "close_app", "switch_app") and len(sys.argv) > 2:
        intent["app_name"] = sys.argv[2]
    elif action == "open_url" and len(sys.argv) > 2:
        intent["url"] = sys.argv[2]
    elif action == "set_timer" and len(sys.argv) > 2:
        intent["duration_seconds"] = int(sys.argv[2])
    elif action == "set_alarm" and len(sys.argv) > 2:
        intent["time"] = sys.argv[2]

    print(f"\nExecuting: {action}")
    print(f"Intent: {intent}")

    success = executor.execute(intent)
    print(f"\nResult: {'Success' if success else 'Failed'}")
