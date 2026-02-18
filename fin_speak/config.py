"""
Configuration module for FinSpeak
Central configuration for model selection, API keys, and runtime settings
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Central configuration for FinSpeak application"""

    # OpenAI API Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    USE_OPENAI_STT: bool = os.getenv("USE_OPENAI_STT", "false").lower() == "true"
    USE_OPENAI_NLU: bool = os.getenv("USE_OPENAI_NLU", "false").lower() == "true"

    # Whisper Model Configuration
    # Options: tiny, base, small, medium, large
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "small")

    # NLU Model Configuration
    NLU_MODEL: str = "google/flan-t5-small"  # Lightweight T5 model
    USE_RULE_BASED_NLU: bool = True  # Use rule-based approach as primary

    # TTS Configuration
    TTS_BACKEND: str = "gtts"  # Options: gtts, pyttsx3

    # Data paths
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    FUNDS_CSV: str = os.path.join(DATA_DIR, "funds.csv")
    NAV_HISTORY_CSV: str = os.path.join(DATA_DIR, "nav_history.csv")

    # Audio settings
    SAMPLE_RATE: int = 16000  # Target sample rate for audio processing
    AUDIO_CHANNELS: int = 1  # Mono audio

    # Fuzzy matching threshold
    FUZZY_MATCH_THRESHOLD: float = 70.0  # Minimum score for fuzzy matching

    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def get_whisper_model_name(cls) -> str:
        """Get the full Whisper model name"""
        return cls.WHISPER_MODEL_SIZE

    @classmethod
    def use_openai_stt(cls) -> bool:
        """Check if OpenAI STT should be used"""
        return cls.USE_OPENAI_STT and cls.OPENAI_API_KEY is not None

    @classmethod
    def use_openai_nlu(cls) -> bool:
        """Check if OpenAI NLU should be used"""
        return cls.USE_OPENAI_NLU and cls.OPENAI_API_KEY is not None

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if cls.USE_OPENAI_STT or cls.USE_OPENAI_NLU:
            if not cls.OPENAI_API_KEY:
                print("Warning: OpenAI features enabled but no API key found")
                return False
        return True


# Initialize configuration validation
Config.validate()
