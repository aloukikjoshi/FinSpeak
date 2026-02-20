"""
FastAPI backend for FinSpeak
Serverless function for Vercel deployment
"""

import os
import sys
import base64
import tempfile
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fin_speak.nlp import detect_intent_rule_based, extract_fund
from fin_speak.kb import query_nav, query_returns, search_fund
from fin_speak.education import get_explanation, get_available_terms
from fin_speak.config import Config

app = FastAPI(title="FinSpeak API", version="1.0.0")

# Static files for local development
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
if os.path.exists(PUBLIC_DIR):
    app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    text: str
    language: str = "en"
    
    
class SearchRequest(BaseModel):
    query: str


class AudioRequest(BaseModel):
    audio_base64: str


class ExplainRequest(BaseModel):
    term: str
    language: str = "hi"


class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    

@app.get("/")
async def root():
    # Serve index.html for local development
    index_path = os.path.join(PUBLIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"status": "ok", "service": "FinSpeak API"}


@app.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(PUBLIC_DIR, "style.css"), media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(os.path.join(PUBLIC_DIR, "app.js"), media_type="application/javascript")


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/query")
async def process_query(request: QueryRequest):
    """Process a text query about mutual funds (English + Hindi + Hinglish)"""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty query")
    
    language = request.language or "en"
    
    # Detect intent (now understands Hindi/Hinglish too)
    intent_result = detect_intent_rule_based(text)
    intent = intent_result.get("intent", "unknown")
    period = intent_result.get("period_months", 12)
    
    # ── If user is asking "what is X?" → route to Learn Mode ──
    if intent == "explain_term":
        term = intent_result.get("term", text)
        result = await get_explanation(term, language)
        return {
            "success": result.get("success", False),
            "intent": "explain",
            "answer": result.get("explanation") or result.get("message", ""),
            "data": {
                "term": result.get("term", term),
                "source": result.get("source", ""),
            }
        }
    
    # Extract fund name
    fund_name = extract_fund(text)
    
    if not fund_name:
        # Helpful error in the user's language
        msg = (
            "Fund ka naam samajh nahi aaya. Kripya fund ka naam likhein, jaise 'HDFC Equity Fund NAV batao'"
            if language in ("hi", "hi-in") else
            "Could not identify a fund name in your query. Try something like 'NAV of HDFC Equity Fund'"
        )
        return {
            "success": False,
            "message": msg,
            "intent": intent
        }
    
    # Process based on intent
    if intent == "get_nav":
        result = await query_nav(fund_name)
        if result.get("success"):
            if language in ("hi", "hi-in"):
                answer = f"{result['fund_name']} ka current NAV ₹{result['nav']} hai ({result['date']})."
            else:
                answer = f"The current NAV of {result['fund_name']} is ₹{result['nav']} as of {result['date']}."
            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result
            }
        return {"success": False, "message": result.get("error", "Failed to get NAV")}
    
    elif intent == "get_return":
        result = await query_returns(fund_name, period or 12)
        if result.get("success"):
            if language in ("hi", "hi-in"):
                answer = f"{result['fund_name']} ne last {result['period_months']} months mein {result['returns_percent']}% return diya hai."
            else:
                answer = f"{result['fund_name']} has given {result['returns_percent']}% returns over the last {result['period_months']} months."
            return {
                "success": True,
                "intent": intent,
                "answer": answer,
                "data": result
            }
        return {"success": False, "message": result.get("error", "Failed to get returns")}
    
    else:
        # Default to NAV query
        result = await query_nav(fund_name)
        if result.get("success"):
            if language in ("hi", "hi-in"):
                answer = f"{result['fund_name']} ka current NAV ₹{result['nav']} hai ({result['date']})."
            else:
                answer = f"The current NAV of {result['fund_name']} is ₹{result['nav']} as of {result['date']}."
            return {
                "success": True,
                "intent": "get_nav",
                "answer": answer,
                "data": result
            }
        return {"success": False, "message": result.get("error", "Query failed")}


@app.post("/api/search")
async def search_funds(request: SearchRequest):
    """Search for mutual funds by name"""
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Empty search query")
    
    result = await search_fund(query)
    return result


@app.post("/api/transcribe")
async def transcribe_audio(request: AudioRequest):
    """Transcribe audio using Azure Speech"""
    if not Config.AZURE_SPEECH_KEY or not Config.AZURE_SPEECH_REGION:
        raise HTTPException(status_code=500, detail="Azure Speech not configured")
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio_base64)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            # Transcribe
            speech_config = speechsdk.SpeechConfig(
                subscription=Config.AZURE_SPEECH_KEY,
                region=Config.AZURE_SPEECH_REGION
            )
            audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            result = recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {"success": True, "text": result.text.strip()}
            else:
                return {"success": False, "message": "Could not recognize speech"}
        finally:
            os.unlink(temp_path)
            
    except ImportError:
        raise HTTPException(status_code=500, detail="Azure Speech SDK not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """Get client-side configuration"""
    return {
        "azure_configured": Config.validate(),
        "azure_region": Config.AZURE_SPEECH_REGION if Config.validate() else None,
        "groq_configured": bool(Config.GROQ_API_KEY),
        "supported_languages": [
            {"code": "en-IN", "name": "English", "flag": "🇬🇧"},
            {"code": "hi-IN", "name": "Hindi", "flag": "🇮🇳"},
            {"code": "ta-IN", "name": "Tamil", "flag": "🇮🇳"},
            {"code": "te-IN", "name": "Telugu", "flag": "🇮🇳"},
            {"code": "bn-IN", "name": "Bengali", "flag": "🇮🇳"},
            {"code": "mr-IN", "name": "Marathi", "flag": "🇮🇳"},
            {"code": "gu-IN", "name": "Gujarati", "flag": "🇮🇳"},
            {"code": "kn-IN", "name": "Kannada", "flag": "🇮🇳"},
            {"code": "ml-IN", "name": "Malayalam", "flag": "🇮🇳"}
        ]
    }


@app.post("/api/explain")
async def explain_term(request: ExplainRequest):
    """Explain a financial term in simple language"""
    term = request.term.strip()
    if not term:
        raise HTTPException(status_code=400, detail="Empty term")
    
    result = await get_explanation(term, request.language)
    return result


@app.get("/api/terms")
async def list_terms():
    """List available financial terms for education"""
    return {"terms": get_available_terms()}


@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using Azure Neural Voices"""
    if not Config.AZURE_SPEECH_KEY or not Config.AZURE_SPEECH_REGION:
        return {"success": False, "message": "Azure TTS not configured", "use_browser": True}
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        speech_config = speechsdk.SpeechConfig(
            subscription=Config.AZURE_SPEECH_KEY,
            region=Config.AZURE_SPEECH_REGION
        )
        
        # Select voice based on language
        if request.language.startswith("hi"):
            speech_config.speech_synthesis_voice_name = Config.TTS_VOICE_HI
        else:
            speech_config.speech_synthesis_voice_name = Config.TTS_VOICE_EN
        
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None  # output to stream
        )
        
        result = synthesizer.speak_text_async(request.text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_base64 = base64.b64encode(result.audio_data).decode("utf-8")
            return {
                "success": True,
                "audio_base64": audio_base64,
                "format": "mp3"
            }
        else:
            return {"success": False, "message": "TTS synthesis failed", "use_browser": True}
            
    except ImportError:
        return {"success": False, "message": "Azure Speech SDK not available", "use_browser": True}
    except Exception as e:
        return {"success": False, "message": str(e), "use_browser": True}
