"""
FinSpeak - Speech-driven Investment Q&A Assistant
A complete ML pipeline for voice-based financial queries.
"""

__version__ = "1.0.0"
__author__ = "FinSpeak Team"

from .config import Config
from .stt import transcribe
from .nlp import detect_intent, extract_fund
from .kb import match_fund, compute_return, search_funds, get_all_funds
from .tts import synthesize_text
from .app import generate_answer

__all__ = [
    "Config",
    "transcribe",
    "detect_intent",
    "extract_fund",
    "match_fund",
    "compute_return",
    "search_funds",
    "get_all_funds",
    "synthesize_text",
    "generate_answer",
]
