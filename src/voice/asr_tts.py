from __future__ import annotations
import os

class VoiceIO:
    """Simple stub that degrades gracefully.
    In real use: install SpeechRecognition/pyttsx3/pyaudio and wire them here."""
    def __init__(self):
        self.enabled = os.getenv("EMO_VOICE","0") == "1"
        self.lang = os.getenv("EMO_LANG","en")

    def listen(self) -> str:
        if not self.enabled:
            return ""
        # Placeholder: would capture mic, run ASR
        return ""

    def speak(self, text: str):
        if not self.enabled:
            return
        # Placeholder: would call TTS engine
        print(f"[TTS:{self.lang}] {text}")