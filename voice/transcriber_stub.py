# voice/transcriber_stub.py
# placeholder "ASR" that just forwards text; swap with real STT later
import random

def transcribe_from_microphone(timeout_sec: int = 10) -> str:
    """
    Stub transcriber that returns sample commands for testing.
    In production, this would use actual speech recognition.
    """
    print(f"[voice] (stub) Listening for {timeout_sec} seconds...")
    
    # Sample commands for testing
    sample_commands = [
        "Build an iron condor on SPY with 7 DTE and wings 5",
        "Create a put credit spread on QQQ with low risk",
        "Set up a covered call on AAPL with moderate risk",
        "Build a protective put on TSLA",
        "Make an iron condor on NVDA with 14 DTE",
        "Create a call credit spread on SPY with high risk",
        "What's the status of my positions",
        "Diagnose my current portfolio"
    ]
    
    # Return a random sample command
    command = random.choice(sample_commands)
    print(f"[voice] (stub) Simulated transcription: '{command}'")
    return command

def transcribe_text(text_input: str = None) -> str:
    """
    Alternative transcriber that uses text input for testing.
    """
    if text_input:
        print(f"[voice] (stub) Processing text input: '{text_input}'")
        return text_input
    else:
        return transcribe_from_microphone()

def is_voice_available() -> bool:
    """Check if voice recognition is available (always False for stub)."""
    return False

def get_voice_status() -> dict:
    """Get voice system status."""
    return {
        "available": False,
        "type": "stub",
        "message": "Using stub transcriber - replace with real STT implementation"
    }