"""Audio feedback cues for voice assistant state changes."""

import numpy as np
import sounddevice as sd
from config import SAMPLE_RATE


class AudioFeedback:
    """Generates and plays audio feedback cues."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate

    def _generate_tone(
        self,
        frequency: float,
        duration: float,
        volume: float = 0.3
    ) -> np.ndarray:
        """Generate a sine wave tone."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        tone = np.sin(2 * np.pi * frequency * t)

        # Apply fade in/out to avoid clicks
        fade_samples = int(self.sample_rate * 0.01)  # 10ms fade
        tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
        tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)

        return (tone * volume).astype(np.float32)

    def _play(self, audio: np.ndarray):
        """Play audio non-blocking."""
        try:
            sd.play(audio, self.sample_rate)
        except Exception as e:
            print(f"Audio feedback error: {e}")

    def play_start(self):
        """Play sound when recording starts (ascending tone)."""
        # Two quick ascending beeps
        tone1 = self._generate_tone(440, 0.08)  # A4
        silence = np.zeros(int(self.sample_rate * 0.03), dtype=np.float32)
        tone2 = self._generate_tone(554, 0.08)  # C#5

        audio = np.concatenate([tone1, silence, tone2])
        self._play(audio)

    def play_stop(self):
        """Play sound when recording stops (descending tone)."""
        # Two quick descending beeps
        tone1 = self._generate_tone(554, 0.08)  # C#5
        silence = np.zeros(int(self.sample_rate * 0.03), dtype=np.float32)
        tone2 = self._generate_tone(440, 0.08)  # A4

        audio = np.concatenate([tone1, silence, tone2])
        self._play(audio)

    def play_processing(self):
        """Play sound when processing starts (single mid tone)."""
        tone = self._generate_tone(523, 0.1, volume=0.2)  # C5
        self._play(tone)

    def play_success(self):
        """Play sound on successful action (happy chord)."""
        # Major chord: C-E-G ascending
        tone1 = self._generate_tone(523, 0.1)   # C5
        silence = np.zeros(int(self.sample_rate * 0.02), dtype=np.float32)
        tone2 = self._generate_tone(659, 0.1)   # E5
        tone3 = self._generate_tone(784, 0.15)  # G5

        audio = np.concatenate([tone1, silence, tone2, silence, tone3])
        self._play(audio)

    def play_error(self):
        """Play sound on error (warning tone)."""
        # Two low descending tones
        tone1 = self._generate_tone(300, 0.15, volume=0.4)
        silence = np.zeros(int(self.sample_rate * 0.05), dtype=np.float32)
        tone2 = self._generate_tone(200, 0.2, volume=0.4)

        audio = np.concatenate([tone1, silence, tone2])
        self._play(audio)

    def play_acknowledge(self):
        """Play quick chirp when Fast Lane intent recognized (before execution).

        This sound plays immediately after semantic classification to provide
        optimistic feedback before command execution begins.
        """
        # Quick ascending double chirp - bright and snappy
        tone1 = self._generate_tone(880, 0.04, volume=0.25)   # A5
        silence = np.zeros(int(self.sample_rate * 0.02), dtype=np.float32)
        tone2 = self._generate_tone(1047, 0.04, volume=0.25)  # C6

        audio = np.concatenate([tone1, silence, tone2])
        self._play(audio)


# Global instance for easy access
feedback = AudioFeedback()


if __name__ == "__main__":
    import time

    print("Testing audio feedback cues...")

    print("\n1. Start recording sound:")
    feedback.play_start()
    time.sleep(0.5)

    print("2. Stop recording sound:")
    feedback.play_stop()
    time.sleep(0.5)

    print("3. Processing sound:")
    feedback.play_processing()
    time.sleep(0.5)

    print("4. Success sound:")
    feedback.play_success()
    time.sleep(0.5)

    print("5. Error sound:")
    feedback.play_error()
    time.sleep(0.5)

    print("6. Acknowledge sound (Fast Lane):")
    feedback.play_acknowledge()
    time.sleep(0.5)

    print("\nDone!")
