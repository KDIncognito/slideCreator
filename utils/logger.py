import logging
import sys
from typing import Optional
from pathlib import Path

class SlideCreatorLogger:
    """Centralized logging configuration for the SlideCreator project."""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SlideCreatorLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup the logger with appropriate formatting and handlers."""
        self._logger = logging.getLogger('slideCreator')
        self._logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self._logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
    
    def get_logger(self):
        """Get the configured logger instance."""
        return self._logger
    
    def set_level(self, level: str):
        """Set logging level."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self._logger.setLevel(level_map.get(level.upper(), logging.INFO))
    
    def add_file_handler(self, log_file_path: str):
        """Add file handler for logging to file."""
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self._logger.addHandler(file_handler)

# Global logger instance
def get_logger():
    """Get the global logger instance."""
    return SlideCreatorLogger().get_logger()

# Convenience functions
logger = get_logger()

def info(message: str):
    logger.info(message)

def debug(message: str):
    logger.debug(message)

def warning(message: str):
    logger.warning(message)

def error(message: str):
    logger.error(message)

def critical(message: str):
    logger.critical(message)
