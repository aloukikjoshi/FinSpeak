"""
Speech-to-Text (STT) module
Handles audio transcription using local Whisper or Azure Speech
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


def transcribe(audio_path: str) -> str:
    """
    Transcribe audio using the configured backend (priority: Azure -> Local)
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Transcribed text
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Build backend priority list
    backends = []
    if Config.use_azure_speech():
        backends.append('azure')
    backends.append('local')

    if Config.DEBUG:
        print(f"STT backend priority: {backends}")

    last_exc = None
    for backend in backends:
        try:
            if backend == 'azure':
                return transcribe_azure(audio_path)
            if backend == 'local':
                return transcribe_local(audio_path)
        except Exception as e:
            last_exc = e
            if Config.DEBUG:
                print(f"Backend {backend} failed: {e}")
            continue

    # If we exhausted all backends, raise the last error
    if last_exc:
        raise last_exc
    else:
        raise RuntimeError("No STT backend available")


def transcribe_azure(audio_path: str) -> str:
    """
    Transcribe audio using Azure Cognitive Services Speech SDK (from file)
    """
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError as e:
        raise ImportError("Azure Speech SDK not installed. Install with: pip install azure-cognitiveservices-speech") from e

    if not Config.AZURE_SPEECH_KEY or not Config.AZURE_SPEECH_REGION:
        raise ValueError("Azure Speech credentials not found in configuration")

    speech_config = speechsdk.SpeechConfig(subscription=Config.AZURE_SPEECH_KEY, region=Config.AZURE_SPEECH_REGION)
    audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text.strip()
    else:
        raise RuntimeError(f"Azure STT failed: {result.reason}")


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
