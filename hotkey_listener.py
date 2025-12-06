from pynput import keyboard
from typing import Callable, Optional

class HotkeyListener:
    """Listens for Right Option key press/release to trigger recording."""

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None]
    ):
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.is_pressed = False
        self.listener: Optional[keyboard.Listener] = None

    def _on_press(self, key):
        """Handle key press events."""
        try:
            # Check for Right Command key (cmd_r) on Mac
            if key == keyboard.Key.cmd_r and not self.is_pressed:
                self.is_pressed = True
                self.on_press_callback()
        except AttributeError:
            pass

    def _on_release(self, key):
        """Handle key release events."""
        try:
            if key == keyboard.Key.cmd_r and self.is_pressed:
                self.is_pressed = False
                self.on_release_callback()
        except AttributeError:
            pass

    def start(self):
        """Start listening for hotkey events."""
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        print("Hotkey listener started. Hold Right Command (⌘) to record.")

    def stop(self):
        """Stop the listener."""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def join(self):
        """Wait for the listener to finish."""
        if self.listener:
            self.listener.join()


if __name__ == "__main__":
    # Test the hotkey listener
    def on_press():
        print("Key pressed - would start recording")

    def on_release():
        print("Key released - would stop recording")

    listener = HotkeyListener(on_press, on_release)
    listener.start()

    print("Press Ctrl+C to exit")
    try:
        listener.join()
    except KeyboardInterrupt:
        listener.stop()
        print("\nStopped.")
