import sounddevice as sd
import numpy as np
from typing import Optional
import threading
from config import SAMPLE_RATE, CHANNELS

class AudioRecorder:
    """Records audio from microphone while triggered."""

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_buffer: list = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream - stores audio data."""
        if status:
            print(f"Audio status: {status}")
        if self.is_recording:
            with self._lock:
                self.audio_buffer.append(indata.copy())

    def start_recording(self):
        """Start recording audio."""
        with self._lock:
            self.audio_buffer = []
        self.is_recording = True

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            callback=self._audio_callback
        )
        self._stream.start()
        print("🎤 Recording...")

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the audio data."""
        self.is_recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if self.audio_buffer:
                audio_data = np.concatenate(self.audio_buffer, axis=0)
                # Flatten to 1D array for Whisper
                audio_data = audio_data.flatten()
            else:
                audio_data = np.array([], dtype=np.float32)

        duration = len(audio_data) / self.sample_rate
        print(f"🛑 Recording stopped. Duration: {duration:.1f}s")

        return audio_data

    def get_audio_duration(self, audio_data: np.ndarray) -> float:
        """Get duration of audio in seconds."""
        return len(audio_data) / self.sample_rate


if __name__ == "__main__":
    import time

    recorder = AudioRecorder()
    print("Recording for 3 seconds...")

    recorder.start_recording()
    time.sleep(3)
    audio = recorder.stop_recording()

    print(f"Recorded {len(audio)} samples ({recorder.get_audio_duration(audio):.1f}s)")
