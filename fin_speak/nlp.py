"""
Natural Language Processing (NLP) module
Handles intent detection and entity extraction
"""

import re
from typing import Dict, Tuple, Optional, List

from .config import Config


# Intent categories
INTENT_GET_NAV = "get_nav"
INTENT_GET_RETURN = "get_return"
INTENT_EXPLAIN_CHANGE = "explain_change"
INTENT_UNKNOWN = "unknown"


def detect_intent_rule_based(transcript: str) -> Dict[str, any]:
    """
    Detect intent using rule-based approach
    
    Args:
        transcript: Transcribed text
        
    Returns:
        Dictionary with intent, confidence, and extracted info
    """
    transcript_lower = transcript.lower()
    
    # Patterns for different intents
    nav_patterns = [
        r'\b(what|current|latest|today)\b.*\b(nav|price|value)\b',
        r'\bnav\b.*\bof\b',
        r'\bprice\b.*\bof\b',
        r'\bcurrent\s+value\b',
    ]
    
    return_patterns = [
        r'\b(return|returns|performance|gain|growth)\b',
        r'\bhow\s+(much|well)\b.*\b(perform|doing|grown)\b',
        r'\b(profit|loss)\b',
        r'\b(\d+)\s*(month|year|day)\b.*\b(return|performance)\b',
        r'\breturn\b.*\b(over|in|for)\b.*\b(month|year)\b',
    ]
    
    explain_patterns = [
        r'\bwhy\b.*\b(change|increase|decrease|drop|rise)\b',
        r'\bexplain\b.*\b(performance|change)\b',
        r'\breason\b.*\b(for)\b',
    ]
    
    # Check patterns
    intent = INTENT_UNKNOWN
    confidence = 0.5
    
    for pattern in nav_patterns:
        if re.search(pattern, transcript_lower):
            intent = INTENT_GET_NAV
            confidence = 0.9
            break
    
    if intent == INTENT_UNKNOWN:
        for pattern in return_patterns:
            if re.search(pattern, transcript_lower):
                intent = INTENT_GET_RETURN
                confidence = 0.85
                break
    
    if intent == INTENT_UNKNOWN:
        for pattern in explain_patterns:
            if re.search(pattern, transcript_lower):
                intent = INTENT_EXPLAIN_CHANGE
                confidence = 0.8
                break
    
    # Extract time period if present
    period_months = extract_time_period(transcript)
    
    return {
        "intent": intent,
        "confidence": confidence,
        "period_months": period_months,
        "method": "rule_based"
    }


def extract_time_period(text: str) -> Optional[int]:
    """
    Extract time period in months from text
    
    Args:
        text: Input text
        
    Returns:
        Number of months or None
    """
    text_lower = text.lower()
    
    # Look for explicit month mentions
    month_match = re.search(r'(\d+)\s*month', text_lower)
    if month_match:
        return int(month_match.group(1))
    
    # Look for year mentions
    year_match = re.search(r'(\d+)\s*year', text_lower)
    if year_match:
        return int(year_match.group(1)) * 12
    
    # Common phrases
    if 'one year' in text_lower or '1 year' in text_lower:
        return 12
    if 'six month' in text_lower or '6 month' in text_lower:
        return 6
    if 'three month' in text_lower or '3 month' in text_lower:
        return 3
    
    # Default to 12 months for return queries
    if any(word in text_lower for word in ['return', 'performance', 'gain']):
        return 12
    
    return None


def detect_intent_ml(transcript: str) -> Dict[str, any]:
    """
    Detect intent using ML model (transformers)
    
    Args:
        transcript: Transcribed text
        
    Returns:
        Dictionary with intent and confidence
    """
    try:
        from transformers import pipeline
        
        # Use zero-shot classification
        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        candidate_labels = [
            "get net asset value",
            "get return performance",
            "explain price change",
            "other question"
        ]
        
        result = classifier(transcript, candidate_labels)
        
        # Map to our intent types
        label_map = {
            "get net asset value": INTENT_GET_NAV,
            "get return performance": INTENT_GET_RETURN,
            "explain price change": INTENT_EXPLAIN_CHANGE,
            "other question": INTENT_UNKNOWN
        }
        
        top_label = result['labels'][0]
        intent = label_map.get(top_label, INTENT_UNKNOWN)
        confidence = result['scores'][0]
        
        return {
            "intent": intent,
            "confidence": confidence,
            "period_months": extract_time_period(transcript),
            "method": "ml"
        }
        
    except Exception as e:
        if Config.DEBUG:
            print(f"ML intent detection failed: {e}")
        # Fallback to rule-based
        return detect_intent_rule_based(transcript)


def detect_intent(transcript: str) -> Dict[str, any]:
    """
    Detect intent using configured method
    
    Args:
        transcript: Transcribed text
        
    Returns:
        Dictionary with intent, confidence, and metadata
    """
    if Config.USE_RULE_BASED_NLU:
        return detect_intent_rule_based(transcript)
    else:
        return detect_intent_ml(transcript)


def extract_fund(transcript: str, fund_names: Optional[List[str]] = None) -> Tuple[Optional[str], float]:
    """
    Extract fund name from transcript using fuzzy matching
    
    Args:
        transcript: Transcribed text
        fund_names: List of fund names to match against (optional)
        
    Returns:
        Tuple of (matched_fund_name, confidence)
    """
    try:
        from rapidfuzz import fuzz, process
        
        if fund_names is None:
            # Load from KB
            from .kb import load_funds_data
            df = load_funds_data()
            fund_names = df['fund_name'].tolist()
        
        # Find best match
        result = process.extractOne(
            transcript,
            fund_names,
            scorer=fuzz.token_set_ratio
        )
        
        if result:
            matched_name, score, _ = result
            if score >= Config.FUZZY_MATCH_THRESHOLD:
                return matched_name, score / 100.0
        
        return None, 0.0
        
    except ImportError as e:
        if Config.DEBUG:
            print(f"Fuzzy matching not available: {e}")
        
        # Simple substring matching fallback
        if fund_names is None:
            from .kb import load_funds_data
            df = load_funds_data()
            fund_names = df['fund_name'].tolist()
        
        transcript_lower = transcript.lower()
        for name in fund_names:
            if name.lower() in transcript_lower:
                return name, 0.8
        
        return None, 0.0
