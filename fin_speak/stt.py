"""
Speech-to-Text (STT) module
Handles audio transcription using Whisper or OpenAI API
"""

import os
from typing import Optional
import warnings

from .config import Config

# Suppress warnings
warnings.filterwarnings("ignore")


def transcribe_local(audio_path: str) -> str:
    """
    Transcribe audio using local Whisper model
    
    Args:
        audio_path: Path to audio file (wav, mp3, etc.)
        
    Returns:
        Transcribed text
    """
    try:
        import whisper
        import torch
        
        # Load model (cached after first load)
        model_name = Config.get_whisper_model_name()
        if Config.DEBUG:
            print(f"Loading Whisper model: {model_name}")
        
        model = whisper.load_model(model_name)
        
        # Transcribe
        result = model.transcribe(audio_path, fp16=torch.cuda.is_available())
        
        return result["text"].strip()
        
    except ImportError as e:
        raise ImportError(
            "Whisper is not installed. Install with: pip install openai-whisper"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error transcribing audio with Whisper: {e}") from e


def transcribe_openai(audio_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Transcribed text
    """
    try:
        from openai import OpenAI
        
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found in configuration")
        
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        return transcript.text.strip()
        
    except ImportError as e:
        raise ImportError(
            "OpenAI library is not installed. Install with: pip install openai"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error transcribing audio with OpenAI API: {e}") from e


def transcribe(audio_path: str, force_local: bool = False) -> str:
    """
    Transcribe audio using the configured backend (local or OpenAI)
    
    Args:
        audio_path: Path to audio file
        force_local: Force use of local model even if OpenAI is configured
        
    Returns:
        Transcribed text
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Choose backend
    use_openai = Config.use_openai_stt() and not force_local
    
    if Config.DEBUG:
        backend = "OpenAI API" if use_openai else "Local Whisper"
        print(f"Using STT backend: {backend}")
    
    try:
        if use_openai:
            return transcribe_openai(audio_path)
        else:
            return transcribe_local(audio_path)
    except Exception as e:
        # Fallback to the other method if one fails
        if use_openai:
            if Config.DEBUG:
                print(f"OpenAI STT failed, falling back to local: {e}")
            return transcribe_local(audio_path)
        else:
            if Config.use_openai_stt():
                if Config.DEBUG:
                    print(f"Local STT failed, falling back to OpenAI: {e}")
                return transcribe_openai(audio_path)
            else:
                raise


def preprocess_audio(audio_path: str, output_path: Optional[str] = None) -> str:
    """
    Preprocess audio file (convert to 16kHz mono WAV)
    
    Args:
        audio_path: Path to input audio file
        output_path: Path to output file (optional)
        
    Returns:
        Path to preprocessed audio file
    """
    try:
        import librosa
        import soundfile as sf
        
        # Load audio
        audio, sr = librosa.load(audio_path, sr=Config.SAMPLE_RATE, mono=True)
        
        # Determine output path
        if output_path is None:
            base, _ = os.path.splitext(audio_path)
            output_path = f"{base}_processed.wav"
        
        # Save preprocessed audio
        sf.write(output_path, audio, Config.SAMPLE_RATE)
        
        return output_path
        
    except ImportError as e:
        # If preprocessing libraries not available, return original path
        if Config.DEBUG:
            print(f"Audio preprocessing skipped: {e}")
        return audio_path
    except Exception as e:
        if Config.DEBUG:
            print(f"Error preprocessing audio: {e}")
        return audio_path
