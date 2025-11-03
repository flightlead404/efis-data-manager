"""Logging utilities for EFIS Data Manager."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
                
        return json.dumps(log_entry, default=str)


class EFISLogger:
    """Enhanced logger for EFIS Data Manager with structured logging."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize EFIS logger.
        
        Args:
            name: Logger name
            config: Logging configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(name)
        self._setup_logger()
        
    def _setup_logger(self) -> None:
        """Set up logger with handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        level = self.config.get('level', 'INFO')
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create formatters
        json_formatter = JSONFormatter()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        log_file = self.config.get('file', 'efis-data-manager.log')
        if log_file.startswith('~'):
            log_file = os.path.expanduser(log_file)
            
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        max_bytes = self._parse_size(self.config.get('maxSize', '10MB'))
        backup_count = self.config.get('backupCount', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(json_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (only for development/debugging)
        if self.config.get('console', False) or '--debug' in sys.argv:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
        # Prevent propagation to root logger
        self.logger.propagate = False
        
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '10MB') to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
            
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional extra fields."""
        self.logger.debug(message, extra=kwargs)
        
    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional extra fields."""
        self.logger.info(message, extra=kwargs)
        
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional extra fields."""
        self.logger.warning(message, extra=kwargs)
        
    def error(self, message: str, **kwargs) -> None:
        """Log error message with optional extra fields."""
        self.logger.error(message, extra=kwargs)
        
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with optional extra fields."""
        self.logger.critical(message, extra=kwargs)
        
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)
        
    def log_operation(self, operation: str, status: str, **kwargs) -> None:
        """Log operation with structured data."""
        self.info(f"Operation: {operation}", 
                 operation=operation, status=status, **kwargs)
        
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics."""
        self.info(f"Performance: {operation} completed in {duration:.2f}s",
                 operation=operation, duration=duration, **kwargs)
        
    def log_sync_result(self, result: 'SyncResult') -> None:
        """Log synchronization result."""
        self.info(f"Sync completed: {result.files_transferred} files, "
                 f"{result.bytes_transferred} bytes",
                 sync_status=result.status.value,
                 files_transferred=result.files_transferred,
                 bytes_transferred=result.bytes_transferred,
                 duration=result.duration,
                 error_count=len(result.errors))
        
        for error in result.errors:
            self.error(f"Sync error: {error}", sync_error=True)


def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> EFISLogger:
    """Get configured EFIS logger instance.
    
    Args:
        name: Logger name
        config: Optional logging configuration
        
    Returns:
        Configured EFISLogger instance
    """
    if config is None:
        # Try to load from platform config
        try:
            from .config import get_platform_config
            platform_config = get_platform_config()
            config = platform_config.get('logging', {})
        except ImportError:
            config = {}
            
    return EFISLogger(name, config)


def setup_root_logger(config: Optional[Dict[str, Any]] = None) -> EFISLogger:
    """Set up root logger for the application.
    
    Args:
        config: Optional logging configuration
        
    Returns:
        Root logger instance
    """
    return get_logger('efis-data-manager', config)