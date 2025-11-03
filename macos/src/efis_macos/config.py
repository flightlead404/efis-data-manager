"""
Configuration management for macOS EFIS Data Manager daemon.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class GRTUrlConfig:
    """Configuration for GRT Avionics URLs."""
    nav_database: str = "https://grtavionics.com/downloads/nav-database/"
    hxr_software: str = "https://grtavionics.com/downloads/hxr-software/"
    mini_ap_software: str = "https://grtavionics.com/downloads/mini-ap-software/"
    ahrs_software: str = "https://grtavionics.com/downloads/ahrs-software/"
    servo_software: str = "https://grtavionics.com/downloads/servo-software/"


@dataclass
class MacOSConfig:
    """Configuration for macOS daemon settings."""
    archive_path: str = "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
    demo_path: str = "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
    logbook_path: str = "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks"
    check_interval: int = 3600  # 1 hour in seconds
    nav_check_time: str = "01:00"  # Daily NAV database check time
    software_check_time: str = "01:30"  # Daily software check time
    grt_urls: GRTUrlConfig = field(default_factory=GRTUrlConfig)
    log_level: str = "INFO"
    log_file: str = "/Users/mwalker/Library/Logs/efis-data-manager.log"
    pid_file: str = "/tmp/efis-macos-daemon.pid"


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[MacOSConfig] = None
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Try multiple locations in order of preference
        possible_paths = [
            os.path.expanduser("~/.config/efis-data-manager/macos-config.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "..", "config", "macos-config.yaml"),
            "/etc/efis-data-manager/macos-config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return the first path as default (will be created if needed)
        return possible_paths[0]
    
    def load_config(self) -> MacOSConfig:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                config_data = {}
                self.logger.info("No configuration file found, using defaults")
            
            # Create config object with defaults, overridden by file data
            self._config = self._create_config_from_dict(config_data)
            
            # Validate and create directories
            self._validate_and_create_paths()
            
            return self._config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            # Return default configuration on error
            self._config = MacOSConfig()
            return self._config
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> MacOSConfig:
        """Create MacOSConfig from dictionary data."""
        # Extract GRT URLs if present
        grt_urls_data = config_data.get('grt_urls', {})
        grt_urls = GRTUrlConfig(
            nav_database=grt_urls_data.get('nav_database', GRTUrlConfig().nav_database),
            hxr_software=grt_urls_data.get('hxr_software', GRTUrlConfig().hxr_software),
            mini_ap_software=grt_urls_data.get('mini_ap_software', GRTUrlConfig().mini_ap_software),
            ahrs_software=grt_urls_data.get('ahrs_software', GRTUrlConfig().ahrs_software),
            servo_software=grt_urls_data.get('servo_software', GRTUrlConfig().servo_software)
        )
        
        # Create main config
        return MacOSConfig(
            archive_path=config_data.get('archive_path', MacOSConfig().archive_path),
            demo_path=config_data.get('demo_path', MacOSConfig().demo_path),
            logbook_path=config_data.get('logbook_path', MacOSConfig().logbook_path),
            check_interval=config_data.get('check_interval', MacOSConfig().check_interval),
            nav_check_time=config_data.get('nav_check_time', MacOSConfig().nav_check_time),
            software_check_time=config_data.get('software_check_time', MacOSConfig().software_check_time),
            grt_urls=grt_urls,
            log_level=config_data.get('log_level', MacOSConfig().log_level),
            log_file=config_data.get('log_file', MacOSConfig().log_file),
            pid_file=config_data.get('pid_file', MacOSConfig().pid_file)
        )
    
    def _validate_and_create_paths(self):
        """Validate configuration and create necessary directories."""
        if not self._config:
            return
        
        # Create directories if they don't exist
        paths_to_create = [
            self._config.archive_path,
            self._config.demo_path,
            self._config.logbook_path,
            os.path.dirname(self._config.log_file),
            os.path.dirname(self._config.pid_file)
        ]
        
        for path in paths_to_create:
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Ensured directory exists: {path}")
            except Exception as e:
                self.logger.warning(f"Could not create directory {path}: {e}")
    
    def save_default_config(self):
        """Save a default configuration file."""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            Path(config_dir).mkdir(parents=True, exist_ok=True)
            
            # Create default config dictionary
            default_config = {
                'archive_path': MacOSConfig().archive_path,
                'demo_path': MacOSConfig().demo_path,
                'logbook_path': MacOSConfig().logbook_path,
                'check_interval': MacOSConfig().check_interval,
                'nav_check_time': MacOSConfig().nav_check_time,
                'software_check_time': MacOSConfig().software_check_time,
                'log_level': MacOSConfig().log_level,
                'log_file': MacOSConfig().log_file,
                'pid_file': MacOSConfig().pid_file,
                'grt_urls': {
                    'nav_database': GRTUrlConfig().nav_database,
                    'hxr_software': GRTUrlConfig().hxr_software,
                    'mini_ap_software': GRTUrlConfig().mini_ap_software,
                    'ahrs_software': GRTUrlConfig().ahrs_software,
                    'servo_software': GRTUrlConfig().servo_software
                }
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Created default configuration file: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving default configuration: {e}")
    
    def get_config(self) -> MacOSConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config