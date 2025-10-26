# src/voice/asr_tts.py
"""
Enhanced Voice Interface for EMO Options Bot
Production-ready with multiple provider support, fallbacks, and robust error handling
"""
from __future__ import annotations
import os
import logging
import threading
import time
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import queue

# Configure logging
logger = logging.getLogger(__name__)

# Provider availability detection
_PROVIDERS_AVAILABLE = {
    "speech_recognition": False,
    "pyttsx3": False,
    "azure_speech": False,
    "google_speech": False
}

# Speech Recognition detection
try:
    import speech_recognition as sr
    _PROVIDERS_AVAILABLE["speech_recognition"] = True
    logger.info("Speech Recognition library available")
except ImportError:
    logger.info("Speech Recognition not available (pip install SpeechRecognition)")
except Exception as e:
    logger.warning(f"Speech Recognition initialization failed: {e}")

# Text-to-Speech detection
try:
    import pyttsx3
    _PROVIDERS_AVAILABLE["pyttsx3"] = True
    logger.info("pyttsx3 TTS library available")
except ImportError:
    logger.info("pyttsx3 not available (pip install pyttsx3)")
except Exception as e:
    logger.warning(f"pyttsx3 initialization failed: {e}")

# Azure Speech Services detection
try:
    import azure.cognitiveservices.speech as speechsdk
    if os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION"):
        _PROVIDERS_AVAILABLE["azure_speech"] = True
        logger.info("Azure Speech Services available")
except ImportError:
    logger.info("Azure Speech SDK not available")
except Exception as e:
    logger.warning(f"Azure Speech initialization failed: {e}")

# Google Cloud Speech detection
try:
    from google.cloud import speech as google_speech
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        _PROVIDERS_AVAILABLE["google_speech"] = True
        logger.info("Google Cloud Speech available")
except ImportError:
    logger.info("Google Cloud Speech not available")
except Exception as e:
    logger.warning(f"Google Cloud Speech initialization failed: {e}")

class VoiceProvider:
    """Base class for voice providers"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.usage_count = 0
        self.error_count = 0
        self.last_used = None
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return _PROVIDERS_AVAILABLE.get(self.provider_name, False)
    
    def transcribe(self, audio_data: Any, **kwargs) -> Optional[str]:
        """Transcribe audio to text - to be implemented by subclasses"""
        raise NotImplementedError
    
    def speak(self, text: str, **kwargs) -> bool:
        """Convert text to speech - to be implemented by subclasses"""
        raise NotImplementedError
    
    def track_usage(self, success: bool = True):
        """Track usage statistics"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        if not success:
            self.error_count += 1

class BasicSpeechProvider(VoiceProvider):
    """Basic speech recognition using speech_recognition library"""
    
    def __init__(self):
        super().__init__("speech_recognition")
        self.recognizer = None
        if self.is_available():
            try:
                self.recognizer = sr.Recognizer()
                # Optimize recognizer settings
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                self.recognizer.phrase_threshold = 0.3
            except Exception as e:
                logger.error(f"Failed to initialize speech recognizer: {e}")
    
    def transcribe(self, audio_data: Any, language: str = "en-US", **kwargs) -> Optional[str]:
        """Transcribe audio using Google Speech Recognition"""
        if not self.recognizer:
            return None
        
        try:
            # Try Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio_data, language=language)
            self.track_usage(success=True)
            logger.debug(f"Transcribed: {text}")
            return text
            
        except sr.UnknownValueError:
            logger.debug("Speech not understood")
            self.track_usage(success=False)
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            self.track_usage(success=False)
            return None
        except Exception as e:
            logger.error(f"Speech transcription failed: {e}")
            self.track_usage(success=False)
            return None

class BasicTTSProvider(VoiceProvider):
    """Basic text-to-speech using pyttsx3"""
    
    def __init__(self):
        super().__init__("pyttsx3")
        self.engine = None
        self.is_speaking = False
        
        if self.is_available():
            try:
                self.engine = pyttsx3.init()
                # Configure voice settings
                self._configure_voice()
            except Exception as e:
                logger.error(f"Failed to initialize TTS engine: {e}")
    
    def _configure_voice(self):
        """Configure voice properties"""
        if not self.engine:
            return
        
        try:
            # Set speaking rate (words per minute)
            self.engine.setProperty('rate', 180)
            
            # Set volume (0.0 to 1.0)
            self.engine.setProperty('volume', 0.8)
            
            # Try to select a better voice
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voices or specific voice types
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.engine.setProperty('voice', voices[0].id)
                    
        except Exception as e:
            logger.warning(f"Voice configuration failed: {e}")
    
    def speak(self, text: str, **kwargs) -> bool:
        """Convert text to speech"""
        if not self.engine or self.is_speaking:
            return False
        
        try:
            self.is_speaking = True
            
            # Clean text for better speech
            cleaned_text = self._clean_text_for_speech(text)
            
            # Speak the text
            self.engine.say(cleaned_text)
            self.engine.runAndWait()
            
            self.is_speaking = False
            self.track_usage(success=True)
            return True
            
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            self.is_speaking = False
            self.track_usage(success=False)
            return False
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        # Replace common symbols and abbreviations
        replacements = {
            "$": " dollars ",
            "%": " percent ",
            "&": " and ",
            "@": " at ",
            "USD": " US dollars ",
            "CEO": " C E O ",
            "IPO": " I P O ",
            "AI": " A I ",
            "ML": " M L ",
            "API": " A P I ",
            "URL": " U R L ",
            "HTTP": " H T T P ",
            "vs": " versus ",
            "etc": " etcetera ",
            "e.g.": " for example ",
            "i.e.": " that is ",
        }
        
        cleaned = text
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned

class AzureSpeechProvider(VoiceProvider):
    """Azure Cognitive Services Speech provider"""
    
    def __init__(self):
        super().__init__("azure_speech")
        self.speech_config = None
        
        if self.is_available():
            try:
                import azure.cognitiveservices.speech as speechsdk
                
                speech_key = os.getenv("AZURE_SPEECH_KEY")
                speech_region = os.getenv("AZURE_SPEECH_REGION")
                
                self.speech_config = speechsdk.SpeechConfig(
                    subscription=speech_key,
                    region=speech_region
                )
                
                # Configure speech settings
                self.speech_config.speech_recognition_language = "en-US"
                self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
                
            except Exception as e:
                logger.error(f"Failed to initialize Azure Speech: {e}")
    
    def transcribe(self, audio_data: Any, language: str = "en-US", **kwargs) -> Optional[str]:
        """Transcribe audio using Azure Speech Services"""
        if not self.speech_config:
            return None
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Configure for the specified language
            self.speech_config.speech_recognition_language = language
            
            # Create recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                self.track_usage(success=True)
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.debug("No speech could be recognized")
                self.track_usage(success=False)
                return None
            else:
                logger.error(f"Speech recognition failed: {result.reason}")
                self.track_usage(success=False)
                return None
                
        except Exception as e:
            logger.error(f"Azure speech transcription failed: {e}")
            self.track_usage(success=False)
            return None
    
    def speak(self, text: str, voice: str = "en-US-JennyNeural", **kwargs) -> bool:
        """Convert text to speech using Azure Neural voices"""
        if not self.speech_config:
            return False
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Configure voice
            self.speech_config.speech_synthesis_voice_name = voice
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            
            # Synthesize speech
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.track_usage(success=True)
                return True
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                self.track_usage(success=False)
                return False
                
        except Exception as e:
            logger.error(f"Azure speech synthesis failed: {e}")
            self.track_usage(success=False)
            return False

class VoiceIO:
    """Enhanced voice interface with multiple providers and robust fallbacks"""
    
    def __init__(
        self, 
        wake_words: tuple = ("emo", "trading bot", "options bot", "hey bot"),
        language: str = "en-US",
        tts_provider: str = "auto",
        asr_provider: str = "auto",
        enable_wake_word: bool = True
    ):
        self.wake_words = tuple(w.lower().strip() for w in wake_words)
        self.language = language
        self.enable_wake_word = enable_wake_word
        
        # Initialize providers
        self.providers = {
            "basic_speech": BasicSpeechProvider(),
            "basic_tts": BasicTTSProvider(),
            "azure_speech": AzureSpeechProvider(),
        }
        
        # Select active providers
        self.active_asr = self._select_provider("asr", asr_provider)
        self.active_tts = self._select_provider("tts", tts_provider)
        
        # Voice interface state
        self.is_listening = False
        self.is_speaking = False
        self.conversation_context = []
        
        logger.info(f"VoiceIO initialized - ASR: {self.active_asr}, TTS: {self.active_tts}")
    
    def _select_provider(self, service_type: str, preference: str) -> str:
        """Select best available provider for service type"""
        if preference == "auto":
            if service_type == "asr":
                # Preference order for ASR
                for provider in ["azure_speech", "basic_speech"]:
                    if provider in self.providers and self.providers[provider].is_available():
                        return provider
            else:  # TTS
                # Preference order for TTS
                for provider in ["azure_speech", "basic_tts"]:
                    if provider in self.providers and self.providers[provider].is_available():
                        return provider
            return "text_fallback"
        elif preference in self.providers and self.providers[preference].is_available():
            return preference
        else:
            return "text_fallback"
    
    def get_available_providers(self) -> Dict[str, Dict[str, bool]]:
        """Get status of all providers"""
        return {
            "asr_providers": {
                name: provider.is_available() 
                for name, provider in self.providers.items()
                if hasattr(provider, 'transcribe')
            },
            "tts_providers": {
                name: provider.is_available()
                for name, provider in self.providers.items()
                if hasattr(provider, 'speak')
            }
        }
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get provider usage statistics"""
        stats = {}
        for name, provider in self.providers.items():
            stats[name] = {
                "available": provider.is_available(),
                "usage_count": provider.usage_count,
                "error_count": provider.error_count,
                "last_used": provider.last_used,
                "error_rate": provider.error_count / max(provider.usage_count, 1)
            }
        return stats
    
    def listen_once(
        self, 
        prompt: str = "🎙️  Listening... (or type your command)",
        timeout: int = 5,
        phrase_time_limit: int = 10
    ) -> Optional[str]:
        """
        Listen for a single voice command with text fallback
        
        Args:
            prompt: Prompt to display to user
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for phrase
        """
        if self.active_asr == "text_fallback":
            return self._text_input_fallback(prompt)
        
        try:
            import speech_recognition as sr
            
            # Get the appropriate provider
            provider = self.providers.get(self.active_asr)
            if not provider or not provider.is_available():
                return self._text_input_fallback(prompt)
            
            # Set up microphone
            recognizer = sr.Recognizer()
            
            with sr.Microphone() as source:
                print(prompt)
                
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                try:
                    # Listen for audio
                    audio = recognizer.listen(
                        source, 
                        timeout=timeout, 
                        phrase_time_limit=phrase_time_limit
                    )
                    
                    # Transcribe audio
                    text = provider.transcribe(audio, language=self.language)
                    
                    if text:
                        print(f"🗣️  You said: {text}")
                        self.conversation_context.append({
                            "timestamp": datetime.utcnow(),
                            "type": "user_speech",
                            "content": text
                        })
                        return text
                    else:
                        print("❓ Could not understand speech")
                        return self._text_input_fallback("Type your command instead: ")
                        
                except sr.WaitTimeoutError:
                    print("⏱️  No speech detected")
                    return self._text_input_fallback("Type your command instead: ")
                    
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            return self._text_input_fallback("Speech recognition failed. Type your command: ")
    
    def speak(self, text: str, force: bool = False) -> bool:
        """
        Convert text to speech with fallback to text display
        
        Args:
            text: Text to speak
            force: Force speech even if TTS is disabled
        """
        if not text or not text.strip():
            return False
        
        # Add to conversation context
        self.conversation_context.append({
            "timestamp": datetime.utcnow(),
            "type": "bot_response", 
            "content": text
        })
        
        # Try TTS if available
        if self.active_tts != "text_fallback":
            provider = self.providers.get(self.active_tts)
            if provider and provider.is_available():
                try:
                    success = provider.speak(text)
                    if success:
                        return True
                except Exception as e:
                    logger.error(f"TTS failed: {e}")
        
        # Fallback to text display
        print(f"🤖 Bot: {text}")
        return True
    
    def _text_input_fallback(self, prompt: str) -> Optional[str]:
        """Fallback to text input when voice is not available"""
        try:
            text = input(prompt).strip()
            if text:
                self.conversation_context.append({
                    "timestamp": datetime.utcnow(),
                    "type": "user_text",
                    "content": text
                })
            return text if text else None
        except KeyboardInterrupt:
            return None
        except Exception as e:
            logger.error(f"Text input failed: {e}")
            return None
    
    def is_wake_word_detected(self, text: str) -> bool:
        """Check if text contains wake words"""
        if not self.enable_wake_word:
            return True
        
        if not text:
            return False
        
        text_lower = text.lower().strip()
        
        # Check if any wake word is present
        return any(
            wake_word in text_lower or text_lower.startswith(wake_word)
            for wake_word in self.wake_words
        )
    
    def extract_command(self, text: str) -> str:
        """Extract command after wake word"""
        if not text:
            return ""
        
        text_lower = text.lower().strip()
        
        # Find wake word and extract command after it
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                # Find position after wake word
                idx = text_lower.find(wake_word)
                command_start = idx + len(wake_word)
                
                # Extract command part
                command = text[command_start:].strip()
                
                # Remove common connectors
                for connector in [",", "please", "can you", "could you"]:
                    if command.lower().startswith(connector):
                        command = command[len(connector):].strip()
                
                return command
        
        # If no wake word found, return full text
        return text.strip()
    
    def listen_for_wake_word(self, timeout: int = 30) -> Optional[str]:
        """
        Listen continuously for wake word, then capture command
        
        Args:
            timeout: Maximum seconds to listen for wake word
        """
        if self.active_asr == "text_fallback":
            return self._text_input_fallback("Enter command (with wake word): ")
        
        try:
            print(f"🎧 Listening for wake words: {', '.join(self.wake_words)}")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Listen for a short phrase
                text = self.listen_once(
                    prompt="🎙️  Say wake word + command...",
                    timeout=3,
                    phrase_time_limit=8
                )
                
                if text and self.is_wake_word_detected(text):
                    command = self.extract_command(text)
                    if command:
                        print(f"✅ Command detected: {command}")
                        return command
                    else:
                        print("🤖 Yes? What would you like me to do?")
                        # Listen for follow-up command
                        follow_up = self.listen_once(
                            prompt="🎙️  Listening for command...",
                            timeout=10
                        )
                        if follow_up:
                            return follow_up
                
                # Brief pause before next attempt
                time.sleep(0.5)
            
            print("⏱️  Wake word timeout")
            return None
            
        except KeyboardInterrupt:
            print("\n👋 Voice listening cancelled")
            return None
        except Exception as e:
            logger.error(f"Wake word listening failed: {e}")
            return None
    
    def start_conversation(self, timeout: int = 300) -> List[str]:
        """
        Start an interactive voice conversation
        
        Args:
            timeout: Maximum conversation time in seconds
        """
        commands = []
        start_time = time.time()
        
        self.speak("Voice interface ready. Say a wake word followed by your command.")
        
        try:
            while time.time() - start_time < timeout:
                command = self.listen_for_wake_word(timeout=30)
                
                if command:
                    commands.append(command)
                    
                    # Simple acknowledgment
                    self.speak(f"Received command: {command}")
                    
                    # Ask if user wants to continue
                    self.speak("Any other commands? Or say 'stop' to end.")
                    
                    response = self.listen_once(
                        prompt="🎙️  Continue or say 'stop'...",
                        timeout=10
                    )
                    
                    if response and any(word in response.lower() for word in ["stop", "end", "quit", "exit", "done"]):
                        break
                else:
                    # No command detected, ask if user wants to continue
                    response = self._text_input_fallback("Continue listening? (y/n): ")
                    if response and response.lower().startswith('n'):
                        break
            
            self.speak(f"Conversation ended. Captured {len(commands)} commands.")
            
        except KeyboardInterrupt:
            self.speak("Conversation interrupted.")
        
        return commands
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversation_context[-limit:] if self.conversation_context else []
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_context.clear()

# Utility functions
def test_voice_capabilities() -> Dict[str, Any]:
    """Test voice capabilities and return status"""
    results = {
        "providers_available": _PROVIDERS_AVAILABLE,
        "microphone_test": False,
        "speaker_test": False,
        "recommended_setup": []
    }
    
    # Test microphone availability
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        results["microphone_test"] = True
    except Exception as e:
        logger.debug(f"Microphone test failed: {e}")
        results["recommended_setup"].append("Check microphone connection")
    
    # Test TTS
    try:
        if _PROVIDERS_AVAILABLE["pyttsx3"]:
            engine = pyttsx3.init()
            engine.say("Test")
            engine.runAndWait()
            results["speaker_test"] = True
    except Exception as e:
        logger.debug(f"Speaker test failed: {e}")
        results["recommended_setup"].append("Check speaker/audio output")
    
    # Recommendations
    if not any(_PROVIDERS_AVAILABLE.values()):
        results["recommended_setup"].append("Install voice packages: pip install SpeechRecognition pyttsx3")
    
    return results

def get_optimal_voice_config() -> Dict[str, str]:
    """Get optimal voice configuration based on available providers"""
    if _PROVIDERS_AVAILABLE["azure_speech"]:
        return {"asr_provider": "azure_speech", "tts_provider": "azure_speech"}
    elif _PROVIDERS_AVAILABLE["speech_recognition"] and _PROVIDERS_AVAILABLE["pyttsx3"]:
        return {"asr_provider": "basic_speech", "tts_provider": "basic_tts"}
    else:
        return {"asr_provider": "text_fallback", "tts_provider": "text_fallback"}

# Export main classes and functions
__all__ = [
    "VoiceIO", "VoiceProvider", "BasicSpeechProvider", "BasicTTSProvider", 
    "AzureSpeechProvider", "test_voice_capabilities", "get_optimal_voice_config"
]