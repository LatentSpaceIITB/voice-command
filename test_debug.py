#!/usr/bin/env python3
"""Debug script to test hotkey and microphone separately."""

import sys

def test_microphone():
    """Test if microphone recording works."""
    print("\n=== MICROPHONE TEST ===")
    print("Recording for 3 seconds... Speak now!")

    import sounddevice as sd
    import numpy as np

    duration = 3  # seconds
    sample_rate = 16000

    try:
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
        sd.wait()

        # Check if we got audio
        max_amplitude = np.max(np.abs(audio))
        print(f"Recording complete!")
        print(f"Max amplitude: {max_amplitude:.4f}")

        if max_amplitude < 0.01:
            print("WARNING: Very low audio level - microphone may not be working")
            print("Check: System Settings > Privacy & Security > Microphone")
        else:
            print("SUCCESS: Microphone is working!")

    except Exception as e:
        print(f"ERROR: {e}")
        print("Check: System Settings > Privacy & Security > Microphone")

def test_hotkey():
    """Test if hotkey detection works."""
    print("\n=== HOTKEY TEST ===")
    print("Press Option (⌥) key... (Ctrl+C to exit)")
    print()
    print("NOTE: Terminal app needs Accessibility permission:")
    print("System Settings > Privacy & Security > Accessibility > Terminal (or iTerm)")
    print()

    from pynput import keyboard

    def on_press(key):
        try:
            if key == keyboard.Key.alt:
                print("OPTION PRESSED!")
            else:
                print(f"Key pressed: {key}")
        except:
            pass

    def on_release(key):
        try:
            if key == keyboard.Key.alt:
                print("OPTION RELEASED!")
        except:
            pass
        if key == keyboard.Key.esc:
            print("ESC pressed - exiting")
            return False

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "mic":
        test_microphone()
    elif len(sys.argv) > 1 and sys.argv[1] == "key":
        test_hotkey()
    else:
        print("Usage:")
        print("  python test_debug.py mic   - Test microphone")
        print("  python test_debug.py key   - Test hotkey detection")
