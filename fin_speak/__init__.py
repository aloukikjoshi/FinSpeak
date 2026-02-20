"""
FinSpeak - Voice-powered Mutual Fund Assistant
Real-time data with FastAPI backend for Vercel deployment
"""

__version__ = "2.0.0"

from .config import Config
from .nlp import detect_intent_rule_based, extract_fund
from .kb import query_nav, query_returns, search_fund
from .data_service import get_fund_nav, get_fund_returns, search_funds

__all__ = [
    "Config",
    "detect_intent_rule_based",
    "extract_fund",
    "query_nav",
    "query_returns",
    "search_fund",
    "get_fund_nav",
    "get_fund_returns",
    "search_funds",
]
