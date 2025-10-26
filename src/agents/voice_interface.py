"""
Voice Interface - Voice Input/Output for Trading Commands
Handles speech-to-text, text-to-speech, and voice command processing.
"""

from typing import Dict, Any, Optional, Callable
import json
from datetime import datetime
from pathlib import Path

try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("[Voice] Voice libraries not available. Install with: pip install SpeechRecognition pyttsx3")

class VoiceInterface:
    """Handles voice input and output for trading commands."""
    
    def __init__(self, voice_enabled: bool = True):
        """
        Initialize voice interface.
        
        Args:
            voice_enabled: Enable actual voice I/O (False for testing)
        """
        self.voice_enabled = voice_enabled and VOICE_AVAILABLE
        self.is_listening = False
        
        # Initialize speech recognition
        if self.voice_enabled:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                
                # Initialize text-to-speech
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 180)  # Slightly slower
                self.tts_engine.setProperty('volume', 0.9)
                
                # Adjust for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("[Voice] Voice interface initialized successfully")
                
            except Exception as e:
                print(f"[Voice] Error initializing voice: {e}")
                self.voice_enabled = False
        else:
            self.recognizer = None
            self.microphone = None
            self.tts_engine = None
            print("[Voice] Voice interface disabled")
    
    def listen_for_command(self, timeout: float = 5.0, phrase_timeout: float = 1.0) -> Optional[str]:
        """
        Listen for a voice command.
        
        Args:
            timeout: Maximum time to wait for speech
            phrase_timeout: Time to wait after speech stops
            
        Returns:
            Recognized text or None if failed
        """
        if not self.voice_enabled:
            return self._mock_voice_input()
        
        try:
            print("[Voice] Listening for command...")
            self.is_listening = True
            
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            self.is_listening = False
            
            # Recognize speech using Google Web Speech API
            text = self.recognizer.recognize_google(audio)
            print(f"[Voice] Recognized: '{text}'")
            
            return text.strip()
            
        except sr.WaitTimeoutError:
            print("[Voice] Listening timeout - no speech detected")
            self.is_listening = False
            return None
            
        except sr.UnknownValueError:
            print("[Voice] Could not understand audio")
            self.is_listening = False
            return None
            
        except sr.RequestError as e:
            print(f"[Voice] Speech recognition error: {e}")
            self.is_listening = False
            return None
            
        except Exception as e:
            print(f"[Voice] Unexpected error during speech recognition: {e}")
            self.is_listening = False
            return None
    
    def speak_response(self, text: str, interrupt_listening: bool = True) -> bool:
        """
        Speak a text response.
        
        Args:
            text: Text to speak
            interrupt_listening: Stop listening while speaking
            
        Returns:
            True if successful, False otherwise
        """
        if not self.voice_enabled:
            print(f"[Voice] Would speak: '{text}'")
            return True
        
        try:
            if interrupt_listening:
                self.is_listening = False
            
            print(f"[Voice] Speaking: '{text}'")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            return True
            
        except Exception as e:
            print(f"[Voice] Error speaking: {e}")
            return False
    
    def _mock_voice_input(self) -> Optional[str]:
        """Mock voice input for testing when voice is disabled."""
        
        # Simulate some common trading commands for testing
        mock_commands = [
            "Generate low risk income from SPY this month",
            "Create a bullish strategy on Apple before earnings",
            "Set up protective puts for my QQQ position",
            "Build an iron condor on SPY with high probability",
            "Cancel listening",
            None  # Simulate timeout
        ]
        
        # For actual implementation, you might want to use input() for testing
        # return input("[Voice Mock] Enter command (or press Enter for timeout): ").strip() or None
        
        # Return None to simulate timeout in automated testing
        return None
    
    def start_continuous_listening(
        self, 
        command_callback: Callable[[str], None],
        wake_word: str = "trading assistant"
    ) -> None:
        """
        Start continuous listening mode with wake word detection.
        
        Args:
            command_callback: Function to call with recognized commands
            wake_word: Wake word to activate command listening
        """
        print(f"[Voice] Starting continuous listening for wake word: '{wake_word}'")
        
        while True:
            try:
                # Listen for wake word
                text = self.listen_for_command(timeout=10.0)
                
                if text and wake_word.lower() in text.lower():
                    self.speak_response("Yes, I'm listening. What's your trading command?")
                    
                    # Listen for actual command
                    command = self.listen_for_command(timeout=10.0)
                    
                    if command:
                        print(f"[Voice] Processing command: '{command}'")
                        command_callback(command)
                    else:
                        self.speak_response("I didn't catch that. Please try again.")
                
                elif text and "stop listening" in text.lower():
                    self.speak_response("Stopping voice assistant. Goodbye!")
                    break
                    
            except KeyboardInterrupt:
                print("\n[Voice] Stopping continuous listening")
                self.speak_response("Voice assistant stopped.")
                break
                
            except Exception as e:
                print(f"[Voice] Error in continuous listening: {e}")
    
    def configure_voice_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Configure voice settings.
        
        Args:
            settings: Dict with voice configuration
            
        Returns:
            True if successful
        """
        if not self.voice_enabled:
            return False
        
        try:
            if "rate" in settings:
                self.tts_engine.setProperty('rate', settings["rate"])
            
            if "volume" in settings:
                self.tts_engine.setProperty('volume', settings["volume"])
            
            if "voice" in settings:
                voices = self.tts_engine.getProperty('voices')
                if settings["voice"] < len(voices):
                    self.tts_engine.setProperty('voice', voices[settings["voice"]].id)
            
            print(f"[Voice] Settings updated: {settings}")
            return True
            
        except Exception as e:
            print(f"[Voice] Error updating settings: {e}")
            return False
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get information about voice capabilities."""
        
        info = {
            "voice_enabled": self.voice_enabled,
            "libraries_available": VOICE_AVAILABLE,
            "is_listening": self.is_listening
        }
        
        if self.voice_enabled and self.tts_engine:
            try:
                voices = self.tts_engine.getProperty('voices')
                info["available_voices"] = len(voices) if voices else 0
                info["current_rate"] = self.tts_engine.getProperty('rate')
                info["current_volume"] = self.tts_engine.getProperty('volume')
            except:
                info["tts_error"] = "Could not get TTS properties"
        
        return info
    
    def test_voice_system(self) -> Dict[str, bool]:
        """Test voice input and output capabilities."""
        
        results = {
            "speech_recognition": False,
            "text_to_speech": False,
            "microphone_access": False
        }
        
        if not self.voice_enabled:
            print("[Voice] Voice system disabled - skipping tests")
            return results
        
        # Test text-to-speech
        try:
            self.speak_response("Testing voice output. Can you hear this?")
            results["text_to_speech"] = True
            print("[Voice] ✓ Text-to-speech working")
        except Exception as e:
            print(f"[Voice] ✗ Text-to-speech failed: {e}")
        
        # Test microphone access
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            results["microphone_access"] = True
            print("[Voice] ✓ Microphone access working")
        except Exception as e:
            print(f"[Voice] ✗ Microphone access failed: {e}")
        
        # Test speech recognition
        try:
            self.speak_response("Please say 'test command' to test speech recognition")
            text = self.listen_for_command(timeout=5.0)
            if text:
                results["speech_recognition"] = True
                print(f"[Voice] ✓ Speech recognition working: '{text}'")
            else:
                print("[Voice] ✗ Speech recognition timeout")
        except Exception as e:
            print(f"[Voice] ✗ Speech recognition failed: {e}")
        
        return results


class VoiceCommandProcessor:
    """Processes voice commands and integrates with trading agent."""
    
    def __init__(self, trading_agent_callback: Callable[[str], Dict[str, Any]]):
        """
        Initialize command processor.
        
        Args:
            trading_agent_callback: Function to process trading commands
        """
        self.voice_interface = VoiceInterface()
        self.trading_callback = trading_agent_callback
        self.command_history: List[Dict[str, Any]] = []
        
    def process_voice_command(self, command_text: str) -> Dict[str, Any]:
        """
        Process a voice command through the trading agent.
        
        Args:
            command_text: Recognized voice command
            
        Returns:
            Result from trading agent
        """
        print(f"[VoiceProcessor] Processing: '{command_text}'")
        
        # Log command
        command_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command_text,
            "source": "voice"
        }
        
        try:
            # Process through trading agent
            result = self.trading_callback(command_text)
            
            command_entry["result"] = "success"
            command_entry["response"] = result
            
            # Speak the response
            if result.get("explanation"):
                self.voice_interface.speak_response(result["explanation"])
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing command: {e}"
            command_entry["result"] = "error"
            command_entry["error"] = str(e)
            
            self.voice_interface.speak_response(f"Sorry, I encountered an error: {e}")
            
            return {"error": error_msg}
            
        finally:
            self.command_history.append(command_entry)
    
    def start_voice_assistant(self, wake_word: str = "trading assistant") -> None:
        """Start the voice assistant in continuous listening mode."""
        
        print(f"[VoiceProcessor] Starting voice assistant with wake word: '{wake_word}'")
        
        # Test voice system first
        test_results = self.voice_interface.test_voice_system()
        if not any(test_results.values()):
            print("[VoiceProcessor] Voice system tests failed - continuing with text mode")
        
        def handle_command(command: str):
            """Handle voice command callback."""
            self.process_voice_command(command)
        
        try:
            self.voice_interface.start_continuous_listening(
                command_callback=handle_command,
                wake_word=wake_word
            )
        except KeyboardInterrupt:
            print("\n[VoiceProcessor] Voice assistant stopped by user")
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history."""
        return self.command_history[-limit:] if self.command_history else []


# Convenience functions
def create_voice_interface(voice_enabled: bool = True) -> VoiceInterface:
    """Create a voice interface instance."""
    return VoiceInterface(voice_enabled)

def create_voice_processor(trading_callback: Callable) -> VoiceCommandProcessor:
    """Create a voice command processor."""
    return VoiceCommandProcessor(trading_callback)