"""
Configuration management for EFIS Data Manager.
Handles loading, validation, migration, and management of YAML configuration files.
Supports environment-specific configurations and secure credential storage.
"""

import os
import yaml
import json
import logging
import platform
import keyring
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import base64
import hashlib

from .validation import ConfigSchema


@dataclass
class WindowsConfig:
    """Windows system configuration."""
    virtualDriveFile: str
    mountTool: str
    driveLetter: str
    logFile: str
    logLevel: str = "INFO"
    syncInterval: int = 1800
    macbookIP: str = "192.168.1.100"
    syncPort: int = 22
    retryAttempts: int = 3
    retryDelay: int = 600
    serviceName: str = "EFISDataManager"
    serviceDisplayName: str = "EFIS Data Manager Service"


@dataclass
class MacOSConfig:
    """macOS system configuration."""
    archivePath: str
    demoPath: str
    logbookPath: str
    logLevel: str = "INFO"
    checkInterval: int = 3600
    navCheckTime: str = "01:00"
    softwareCheckTime: str = "01:30"
    usbMountPath: str = "/Volumes"
    driveIdentifiers: List[str] = None
    userAgent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    requestTimeout: int = 30
    maxRetries: int = 3
    daemonName: str = "com.efis.datamanager"
    pidFile: str = "/tmp/efis_data_manager.pid"
    
    def __post_init__(self):
        if self.driveIdentifiers is None:
            self.driveIdentifiers = ["EFIS_DRIVE", ".efis_marker"]


@dataclass
class GRTUrlConfig:
    """GRT Avionics URL configuration."""
    navDatabase: str
    hxrSoftware: str
    miniAPSoftware: str
    ahrsSoftware: str
    servoSoftware: str


@dataclass
class NotificationConfig:
    """Notification configuration."""
    enabled: bool = True
    email: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.email is None:
            self.email = {
                "enabled": False,
                "smtpServer": "",
                "smtpPort": 587,
                "username": "",
                "password": "",
                "recipient": ""
            }


@dataclass
class EFISConfig:
    """Main EFIS Data Manager configuration."""
    version: str = "1.0.0"
    environment: str = "production"
    windows: WindowsConfig = None
    macos: MacOSConfig = None
    grtUrls: GRTUrlConfig = None
    notifications: NotificationConfig = None
    logging: Dict[str, Any] = None
    transfer: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.logging is None:
            self.logging = {
                "maxBytes": 10485760,
                "backupCount": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "dateFormat": "%Y-%m-%d %H:%M:%S"
            }
        if self.transfer is None:
            self.transfer = {
                "chunkSize": 8192,
                "verifyIntegrity": True,
                "compressionLevel": 6,
                "preserveTimestamps": True
            }


class ConfigMigration:
    """Handles configuration migration between versions."""
    
    MIGRATIONS = {
        "1.0.0": {
            "description": "Initial configuration version",
            "changes": []
        }
    }
    
    @classmethod
    def migrate_config(cls, config: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Migrate configuration from one version to another.
        
        Args:
            config: Configuration dictionary to migrate
            from_version: Source version
            to_version: Target version
            
        Returns:
            Migrated configuration dictionary
        """
        # For now, just update version - add migration logic as needed
        config["version"] = to_version
        return config


class SecureCredentialManager:
    """Manages secure storage of credentials using system keyring."""
    
    def __init__(self, service_name: str = "efis-data-manager"):
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        
    def store_credential(self, key: str, value: str) -> bool:
        """
        Store credential securely in system keyring.
        
        Args:
            key: Credential key/identifier
            value: Credential value to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            keyring.set_password(self.service_name, key, value)
            self.logger.info(f"Credential stored for key: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store credential for key {key}: {e}")
            return False
            
    def get_credential(self, key: str) -> Optional[str]:
        """
        Retrieve credential from system keyring.
        
        Args:
            key: Credential key/identifier
            
        Returns:
            Credential value or None if not found
        """
        try:
            value = keyring.get_password(self.service_name, key)
            if value:
                self.logger.debug(f"Credential retrieved for key: {key}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential for key {key}: {e}")
            return None
            
    def delete_credential(self, key: str) -> bool:
        """
        Delete credential from system keyring.
        
        Args:
            key: Credential key/identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            keyring.delete_password(self.service_name, key)
            self.logger.info(f"Credential deleted for key: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete credential for key {key}: {e}")
            return False


class ConfigManager:
    """Enhanced configuration manager with validation, migration, and secure credentials."""
    
    CONFIG_VERSION = "1.0.0"
    
    def __init__(self, config_path: Optional[str] = None, environment: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default locations.
            environment: Environment name (development, staging, production)
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.environment = environment or os.getenv("EFIS_ENV", "production")
        self._config: Optional[EFISConfig] = None
        self._raw_config = {}
        self.credential_manager = SecureCredentialManager()
        
    def load_config(self, config_file: str = None) -> EFISConfig:
        """
        Load and validate configuration from YAML file with environment support.
        
        Args:
            config_file: Specific config file to load
            
        Returns:
            EFISConfig object containing validated configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
            ValueError: If configuration is invalid
        """
        config_path = self._resolve_config_path(config_file)
        
        if not config_path.exists():
            # Try to create default config if it doesn't exist
            self._create_default_config(config_path)
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._raw_config = yaml.safe_load(f) or {}
                
            # Handle environment-specific overrides
            self._apply_environment_overrides()
            
            # Handle configuration migration if needed
            self._migrate_config_if_needed()
            
            # Load secure credentials
            self._load_secure_credentials()
            
            # Parse into structured config object
            self._config = self._parse_config(self._raw_config)
            
            # Validate configuration
            if not self.validate_config():
                raise ValueError("Configuration validation failed")
                
            self.logger.info(f"Configuration loaded from {config_path} (environment: {self.environment})")
            return self._config
            
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in config file {config_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading config file {config_path}: {e}")
            raise
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key with support for structured config.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'windows.virtualDriveFile')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if self._config is None:
            return default
            
        keys = key.split('.')
        value = asdict(self._config) if hasattr(self._config, '__dict__') else self._raw_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError, AttributeError):
            return default
            
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._raw_config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        # Set the value
        config[keys[-1]] = value
        
        # Rebuild structured config
        self._config = self._parse_config(self._raw_config)
        
    def save_config(self, config_file: str = None) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            config_file: File to save to. If None, uses loaded config path.
        """
        config_path = self._resolve_config_path(config_file)
            
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup of existing config
            if config_path.exists():
                backup_path = config_path.with_suffix(f"{config_path.suffix}.backup")
                config_path.rename(backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._raw_config, f, default_flow_style=False, indent=2)
                
            self.logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving config file {config_path}: {e}")
            raise
            
    def validate_config(self) -> bool:
        """
        Validate current configuration against required schema.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if self._config is None:
            self.logger.error("No configuration loaded")
            return False
            
        errors = []
        
        # Validate platform-specific configurations
        current_platform = platform.system().lower()
        
        if current_platform == "windows":
            if not self._config.windows:
                errors.append("Windows configuration is required on Windows platform")
            else:
                errors.extend(self._validate_windows_config(self._config.windows))
                
        elif current_platform == "darwin":
            if not self._config.macos:
                errors.append("macOS configuration is required on macOS platform")
            else:
                errors.extend(self._validate_macos_config(self._config.macos))
        
        # Validate common configurations
        if self._config.grtUrls:
            errors.extend(self._validate_grt_urls(self._config.grtUrls))
            
        # Log all validation errors
        for error in errors:
            self.logger.error(f"Configuration validation error: {error}")
            
        return len(errors) == 0
    
    def _validate_windows_config(self, config: WindowsConfig) -> List[str]:
        """Validate Windows-specific configuration using schema validation."""
        from dataclasses import asdict
        config_dict = asdict(config)
        return ConfigSchema.validate_section("windows", config_dict)
    
    def _validate_macos_config(self, config: MacOSConfig) -> List[str]:
        """Validate macOS-specific configuration using schema validation."""
        from dataclasses import asdict
        config_dict = asdict(config)
        return ConfigSchema.validate_section("macos", config_dict)
    
    def _validate_grt_urls(self, config: GRTUrlConfig) -> List[str]:
        """Validate GRT URL configuration using schema validation."""
        from dataclasses import asdict
        config_dict = asdict(config)
        return ConfigSchema.validate_section("grtUrls", config_dict)
        
    def get_config(self) -> Optional[EFISConfig]:
        """Get the current configuration object."""
        return self._config
    
    def store_secure_credential(self, key: str, value: str) -> bool:
        """Store a credential securely."""
        return self.credential_manager.store_credential(key, value)
    
    def get_secure_credential(self, key: str) -> Optional[str]:
        """Retrieve a secure credential."""
        return self.credential_manager.get_credential(key)
    
    def delete_secure_credential(self, key: str) -> bool:
        """Delete a secure credential."""
        return self.credential_manager.delete_credential(key)
    
    def _resolve_config_path(self, config_file: str = None) -> Path:
        """Resolve configuration file path."""
        if config_file:
            return Path(config_file)
        elif self.config_path:
            return Path(self.config_path)
        else:
            return self._find_default_config()
    
    def _find_default_config(self) -> Path:
        """Find default configuration file location with environment support."""
        current_dir = Path.cwd()
        
        # Environment-specific config files
        env_config_name = f"efis_config.{self.environment}.yaml"
        
        config_candidates = [
            current_dir / 'config' / env_config_name,
            current_dir / 'config' / 'efis_config.yaml',
            current_dir / env_config_name,
            current_dir / 'efis_config.yaml',
            Path.home() / '.efis' / env_config_name,
            Path.home() / '.efis' / 'config.yaml'
        ]
        
        for candidate in config_candidates:
            if candidate.exists():
                return candidate
                
        # Return environment-specific config as default location
        return config_candidates[0]
    
    def _create_default_config(self, config_path: Path) -> None:
        """Create a default configuration file."""
        self.logger.info(f"Creating default configuration at {config_path}")
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create default configuration based on platform
        current_platform = platform.system().lower()
        
        default_config = {
            "version": self.CONFIG_VERSION,
            "environment": self.environment,
            "logging": {
                "maxBytes": 10485760,
                "backupCount": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "dateFormat": "%Y-%m-%d %H:%M:%S"
            },
            "notifications": {
                "enabled": True,
                "email": {
                    "enabled": False,
                    "smtpServer": "",
                    "smtpPort": 587,
                    "username": "",
                    "password": "",
                    "recipient": ""
                }
            },
            "transfer": {
                "chunkSize": 8192,
                "verifyIntegrity": True,
                "compressionLevel": 6,
                "preserveTimestamps": True
            }
        }
        
        if current_platform == "windows":
            default_config["windows"] = {
                "virtualDriveFile": "C:\\Users\\fligh\\OneDrive\\Desktop\\virtualEFISUSB.vhd",
                "mountTool": "C:\\Program Files\\ImDisk\\MountImg.exe",
                "driveLetter": "E:",
                "logFile": "C:\\Scripts\\MountEFIS.log",
                "logLevel": "INFO",
                "syncInterval": 1800,
                "macbookIP": "192.168.1.100",
                "syncPort": 22,
                "retryAttempts": 3,
                "retryDelay": 600,
                "serviceName": "EFISDataManager",
                "serviceDisplayName": "EFIS Data Manager Service"
            }
        
        if current_platform == "darwin":
            default_config["macos"] = {
                "archivePath": "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB",
                "demoPath": "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO",
                "logbookPath": "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks",
                "logLevel": "INFO",
                "checkInterval": 3600,
                "navCheckTime": "01:00",
                "softwareCheckTime": "01:30",
                "usbMountPath": "/Volumes",
                "driveIdentifiers": ["EFIS_DRIVE", ".efis_marker"],
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "requestTimeout": 30,
                "maxRetries": 3,
                "daemonName": "com.efis.datamanager",
                "pidFile": "/tmp/efis_data_manager.pid"
            }
            
            default_config["grtUrls"] = {
                "navDatabase": "https://grtavionics.com/downloads/nav-database/",
                "hxrSoftware": "https://grtavionics.com/downloads/hxr-software/",
                "miniAPSoftware": "https://grtavionics.com/downloads/mini-ap-software/",
                "ahrsSoftware": "https://grtavionics.com/downloads/ahrs-software/",
                "servoSoftware": "https://grtavionics.com/downloads/servo-software/"
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides."""
        env_overrides = os.getenv("EFIS_CONFIG_OVERRIDES")
        if env_overrides:
            try:
                overrides = json.loads(env_overrides)
                self._merge_config(self._raw_config, overrides)
                self.logger.info("Applied environment configuration overrides")
            except json.JSONDecodeError as e:
                self.logger.warning(f"Invalid environment config overrides: {e}")
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _migrate_config_if_needed(self) -> None:
        """Migrate configuration if version mismatch detected."""
        current_version = self._raw_config.get("version", "1.0.0")
        if current_version != self.CONFIG_VERSION:
            self.logger.info(f"Migrating configuration from {current_version} to {self.CONFIG_VERSION}")
            self._raw_config = ConfigMigration.migrate_config(
                self._raw_config, current_version, self.CONFIG_VERSION
            )
    
    def _load_secure_credentials(self) -> None:
        """Load secure credentials and merge into configuration."""
        # Load email password if configured
        if self._raw_config.get("notifications", {}).get("email", {}).get("enabled"):
            email_password = self.credential_manager.get_credential("email_password")
            if email_password:
                self._raw_config.setdefault("notifications", {}).setdefault("email", {})["password"] = email_password
    
    def _parse_config(self, raw_config: Dict[str, Any]) -> EFISConfig:
        """Parse raw configuration into structured config object."""
        try:
            # Parse Windows config
            windows_config = None
            if "windows" in raw_config:
                windows_data = raw_config["windows"]
                windows_config = WindowsConfig(**windows_data)
            
            # Parse macOS config
            macos_config = None
            if "macos" in raw_config:
                macos_data = raw_config["macos"]
                macos_config = MacOSConfig(**macos_data)
            
            # Parse GRT URLs
            grt_urls = None
            if "grtUrls" in raw_config:
                grt_data = raw_config["grtUrls"]
                grt_urls = GRTUrlConfig(**grt_data)
            
            # Parse notifications
            notifications = NotificationConfig()
            if "notifications" in raw_config:
                notif_data = raw_config["notifications"]
                notifications = NotificationConfig(**notif_data)
            
            # Create main config object
            config = EFISConfig(
                version=raw_config.get("version", self.CONFIG_VERSION),
                environment=raw_config.get("environment", self.environment),
                windows=windows_config,
                macos=macos_config,
                grtUrls=grt_urls,
                notifications=notifications,
                logging=raw_config.get("logging"),
                transfer=raw_config.get("transfer")
            )
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error parsing configuration: {e}")
            raise ValueError(f"Invalid configuration format: {e}")