# voice/__init__.py
"""
Voice Interface Stubs
Placeholder implementations for speech recognition and text-to-speech.
"""

from .transcriber_stub import (
    transcribe_from_microphone, 
    transcribe_text, 
    is_voice_available, 
    get_voice_status
)
from .tts_stub import (
    speak, 
    speak_status, 
    speak_plan_summary, 
    speak_validation_result,
    is_tts_available, 
    get_tts_status, 
    configure_voice, 
    test_voice
)

__all__ = [
    "transcribe_from_microphone",
    "transcribe_text", 
    "is_voice_available",
    "get_voice_status",
    "speak",
    "speak_status",
    "speak_plan_summary", 
    "speak_validation_result",
    "is_tts_available",
    "get_tts_status",
    "configure_voice",
    "test_voice"
]