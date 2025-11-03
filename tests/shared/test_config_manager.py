"""
Unit tests for configuration manager.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from shared.config.config_manager import ConfigManager
from shared.config.validation import ConfigValidator


class TestConfigManager:
    """Test cases for ConfigManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.sample_config = {
            'windows': {
                'virtualDriveFile': 'C:\\test\\virtual.vhd',
                'driveLetter': 'E:',
                'syncInterval': 1800,
                'retryAttempts': 3
            },
            'macos': {
                'archivePath': '/Users/test/archive',
                'checkInterval': 3600
            },
            'logging': {
                'logLevel': 'INFO',
                'maxBytes': 1048576,
                'backupCount': 3
            }
        }

    def test_load_config_success(self):
        """Test successful configuration loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.sample_config, f)
            config_path = f.name

        try:
            self.config_manager.load_config(config_path)
            assert self.config_manager.get('windows.driveLetter') == 'E:'
            assert self.config_manager.get('macos.archivePath') == '/Users/test/archive'
        finally:
            Path(config_path).unlink()

    def test_load_config_file_not_found(self):
        """Test configuration loading with missing file."""
        with pytest.raises(FileNotFoundError):
            self.config_manager.load_config('/nonexistent/config.yaml')

    def test_get_nested_key(self):
        """Test getting nested configuration values."""
        self.config_manager._config = self.sample_config
        
        assert self.config_manager.get('windows.virtualDriveFile') == 'C:\\test\\virtual.vhd'
        assert self.config_manager.get('logging.logLevel') == 'INFO'
        assert self.config_manager.get('nonexistent.key') is None

    def test_get_with_default(self):
        """Test getting configuration values with defaults."""
        self.config_manager._config = self.sample_config
        
        assert self.config_manager.get('nonexistent.key', 'default') == 'default'
        assert self.config_manager.get('windows.driveLetter', 'F:') == 'E:'

    def test_set_config_value(self):
        """Test setting configuration values."""
        self.config_manager._config = self.sample_config.copy()
        
        self.config_manager.set('windows.driveLetter', 'F:')
        assert self.config_manager.get('windows.driveLetter') == 'F:'
        
        self.config_manager.set('new.nested.key', 'value')
        assert self.config_manager.get('new.nested.key') == 'value'


class TestConfigValidator:
    """Test cases for ConfigValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ConfigValidator()

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        valid_config = {
            'windows': {
                'virtualDriveFile': 'C:\\test\\virtual.vhd',
                'driveLetter': 'E:',
                'syncInterval': 1800
            },
            'macos': {
                'archivePath': '/Users/test/archive'
            },
            'logging': {
                'logLevel': 'INFO'
            }
        }
        
        result = self.validator.validate(valid_config)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields."""
        invalid_config = {
            'windows': {
                'driveLetter': 'E:'
                # Missing virtualDriveFile
            }
        }
        
        result = self.validator.validate(invalid_config)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any('virtualDriveFile' in error for error in result.errors)

    def test_validate_invalid_drive_letter(self):
        """Test validation with invalid drive letter."""
        invalid_config = {
            'windows': {
                'virtualDriveFile': 'C:\\test\\virtual.vhd',
                'driveLetter': 'INVALID',  # Invalid format
                'syncInterval': 1800
            }
        }
        
        result = self.validator.validate(invalid_config)
        assert not result.is_valid
        assert any('driveLetter' in error for error in result.errors)

    def test_validate_invalid_log_level(self):
        """Test validation with invalid log level."""
        invalid_config = {
            'logging': {
                'logLevel': 'INVALID_LEVEL'
            }
        }
        
        result = self.validator.validate(invalid_config)
        assert not result.is_valid
        assert any('logLevel' in error for error in result.errors)