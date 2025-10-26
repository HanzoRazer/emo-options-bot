"""
Voice Interface Requirements and Mock Implementation
"""

# Fallback voice interface for when dependencies are not available
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MockVoiceInterface:
    """Mock voice interface for testing when audio libraries unavailable"""
    
    def __init__(self):
        self.is_active = False
        self.available = False
        self.command_handlers = {}
        
    def start(self) -> bool:
        """Mock start - always succeeds"""
        self.is_active = True
        logger.info("Mock voice interface started (audio libraries not available)")
        return True
    
    def stop(self):
        """Mock stop"""
        self.is_active = False
        logger.info("Mock voice interface stopped")
    
    def speak(self, text: str, blocking: bool = False):
        """Mock speak - just logs the text"""
        logger.info(f"[TTS MOCK] Would say: {text}")
    
    def register_command_handler(self, command_type: str, handler: Callable[[Dict], Any]):
        """Register command handler"""
        self.command_handlers[command_type] = handler
        logger.info(f"Registered mock handler for: {command_type}")
    
    def process_text_command(self, text: str) -> Dict:
        """Process text as if it came from voice (for testing)"""
        # Simple command parsing for testing
        command = {
            "type": "unknown",
            "text": text,
            "timestamp": datetime.now(),
            "parameters": {}
        }
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["buy", "purchase"]):
            command["type"] = "buy"
        elif any(word in text_lower for word in ["sell", "short"]):
            command["type"] = "sell"
        elif any(word in text_lower for word in ["status", "portfolio", "position"]):
            command["type"] = "status"
        elif any(word in text_lower for word in ["help", "commands"]):
            command["type"] = "help"
        
        # Execute handler if available
        if command["type"] in self.command_handlers:
            try:
                result = self.command_handlers[command["type"]](command)
                command["result"] = result
            except Exception as e:
                command["error"] = str(e)
        
        return command