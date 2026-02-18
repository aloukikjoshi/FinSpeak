"""
Text-to-Speech (TTS) module
Handles speech synthesis from text
"""

import os
from typing import Optional

from .config import Config


def synthesize_gtts(text: str, output_path: str) -> None:
    """
    Synthesize speech using gTTS (Google Text-to-Speech)
    
    Args:
        text: Text to synthesize
        output_path: Path to save audio file
    """
    try:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_path)
        
        if Config.DEBUG:
            print(f"Audio saved using gTTS: {output_path}")
            
    except ImportError as e:
        raise ImportError(
            "gTTS is not installed. Install with: pip install gTTS"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error synthesizing speech with gTTS: {e}") from e


def synthesize_pyttsx3(text: str, output_path: str) -> None:
    """
    Synthesize speech using pyttsx3 (offline TTS)
    
    Args:
        text: Text to synthesize
        output_path: Path to save audio file
    """
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', 150)  # Speed
        engine.setProperty('volume', 0.9)  # Volume
        
        # Save to file
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        if Config.DEBUG:
            print(f"Audio saved using pyttsx3: {output_path}")
            
    except ImportError as e:
        raise ImportError(
            "pyttsx3 is not installed. Install with: pip install pyttsx3"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error synthesizing speech with pyttsx3: {e}") from e


def synthesize_text(text: str, output_path: str, backend: Optional[str] = None) -> str:
    """
    Synthesize text to speech using configured backend
    
    Args:
        text: Text to synthesize
        output_path: Path to save audio file
        backend: TTS backend to use ('gtts' or 'pyttsx3'), or None for config default
        
    Returns:
        Path to generated audio file
    """
    if backend is None:
        backend = Config.TTS_BACKEND
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        if backend == "gtts":
            synthesize_gtts(text, output_path)
        elif backend == "pyttsx3":
            synthesize_pyttsx3(text, output_path)
        else:
            raise ValueError(f"Unknown TTS backend: {backend}")
        
        return output_path
        
    except Exception as e:
        # Try fallback backend
        if Config.DEBUG:
            print(f"Primary TTS backend failed: {e}")
        
        fallback = "pyttsx3" if backend == "gtts" else "gtts"
        
        if Config.DEBUG:
            print(f"Trying fallback TTS backend: {fallback}")
        
        try:
            if fallback == "gtts":
                synthesize_gtts(text, output_path)
            else:
                synthesize_pyttsx3(text, output_path)
            return output_path
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both TTS backends failed. Primary: {e}, Fallback: {fallback_error}"
            ) from fallback_error


def get_audio_bytes(audio_path: str) -> bytes:
    """
    Read audio file as bytes for playback
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Audio data as bytes
    """
    with open(audio_path, 'rb') as f:
        return f.read()
