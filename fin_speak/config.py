"""
Configuration module for FinSpeak
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration"""

    # Azure Speech
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION: Optional[str] = os.getenv("AZURE_SPEECH_REGION")

    # Azure Neural TTS voices (Indian English / Hindi)
    TTS_VOICE_EN: str = os.getenv("TTS_VOICE_EN", "en-IN-NeerjaNeural")
    TTS_VOICE_HI: str = os.getenv("TTS_VOICE_HI", "hi-IN-SwaraNeural")

    # Groq API (free LLM for education)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

    # Fuzzy matching threshold
    FUZZY_MATCH_THRESHOLD: float = 60.0

    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """Validate Azure Speech configuration"""
        return bool(cls.AZURE_SPEECH_KEY and cls.AZURE_SPEECH_REGION)
