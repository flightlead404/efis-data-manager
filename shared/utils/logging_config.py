"""
Logging configuration for EFIS Data Manager.
Provides structured logging with rotation and cross-platform support.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
import colorlog


class LoggingManager:
    """Manages logging configuration for EFIS Data Manager components."""
    
    def __init__(self, component_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize logging manager.
        
        Args:
            component_name: Name of the component (e.g., 'windows', 'macos')
            config: Configuration dictionary for logging settings
        """
        self.component_name = component_name
        self.config = config or {}
        self._loggers = {}
        
    def setup_logging(self, log_dir: Optional[str] = None) -> logging.Logger:
        """
        Set up logging configuration with file rotation and console output.
        
        Args:
            log_dir: Directory for log files. If None, uses default location.
            
        Returns:
            Configured logger instance
        """
        # Determine log directory
        if log_dir:
            log_path = Path(log_dir)
        else:
            log_path = self._get_default_log_dir()
            
        # Ensure log directory exists
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logger = logging.getLogger(self.component_name)
        logger.setLevel(self._get_log_level())
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Add file handler with rotation
        file_handler = self._create_file_handler(log_path)
        logger.addHandler(file_handler)
        
        # Add console handler with colors
        console_handler = self._create_console_handler()
        logger.addHandler(console_handler)
        
        # Store logger reference
        self._loggers[self.component_name] = logger
        
        logger.info(f"Logging initialized for {self.component_name}")
        logger.info(f"Log files location: {log_path}")
        
        return logger
        
    def get_logger(self, name: str = None) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name. If None, returns component logger.
            
        Returns:
            Logger instance
        """
        if name is None:
            name = self.component_name
            
        if name in self._loggers:
            return self._loggers[name]
        else:
            # Create child logger
            parent_logger = self._loggers.get(self.component_name)
            if parent_logger:
                return parent_logger.getChild(name)
            else:
                return logging.getLogger(name)
                
    def _create_file_handler(self, log_path: Path) -> logging.Handler:
        """Create rotating file handler."""
        log_file = log_path / f"{self.component_name}.log"
        
        # Get rotation settings from config
        max_bytes = self.config.get('logging', {}).get('maxBytes', 10 * 1024 * 1024)  # 10MB
        backup_count = self.config.get('logging', {}).get('backupCount', 5)
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Set formatter
        formatter = logging.Formatter(
            fmt=self.config.get('logging', {}).get('format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            datefmt=self.config.get('logging', {}).get('dateFormat', 
                '%Y-%m-%d %H:%M:%S')
        )
        handler.setFormatter(formatter)
        
        return handler
        
    def _create_console_handler(self) -> logging.Handler:
        """Create colored console handler."""
        handler = colorlog.StreamHandler(sys.stdout)
        
        # Set colored formatter
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        handler.setFormatter(formatter)
        
        return handler
        
    def _get_log_level(self) -> int:
        """Get log level from configuration."""
        level_str = self.config.get('logging', {}).get('logLevel', 'INFO')
        return getattr(logging, level_str.upper(), logging.INFO)
        
    def _get_default_log_dir(self) -> Path:
        """Get default log directory based on platform and component."""
        if sys.platform == 'win32':
            # Windows: use component-specific directory
            base_dir = Path.cwd() / 'windows' / 'logs'
        elif sys.platform == 'darwin':
            # macOS: use component-specific directory
            base_dir = Path.cwd() / 'macos' / 'logs'
        else:
            # Other Unix-like systems
            base_dir = Path.cwd() / 'logs'
            
        return base_dir
        
    def configure_third_party_loggers(self) -> None:
        """Configure third-party library loggers to reduce noise."""
        # Reduce verbosity of common third-party loggers
        noisy_loggers = [
            'urllib3.connectionpool',
            'requests.packages.urllib3',
            'watchdog.observers.inotify_buffer'
        ]
        
        for logger_name in noisy_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)
            
    def create_operation_logger(self, operation_name: str) -> logging.Logger:
        """
        Create a logger for specific operations with additional context.
        
        Args:
            operation_name: Name of the operation (e.g., 'sync', 'mount', 'download')
            
        Returns:
            Logger with operation context
        """
        logger_name = f"{self.component_name}.{operation_name}"
        logger = logging.getLogger(logger_name)
        
        # Add operation-specific formatting if needed
        return logger


def setup_component_logging(component_name: str, config: Dict[str, Any], 
                          log_dir: Optional[str] = None) -> logging.Logger:
    """
    Convenience function to set up logging for a component.
    
    Args:
        component_name: Name of the component
        config: Configuration dictionary
        log_dir: Optional log directory override
        
    Returns:
        Configured logger
    """
    logging_manager = LoggingManager(component_name, config)
    logger = logging_manager.setup_logging(log_dir)
    logging_manager.configure_third_party_loggers()
    
    return logger