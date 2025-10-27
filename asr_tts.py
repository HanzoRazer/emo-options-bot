"""
Phase 3 ASR/TTS - Voice interface for speech recognition and text-to-speech
Provides voice input/output capabilities with graceful degradation
"""

from __future__ import annotations
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Check for audio capabilities
HAS_AUDIO = False
try:
    # In a real implementation, would check for:
    # import speech_recognition as sr
    # import pyttsx3
    # or other audio libraries
    HAS_AUDIO = False  # Set to False for development/testing
except ImportError:
    HAS_AUDIO = False

# Import schemas if available
try:
    from schemas import VoiceCommand, VoiceResponse
except ImportError:
    VoiceCommand = Dict[str, Any]
    VoiceResponse = Dict[str, Any]


class MockASRProvider:
    """Mock ASR provider for testing without audio hardware"""
    
    def __init__(self):
        self.is_listening = False
        self.recognition_count = 0
    
    def listen(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Mock speech recognition"""
        self.recognition_count += 1
        
        # Simulate different voice commands
        mock_commands = [
            "Buy SPY iron condor with max risk 500 dollars",
            "Show me QQQ put credit spread analysis", 
            "What's the current portfolio risk",
            "Cancel order 12345",
            "Set risk limit to 2 percent"
        ]
        
        command_text = mock_commands[self.recognition_count % len(mock_commands)]
        
        return {
            "text": command_text,
            "confidence": 0.85,
            "timestamp": datetime.now(),
            "mock": True
        }
    
    def start_listening(self) -> bool:
        """Start continuous listening mode"""
        self.is_listening = True
        return True
    
    def stop_listening(self) -> bool:
        """Stop listening mode"""
        self.is_listening = False
        return True


class MockTTSProvider:
    """Mock TTS provider for testing without audio hardware"""
    
    def __init__(self):
        self.voice_settings = {
            "rate": 200,
            "volume": 0.9,
            "voice_id": "default"
        }
        self.speech_count = 0
    
    def speak(self, text: str) -> Dict[str, Any]:
        """Mock text-to-speech"""
        self.speech_count += 1
        
        # In real implementation, would generate audio
        print(f"🗣️ TTS: {text}")
        
        return {
            "text": text,
            "audio_url": None,  # Would be actual audio file/stream
            "duration": len(text) * 0.1,  # Mock duration
            "timestamp": datetime.now(),
            "mock": True
        }
    
    def set_voice(self, voice_id: str) -> bool:
        """Set TTS voice"""
        self.voice_settings["voice_id"] = voice_id
        return True
    
    def set_rate(self, rate: int) -> bool:
        """Set speech rate"""
        self.voice_settings["rate"] = rate
        return True


class VoiceInterface:
    """Main voice interface combining ASR and TTS"""
    
    def __init__(self, enable_asr: bool = True, enable_tts: bool = True):
        """Initialize voice interface"""
        self.asr_enabled = enable_asr and (HAS_AUDIO or os.getenv("VOICE_MODE") == "mock")
        self.tts_enabled = enable_tts and (HAS_AUDIO or os.getenv("VOICE_MODE") == "mock")
        
        # Initialize providers
        if self.asr_enabled:
            if HAS_AUDIO:
                # Would initialize real ASR provider
                self.asr = MockASRProvider()  # Fallback for now
            else:
                self.asr = MockASRProvider()
        else:
            self.asr = None
        
        if self.tts_enabled:
            if HAS_AUDIO:
                # Would initialize real TTS provider
                self.tts = MockTTSProvider()  # Fallback for now
            else:
                self.tts = MockTTSProvider()
        else:
            self.tts = None
        
        self.session_active = False
    
    def listen_for_command(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Listen for voice command"""
        if not self.asr_enabled or not self.asr:
            return {
                "error": "ASR not available",
                "text": "",
                "confidence": 0.0,
                "timestamp": datetime.now()
            }
        
        try:
            result = self.asr.listen(timeout)
            return result
        except Exception as e:
            return {
                "error": str(e),
                "text": "",
                "confidence": 0.0,
                "timestamp": datetime.now()
            }
    
    def speak_response(self, text: str) -> Dict[str, Any]:
        """Convert text to speech"""
        if not self.tts_enabled or not self.tts:
            # Fallback to text output
            print(f"📢 Response: {text}")
            return {
                "text": text,
                "audio_url": None,
                "timestamp": datetime.now(),
                "fallback": True
            }
        
        try:
            result = self.tts.speak(text)
            return result
        except Exception as e:
            print(f"📢 Response (TTS Error): {text}")
            return {
                "text": text,
                "audio_url": None,
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    def start_voice_session(self) -> bool:
        """Start interactive voice session"""
        if not self.asr_enabled:
            print("ℹ️ Voice input not available, continuing in text mode")
            return False
        
        try:
            self.session_active = True
            if self.asr:
                self.asr.start_listening()
            return True
        except Exception as e:
            print(f"❌ Failed to start voice session: {e}")
            return False
    
    def stop_voice_session(self) -> bool:
        """Stop voice session"""
        try:
            self.session_active = False
            if self.asr:
                self.asr.stop_listening()
            return True
        except Exception as e:
            print(f"❌ Failed to stop voice session: {e}")
            return False
    
    def process_voice_interaction(self, user_input: str = None) -> Dict[str, Any]:
        """Complete voice interaction cycle"""
        # Step 1: Get input (voice or text)
        if user_input is None and self.asr_enabled:
            print("🎤 Listening for command...")
            command_result = self.listen_for_command()
            if "error" in command_result:
                return command_result
            user_input = command_result.get("text", "")
        elif user_input is None:
            return {"error": "No input provided and ASR not available"}
        
        # Step 2: Process command (would integrate with orchestrator)
        response_text = f"I heard: '{user_input}'. Processing your request..."
        
        # Step 3: Speak response
        speech_result = self.speak_response(response_text)
        
        return {
            "input_text": user_input,
            "response_text": response_text,
            "speech_result": speech_result,
            "timestamp": datetime.now()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check voice interface health"""
        return {
            "status": "healthy",
            "asr_enabled": self.asr_enabled,
            "tts_enabled": self.tts_enabled,
            "has_audio": HAS_AUDIO,
            "session_active": self.session_active,
            "asr_provider": type(self.asr).__name__ if self.asr else None,
            "tts_provider": type(self.tts).__name__ if self.tts else None
        }


# Convenience functions
def create_voice_interface(mock_mode: bool = True) -> VoiceInterface:
    """Create voice interface with appropriate configuration"""
    if mock_mode:
        os.environ["VOICE_MODE"] = "mock"
    
    return VoiceInterface()


def speak(text: str) -> None:
    """Quick text-to-speech function"""
    interface = create_voice_interface()
    interface.speak_response(text)


def listen() -> str:
    """Quick speech-to-text function"""
    interface = create_voice_interface()
    result = interface.listen_for_command()
    return result.get("text", "")


# Example usage and testing
if __name__ == "__main__":
    print("🎤 Testing Phase 3 Voice Interface")
    
    # Test voice interface
    voice = create_voice_interface(mock_mode=True)
    print(f"✅ Voice interface created")
    
    # Health check
    health = voice.health_check()
    print(f"Health: {health['status']}")
    print(f"ASR enabled: {health['asr_enabled']}")
    print(f"TTS enabled: {health['tts_enabled']}")
    
    # Test voice interaction
    print("\n🎯 Testing voice interaction...")
    
    # Test 1: Mock listening
    if voice.asr_enabled:
        command = voice.listen_for_command()
        print(f"Heard: '{command.get('text', '')}' (confidence: {command.get('confidence', 0):.2f})")
    
    # Test 2: Text-to-speech
    voice.speak_response("Welcome to EMO Options Bot Phase 3 voice interface")
    
    # Test 3: Complete interaction
    interaction = voice.process_voice_interaction("Show me SPY iron condor analysis")
    print(f"Interaction completed: {interaction.get('response_text', '')}")
    
    # Test 4: Voice session
    print("\n🎯 Testing voice session...")
    session_started = voice.start_voice_session()
    print(f"Session started: {session_started}")
    
    if session_started:
        voice.stop_voice_session()
        print("Session stopped")
    
    print("\n🎤 Voice interface testing complete")