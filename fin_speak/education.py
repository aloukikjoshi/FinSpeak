"""
Education module - Uses Groq (free LLM) to explain financial terms
Supports English, Hindi (Devanagari), and Hinglish (Roman Hindi)
"""

import os
import re
import httpx
from typing import Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-70b-versatile"

# ── Hindi / Hinglish → English term mapping ───────────────────────────
TERM_ALIASES = {
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
    # Hinglish (Roman)
    "net asset value": "nav",
    "systematic investment plan": "sip",
    "equity linked savings scheme": "elss",
    "assets under management": "aum",
    "compound annual growth rate": "cagr",
}

# Predefined explanations as fallback (no API needed)
TERM_EXPLANATIONS = {
    "nav": {
        "en": "NAV (Net Asset Value) is the per-unit price of a mutual fund. Think of it like the price of one share. If a fund's NAV is ₹50, you get one unit for ₹50.",
        "hi": "NAV (Net Asset Value) ka matlab hai ek mutual fund unit ki keemat. Jaise ek share ka price hota hai, waise hi NAV ek unit ka price hai. Agar NAV ₹50 hai, toh ₹50 mein aapko ek unit milega.",
        "hinglish": "NAV matlab Net Asset Value — basically ek unit ki price. Jaise ek share ka rate hota hai, waise hi NAV ek unit ka rate hai. NAV ₹50 hai toh ₹50 mein ek unit milega."
    },
    "sip": {
        "en": "SIP (Systematic Investment Plan) means investing a fixed amount every month in a mutual fund. Like a recurring deposit, but in mutual funds. Even ₹500/month can grow significantly over time.",
        "hi": "SIP (Systematic Investment Plan) ka matlab hai har mahine ek fixed amount mutual fund mein invest karna. Jaise recurring deposit hota hai bank mein, waise hi SIP hota hai mutual fund mein. ₹500 per month se bhi shuruat kar sakte hain.",
        "hinglish": "SIP matlab har month ek fixed amount invest karna mutual fund mein. Jaise RD hoti hai bank mein, waise hi SIP hoti hai. ₹500/month se bhi start kar sakte ho. Time ke saath bahut grow hota hai."
    },
    "returns": {
        "en": "Returns means how much profit your investment has made. If you invested ₹1000 and it became ₹1200, your return is 20%. Returns can be positive (profit) or negative (loss).",
        "hi": "Returns ka matlab hai aapke investment ne kitna profit kamaya. Agar aapne ₹1000 lagaye aur woh ₹1200 ho gaye, toh aapka return 20% hai. Returns positive (profit) ya negative (loss) ho sakta hai.",
        "hinglish": "Returns matlab aapke paison ne kitna kamaya. ₹1000 invest kiya, ₹1200 ho gaye — toh 20% return mila. Positive bhi ho sakta hai (profit) aur negative bhi (loss)."
    },
    "mutual fund": {
        "en": "A mutual fund collects money from many investors and invests it in stocks, bonds, etc. A professional fund manager handles everything. You don't need to pick stocks yourself.",
        "hi": "Mutual fund bahut saare logon se paisa collect karta hai aur usse stocks, bonds mein invest karta hai. Ek professional fund manager sab handle karta hai. Aapko khud stocks choose nahi karne padte.",
        "hinglish": "Mutual fund matlab — bahut log milke paisa dete hain, aur ek expert fund manager usse stocks-bonds mein lagata hai. Aapko khud kuch choose nahi karna — sab manager dekhta hai."
    },
    "expense ratio": {
        "en": "Expense ratio is the annual fee charged by the fund for managing your money. If it's 1%, and you invest ₹10,000, ₹100/year goes as fees. Lower expense ratio = more money stays with you.",
        "hi": "Expense ratio woh annual fee hai jo fund aapke paisa manage karne ke liye charge karta hai. Agar 1% hai aur aapne ₹10,000 invest kiye, toh ₹100 per year fees jaati hai. Kam expense ratio = zyada paisa aapke paas.",
        "hinglish": "Expense ratio ek annual fee hai jo fund charge karta hai paisa manage karne ke liye. 1% ratio + ₹10,000 investment = ₹100/year fees. Jitna kam ratio, utna zyada paisa aapka."
    },
    "aum": {
        "en": "AUM (Assets Under Management) is the total money managed by a fund. A fund with ₹50,000 crore AUM means investors have put that much money in it. Higher AUM generally means more trust.",
        "hi": "AUM (Assets Under Management) ka matlab hai fund ke paas total kitna paisa hai manage karne ke liye. Agar ₹50,000 crore AUM hai toh investors ne utna paisa lagaya hai. Zyada AUM matlab zyada bharosa.",
        "hinglish": "AUM means total paisa jo ek fund manage kar raha hai. ₹50,000 crore AUM matlab itne investors ne paisa lagaya hai. Zyada AUM = zyada log trust karte hain."
    },
    "cagr": {
        "en": "CAGR (Compound Annual Growth Rate) shows the average yearly return of your investment. If CAGR is 12%, it means your money grew by ~12% every year on average.",
        "hi": "CAGR (Compound Annual Growth Rate) aapke investment ka average yearly return batata hai. Agar CAGR 12% hai, toh aapka paisa har saal average mein ~12% badha.",
        "hinglish": "CAGR matlab average yearly growth rate. Agar CAGR 12% hai toh har saal average mein aapka paisa ~12% badha. Investment compare karne ke liye bahut useful hai."
    },
    "exit load": {
        "en": "Exit load is a penalty fee if you withdraw your money too early. Usually 1% if you redeem within 1 year. After that, no charge. It discourages short-term withdrawals.",
        "hi": "Exit load ek penalty fee hai agar aap apna paisa jaldi nikal lete hain. Usually 1% hota hai agar 1 saal ke andar nikalte hain. Uske baad koi charge nahi. Yeh jaldi paisa nikalne se rokta hai.",
        "hinglish": "Exit load matlab jaldi paisa nikalne ki penalty. Usually 1% charge hota hai agar 1 saal ke andar nikalte ho. 1 saal ke baad — free, koi charge nahi."
    },
    "elss": {
        "en": "ELSS (Equity Linked Savings Scheme) is a type of mutual fund that saves tax under Section 80C. You can save up to ₹46,800 in taxes per year. But money is locked for 3 years.",
        "hi": "ELSS (Equity Linked Savings Scheme) ek mutual fund hai jo Section 80C ke under tax bachata hai. Aap ₹46,800 tak tax bacha sakte hain per year. Lekin paisa 3 saal ke liye lock rehta hai.",
        "hinglish": "ELSS ek tax-saving mutual fund hai. Section 80C ke under ₹46,800 tak tax bacha sakte ho. Bas ek catch — paisa 3 saal lock rehta hai. Tax + returns dono milte hain."
    },
    "large cap": {
        "en": "Large cap funds invest in big, well-established companies like Reliance, TCS, HDFC. They are safer but give moderate returns. Good for beginners and conservative investors.",
        "hi": "Large cap funds badi aur established companies jaise Reliance, TCS, HDFC mein invest karte hain. Yeh safe hote hain lekin returns moderate milte hain. Beginners ke liye accha hai.",
        "hinglish": "Large cap = badi companies mein invest. Reliance, TCS, HDFC jaise. Safe hota hai, returns moderate milte hain. Agar naye ho investing mein toh yahi se shuru karo."
    },
    "small cap": {
        "en": "Small cap funds invest in small companies with high growth potential. They can give very high returns but are also very risky. Suitable for long-term investors who can handle ups and downs.",
        "hi": "Small cap funds chhoti companies mein invest karte hain jinme bahut growth ho sakti hai. Bahut zyada return de sakte hain lekin risk bhi bahut hai. Long-term investors ke liye suitable hai jo ups-downs handle kar sakein.",
        "hinglish": "Small cap = chhoti companies mein paisa lagana. Risk zyada hai but returns bhi bahut zyada ho sakte hain. Long-term ke liye hi best hai — short-term mein bahut uthak-baithak hoti hai."
    }
}


def _resolve_term(term: str) -> str:
    """Resolve a Hindi/Hinglish/English term to its canonical English key"""
    term_lower = term.lower().strip()
    
    # Direct match
    if term_lower in TERM_EXPLANATIONS:
        return term_lower
    
    # Check aliases (Hindi / Hinglish / expanded forms)
    for alias, canonical in TERM_ALIASES.items():
        if alias in term_lower or term_lower in alias:
            return canonical
    
    # Partial match against known terms
    for key in TERM_EXPLANATIONS:
        if key in term_lower or term_lower in key:
            return key
    
    return term_lower


def _get_lang_key(language: str) -> str:
    """Map language code to dict key: en, hi, or hinglish"""
    lang = language.lower().strip()
    if lang in ("hi", "hinglish", "hi-in"):
        return "hi"
    if lang == "hinglish":
        return "hinglish"
    return "en"


async def explain_term_groq(term: str, language: str = "hi") -> Optional[str]:
    """Use Groq API (free) to explain a term"""
    if not GROQ_API_KEY:
        return None

    if language in ("hi", "hi-in", "hinglish"):
        lang_instruction = (
            "Respond in Hinglish (Hindi written in English/Roman script mixed with English). "
            "Keep it simple so a first-time investor can understand."
        )
    else:
        lang_instruction = (
            "Respond in simple English. Keep it simple so a first-time investor can understand."
        )

    # Resolve the term to English so the LLM understands it
    resolved = _resolve_term(term)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a friendly Indian mutual fund advisor. {lang_instruction} Use examples with Indian Rupees (₹). Keep response under 100 words."
                        },
                        {
                            "role": "user",
                            "content": f"Explain '{resolved}' in mutual funds in very simple language for someone who knows nothing about investing."
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
    except Exception:
        pass

    return None


async def get_explanation(term: str, language: str = "hi") -> dict:
    """Get explanation - tries Groq first, falls back to predefined"""
    resolved = _resolve_term(term)

    # Try Groq API first
    groq_explanation = await explain_term_groq(term, language)
    if groq_explanation:
        return {
            "success": True,
            "term": resolved,
            "explanation": groq_explanation,
            "source": "ai",
            "language": language
        }

    # Fallback to predefined
    lang_key = _get_lang_key(language)

    if resolved in TERM_EXPLANATIONS:
        explanations = TERM_EXPLANATIONS[resolved]
        # Try requested language, fall back to "en"
        explanation = explanations.get(lang_key) or explanations.get("en", "")
        return {
            "success": True,
            "term": resolved,
            "explanation": explanation,
            "source": "predefined",
            "language": language
        }

    # Partial match
    for key, value in TERM_EXPLANATIONS.items():
        if key in resolved or resolved in key:
            explanation = value.get(lang_key) or value.get("en", "")
            return {
                "success": True,
                "term": key,
                "explanation": explanation,
                "source": "predefined",
                "language": language
            }

    no_result_msg = {
        "en": f"No explanation available for '{term}'. Try terms like NAV, SIP, ELSS, etc.",
        "hi": f"'{term}' ki explanation abhi available nahi hai. NAV, SIP, ELSS jaise terms try karein.",
    }
    return {
        "success": False,
        "term": term,
        "message": no_result_msg.get(lang_key, no_result_msg["en"])
    }


def get_available_terms() -> list:
    """Return list of terms with predefined explanations"""
    return list(TERM_EXPLANATIONS.keys())
