"""Configuration management for EFIS Data Manager."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class ConfigManager:
    """Manages configuration loading and validation for EFIS Data Manager."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Args:
            config_name: Name of config file (without .json extension)
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if config_name in self._config_cache:
            return self._config_cache[config_name]
            
        config_path = self.config_dir / f"{config_name}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            self._validate_config(config_name, config)
            self._config_cache[config_name] = config
            return config
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {config_path}: {e}")
            
    def get_config_value(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """Get specific configuration value using dot notation.
        
        Args:
            config_name: Name of config file
            key_path: Dot-separated path to config value (e.g., 'sync.interval')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.load_config(config_name)
        
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def _validate_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """Validate configuration structure and required fields.
        
        Args:
            config_name: Name of config being validated
            config: Configuration dictionary to validate
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        if config_name == "windows-config":
            self._validate_windows_config(config)
        elif config_name == "macos-config":
            self._validate_macos_config(config)
            
    def _validate_windows_config(self, config: Dict[str, Any]) -> None:
        """Validate Windows-specific configuration."""
        required_sections = ['virtualDrive', 'sync', 'monitoring', 'logging']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
                
        # Validate virtual drive settings
        vd_config = config['virtualDrive']
        required_vd_keys = ['vhdPath', 'mountTool', 'driveLetter']
        for key in required_vd_keys:
            if key not in vd_config:
                raise ValueError(f"Missing required virtualDrive setting: {key}")
                
    def _validate_macos_config(self, config: Dict[str, Any]) -> None:
        """Validate macOS-specific configuration."""
        required_sections = ['paths', 'grt', 'usb', 'logging']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
                
        # Validate paths
        paths_config = config['paths']
        required_paths = ['archivePath', 'demoPath', 'logbookPath']
        for path_key in required_paths:
            if path_key not in paths_config:
                raise ValueError(f"Missing required path setting: {path_key}")


def get_platform_config() -> Dict[str, Any]:
    """Get configuration for current platform.
    
    Returns:
        Platform-specific configuration dictionary
    """
    config_manager = ConfigManager()
    
    if os.name == 'nt':  # Windows
        return config_manager.load_config('windows-config')
    else:  # macOS/Unix
        return config_manager.load_config('macos-config')


def setup_logging(config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Set up logging based on configuration.
    
    Args:
        config: Configuration dictionary, or None to load from platform config
        
    Returns:
        Configured logger instance
    """
    if config is None:
        config = get_platform_config()
        
    log_config = config.get('logging', {})
    
    # Create logger
    logger = logging.getLogger('efis-data-manager')
    logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    log_file = log_config.get('file', 'efis-data-manager.log')
    if log_file.startswith('~'):
        log_file = os.path.expanduser(log_file)
        
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger