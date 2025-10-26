"""
Robust Error Handling and Logging System
Provides consistent error handling and logging across all modules
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime
import json

class RobustLogger:
    """Enhanced logging with error tracking and context."""
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Error tracking
        self.error_count = 0
        self.warning_count = 0
        self.last_errors = []
    
    def _setup_handlers(self):
        """Setup file and console handlers."""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_file = self.log_dir / f"{self.name}_errors.log"
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, context: Optional[Dict] = None):
        """Log info message with optional context."""
        if context:
            message = f"{message} | Context: {json.dumps(context, default=str)}"
        self.logger.info(message)
    
    def warning(self, message: str, context: Optional[Dict] = None):
        """Log warning with tracking."""
        self.warning_count += 1
        if context:
            message = f"{message} | Context: {json.dumps(context, default=str)}"
        self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None, context: Optional[Dict] = None):
        """Log error with exception details and tracking."""
        self.error_count += 1
        
        error_info = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        if exception:
            error_info["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc()
            }
            message = f"{message} | Exception: {exception}"
        
        self.last_errors.append(error_info)
        if len(self.last_errors) > 50:  # Keep last 50 errors
            self.last_errors.pop(0)
        
        if context:
            message = f"{message} | Context: {json.dumps(context, default=str)}"
        
        self.logger.error(message)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get logger health summary."""
        return {
            "name": self.name,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "last_errors": self.last_errors[-5:],  # Last 5 errors
            "log_dir": str(self.log_dir)
        }

class SafeExecutor:
    """Safe execution wrapper with comprehensive error handling."""
    
    def __init__(self, logger: Optional[RobustLogger] = None):
        self.logger = logger or RobustLogger("safe_executor")
    
    def safe_call(self, 
                  func: Callable, 
                  *args, 
                  fallback_value: Any = None,
                  context: Optional[Dict] = None,
                  critical: bool = False,
                  **kwargs) -> Any:
        """
        Safely execute a function with comprehensive error handling.
        
        Args:
            func: Function to execute
            *args: Function arguments
            fallback_value: Value to return on error
            context: Additional context for logging
            critical: If True, re-raise exceptions after logging
            **kwargs: Function keyword arguments
        """
        try:
            result = func(*args, **kwargs)
            self.logger.info(f"Successfully executed {func.__name__}", context)
            return result
            
        except Exception as e:
            error_context = {
                "function": func.__name__,
                "args": str(args)[:200],  # Truncate long args
                "kwargs": str(kwargs)[:200],
                **(context or {})
            }
            
            self.logger.error(
                f"Error executing {func.__name__}", 
                exception=e, 
                context=error_context
            )
            
            if critical:
                raise
            
            return fallback_value
    
    def safe_import(self, 
                   module_name: str, 
                   fallback_class: Optional[type] = None,
                   context: Optional[Dict] = None) -> Any:
        """
        Safely import a module with fallback.
        
        Args:
            module_name: Module to import
            fallback_class: Class to return if import fails
            context: Additional context
        """
        try:
            parts = module_name.split('.')
            module = __import__(module_name)
            
            # Navigate to the final module/class
            for part in parts[1:]:
                module = getattr(module, part)
            
            self.logger.info(f"Successfully imported {module_name}", context)
            return module
            
        except ImportError as e:
            self.logger.warning(
                f"Could not import {module_name}, using fallback", 
                context={"error": str(e), **(context or {})}
            )
            return fallback_class
        
        except Exception as e:
            self.logger.error(
                f"Error importing {module_name}", 
                exception=e, 
                context=context
            )
            return fallback_class

def robust_function(logger_name: str = None, 
                   fallback_value: Any = None,
                   critical: bool = False):
    """
    Decorator for adding robust error handling to functions.
    
    Args:
        logger_name: Name for the logger (defaults to function name)
        fallback_value: Value to return on error
        critical: If True, re-raise exceptions after logging
    """
    def decorator(func):
        nonlocal logger_name
        if logger_name is None:
            logger_name = func.__name__
            
        logger = RobustLogger(logger_name)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                
                logger.error(
                    f"Error in {func.__name__}", 
                    exception=e, 
                    context=context
                )
                
                if critical:
                    raise
                
                return fallback_value
        
        # Add logger to function for external access
        wrapper._logger = logger
        return wrapper
    
    return decorator

def create_fallback_class(class_name: str, methods: Dict[str, Any]) -> type:
    """
    Dynamically create a fallback class with mock methods.
    
    Args:
        class_name: Name of the fallback class
        methods: Dictionary of method names and their fallback return values
    """
    def create_method(return_value):
        def method(self, *args, **kwargs):
            return return_value
        return method
    
    class_dict = {
        "__init__": lambda self, *args, **kwargs: None
    }
    
    for method_name, return_value in methods.items():
        class_dict[method_name] = create_method(return_value)
    
    return type(class_name, (), class_dict)

# Global logger instances for common use
system_logger = RobustLogger("system")
trading_logger = RobustLogger("trading")
ai_logger = RobustLogger("ai")
risk_logger = RobustLogger("risk")

# Safe executor instance
safe_executor = SafeExecutor(system_logger)

def get_all_loggers_health() -> Dict[str, Dict]:
    """Get health summary for all active loggers."""
    loggers = {
        "system": system_logger,
        "trading": trading_logger,
        "ai": ai_logger,
        "risk": risk_logger
    }
    
    return {
        name: logger.get_health_summary() 
        for name, logger in loggers.items()
    }