"""Text-to-Speech client using OpenAI TTS API."""

import io
import subprocess
import tempfile
import os
import numpy as np
import sounddevice as sd
from openai import OpenAI
from config import OPENAI_API_KEY


class TTSClient:
    """Synthesizes speech from text using OpenAI TTS API and plays it."""

    def __init__(self, model: str = "tts-1", voice: str = "alloy"):
        """
        Initialize TTS client.

        Args:
            model: "tts-1" (fast) or "tts-1-hd" (higher quality)
            voice: alloy, echo, fable, onyx, nova, shimmer
        """
        print("Initializing OpenAI TTS...")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.voice = voice
        self._is_playing = False
        print(f"TTS ready (model={model}, voice={voice})")

    def synthesize(self, text: str) -> bytes:
        """Synthesize text to speech, return audio bytes (mp3)."""
        if not text.strip():
            return b""

        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3"
        )

        return response.content

    def _mp3_to_numpy(self, mp3_bytes: bytes) -> tuple:
        """Convert MP3 bytes to numpy array using ffmpeg."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_file:
            mp3_file.write(mp3_bytes)
            mp3_path = mp3_file.name

        try:
            # Use ffmpeg to convert to raw PCM
            result = subprocess.run(
                [
                    "ffmpeg", "-i", mp3_path,
                    "-f", "s16le",  # 16-bit signed little-endian
                    "-acodec", "pcm_s16le",
                    "-ar", "24000",  # OpenAI TTS uses 24kHz
                    "-ac", "1",  # Mono
                    "-loglevel", "error",
                    "-"  # Output to stdout
                ],
                capture_output=True
            )

            if result.returncode != 0:
                raise Exception(f"ffmpeg error: {result.stderr.decode()}")

            # Convert to numpy
            samples = np.frombuffer(result.stdout, dtype=np.int16)
            samples = samples.astype(np.float32) / 32768.0

            return samples, 24000

        finally:
            os.unlink(mp3_path)

    def speak(self, text: str) -> bool:
        """Synthesize and play text as speech."""
        if not text.strip():
            return False

        print(f"🔊 Speaking: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")

        try:
            # Synthesize speech
            audio_bytes = self.synthesize(text)

            if not audio_bytes:
                return False

            # Convert MP3 to numpy array
            samples, sample_rate = self._mp3_to_numpy(audio_bytes)

            # Play audio
            self._is_playing = True
            sd.play(samples, samplerate=sample_rate)
            sd.wait()  # Wait until audio finishes
            self._is_playing = False

            return True

        except Exception as e:
            print(f"❌ TTS error: {e}")
            self._is_playing = False
            return False

    def stop(self):
        """Stop current playback."""
        if self._is_playing:
            sd.stop()
            self._is_playing = False

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._is_playing


if __name__ == "__main__":
    # Test TTS
    tts = TTSClient()

    print("\nTest 1: Simple greeting")
    tts.speak("Hello! I'm your voice assistant. How can I help you today?")

    print("\nTest 2: Action confirmation")
    tts.speak("Opening Safari now.")

    print("\nTest 3: Longer response")
    tts.speak("I've created a calendar event for tomorrow at 8 PM with Navyansh. The meeting is titled Gameramp IO discussion.")
