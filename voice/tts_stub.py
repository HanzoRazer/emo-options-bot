# voice/tts_stub.py
import datetime

def speak(text: str, voice_enabled: bool = True):
    """
    Stub text-to-speech that prints to console.
    In production, this would use actual TTS.
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    if voice_enabled:
        print(f"[TTS {timestamp}] 🔊 {text}")
    else:
        print(f"[TTS {timestamp}] (silent) {text}")

def speak_status(status_info: dict):
    """Speak system status information."""
    if status_info.get("ok", False):
        speak("System status is normal. All components operational.")
    else:
        issues = len(status_info.get("errors", []))
        speak(f"System has {issues} issue{'s' if issues != 1 else ''}. Check dashboard for details.")

def speak_plan_summary(plan):
    """Speak a trading plan summary."""
    if hasattr(plan, 'strategy') and hasattr(plan, 'symbol'):
        risk_text = f"with {plan.risk_level} risk" if hasattr(plan, 'risk_level') else ""
        speak(f"Created {plan.strategy.replace('_', ' ')} plan for {plan.symbol} {risk_text}")
    else:
        speak("Plan created successfully")

def speak_validation_result(validation):
    """Speak validation results."""
    if hasattr(validation, 'ok'):
        if validation.ok:
            warnings_count = len(validation.warnings) if hasattr(validation, 'warnings') else 0
            if warnings_count > 0:
                speak(f"Plan passed validation with {warnings_count} warning{'s' if warnings_count != 1 else ''}")
            else:
                speak("Plan passed all validation checks")
        else:
            errors_count = len(validation.errors) if hasattr(validation, 'errors') else 0
            speak(f"Plan failed validation with {errors_count} error{'s' if errors_count != 1 else ''}")
    else:
        speak("Validation completed")

def is_tts_available() -> bool:
    """Check if TTS is available (always False for stub)."""
    return False

def get_tts_status() -> dict:
    """Get TTS system status."""
    return {
        "available": False,
        "type": "stub", 
        "message": "Using stub TTS - replace with real text-to-speech implementation"
    }

def configure_voice(rate: int = 180, volume: float = 0.9):
    """Configure voice settings (stub - no actual effect)."""
    print(f"[TTS] (stub) Voice configured: rate={rate}, volume={volume}")

def test_voice():
    """Test the voice system."""
    speak("Testing voice system. This is a test message.")
    return get_tts_status()