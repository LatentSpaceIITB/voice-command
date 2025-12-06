"""Local Transcriber using whisper.cpp with CoreML acceleration.

Provides fast local speech-to-text transcription for the Fast Lane pipeline.
Falls back gracefully if whisper.cpp is not available.
"""

import time
import numpy as np
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from config import (
    LOCAL_WHISPER_MODEL,
    LOCAL_WHISPER_USE_COREML,
    SAMPLE_RATE,
)


@dataclass
class TranscriptionResult:
    """Result from local transcription."""
    text: str
    confidence: float  # 0-1, estimated from audio quality/duration
    latency_ms: float  # Time taken in milliseconds
    model: str  # Model used for transcription


class LocalTranscriber:
    """Local transcription using whisper.cpp with CoreML."""

    def __init__(self, model_size: str = LOCAL_WHISPER_MODEL):
        """Initialize the local transcriber.

        Args:
            model_size: Whisper model size (tiny.en, base.en, small.en)
        """
        self.model_size = model_size
        self.model = None
        self._available = False
        self._use_coreml = LOCAL_WHISPER_USE_COREML

        self._initialize()

    def _initialize(self):
        """Initialize the whisper.cpp model."""
        try:
            from pywhispercpp.model import Model

            print(f"Loading local Whisper model: {self.model_size}...")
            start = time.time()

            # Initialize model (will download if needed)
            self.model = Model(self.model_size)

            elapsed = time.time() - start
            print(f"Local Whisper model loaded in {elapsed:.1f}s")

            self._available = True

        except ImportError:
            print("Warning: pywhispercpp not installed.")
            print("Install with: pip install pywhispercpp")
            self._available = False

        except Exception as e:
            print(f"Warning: Failed to initialize local Whisper: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if local transcription is available."""
        return self._available

    def transcribe(self, audio_data: np.ndarray) -> TranscriptionResult:
        """Transcribe audio data to text.

        Args:
            audio_data: NumPy array of audio samples (16kHz, mono, float32)

        Returns:
            TranscriptionResult with text, confidence, and latency
        """
        if not self._available:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                latency_ms=0.0,
                model="unavailable"
            )

        start = time.time()

        try:
            # Ensure audio is in correct format (float32)
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Normalize if needed (should be in [-1, 1] range)
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = audio_data / 32768.0

            # Transcribe using whisper.cpp
            segments = self.model.transcribe(audio_data)

            # Combine all segments into single text
            text = " ".join(seg.text for seg in segments).strip()

            elapsed_ms = (time.time() - start) * 1000

            # Estimate confidence based on audio duration and model output
            duration = len(audio_data) / SAMPLE_RATE
            confidence = self._estimate_confidence(text, duration)

            return TranscriptionResult(
                text=text,
                confidence=confidence,
                latency_ms=elapsed_ms,
                model=self.model_size
            )

        except Exception as e:
            print(f"Local transcription error: {e}")
            elapsed_ms = (time.time() - start) * 1000
            return TranscriptionResult(
                text="",
                confidence=0.0,
                latency_ms=elapsed_ms,
                model=self.model_size
            )

    def _estimate_confidence(self, text: str, duration: float) -> float:
        """Estimate transcription confidence.

        This is a heuristic based on:
        - Whether text was produced
        - Audio duration (very short audio is less reliable)
        - Text length relative to duration (speech rate sanity check)
        """
        if not text:
            return 0.0

        # Base confidence
        confidence = 0.8

        # Penalize very short audio (< 0.5s)
        if duration < 0.5:
            confidence *= 0.7

        # Penalize very short text (might be noise)
        if len(text) < 3:
            confidence *= 0.5

        # Check speech rate sanity (words per second)
        words = len(text.split())
        words_per_second = words / max(duration, 0.1)

        # Normal speech is 2-4 words/second
        if words_per_second < 0.5:
            confidence *= 0.8  # Too slow, might be mostly silence
        elif words_per_second > 8:
            confidence *= 0.7  # Too fast, might be hallucination

        return min(confidence, 1.0)


# Fallback implementation using mlx-whisper (Apple Silicon optimized)
class MLXWhisperTranscriber:
    """Alternative local transcriber using mlx-whisper.

    mlx-whisper is optimized for Apple Silicon and can be faster
    than whisper.cpp on M1/M2/M3 Macs.
    """

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._available = False

        try:
            import mlx_whisper
            self._available = True
            print(f"mlx-whisper available with model: {model_size}")
        except ImportError:
            pass

    def is_available(self) -> bool:
        return self._available

    def transcribe(self, audio_data: np.ndarray) -> TranscriptionResult:
        if not self._available:
            return TranscriptionResult("", 0.0, 0.0, "unavailable")

        try:
            import mlx_whisper

            start = time.time()

            # mlx-whisper expects float32 audio at 16kHz
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            result = mlx_whisper.transcribe(
                audio_data,
                path_or_hf_repo=f"mlx-community/whisper-{self.model_size}-mlx"
            )

            text = result.get("text", "").strip()
            elapsed_ms = (time.time() - start) * 1000

            return TranscriptionResult(
                text=text,
                confidence=0.9 if text else 0.0,
                latency_ms=elapsed_ms,
                model=f"mlx-{self.model_size}"
            )

        except Exception as e:
            print(f"mlx-whisper error: {e}")
            return TranscriptionResult("", 0.0, 0.0, f"mlx-{self.model_size}")


# Factory function to get the best available local transcriber
def get_local_transcriber() -> LocalTranscriber:
    """Get the best available local transcriber.

    Tries whisper.cpp first (most compatible), then mlx-whisper (fastest on Apple Silicon).
    """
    # Try pywhispercpp first
    transcriber = LocalTranscriber()
    if transcriber.is_available():
        return transcriber

    # Try mlx-whisper as fallback
    mlx = MLXWhisperTranscriber()
    if mlx.is_available():
        print("Using mlx-whisper as local transcriber")
        return mlx

    # Return unavailable transcriber
    print("No local transcriber available. Install pywhispercpp or mlx-whisper.")
    return transcriber


if __name__ == "__main__":
    import sounddevice as sd

    print("Local Transcriber Test")
    print("=" * 50)

    transcriber = LocalTranscriber()

    if not transcriber.is_available():
        print("\nLocal transcriber not available.")
        print("Install whisper.cpp: pip install pywhispercpp")
        exit(1)

    print("\nRecording 3 seconds of audio...")
    print("Say something!")

    # Record audio
    duration = 3.0
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32
    )
    sd.wait()

    audio = audio.flatten()

    print(f"\nTranscribing {len(audio) / SAMPLE_RATE:.1f}s of audio...")

    result = transcriber.transcribe(audio)

    print(f"\nResult:")
    print(f"  Text: '{result.text}'")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Latency: {result.latency_ms:.0f}ms")
    print(f"  Model: {result.model}")
