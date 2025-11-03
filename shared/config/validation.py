"""
Configuration validation schemas and utilities for EFIS Data Manager.
"""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import ipaddress


class ConfigValidator:
    """Validates configuration values against defined schemas."""
    
    @staticmethod
    def validate_path(path: str, must_exist: bool = False, create_parent: bool = False) -> List[str]:
        """
        Validate file or directory path.
        
        Args:
            path: Path to validate
            must_exist: Whether path must already exist
            create_parent: Whether to create parent directory if it doesn't exist
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not path:
            errors.append("Path cannot be empty")
            return errors
        
        try:
            path_obj = Path(path)
            
            if must_exist and not path_obj.exists():
                errors.append(f"Path does not exist: {path}")
            
            if create_parent:
                try:
                    path_obj.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create parent directory for {path}: {e}")
            elif not path_obj.parent.exists():
                errors.append(f"Parent directory does not exist: {path_obj.parent}")
                
        except Exception as e:
            errors.append(f"Invalid path format: {path} - {e}")
        
        return errors
    
    @staticmethod
    def validate_url(url: str) -> List[str]:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not url:
            errors.append("URL cannot be empty")
            return errors
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            errors.append(f"Invalid URL format: {url}")
        
        return errors
    
    @staticmethod
    def validate_ip_address(ip: str) -> List[str]:
        """
        Validate IP address format.
        
        Args:
            ip: IP address to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not ip:
            errors.append("IP address cannot be empty")
            return errors
        
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            errors.append(f"Invalid IP address format: {ip}")
        
        return errors
    
    @staticmethod
    def validate_port(port: int) -> List[str]:
        """
        Validate port number.
        
        Args:
            port: Port number to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not isinstance(port, int):
            errors.append("Port must be an integer")
        elif port < 1 or port > 65535:
            errors.append(f"Port must be between 1 and 65535, got: {port}")
        
        return errors
    
    @staticmethod
    def validate_time_format(time_str: str) -> List[str]:
        """
        Validate time format (HH:MM).
        
        Args:
            time_str: Time string to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not time_str:
            errors.append("Time cannot be empty")
            return errors
        
        time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
        
        if not time_pattern.match(time_str):
            errors.append(f"Invalid time format (expected HH:MM): {time_str}")
        
        return errors
    
    @staticmethod
    def validate_drive_letter(drive_letter: str) -> List[str]:
        """
        Validate Windows drive letter format.
        
        Args:
            drive_letter: Drive letter to validate (e.g., "C:")
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not drive_letter:
            errors.append("Drive letter cannot be empty")
            return errors
        
        drive_pattern = re.compile(r'^[A-Za-z]:$')
        
        if not drive_pattern.match(drive_letter):
            errors.append(f"Invalid drive letter format (expected X:): {drive_letter}")
        
        return errors
    
    @staticmethod
    def validate_interval(interval: int, min_value: int = 1) -> List[str]:
        """
        Validate time interval in seconds.
        
        Args:
            interval: Interval in seconds
            min_value: Minimum allowed value
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not isinstance(interval, int):
            errors.append("Interval must be an integer")
        elif interval < min_value:
            errors.append(f"Interval must be at least {min_value} seconds, got: {interval}")
        
        return errors
    
    @staticmethod
    def validate_log_level(level: str) -> List[str]:
        """
        Validate logging level.
        
        Args:
            level: Log level to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        if not level:
            errors.append("Log level cannot be empty")
        elif level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {level}. Must be one of: {', '.join(valid_levels)}")
        
        return errors
    
    @staticmethod
    def validate_email(email: str) -> List[str]:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not email:
            errors.append("Email address cannot be empty")
            return errors
        
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        if not email_pattern.match(email):
            errors.append(f"Invalid email address format: {email}")
        
        return errors


class ConfigSchema:
    """Defines validation schemas for configuration sections."""
    
    WINDOWS_SCHEMA = {
        "virtualDriveFile": {
            "required": True,
            "validator": lambda x: ConfigValidator.validate_path(x, must_exist=False, create_parent=True)
        },
        "mountTool": {
            "required": True,
            "validator": lambda x: ConfigValidator.validate_path(x, must_exist=True)
        },
        "driveLetter": {
            "required": True,
            "validator": ConfigValidator.validate_drive_letter
        },
        "logFile": {
            "required": True,
            "validator": lambda x: ConfigValidator.validate_path(x, must_exist=False, create_parent=True)
        },
        "logLevel": {
            "required": False,
            "validator": ConfigValidator.validate_log_level
        },
        "syncInterval": {
            "required": False,
            "validator": lambda x: ConfigValidator.validate_interval(x, min_value=60)
        },
        "macbookIP": {
            "required": True,
            "validator": ConfigValidator.validate_ip_address
        },
        "syncPort": {
            "required": False,
            "validator": ConfigValidator.validate_port
        },
        "retryAttempts": {
            "required": False,
            "validator": lambda x: ConfigValidator.validate_interval(x, min_value=1)
        },
        "retryDelay": {
            "required": False,
            "validator": lambda x: ConfigValidator.validate_interval(x, min_value=1)
        }
    }
    
    MACOS_SCHEMA = {
        "archivePath": {
            "required": True,
            "validator": lambda x: ConfigValidator.validate_path(x, must_exist=False, create_parent=True)
        },
        "demoPath": {
            "required": True,
            "validator": lambda x: ConfigValidator.validate_path(x, must_exist=False, create_parent=True)
        },
        "logbookPath": {
            "required": True,
            "validator": lambda x: ConfigValidator.validate_path(x, must_exist=False, create_parent=True)
        },
        "logLevel": {
            "required": False,
            "validator": ConfigValidator.validate_log_level
        },
        "checkInterval": {
            "required": False,
            "validator": lambda x: ConfigValidator.validate_interval(x, min_value=60)
        },
        "navCheckTime": {
            "required": False,
            "validator": ConfigValidator.validate_time_format
        },
        "softwareCheckTime": {
            "required": False,
            "validator": ConfigValidator.validate_time_format
        },
        "requestTimeout": {
            "required": False,
            "validator": lambda x: ConfigValidator.validate_interval(x, min_value=1)
        },
        "maxRetries": {
            "required": False,
            "validator": lambda x: ConfigValidator.validate_interval(x, min_value=1)
        }
    }
    
    GRT_URLS_SCHEMA = {
        "navDatabase": {
            "required": True,
            "validator": ConfigValidator.validate_url
        },
        "hxrSoftware": {
            "required": True,
            "validator": ConfigValidator.validate_url
        },
        "miniAPSoftware": {
            "required": True,
            "validator": ConfigValidator.validate_url
        },
        "ahrsSoftware": {
            "required": True,
            "validator": ConfigValidator.validate_url
        },
        "servoSoftware": {
            "required": True,
            "validator": ConfigValidator.validate_url
        }
    }
    
    @classmethod
    def validate_section(cls, section_name: str, config_data: Dict[str, Any]) -> List[str]:
        """
        Validate a configuration section against its schema.
        
        Args:
            section_name: Name of the configuration section
            config_data: Configuration data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        schema_map = {
            "windows": cls.WINDOWS_SCHEMA,
            "macos": cls.MACOS_SCHEMA,
            "grtUrls": cls.GRT_URLS_SCHEMA
        }
        
        schema = schema_map.get(section_name)
        if not schema:
            return [f"Unknown configuration section: {section_name}"]
        
        errors = []
        
        # Check required fields
        for field_name, field_config in schema.items():
            if field_config["required"] and field_name not in config_data:
                errors.append(f"Missing required field in {section_name}: {field_name}")
                continue
            
            if field_name in config_data:
                field_value = config_data[field_name]
                validator = field_config["validator"]
                
                try:
                    field_errors = validator(field_value)
                    for error in field_errors:
                        errors.append(f"{section_name}.{field_name}: {error}")
                except Exception as e:
                    errors.append(f"{section_name}.{field_name}: Validation error - {e}")
        
        return errors