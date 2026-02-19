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

    # Whisper Model Configuration
    # Options: tiny, base, small, medium, large
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "small")

    # NLU Model Configuration
    # Use a lightweight model compatible with zero-shot-classification pipeline
    NLU_MODEL: str = "typeform/distilbert-base-uncased-mnli"
    USE_RULE_BASED_NLU: bool = True  # Use rule-based approach as primary

    # TTS Configuration
    TTS_BACKEND: str = "gtts"  # Options: gtts, pyttsx3, azure

    # Azure Speech (optional)
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION: Optional[str] = os.getenv("AZURE_SPEECH_REGION")
    USE_AZURE_SPEECH: bool = os.getenv("USE_AZURE_SPEECH", "false").lower() == "true"
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
    def use_azure_speech(cls) -> bool:
        """Check if Azure Speech should be used"""
        return cls.USE_AZURE_SPEECH and cls.AZURE_SPEECH_KEY is not None and cls.AZURE_SPEECH_REGION is not None

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if cls.USE_AZURE_SPEECH:
            if not (cls.AZURE_SPEECH_KEY and cls.AZURE_SPEECH_REGION):
                print("Warning: Azure Speech enabled but credentials not found")
                return False
        return True


# Initialize configuration validation
Config.validate()
