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


def synthesize_azure(text: str, output_path: str) -> None:
    """
    Synthesize speech using Azure Cognitive Services Speech SDK
    """
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError as e:
        raise ImportError("Azure Speech SDK not installed. Install with: pip install azure-cognitiveservices-speech") from e

    if not Config.AZURE_SPEECH_KEY or not Config.AZURE_SPEECH_REGION:
        raise ValueError("Azure Speech credentials not found in configuration")

    speech_config = speechsdk.SpeechConfig(subscription=Config.AZURE_SPEECH_KEY, region=Config.AZURE_SPEECH_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text(text)
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"Azure TTS failed: {result.reason}")


def synthesize_text(text: str, output_path: str, backend: Optional[str] = None) -> str:
    """
    Synthesize text to speech using configured backend
    
    Args:
        text: Text to synthesize
        output_path: Path to save audio file
        backend: TTS backend to use ('gtts', 'pyttsx3' or 'azure'), or None for config default
        
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
        elif backend == "azure":
            synthesize_azure(text, output_path)
        else:
            raise ValueError(f"Unknown TTS backend: {backend}")
        
        return output_path
        
    except Exception as e:
        # Try fallback backend
        if Config.DEBUG:
            print(f"Primary TTS backend failed: {e}")
        
        # Choose fallback order (prefer offline gTTS/pyttsx3)
        fallbacks = [b for b in ["pyttsx3", "gtts"] if b != backend]
        
        for fb in fallbacks:
            try:
                if fb == "gtts":
                    synthesize_gtts(text, output_path)
                else:
                    synthesize_pyttsx3(text, output_path)
                return output_path
            except Exception:
                if Config.DEBUG:
                    print(f"Fallback {fb} failed")
                continue
        
        raise RuntimeError(f"All TTS backends failed. Primary error: {e}")


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
