"""
Voice I/O System - Phase 3 Implementation
Automatic Speech Recognition (ASR) and Text-to-Speech (TTS) for voice-driven trading.
"""
import logging
import asyncio
import queue
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import json
import os

# Speech recognition
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

# Text-to-speech
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    pyttsx3 = None

# Audio processing
try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    pyaudio = None

logger = logging.getLogger(__name__)

class VoiceConfig:
    """Configuration for voice I/O system"""
    
    # Wake words for activation
    WAKE_WORDS = ["emo", "trading bot", "options bot"]
    
    # Speech recognition settings
    ASR_TIMEOUT = 5  # seconds
    ASR_PHRASE_TIMEOUT = 1  # seconds
    ASR_ENERGY_THRESHOLD = 300
    ASR_DYNAMIC_ENERGY = True
    
    # TTS settings
    TTS_RATE = 180  # words per minute
    TTS_VOLUME = 0.8  # 0.0 to 1.0
    TTS_VOICE_INDEX = 0  # 0 for default, 1 for alternative
    
    # Language settings
    DEFAULT_LANGUAGE = "en-US"
    SUPPORTED_LANGUAGES = {
        "en-US": "English (US)",
        "en-GB": "English (UK)", 
        "es-ES": "Spanish",
        "fr-FR": "French",
        "de-DE": "German",
        "it-IT": "Italian",
        "pt-BR": "Portuguese (Brazil)",
        "zh-CN": "Chinese (Simplified)"
    }
    
    # Command patterns
    TRADING_COMMANDS = {
        "buy": ["buy", "purchase", "long", "go long"],
        "sell": ["sell", "short", "go short", "exit"],
        "close": ["close", "exit position", "liquidate"],
        "status": ["status", "position", "portfolio", "how am i doing"],
        "help": ["help", "what can you do", "commands"],
        "cancel": ["cancel", "stop", "nevermind", "abort"]
    }

class ASREngine:
    """Automatic Speech Recognition Engine"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.error("speech_recognition not available. Install with: pip install SpeechRecognition")
            return
            
        if not AUDIO_AVAILABLE:
            logger.error("pyaudio not available. Install with: pip install pyaudio")
            return
            
        self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize speech recognizer and microphone"""
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            logger.info("Adjusting for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Configure recognizer
            self.recognizer.energy_threshold = self.config.ASR_ENERGY_THRESHOLD
            self.recognizer.dynamic_energy_threshold = self.config.ASR_DYNAMIC_ENERGY
            self.recognizer.phrase_threshold = self.config.ASR_PHRASE_TIMEOUT
            
            logger.info("ASR engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ASR engine: {e}")
            self.recognizer = None
            self.microphone = None
    
    def start_listening(self, callback: Callable[[str], None]):
        """Start continuous listening in background thread"""
        if not self.recognizer or not self.microphone:
            logger.error("ASR engine not properly initialized")
            return False
        
        self.is_listening = True
        
        def listen_continuously():
            while self.is_listening:
                try:
                    # Listen for audio with timeout
                    with self.microphone as source:
                        audio = self.recognizer.listen(
                            source, 
                            timeout=self.config.ASR_TIMEOUT,
                            phrase_time_limit=self.config.ASR_PHRASE_TIMEOUT
                        )
                    
                    # Add to queue for processing
                    self.audio_queue.put(audio)
                    
                except sr.WaitTimeoutError:
                    continue  # Timeout is normal
                except Exception as e:
                    logger.warning(f"Listening error: {e}")
                    continue
        
        def process_audio():
            while self.is_listening:
                try:
                    # Get audio from queue
                    audio = self.audio_queue.get(timeout=1)
                    
                    # Recognize speech
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=self.config.DEFAULT_LANGUAGE
                    )
                    
                    if text:
                        logger.info(f"Recognized: {text}")
                        callback(text.lower())
                        
                except queue.Empty:
                    continue
                except sr.UnknownValueError:
                    continue  # Could not understand audio
                except sr.RequestError as e:
                    logger.error(f"Speech recognition error: {e}")
                    continue
        
        # Start threads
        self.listen_thread = threading.Thread(target=listen_continuously, daemon=True)
        self.process_thread = threading.Thread(target=process_audio, daemon=True)
        
        self.listen_thread.start()
        self.process_thread.start()
        
        logger.info("Started continuous listening")
        return True
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
        logger.info("Stopped listening")
    
    def recognize_once(self, timeout: int = 5) -> Optional[str]:
        """Recognize speech once with timeout"""
        if not self.recognizer or not self.microphone:
            return None
        
        try:
            with self.microphone as source:
                logger.info("Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout)
            
            text = self.recognizer.recognize_google(
                audio, 
                language=self.config.DEFAULT_LANGUAGE
            )
            
            logger.info(f"Recognized: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            logger.info("Listening timeout")
            return None
        except sr.UnknownValueError:
            logger.info("Could not understand speech")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return None

class TTSEngine:
    """Text-to-Speech Engine"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.engine = None
        self.is_speaking = False
        
        if not TTS_AVAILABLE:
            logger.error("pyttsx3 not available. Install with: pip install pyttsx3")
            return
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize TTS engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > self.config.TTS_VOICE_INDEX:
                self.engine.setProperty('voice', voices[self.config.TTS_VOICE_INDEX].id)
            
            self.engine.setProperty('rate', self.config.TTS_RATE)
            self.engine.setProperty('volume', self.config.TTS_VOLUME)
            
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def speak(self, text: str, blocking: bool = True):
        """Speak text using TTS"""
        if not self.engine:
            logger.error("TTS engine not available")
            return
        
        try:
            self.is_speaking = True
            logger.info(f"Speaking: {text}")
            
            self.engine.say(text)
            
            if blocking:
                self.engine.runAndWait()
            else:
                # Non-blocking speech in separate thread
                def speak_async():
                    self.engine.runAndWait()
                    self.is_speaking = False
                
                thread = threading.Thread(target=speak_async, daemon=True)
                thread.start()
            
            if blocking:
                self.is_speaking = False
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            self.is_speaking = False
    
    def stop_speaking(self):
        """Stop current speech"""
        if self.engine:
            self.engine.stop()
            self.is_speaking = False

class VoiceCommander:
    """Voice command processor for trading operations"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.command_handlers = {}
        self.context = {}
        self.wake_word_detected = False
        
    def register_handler(self, command_type: str, handler: Callable[[Dict], Any]):
        """Register handler for command type"""
        self.command_handlers[command_type] = handler
        logger.info(f"Registered handler for command: {command_type}")
    
    def process_voice_input(self, text: str) -> Dict:
        """Process voice input and extract trading command"""
        text = text.lower().strip()
        
        # Check for wake words first
        if not self.wake_word_detected:
            for wake_word in self.config.WAKE_WORDS:
                if wake_word in text:
                    self.wake_word_detected = True
                    # Remove wake word from text
                    text = text.replace(wake_word, "").strip()
                    logger.info(f"Wake word detected: {wake_word}")
                    break
            
            if not self.wake_word_detected:
                return {"type": "ignored", "reason": "no_wake_word"}
        
        # Parse command
        command = self._parse_command(text)
        
        # Execute command if handler exists
        if command["type"] in self.command_handlers:
            try:
                result = self.command_handlers[command["type"]](command)
                command["result"] = result
            except Exception as e:
                logger.error(f"Command handler error: {e}")
                command["error"] = str(e)
        
        # Reset wake word after processing
        if command["type"] in ["cancel", "stop", "exit"]:
            self.wake_word_detected = False
        
        return command
    
    def _parse_command(self, text: str) -> Dict:
        """Parse voice text into structured command"""
        command = {
            "type": "unknown",
            "text": text,
            "timestamp": datetime.now(),
            "parameters": {}
        }
        
        # Identify command type
        for cmd_type, keywords in self.config.TRADING_COMMANDS.items():
            for keyword in keywords:
                if keyword in text:
                    command["type"] = cmd_type
                    break
            if command["type"] != "unknown":
                break
        
        # Extract parameters based on command type
        if command["type"] == "buy":
            command["parameters"] = self._extract_buy_parameters(text)
        elif command["type"] == "sell":
            command["parameters"] = self._extract_sell_parameters(text)
        elif command["type"] == "status":
            command["parameters"] = self._extract_status_parameters(text)
        
        return command
    
    def _extract_buy_parameters(self, text: str) -> Dict:
        """Extract parameters for buy command"""
        params = {}
        
        # Extract symbol
        words = text.split()
        for i, word in enumerate(words):
            if word.upper() in ["SPY", "QQQ", "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]:
                params["symbol"] = word.upper()
                break
            # Look for "buy X" pattern
            if word in ["buy", "purchase"] and i + 1 < len(words):
                next_word = words[i + 1].upper()
                if len(next_word) <= 5:  # Likely a symbol
                    params["symbol"] = next_word
                    break
        
        # Extract strategy
        if "call" in text:
            params["strategy"] = "call"
        elif "put" in text:
            params["strategy"] = "put"
        elif "spread" in text:
            params["strategy"] = "spread"
        elif "iron condor" in text or "condor" in text:
            params["strategy"] = "iron_condor"
        elif "covered call" in text:
            params["strategy"] = "covered_call"
        
        # Extract quantity
        for word in text.split():
            if word.isdigit():
                params["quantity"] = int(word)
                break
        
        return params
    
    def _extract_sell_parameters(self, text: str) -> Dict:
        """Extract parameters for sell command"""
        params = {}
        
        # Similar to buy parameters
        params.update(self._extract_buy_parameters(text))
        params["action"] = "sell"
        
        return params
    
    def _extract_status_parameters(self, text: str) -> Dict:
        """Extract parameters for status command"""
        params = {}
        
        if "position" in text or "positions" in text:
            params["detail"] = "positions"
        elif "portfolio" in text:
            params["detail"] = "portfolio"
        elif "pnl" in text or "profit" in text or "loss" in text:
            params["detail"] = "pnl"
        else:
            params["detail"] = "summary"
        
        return params

class VoiceInterface:
    """Main voice interface coordinating ASR, TTS, and command processing"""
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.asr = ASREngine(self.config)
        self.tts = TTSEngine(self.config)
        self.commander = VoiceCommander(self.config)
        self.is_active = False
        
        # Check if voice I/O is available
        self.available = (
            SPEECH_RECOGNITION_AVAILABLE and 
            TTS_AVAILABLE and 
            AUDIO_AVAILABLE and
            self.asr.recognizer is not None and
            self.tts.engine is not None
        )
        
        if not self.available:
            logger.warning("Voice I/O not fully available - missing dependencies")
    
    def start(self):
        """Start voice interface"""
        if not self.available:
            logger.error("Cannot start voice interface - not available")
            return False
        
        self.is_active = True
        
        # Start listening
        success = self.asr.start_listening(self._handle_voice_input)
        
        if success:
            self.tts.speak("Voice interface activated. Say a wake word to begin.")
            logger.info("Voice interface started successfully")
        else:
            self.is_active = False
            logger.error("Failed to start voice interface")
        
        return success
    
    def stop(self):
        """Stop voice interface"""
        self.is_active = False
        self.asr.stop_listening()
        self.tts.stop_speaking()
        logger.info("Voice interface stopped")
    
    def _handle_voice_input(self, text: str):
        """Handle recognized voice input"""
        if not self.is_active:
            return
        
        try:
            command = self.commander.process_voice_input(text)
            
            if command["type"] == "ignored":
                return  # No response needed
            
            # Generate response
            response = self._generate_response(command)
            
            # Speak response
            if response:
                self.tts.speak(response, blocking=False)
                
        except Exception as e:
            logger.error(f"Voice input handling error: {e}")
            self.tts.speak("Sorry, I encountered an error processing your request.")
    
    def _generate_response(self, command: Dict) -> str:
        """Generate spoken response for command"""
        cmd_type = command["type"]
        
        if cmd_type == "unknown":
            return "I didn't understand that command. You can say things like 'buy SPY calls' or 'show my positions'."
        
        elif cmd_type == "help":
            return "I can help you with trading commands. Try saying 'buy SPY calls', 'sell positions', or 'show my portfolio status'."
        
        elif cmd_type == "status":
            if "result" in command:
                return f"Here's your {command['parameters'].get('detail', 'status')}: {command['result']}"
            else:
                return "Let me check your status..."
        
        elif cmd_type in ["buy", "sell"]:
            params = command["parameters"]
            symbol = params.get("symbol", "the requested symbol")
            strategy = params.get("strategy", "strategy")
            
            if "result" in command:
                return f"Successfully executed {cmd_type} order for {symbol} {strategy}."
            elif "error" in command:
                return f"Unable to execute {cmd_type} order: {command['error']}"
            else:
                return f"Processing {cmd_type} order for {symbol} {strategy}..."
        
        elif cmd_type == "cancel":
            return "Command cancelled."
        
        return "Command processed."
    
    def register_command_handler(self, command_type: str, handler: Callable[[Dict], Any]):
        """Register handler for voice commands"""
        self.commander.register_handler(command_type, handler)
    
    def speak(self, text: str, blocking: bool = False):
        """Speak text (external interface)"""
        if self.available:
            self.tts.speak(text, blocking)
        else:
            logger.info(f"TTS not available, would say: {text}")

# Example usage and testing
if __name__ == "__main__":
    # Example command handlers
    def handle_buy_command(command: Dict) -> str:
        params = command["parameters"]
        symbol = params.get("symbol", "UNKNOWN")
        strategy = params.get("strategy", "call")
        quantity = params.get("quantity", 1)
        
        return f"Simulated buy: {quantity} {symbol} {strategy} contracts"
    
    def handle_status_command(command: Dict) -> str:
        detail = command["parameters"].get("detail", "summary")
        return f"Portfolio {detail}: All systems normal, 5 open positions, +$1,250 today"
    
    # Test voice interface
    config = VoiceConfig()
    voice = VoiceInterface(config)
    
    # Register handlers
    voice.register_command_handler("buy", handle_buy_command)
    voice.register_command_handler("status", handle_status_command)
    
    print("Voice I/O System Test")
    print(f"Available: {voice.available}")
    
    if voice.available:
        print("Starting voice interface... (Press Ctrl+C to stop)")
        voice.start()
        
        try:
            # Keep running
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping voice interface...")
            voice.stop()
    else:
        print("Voice I/O not available - install dependencies:")
        print("pip install SpeechRecognition pyttsx3 pyaudio")
        
        # Test with mock input
        print("\nTesting command parsing...")
        commander = VoiceCommander(config)
        
        test_commands = [
            "emo buy SPY calls",
            "trading bot sell 5 AAPL puts", 
            "options bot show my portfolio status",
            "buy iron condor on QQQ",
            "what are my positions"
        ]
        
        for test_cmd in test_commands:
            result = commander.process_voice_input(test_cmd)
            print(f"Input: '{test_cmd}' -> {result['type']} {result.get('parameters', {})}")