"""
Logging configuration for macOS EFIS Data Manager daemon.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import colorlog


class LoggingManager:
    """Manages structured logging with rotation for the daemon."""
    
    def __init__(self, log_file: str, log_level: str = "INFO", max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration with rotation and formatting."""
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file)
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = colorlog.ColoredFormatter(
            fmt='%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Set specific logger levels
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module."""
        return logging.getLogger(name)
    
    def set_level(self, level: str):
        """Change the logging level dynamically."""
        new_level = getattr(logging, level.upper(), logging.INFO)
        root_logger = logging.getLogger()
        root_logger.setLevel(new_level)
        
        for handler in root_logger.handlers:
            handler.setLevel(new_level)


def setup_daemon_logging(log_file: str, log_level: str = "INFO") -> LoggingManager:
    """Set up logging for the daemon process."""
    return LoggingManager(log_file, log_level)