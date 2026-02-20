"""
NLP module - Intent detection and entity extraction
Supports English, Hindi (Devanagari), and Hinglish (Hindi in Roman script)
"""

import re
from typing import Dict, Optional, Tuple

INTENT_GET_NAV = "get_nav"
INTENT_GET_RETURN = "get_return"
INTENT_EXPLAIN = "explain_term"
INTENT_UNKNOWN = "unknown"

# ── Hindi / Hinglish term-to-English mapping ──────────────────────────
# Maps Devanagari and Romanised Hindi words to their English equivalents
HINDI_TERM_MAP = {
    # Devanagari
    "एनएवी": "nav", "एन ए वी": "nav",
    "एसआईपी": "sip", "एस आई पी": "sip",
    "रिटर्न": "returns", "रिटर्न्स": "returns",
    "म्यूचुअल फंड": "mutual fund", "म्युचुअल फंड": "mutual fund",
    "एक्सपेंस रेशियो": "expense ratio",
    "ईएलएसएस": "elss",
    "लार्ज कैप": "large cap", "लार्ज़ कैप": "large cap",
    "स्मॉल कैप": "small cap",
    "सीएजीआर": "cagr",
    "एक्जिट लोड": "exit load",
    "एयूएम": "aum",
    # Romanised Hindi (Hinglish)
    "kya hai": "", "kya hota hai": "", "kya hoti hai": "",
    "matlab": "", "matlab kya hai": "",
    "samjhao": "", "samjhaiye": "", "batao": "", "bataiye": "",
}

# Words that signal "explain this term" intent in any language
EXPLAIN_SIGNALS_HI = [
    r"क्या\s*(है|होता|होती|हैं|होते)",       # क्या है / क्या होता है
    r"(मतलब|अर्थ|meaning)",                   # मतलब / अर्थ
    r"(समझाओ|समझाइए|बताओ|बताइए)",             # समझाओ / बताओ
]
EXPLAIN_SIGNALS_HINGLISH = [
    r"\b(kya\s+h[ao]i|kya\s+hota?\s+h[ao]i)\b",
    r"\b(matlab|meaning|samjh[ao]|bata[oi])\b",
    r"\b(explain|define)\b",
]
EXPLAIN_SIGNALS_EN = [
    r"\b(what\s+is|what\s+are|explain|define|meaning\s+of|tell\s+me\s+about)\b",
    r"\b(what\s+does)\b.*\b(mean)\b",
]


def _has_devanagari(text: str) -> bool:
    """Check if text contains Devanagari characters"""
    return bool(re.search(r'[\u0900-\u097F]', text))


def _normalise(text: str) -> str:
    """Light normalisation: lowercase, collapse whitespace"""
    return re.sub(r'\s+', ' ', text.strip().lower())


def detect_intent_rule_based(text: str) -> Dict:
    """
    Detect intent using pattern matching.
    Supports English, Hindi (Devanagari), and Hinglish.
    """
    text_lower = _normalise(text)
    is_hindi = _has_devanagari(text)

    # ── Known fund house names → indicates a FUND query, not explain ──
    fund_house_hints = [
        'hdfc', 'sbi', 'icici', 'axis', 'kotak', 'nippon', 'tata',
        'birla', 'aditya', 'dsp', 'franklin', 'mirae', 'parag',
        'uti', 'canara', 'idfc', 'sundaram', 'motilal', 'edelweiss',
        'bandhan', 'pgim', 'invesco', 'quant', 'baroda', 'hsbc',
        'mahindra', 'union', 'lic', 'ppfas', 'quantum',
    ]
    has_fund_hint = any(fh in text_lower for fh in fund_house_hints)

    # ── 1. NAV intent ─────────────────────────────────────────────
    nav_patterns = [
        # English
        r'\b(what|current|latest|today)\b.*\b(nav|price|value)\b',
        r'\bnav\b.*\bof\b',
        r'\bprice\b.*\bof\b',
        r'\bcurrent\s+value\b',
        # Hindi / Hinglish
        r'(एनएवी|nav)\s*(बताओ|batao|dikhao|दिखाओ)',
        r'\b(nav|price|value)\b.*(batao|dikhao|bataiye)\b',
        r'\b(kitna|kitni)\b.*\b(nav|price|value)\b',
    ]

    # ── 2. RETURNS intent ─────────────────────────────────────────
    return_patterns = [
        # English
        r'\b(return|returns|performance|gain|growth)\b',
        r'\bhow\s+(much|well)\b.*\b(perform|doing|grown)\b',
        r'\b(\d+)\s*(month|year)\b.*\b(return|performance)\b',
        # Hindi / Hinglish
        r'(रिटर्न|return)\s*(बताओ|दिखाओ|कितना|kitna)',
        r'\b(return|returns|performance)\b.*(batao|dikhao)\b',
        r'\b(kitna|kitni)\b.*(return|badha|growth)\b',
    ]

    intent = INTENT_UNKNOWN

    for pattern in nav_patterns:
        if re.search(pattern, text_lower):
            intent = INTENT_GET_NAV
            break

    if intent == INTENT_UNKNOWN:
        for pattern in return_patterns:
            if re.search(pattern, text_lower):
                intent = INTENT_GET_RETURN
                break

    # ── 3. If we found a fund intent OR a fund house hint, return fund query ─
    if intent != INTENT_UNKNOWN or has_fund_hint:
        if intent == INTENT_UNKNOWN and has_fund_hint:
            intent = INTENT_GET_NAV  # default fund queries to NAV
        period_months = extract_time_period(text)
        return {
            "intent": intent,
            "period_months": period_months,
        }

    # ── 4. Check for EXPLAIN intent (only if no fund context) ─────
    explain_patterns = (
        EXPLAIN_SIGNALS_HI + EXPLAIN_SIGNALS_HINGLISH
        if is_hindi else
        EXPLAIN_SIGNALS_EN + EXPLAIN_SIGNALS_HINGLISH
    )
    for pat in explain_patterns:
        if re.search(pat, text_lower):
            term = _extract_term_to_explain(text_lower, is_hindi)
            return {
                "intent": INTENT_EXPLAIN,
                "term": term,
                "period_months": None,
            }

    period_months = extract_time_period(text)

    return {
        "intent": intent,
        "period_months": period_months,
    }


def _extract_term_to_explain(text: str, is_hindi: bool) -> str:
    """Pull the financial term out of an explain-type query"""
    cleaned = text

    # Strip Devanagari question markers
    for pat in EXPLAIN_SIGNALS_HI:
        cleaned = re.sub(pat, '', cleaned)
    # Strip Hinglish / English question markers
    for pat in EXPLAIN_SIGNALS_HINGLISH + EXPLAIN_SIGNALS_EN:
        cleaned = re.sub(pat, '', cleaned)

    # Remove punctuation (keep Devanagari + Latin)
    cleaned = re.sub(r'[^\w\s\u0900-\u097F]', '', cleaned)
    cleaned = cleaned.strip()

    # Map known Hindi/Hinglish terms to English keys
    for hindi, eng in HINDI_TERM_MAP.items():
        if hindi in cleaned:
            if eng:
                return eng
            cleaned = cleaned.replace(hindi, '').strip()

    return cleaned if cleaned else text


def extract_time_period(text: str) -> Optional[int]:
    """Extract time period in months from text (EN + Hindi + Hinglish)"""
    text_lower = _normalise(text)

    month_match = re.search(r'(\d+)\s*(month|mahine|महीने|mahin[ae])', text_lower)
    if month_match:
        return int(month_match.group(1))

    year_match = re.search(r'(\d+)\s*(year|saal|साल)', text_lower)
    if year_match:
        return int(year_match.group(1)) * 12

    if any(w in text_lower for w in ['one year', 'ek saal', 'एक साल']):
        return 12
    if any(w in text_lower for w in ['six month', 'cheh mahine', 'छह महीने']):
        return 6
    if any(w in text_lower for w in ['three month', 'teen mahine', 'तीन महीने']):
        return 3

    return 12  # Default


def extract_fund(text: str) -> Optional[str]:
    """Extract fund name from text (EN + Hindi + Hinglish)"""
    text_lower = _normalise(text)

    # Remove common query words (English + Hinglish + Hindi)
    stop_words = [
        # English
        'what', 'is', 'the', 'nav', 'of', 'current', 'value', 'price',
        'show', 'me', 'tell', 'about', 'get', 'returns', 'return',
        'performance', 'how', 'much', 'fund', 'mutual', 'month', 'year',
        'latest', 'today', 'give', 'please',
        # Hinglish
        'kya', 'hai', 'ka', 'ki', 'ke', 'batao', 'bataiye', 'dikhao',
        'kitna', 'kitni', 'kitne', 'abhi', 'aaj', 'mujhe',
    ]

    # Strip Devanagari question words
    text_clean = re.sub(
        r'(क्या|है|का|की|के|बताओ|बताइए|दिखाओ|कितना|कितनी|आज|अभी|मुझे)', '', text_lower
    )

    # Remove numbers and punctuation
    text_clean = re.sub(r'\d+', '', text_clean)
    text_clean = re.sub(r'[^\w\s]', '', text_clean)

    # Split and filter
    words = text_clean.split()
    fund_words = [w for w in words if w not in stop_words and len(w) > 1]

    if fund_words:
        return ' '.join(fund_words)

    return None
