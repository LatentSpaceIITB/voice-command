import io
import numpy as np
from openai import OpenAI
from config import OPENAI_API_KEY, SAMPLE_RATE
import wave

class Transcriber:
    """Transcribes audio to text using OpenAI Whisper API."""

    def __init__(self):
        print("Initializing OpenAI Whisper API...")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI Whisper ready.")

    def _audio_to_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        """Convert numpy audio array to WAV bytes for API upload."""
        # Convert float32 [-1, 1] to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 2 bytes for int16
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_int16.tobytes())

        buffer.seek(0)
        return buffer

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data to text using OpenAI API."""
        if len(audio_data) == 0:
            return ""

        # Ensure float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Convert to WAV bytes
        wav_buffer = self._audio_to_wav_bytes(audio_data)

        # Call OpenAI Whisper API
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", wav_buffer, "audio/wav"),
            language="en"
        )

        text = transcript.text.strip()
        print(f"📝 Transcribed: \"{text}\"")

        return text


if __name__ == "__main__":
    transcriber = Transcriber()
    print("Transcriber ready. Use with audio data from AudioRecorder.")
