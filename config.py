import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")

# Audio settings
SAMPLE_RATE = 16000  # Whisper optimal sample rate
CHANNELS = 1  # Mono audio

# Whisper settings (OpenAI API)
WHISPER_MODEL = "whisper-1"  # OpenAI's Whisper model

# Hotkey settings
TRIGGER_KEY = "cmd_r"  # Right Command key on Mac

# File paths
CONTACTS_FILE = os.path.join(os.path.dirname(__file__), "contacts.json")
ROUTES_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "routes_config.json")

# =============================================================================
# LOCAL FAST LANE SETTINGS
# =============================================================================

# Local Whisper (whisper.cpp with CoreML)
LOCAL_WHISPER_MODEL = "base.en"  # Options: tiny.en, base.en, small.en
LOCAL_WHISPER_USE_COREML = True  # Use Apple Neural Engine for acceleration
LOCAL_WHISPER_MAX_DURATION = 5.0  # Max seconds for local transcription (longer goes to cloud)

# Semantic Router (fastembed)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # Lightweight embedding model
FAST_LANE_CONFIDENCE = 0.8  # Minimum confidence for Fast Lane routing
SLOW_LANE_CONFIDENCE = 0.7  # Minimum confidence for Slow Lane (below = uncertain)

# Fallback behavior
FAST_LANE_FALLBACK_TO_CLOUD = True  # If Fast Lane fails, try cloud parsing
